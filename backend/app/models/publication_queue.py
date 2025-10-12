from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PublicationQueue(Base):
    __tablename__ = "publication_queue"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # NULL pour posts directs
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=True)  # NULL pour posts directs
    network = Column(String, nullable=False)  # facebook, linkedin, x
    target_page_id = Column(String, nullable=True)  # ID de la page de destination
    
    # Contenu à publier
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, nullable=True)  # URLs des médias
    
    # Planification
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statut et contrôle
    status = Column(String, default="PENDING")  # PENDING, SCHEDULED, PUBLISHING, PUBLISHED, FAILED, CANCELLED
    is_paused = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Métadonnées
    error_message = Column(Text, nullable=True)
    publication_url = Column(String, nullable=True)  # URL du post publié
    extra_data = Column(JSON, nullable=True)  # Données supplémentaires
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    post = relationship("Post", back_populates="publication_queue")
    feed = relationship("Feed")