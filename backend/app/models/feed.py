from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    frequency_minutes = Column(Integer, default=60)  # Fréquence en minutes
    custom_prompt = Column(Text, nullable=True)  # Prompt général (déprécié)
    network_prompts = Column(JSON, nullable=True)  # Prompts spécifiques par réseau
    target_networks = Column(JSON, nullable=True)  # ["facebook", "linkedin", "x"]
    # Configuration des temps de publication par réseau (en minutes)
    publication_timing = Column(JSON, nullable=True)  # {"facebook": 30, "linkedin": 60, "x": 15}
    # Configuration des pages de destination par réseau
    social_pages = Column(JSON, nullable=True)  # {"facebook": "page_id", "linkedin": "company_id", "x": "user_id"}
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_fetch = Column(DateTime(timezone=True), nullable=True)

    # Relations
    creator = relationship("User", back_populates="feeds")
    posts = relationship("Post", back_populates="feed")
    publication_queue = relationship("PublicationQueue", back_populates="feed")
