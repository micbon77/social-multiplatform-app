from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import httpx
import os
from urllib.parse import urlencode
import json

from db.database import get_db
from models.models import User, SocialToken
from routes.auth_user import get_current_user

router = APIRouter(prefix="/social", tags=["social-auth"])

# Configurazioni OAuth per ogni piattaforma
OAUTH_CONFIGS = {
    "facebook": {
        "client_id": os.getenv("FACEBOOK_CLIENT_ID"),
        "client_secret": os.getenv("FACEBOOK_CLIENT_SECRET"),
        "redirect_uri": os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/social/callback/facebook"),
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scope": "pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish"
    },
    "instagram": {
        # Instagram usa le stesse credenziali di Facebook
        "client_id": os.getenv("FACEBOOK_CLIENT_ID"),
        "client_secret": os.getenv("FACEBOOK_CLIENT_SECRET"),
        "redirect_uri": os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/social/callback/instagram"),
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scope": "instagram_basic,instagram_content_publish"
    },
    "linkedin": {
        "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
        "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
        "redirect_uri": os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/social/callback/linkedin"),
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "scope": "w_member_social,r_liteprofile,r_emailaddress"
    },
    "twitter": {
        "client_id": os.getenv("TWITTER_CLIENT_ID"),
        "client_secret": os.getenv("TWITTER_CLIENT_SECRET"),
        "redirect_uri": os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/social/callback/twitter"),
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "scope": "tweet.read tweet.write users.read offline.access"
    },
    "tiktok": {
        "client_id": os.getenv("TIKTOK_CLIENT_ID"),
        "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
        "redirect_uri": os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/social/callback/tiktok"),
        "auth_url": "https://www.tiktok.com/auth/authorize/",
        "token_url": "https://open-api.tiktok.com/oauth/access_token/",
        "scope": "user.info.basic,video.publish"
    }
}

class SocialTokenResponse(BaseModel):
    platform: str
    platform_user_id: Optional[str]
    platform_username: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/connect/{platform}")
async def connect_social_platform(
    platform: str,
    current_user: User = Depends(get_current_user)
):
    """Inizia il processo di connessione OAuth per una piattaforma social"""
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform {platform} not supported"
        )
    
    config = OAUTH_CONFIGS[platform]
    
    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth credentials not configured for {platform}"
        )
    
    # Parametri per l'autorizzazione OAuth
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "scope": config["scope"],
        "response_type": "code",
        "state": f"{current_user.id}:{platform}"  # Include user_id e platform nello state
    }
    
    # URL di autorizzazione
    auth_url = f"{config['auth_url']}?{urlencode(params)}"
    
    return {"auth_url": auth_url}

@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Gestisce il callback OAuth e salva il token"""
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform {platform} not supported"
        )
    
    # Estrae user_id dallo state
    try:
        user_id, platform_from_state = state.split(":")
        user_id = int(user_id)
        
        if platform_from_state != platform:
            raise ValueError("Platform mismatch")
            
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Verifica che l'utente esista
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    config = OAUTH_CONFIGS[platform]
    
    # Scambia il code per un access token
    token_data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "code": code,
        "redirect_uri": config["redirect_uri"],
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(config["token_url"], data=token_data)
            response.raise_for_status()
            token_response = response.json()
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {str(e)}"
            )
    
    # Estrae i dati del token
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in")
    token_type = token_response.get("token_type", "Bearer")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received"
        )
    
    # Calcola la data di scadenza
    expires_at = None
    if expires_in:
        expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
    
    # Ottiene informazioni sull'utente della piattaforma
    platform_user_info = await get_platform_user_info(platform, access_token)
    
    # Salva o aggiorna il token nel database
    existing_token = db.query(SocialToken).filter(
        SocialToken.user_id == user_id,
        SocialToken.platform == platform
    ).first()
    
    if existing_token:
        # Aggiorna il token esistente
        existing_token.access_token = access_token
        existing_token.refresh_token = refresh_token
        existing_token.token_type = token_type
        existing_token.expires_at = expires_at
        existing_token.platform_user_id = platform_user_info.get("id")
        existing_token.platform_username = platform_user_info.get("username")
        existing_token.is_active = True
        existing_token.updated_at = datetime.utcnow()
    else:
        # Crea un nuovo token
        new_token = SocialToken(
            user_id=user_id,
            platform=platform,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            expires_at=expires_at,
            scope=config["scope"],
            platform_user_id=platform_user_info.get("id"),
            platform_username=platform_user_info.get("username"),
            is_active=True
        )
        db.add(new_token)
    
    db.commit()
    
    # Redirect al frontend con successo
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/dashboard?connected={platform}")

async def get_platform_user_info(platform: str, access_token: str) -> Dict:
    """Ottiene le informazioni dell'utente dalla piattaforma social"""
    
    user_info_urls = {
        "facebook": "https://graph.facebook.com/me?fields=id,name",
        "instagram": "https://graph.facebook.com/me?fields=id,username",
        "linkedin": "https://api.linkedin.com/v2/people/~",
        "twitter": "https://api.twitter.com/2/users/me",
        "tiktok": "https://open-api.tiktok.com/oauth/userinfo/"
    }
    
    if platform not in user_info_urls:
        return {}
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(user_info_urls[platform], headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            # Normalizza i dati per ogni piattaforma
            if platform == "facebook":
                return {"id": user_data.get("id"), "username": user_data.get("name")}
            elif platform == "instagram":
                return {"id": user_data.get("id"), "username": user_data.get("username")}
            elif platform == "linkedin":
                return {"id": user_data.get("id"), "username": user_data.get("localizedFirstName", "")}
            elif platform == "twitter":
                data = user_data.get("data", {})
                return {"id": data.get("id"), "username": data.get("username")}
            elif platform == "tiktok":
                data = user_data.get("data", {})
                return {"id": data.get("user_id"), "username": data.get("display_name")}
                
        except httpx.HTTPError:
            return {}
    
    return {}

@router.get("/tokens", response_model=List[SocialTokenResponse])
async def get_user_social_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene tutti i token social dell'utente corrente"""
    
    tokens = db.query(SocialToken).filter(
        SocialToken.user_id == current_user.id,
        SocialToken.is_active == True
    ).all()
    
    return tokens

@router.delete("/disconnect/{platform}")
async def disconnect_social_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnette una piattaforma social"""
    
    token = db.query(SocialToken).filter(
        SocialToken.user_id == current_user.id,
        SocialToken.platform == platform
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {platform} connection found"
        )
    
    # Disattiva il token invece di eliminarlo
    token.is_active = False
    token.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Successfully disconnected from {platform}"}

