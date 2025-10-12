from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.publication_queue import PublicationQueue
from app.models.network_config import NetworkConfig
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/direct-post", tags=["direct-post"])


class DirectPostRequest(BaseModel):
    network: str
    content: str
    target_page_id: str
    media_urls: Optional[list] = None


@router.post("/")
def create_direct_post(
    post_data: DirectPostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un post direct qui sera ajouté à la file de publication
    """
    try:
        # Récupérer la config globale du réseau pour le délai
        network_config = db.query(NetworkConfig).filter(
            NetworkConfig.network == post_data.network,
            NetworkConfig.is_active == True
        ).first()
        
        if not network_config:
            raise HTTPException(
                status_code=400,
                detail=f"Réseau {post_data.network} non configuré ou inactif"
            )
        
        delay_minutes = network_config.default_publication_delay
        now = datetime.now(timezone.utc)
        
        # Vérifier s'il y a d'autres posts programmés sur ce réseau
        # Pour un post direct, on utilise feed_id = 0 pour le différencier
        last_scheduled = db.query(PublicationQueue).filter(
            PublicationQueue.network == post_data.network,
            PublicationQueue.status.in_(['PENDING', 'PUBLISHING'])
        ).order_by(PublicationQueue.scheduled_at.desc()).first()
        
        if last_scheduled and last_scheduled.scheduled_at:
            scheduled_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
            print(f"🔄 FIFO: Post direct sur {post_data.network} programmé après le dernier post")
        else:
            scheduled_time = now + timedelta(minutes=delay_minutes)
            print(f"✨ Premier post sur {post_data.network}")
        
        # Créer l'item dans la file
        queue_item = PublicationQueue(
            post_id=None,  # Post direct, pas lié à un article RSS
            feed_id=None,
            network=post_data.network,
            content=post_data.content,
            media_urls=post_data.media_urls or [],
            scheduled_at=scheduled_time,
            target_page_id=post_data.target_page_id,
            status="PENDING",
            is_paused=False
        )
        
        db.add(queue_item)
        db.commit()
        db.refresh(queue_item)
        
        return {
            "message": "Post direct créé avec succès",
            "queue_item_id": queue_item.id,
            "scheduled_at": queue_item.scheduled_at.isoformat(),
            "network": queue_item.network
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur création post direct: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

