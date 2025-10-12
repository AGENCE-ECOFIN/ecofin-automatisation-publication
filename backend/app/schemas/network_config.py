from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class NetworkConfigBase(BaseModel):
    network: str
    is_active: bool = True
    default_publication_delay: int = 30
    max_posts_per_day: int = 10
    api_credentials: Optional[Dict] = None
    page_configs: Optional[Dict] = None

    class Config:
        from_attributes = True
        # Permettre la validation même si certains champs sont None
        validate_assignment = True

class NetworkConfigCreate(NetworkConfigBase):
    pass

class NetworkConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    default_publication_delay: Optional[int] = None
    max_posts_per_day: Optional[int] = None
    api_credentials: Optional[Dict] = None
    page_configs: Optional[Dict] = None

class NetworkConfigResponse(NetworkConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

