from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PublicationBase(BaseModel):
    network: str
    content: str


class PublicationCreate(PublicationBase):
    post_id: Optional[int] = None  # NULL pour posts directs


class PublicationResponse(PublicationBase):
    id: int
    post_id: Optional[int] = None  # NULL pour posts directs
    feed_id: Optional[int] = None  # NULL pour posts directs
    published_url: Optional[str] = None
    is_success: bool
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedPublicationsResponse(BaseModel):
    items: List[PublicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int



