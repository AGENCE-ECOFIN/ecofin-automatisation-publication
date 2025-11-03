from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL pour actions système
    username = Column(String, nullable=True)  # Stocké pour traçabilité même si user supprimé
    
    # Action effectuée
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, VALIDATE, REJECT, PUBLISH, etc.
    entity_type = Column(String, nullable=False, index=True)  # post, feed, queue, user, etc.
    entity_id = Column(Integer, nullable=True, index=True)  # ID de l'entité concernée
    
    # Détails
    description = Column(Text, nullable=True)  # Description lisible de l'action
    action_metadata = Column(JSON, nullable=True)  # Détails supplémentaires (anciennes valeurs, nouvelles valeurs, etc.)
    
    # IP et user agent pour sécurité
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relations
    user = relationship("User", foreign_keys=[user_id])

