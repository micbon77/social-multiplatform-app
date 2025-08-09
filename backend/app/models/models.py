from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relazione con i token social
    social_tokens = relationship("SocialToken", back_populates="user")

class SocialToken(Base):
    __tablename__ = "social_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String, nullable=False)  # facebook, instagram, linkedin, tiktok, twitter
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String, default="Bearer")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(String, nullable=True)
    platform_user_id = Column(String, nullable=True)  # ID dell'utente sulla piattaforma social
    platform_username = Column(String, nullable=True)  # Username sulla piattaforma social
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relazione con l'utente
    user = relationship("User", back_populates="social_tokens")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    media_urls = Column(Text, nullable=True)  # JSON string con URLs dei media
    platforms = Column(String, nullable=False)  # JSON string con le piattaforme selezionate
    status = Column(String, default="draft")  # draft, published, failed
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relazione con l'utente
    user = relationship("User")

class PostResult(Base):
    __tablename__ = "post_results"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    platform = Column(String, nullable=False)
    platform_post_id = Column(String, nullable=True)  # ID del post sulla piattaforma
    status = Column(String, nullable=False)  # success, failed
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relazione con il post
    post = relationship("Post")

