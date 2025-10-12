from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class NetworkConfig(Base):
    __tablename__ = "network_configs"

    id = Column(Integer, primary_key=True, index=True)
    network = Column(String, nullable=False, unique=True)  # facebook, linkedin, x
    is_active = Column(Boolean, default=True)
    
    # Configuration globale du réseau
    default_publication_delay = Column(Integer, default=30)  # Délai par défaut en minutes
    api_credentials = Column(JSON, nullable=True)  # Clés API, tokens, etc.
    page_configs = Column(JSON, nullable=True)  # Configuration des pages disponibles
    
    # Paramètres de publication
    max_posts_per_day = Column(Integer, default=10)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())