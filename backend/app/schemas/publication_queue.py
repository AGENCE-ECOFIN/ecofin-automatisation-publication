from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class PublicationQueueBase(BaseModel):
    post_id: Optional[int] = None  # None pour les posts directs
    feed_id: Optional[int] = None  # None pour les posts directs
    network: str
    target_page_id: Optional[str] = None
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    status: str = "PENDING"  # PENDING, SCHEDULED, PUBLISHING, PUBLISHED, FAILED, CANCELLED
    is_paused: bool = False
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    publication_url: Optional[str] = None
    extra_data: Optional[Dict] = None

class PublicationQueueCreate(PublicationQueueBase):
    pass

class PublicationQueueUpdate(BaseModel):
    status: Optional[str] = None
    is_paused: Optional[bool] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    publication_url: Optional[str] = None
    retry_count: Optional[int] = None

class PublicationQueueResponse(PublicationQueueBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedPublicationQueueResponse(BaseModel):
    items: List[PublicationQueueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
