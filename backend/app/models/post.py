from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String, nullable=True)
    source_image = Column(String, nullable=True)
    generated_content = Column(JSON, nullable=True)  # {facebook, linkedin, x}
    network_validations = Column(JSON, nullable=True)  # {facebook: {status, validated_by, validated_at}, ...}
    status = Column(String, default="draft")  # draft, validated, published, rejected
    feed_id = Column(Integer, ForeignKey("feeds.id"))
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    feed = relationship("Feed", back_populates="posts")
    validator = relationship("User", foreign_keys=[validated_by])
    
    # Contrainte unique pour éviter les doublons
    __table_args__ = (
        UniqueConstraint('source_url', name='unique_source_url'),
    )
