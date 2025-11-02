from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class PostBase(BaseModel):
    title: str
    content: str
    source_url: Optional[HttpUrl] = None
    source_image: Optional[str] = None


class PostCreate(PostBase):
    feed_id: int


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    source_image: Optional[str] = None
    status: Optional[str] = None
    generated_content: Optional[dict] = None


class PostValidate(BaseModel):
    generated_content: dict

class NetworkValidationRequest(BaseModel):
    network: str
    action: str  # 'validate' ou 'reject'
    rejection_reason: Optional[str] = None

class PostRejectRequest(BaseModel):
    rejection_reason: Optional[str] = None
    
    class Config:
        # Permettre un body vide (tous les champs sont optionnels)
        extra = "forbid"


class FeedInfo(BaseModel):
    id: int
    name: str
    target_networks: Optional[List[str]] = None
    social_pages: Optional[Dict[str, str]] = None
    publication_timing: Optional[Dict[str, int]] = None

    class Config:
        from_attributes = True


class PostResponse(PostBase):
    id: int
    feed_id: int
    feed: Optional[FeedInfo] = None  # Inclure le feed complet
    status: str
    generated_content: Optional[dict] = None
    network_validations: Optional[dict] = None
    validated_by: Optional[int] = None
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostQueue(BaseModel):
    id: int
    title: str
    content: str
    generated_content: str
    feed_id: int
    validated_at: datetime

    class Config:
        from_attributes = True
