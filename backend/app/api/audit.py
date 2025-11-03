"""
API endpoints pour consulter les logs d'audit
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.services.audit_service import AuditService
from app.models.user import User
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    description: Optional[str]
    action_metadata: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogsListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


@router.get("/", response_model=AuditLogsListResponse)
def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filtrer par utilisateur"),
    entity_type: Optional[str] = Query(None, description="Filtrer par type d'entité"),
    entity_id: Optional[int] = Query(None, description="Filtrer par ID d'entité"),
    action: Optional[str] = Query(None, description="Filtrer par action"),
    limit: int = Query(50, ge=1, le=100, description="Nombre de résultats"),
    offset: int = Query(0, ge=0, description="Offset pour pagination"),
    current_user: User = Depends(get_current_admin_user),  # Seuls les admins peuvent voir les logs
    db: Session = Depends(get_db)
):
    """Récupère les logs d'audit avec filtres et pagination (admin seulement)"""
    audit_service = AuditService(db)
    result = audit_service.get_logs(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit,
        offset=offset
    )
    
    return result


@router.get("/summary", response_model=dict)
def get_audit_summary(
    current_user: User = Depends(get_current_admin_user),  # Seuls les admins peuvent voir les logs
    db: Session = Depends(get_db)
):
    """Récupère un résumé des logs d'audit (admin seulement)"""
    audit_service = AuditService(db)
    
    # Récupérer les logs récents pour le résumé
    result = audit_service.get_logs(limit=1000)
    logs = result.get("logs", [])
    
    # Compter par action
    action_counts = {}
    entity_type_counts = {}
    user_counts = {}
    
    for log in logs:
        # Compter par action
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        # Compter par type d'entité
        entity_type_counts[log.entity_type] = entity_type_counts.get(log.entity_type, 0) + 1
        
        # Compter par utilisateur
        username = log.username or "Système"
        user_counts[username] = user_counts.get(username, 0) + 1
    
    return {
        "total_logs": result.get("total", len(logs)),
        "action_counts": action_counts,
        "entity_type_counts": entity_type_counts,
        "top_users": dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    }

