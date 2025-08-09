from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import json
import os

from db.database import get_db
from models.models import User, SocialToken, Post, PostResult
from routes.auth_user import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])

class PostCreate(BaseModel):
    content: str
    platforms: List[str]
    media_urls: Optional[List[str]] = []
    scheduled_at: Optional[datetime] = None

class PostResponse(BaseModel):
    id: int
    content: str
    platforms: List[str]
    status: str
    created_at: datetime
    published_at: Optional[datetime]
    results: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

@router.post("/create", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea e pubblica un post su multiple piattaforme"""
    
    # Verifica che l'utente abbia i token per le piattaforme richieste
    user_tokens = db.query(SocialToken).filter(
        SocialToken.user_id == current_user.id,
        SocialToken.platform.in_(post_data.platforms),
        SocialToken.is_active == True
    ).all()
    
    available_platforms = [token.platform for token in user_tokens]
    missing_platforms = set(post_data.platforms) - set(available_platforms)
    
    if missing_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing connections for platforms: {', '.join(missing_platforms)}"
        )
    
    # Crea il record del post
    new_post = Post(
        user_id=current_user.id,
        content=post_data.content,
        media_urls=json.dumps(post_data.media_urls) if post_data.media_urls else None,
        platforms=json.dumps(post_data.platforms),
        status="publishing",
        scheduled_at=post_data.scheduled_at
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Se è programmato per il futuro, non pubblicare ora
    if post_data.scheduled_at and post_data.scheduled_at > datetime.utcnow():
        new_post.status = "scheduled"
        db.commit()
        return PostResponse(
            id=new_post.id,
            content=new_post.content,
            platforms=json.loads(new_post.platforms),
            status=new_post.status,
            created_at=new_post.created_at,
            published_at=new_post.published_at,
            results=[]
        )
    
    # Pubblica su ogni piattaforma
    results = []
    success_count = 0
    
    for token in user_tokens:
        if token.platform in post_data.platforms:
            try:
                result = await publish_to_platform(
                    token.platform,
                    token.access_token,
                    post_data.content,
                    post_data.media_urls or []
                )
                
                # Salva il risultato nel database
                post_result = PostResult(
                    post_id=new_post.id,
                    platform=token.platform,
                    platform_post_id=result.get("post_id"),
                    status="success",
                    published_at=datetime.utcnow()
                )
                
                db.add(post_result)
                success_count += 1
                results.append({
                    "platform": token.platform,
                    "status": "success",
                    "post_id": result.get("post_id")
                })
                
            except Exception as e:
                # Salva l'errore nel database
                post_result = PostResult(
                    post_id=new_post.id,
                    platform=token.platform,
                    status="failed",
                    error_message=str(e)
                )
                
                db.add(post_result)
                results.append({
                    "platform": token.platform,
                    "status": "failed",
                    "error": str(e)
                })
    
    # Aggiorna lo status del post
    if success_count == len(post_data.platforms):
        new_post.status = "published"
    elif success_count > 0:
        new_post.status = "partially_published"
    else:
        new_post.status = "failed"
    
    new_post.published_at = datetime.utcnow()
    db.commit()
    
    return PostResponse(
        id=new_post.id,
        content=new_post.content,
        platforms=json.loads(new_post.platforms),
        status=new_post.status,
        created_at=new_post.created_at,
        published_at=new_post.published_at,
        results=results
    )

async def publish_to_platform(platform: str, access_token: str, content: str, media_urls: List[str]) -> Dict[str, Any]:
    """Pubblica contenuto su una specifica piattaforma social"""
    
    if platform == "facebook":
        return await publish_to_facebook(access_token, content, media_urls)
    elif platform == "instagram":
        return await publish_to_instagram(access_token, content, media_urls)
    elif platform == "linkedin":
        return await publish_to_linkedin(access_token, content, media_urls)
    elif platform == "twitter":
        return await publish_to_twitter(access_token, content, media_urls)
    elif platform == "tiktok":
        return await publish_to_tiktok(access_token, content, media_urls)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

async def publish_to_facebook(access_token: str, content: str, media_urls: List[str]) -> Dict[str, Any]:
    """Pubblica su Facebook"""
    
    # Prima ottieni l'ID della pagina Facebook
    async with httpx.AsyncClient() as client:
        # Ottieni le pagine dell'utente
        pages_response = await client.get(
            "https://graph.facebook.com/me/accounts",
            params={"access_token": access_token}
        )
        pages_response.raise_for_status()
        pages_data = pages_response.json()
        
        if not pages_data.get("data"):
            raise Exception("No Facebook pages found")
        
        # Usa la prima pagina disponibile
        page = pages_data["data"][0]
        page_id = page["id"]
        page_access_token = page["access_token"]
        
        # Pubblica il post
        post_data = {
            "message": content,
            "access_token": page_access_token
        }
        
        # Se ci sono media, aggiungi il primo
        if media_urls:
            post_data["link"] = media_urls[0]
        
        response = await client.post(
            f"https://graph.facebook.com/{page_id}/feed",
            data=post_data
        )
        response.raise_for_status()
        result = response.json()
        
        return {"post_id": result.get("id")}

async def publish_to_instagram(access_token: str, content: str, media_urls: List[str]) -> Dict[str, Any]:
    """Pubblica su Instagram"""
    
    async with httpx.AsyncClient() as client:
        # Ottieni l'account Instagram Business collegato
        accounts_response = await client.get(
            "https://graph.facebook.com/me/accounts",
            params={
                "fields": "instagram_business_account",
                "access_token": access_token
            }
        )
        accounts_response.raise_for_status()
        accounts_data = accounts_response.json()
        
        instagram_account_id = None
        for page in accounts_data.get("data", []):
            if page.get("instagram_business_account"):
                instagram_account_id = page["instagram_business_account"]["id"]
                break
        
        if not instagram_account_id:
            raise Exception("No Instagram Business account found")
        
        # Per Instagram, è necessario prima caricare il media, poi pubblicare
        # Questo è un esempio semplificato per post di testo
        if media_urls:
            # Crea un container per il media
            container_data = {
                "image_url": media_urls[0],
                "caption": content,
                "access_token": access_token
            }
            
            container_response = await client.post(
                f"https://graph.facebook.com/{instagram_account_id}/media",
                data=container_data
            )
            container_response.raise_for_status()
            container_result = container_response.json()
            
            # Pubblica il container
            publish_data = {
                "creation_id": container_result["id"],
                "access_token": access_token
            }
            
            publish_response = await client.post(
                f"https://graph.facebook.com/{instagram_account_id}/media_publish",
                data=publish_data
            )
            publish_response.raise_for_status()
            publish_result = publish_response.json()
            
            return {"post_id": publish_result.get("id")}
        else:
            raise Exception("Instagram requires media content")

async def publish_to_linkedin(access_token: str, content: str, media_urls: List[str]) -> Dict[str, Any]:
    """Pubblica su LinkedIn"""
    
    async with httpx.AsyncClient() as client:
        # Ottieni l'ID del profilo
        profile_response = await client.get(
            "https://api.linkedin.com/v2/people/~",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        profile_id = profile_data["id"]
        
        # Prepara il post
        post_data = {
            "author": f"urn:li:person:{profile_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Se ci sono media, aggiungi il link
        if media_urls:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "originalUrl": media_urls[0]
            }]
        
        response = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=post_data
        )
        response.raise_for_status()
        result = response.json()
        
        return {"post_id": result.get("id")}

async def publish_to_twitter(access_token: str, content: str, media_urls: List[str]) -> Dict[str, Any]:
    """Pubblica su Twitter/X"""
    
    async with httpx.AsyncClient() as client:
        post_data = {"text": content}
        
        # Twitter ha un limite di caratteri, tronca se necessario
        if len(content) > 280:
            post_data["text"] = content[:277] + "..."
        
        response = await client.post(
            "https://api.twitter.com/2/tweets",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=post_data
        )
        response.raise_for_status()
        result = response.json()
        
        return {"post_id": result["data"]["id"]}

async def publish_to_tiktok(access_token: str, content: str, media_urls: List[str]) -> Dict[str, Any]:
    """Pubblica su TikTok"""
    
    # TikTok richiede video, non supporta post di solo testo
    if not media_urls:
        raise Exception("TikTok requires video content")
    
    async with httpx.AsyncClient() as client:
        # Questo è un esempio semplificato
        # TikTok API richiede un processo più complesso per il caricamento video
        post_data = {
            "video_url": media_urls[0],
            "text": content,
            "privacy_level": "PUBLIC_TO_EVERYONE"
        }
        
        response = await client.post(
            "https://open-api.tiktok.com/share/video/upload/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=post_data
        )
        response.raise_for_status()
        result = response.json()
        
        return {"post_id": result.get("share_id")}

@router.get("/history")
async def get_post_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Ottiene la cronologia dei post dell'utente"""
    
    posts = db.query(Post).filter(
        Post.user_id == current_user.id
    ).order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for post in posts:
        # Ottieni i risultati per questo post
        post_results = db.query(PostResult).filter(PostResult.post_id == post.id).all()
        
        results = []
        for pr in post_results:
            results.append({
                "platform": pr.platform,
                "status": pr.status,
                "post_id": pr.platform_post_id,
                "error": pr.error_message,
                "published_at": pr.published_at
            })
        
        result.append(PostResponse(
            id=post.id,
            content=post.content,
            platforms=json.loads(post.platforms),
            status=post.status,
            created_at=post.created_at,
            published_at=post.published_at,
            results=results
        ))
    
    return result

