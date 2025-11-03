from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Optional, Dict, Any
from datetime import datetime


class AuditService:
    """Service pour enregistrer les actions des utilisateurs dans le système"""
    
    # Actions importantes à logger (uniquement les actions manuelles)
    IMPORTANT_ACTIONS = {
        # Posts
        'POST_VALIDATE',      # Validation d'un post/réseau
        'POST_MODIFY',        # Modification d'un post
        'POST_REJECT',        # Rejet d'un post/réseau
        'POST_RESTORE',       # Restauration d'un post
        'POST_CREATE',        # Création d'un post direct
        'POST_DELETE',        # Suppression d'un post
        
        # Feeds
        'FEED_CREATE',        # Création d'un flux RSS
        'FEED_DELETE',        # Suppression d'un flux RSS
        
        # Configurations
        'CONFIG_UPDATE',      # Modification de config globale
        
        # Authentification
        'USER_LOGIN',         # Connexion
        'USER_LOGOUT'         # Déconnexion
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        action: str,
        entity_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        entity_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Enregistre une action dans le journal d'audit (uniquement les actions importantes)
        
        Args:
            action: Type d'action (POST_VALIDATE, POST_REJECT, FEED_CREATE, USER_LOGIN, etc.)
            entity_type: Type d'entité (post, feed, config, user, etc.)
            user_id: ID de l'utilisateur (None pour actions système)
            username: Nom d'utilisateur (pour traçabilité même si user supprimé)
            entity_id: ID de l'entité concernée
            description: Description lisible de l'action
            metadata: Détails supplémentaires (JSON)
            ip_address: Adresse IP de l'utilisateur
            user_agent: User agent du navigateur
        
        Returns:
            AuditLog créé ou None si action non importante
        """
        # Ne logger que les actions importantes
        if action not in self.IMPORTANT_ACTIONS:
            return None
        
        try:
            # Si user_id fourni mais pas username, récupérer le username
            if user_id and not username:
                from app.models.user import User
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    username = user.username
            
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                action_metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            print(f"📝 [AUDIT] {action} {entity_type} #{entity_id} par {username or 'SYSTEM'}")
            return audit_log
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ [AUDIT] Erreur lors de l'enregistrement: {e}")
            # Ne pas bloquer l'application si l'audit échoue
            return None
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """
        Récupère les logs d'audit avec filtres et pagination
        
        Args:
            user_id: Filtrer par utilisateur
            entity_type: Filtrer par type d'entité
            entity_id: Filtrer par ID d'entité
            action: Filtrer par action
            limit: Nombre de résultats max
            offset: Offset pour pagination
        
        Returns:
            Dict avec logs, total, limit, offset
        """
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if action:
            query = query.filter(AuditLog.action == action)
        
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }

