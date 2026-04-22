from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # NULL pour certains enregistrements directs
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=True)  # NULL pour posts directs
    network = Column(String, nullable=False)  # facebook, linkedin, x
    content = Column(Text, nullable=False)
    published_url = Column(String, nullable=True)
    is_success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    media_urls = Column(JSON, nullable=True)  # URLs des images MinIO
    # extra_data sera ajouté par migration - temporairement commenté
    # extra_data = Column(JSON, nullable=True)  # Données supplémentaires (postSubmissionId, etc.)

    # Relations
    feed = relationship("Feed")

