from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict, Union, List
from datetime import datetime


class FeedBase(BaseModel):
    name: str
    url: Union[HttpUrl, str]
    frequency_minutes: int = 60
    custom_prompt: Optional[str] = None  # Prompt général (déprécié)
    network_prompts: Optional[Dict[str, str]] = None  # Prompts spécifiques par réseau
    target_networks: Optional[List[str]] = None
    publication_timing: Optional[Dict[str, int]] = None  # {"facebook": 30, "linkedin": 60, "x": 15}
    social_pages: Optional[Dict[str, str]] = None  # {"facebook": "page_id", "linkedin": "company_id", "x": "user_id"}

    @field_validator('url', mode='before')
    @classmethod
    def validate_url(cls, v):
        if isinstance(v, str):
            return v
        return str(v)


class FeedCreate(FeedBase):
    pass


class FeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[Union[HttpUrl, str]] = None
    frequency_minutes: Optional[int] = None
    custom_prompt: Optional[str] = None
    network_prompts: Optional[Dict[str, str]] = None
    target_networks: Optional[List[str]] = None
    publication_timing: Optional[Dict[str, int]] = None
    social_pages: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

    @field_validator('url', mode='before')
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v
        return str(v)


class FeedResponse(FeedBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_fetch: Optional[datetime] = None

    class Config:
        from_attributes = True
