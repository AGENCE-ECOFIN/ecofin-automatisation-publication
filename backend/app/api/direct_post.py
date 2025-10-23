from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.publication_queue import PublicationQueue
from app.models.network_config import NetworkConfig
from app.services.blotato_service import BlotatoService
from app.services.schedule_service import ScheduleService
from datetime import datetime, timezone, timedelta

router = APIRouter()

class DirectPostRequest(BaseModel):
    network: str
    content: str
    target_page_id: str
    media_urls: Optional[List[str]] = []
    force_immediate: Optional[bool] = False  # Forcer publication immédiate même si pas optimal
    scheduled_at: Optional[datetime] = None  # Date/heure de programmation personnalisée
    schedule_type: Optional[str] = "auto"  # "auto", "immediate", "scheduled"

async def _publish_immediately(post_data: DirectPostRequest, db: Session, user_id: int):
    """Publication immédiate d'un post direct"""
    try:
        blotato_service = BlotatoService()
        
        success, message, publication_url = blotato_service.publish_to_network(
            network=post_data.network,
            content=post_data.content,
            media_urls=post_data.media_urls or [],
            target_page_id=post_data.target_page_id
        )
        
        if success:
            # Enregistrer dans l'historique
            from app.models.publication import Publication
            publication = Publication(
                post_id=None,  # Post direct
                feed_id=None,  # Post direct
                network=post_data.network,
                content=post_data.content,
                published_url=publication_url,
                is_success=True,
                published_at=datetime.now(timezone.utc)
            )
            db.add(publication)
            db.commit()
            
            return {
                "message": "✅ Post publié IMMÉDIATEMENT avec succès !",
                "success": True,
                "publication_url": publication_url,
                "network": post_data.network,
                "published_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Enregistrer l'échec
            from app.models.publication import Publication
            publication = Publication(
                post_id=None,
                feed_id=None,
                network=post_data.network,
                content=post_data.content,
                published_url=None,
                is_success=False,
                error_message=message,
                published_at=datetime.now(timezone.utc)
            )
            db.add(publication)
            db.commit()
            
            raise HTTPException(status_code=400, detail=f"Erreur de publication: {message}")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

async def _add_to_queue_with_priority(post_data: DirectPostRequest, db: Session, user_id: int, reasons: List[str]):
    """Ajouter un post direct à la queue avec priorité"""
    try:
        # Calculer l'heure de programmation avec priorité
        now = datetime.now(timezone.utc)
        
        # Posts directs ont priorité - programmer immédiatement si horaires OK
        schedule_service = ScheduleService(db)
        config = schedule_service.get_active_config_for_network_now(post_data.network)
        
        if config and config.is_active:
            # Programmer à l'heure d'ouverture si on est avant
            start_hour = config.start_time.hour
            start_min = config.start_time.minute
            today_start = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            
            if now < today_start:
                scheduled_time = today_start
                status = "SCHEDULED"
            else:
                # Programmer immédiatement (priorité)
                scheduled_time = now
                status = "PENDING"
        else:
            # Pas de config horaire, programmer immédiatement
            scheduled_time = now
            status = "PENDING"
        
        # Créer l'entrée dans la queue avec priorité
        queue_item = PublicationQueue(
            post_id=None,  # Post direct
            feed_id=None,  # Post direct
            network=post_data.network,
            content=post_data.content,
            media_urls=post_data.media_urls,
            scheduled_at=scheduled_time,
            target_page_id=post_data.target_page_id,
            status=status,
            is_paused=False,
            extra_data={
                "is_direct_post": True,
                "created_by": user_id,
                "reasons_not_immediate": reasons
            }
        )
        db.add(queue_item)
        db.commit()
        db.refresh(queue_item)
        
        return {
            "message": f"📅 Post ajouté à la queue avec PRIORITÉ (ID: {queue_item.id})",
            "success": True,
            "queue_id": queue_item.id,
            "scheduled_at": scheduled_time.isoformat(),
            "status": status,
            "reasons_not_immediate": reasons,
            "can_force_immediate": True
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur ajout queue: {str(e)}")

async def _add_to_queue_with_custom_schedule(post_data: DirectPostRequest, db: Session, user_id: int):
    """Ajouter un post direct à la queue avec programmation personnalisée"""
    try:
        # Vérifier que la date programmée est dans le futur
        now = datetime.now(timezone.utc)
        if post_data.scheduled_at <= now:
            raise HTTPException(status_code=400, detail="La date de programmation doit être dans le futur")
        
        # Vérifier les horaires de publication pour la date programmée
        schedule_service = ScheduleService(db)
        # Note: Ici on pourrait ajouter une vérification plus sophistiquée des horaires
        
        # Créer l'entrée dans la queue avec programmation personnalisée
        queue_item = PublicationQueue(
            post_id=None,  # Post direct
            feed_id=None,  # Post direct
            network=post_data.network,
            content=post_data.content,
            media_urls=post_data.media_urls,
            scheduled_at=post_data.scheduled_at,
            target_page_id=post_data.target_page_id,
            status="SCHEDULED",
            is_paused=False,
            extra_data={
                "is_direct_post": True,
                "created_by": user_id,
                "schedule_type": "custom",
                "scheduled_by_user": True
            }
        )
        db.add(queue_item)
        db.commit()
        db.refresh(queue_item)
        
        return {
            "message": f"Post programmé avec succès pour le {post_data.scheduled_at.strftime('%d/%m/%Y à %H:%M')}",
            "queue_id": queue_item.id,
            "scheduled_at": post_data.scheduled_at,
            "status": "SCHEDULED"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur programmation personnalisée: {str(e)}")

@router.post("/direct-post/")
async def create_direct_post(
    post_data: DirectPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer un post direct avec logique de priorité :
    1. Vérifier si peut publier immédiatement (délai + horaires)
    2. Si OUI → Publication directe
    3. Si NON → Expliquer pourquoi + option publication immédiate
    4. Sinon → Queue avec priorité (sortent en premier)
    """
    try:
        print(f"\n📤 POST DIRECT sur {post_data.network}")
        
        # 1. Vérifier la configuration du réseau
        network_config = db.query(NetworkConfig).filter(
            NetworkConfig.network == post_data.network,
            NetworkConfig.is_active == True
        ).first()
        
        if not network_config:
            raise HTTPException(status_code=400, detail=f"Réseau {post_data.network} non configuré")
        
        # 2. Vérifier les horaires et délais
        schedule_service = ScheduleService(db)
        schedule_status = schedule_service.is_publication_allowed_now(post_data.network)
        delay_minutes = network_config.default_publication_delay
        
        # 3. Vérifier le dernier post programmé sur ce réseau
        last_scheduled = db.query(PublicationQueue).filter(
            PublicationQueue.network == post_data.network,
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
        ).order_by(PublicationQueue.scheduled_at.desc()).first()
        
        now = datetime.now(timezone.utc)
        
        # 4. Calculer si on peut publier immédiatement
        can_publish_immediately = True
        reason_not_immediate = []
        
        # Vérifier horaires
        if not schedule_status["allowed"]:
            can_publish_immediately = False
            reason_not_immediate.append(f"Horaires fermés ({schedule_status['reason']})")
        
        # Vérifier délai depuis dernier post
        if last_scheduled and last_scheduled.scheduled_at:
            time_since_last = now - last_scheduled.scheduled_at
            required_delay = timedelta(minutes=delay_minutes)
            if time_since_last < required_delay:
                can_publish_immediately = False
                remaining_delay = required_delay - time_since_last
                reason_not_immediate.append(f"Délai insuffisant (il faut attendre {remaining_delay})")
        
        # 5. Décision de publication selon le type de planification
        if post_data.schedule_type == "immediate" or post_data.force_immediate:
            # Publication immédiate
            print(f"🚀 Publication IMMÉDIATE sur {post_data.network}")
            return await _publish_immediately(post_data, db, current_user.id)
        elif post_data.schedule_type == "scheduled" and post_data.scheduled_at:
            # Programmation personnalisée
            print(f"📅 Programmation PERSONNALISÉE sur {post_data.network} pour {post_data.scheduled_at}")
            return await _add_to_queue_with_custom_schedule(post_data, db, current_user.id)
        else:
            # Par défaut, essayer de publier immédiatement si possible, sinon ajouter à la queue
            if can_publish_immediately:
                print(f"🚀 Publication IMMÉDIATE (défaut) sur {post_data.network}")
                return await _publish_immediately(post_data, db, current_user.id)
            else:
                print(f"⏳ Ajout à la queue (défaut) sur {post_data.network}")
                return await _add_to_queue_with_priority(post_data, db, current_user.id, reason_not_immediate)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur inattendue: {str(e)}")