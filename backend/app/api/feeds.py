from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.feed import FeedCreate, FeedUpdate, FeedResponse
from app.services.feed_service import FeedService
from app.api.dependencies import get_current_user, get_client_info
from app.models.user import User
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/feeds", tags=["feeds"])


class NetworkPromptsUpdate(BaseModel):
    network_prompts: Dict[str, str]


@router.post("/", response_model=FeedResponse)
def create_feed(
    feed: FeedCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feed_service = FeedService(db)
    return feed_service.create_feed(feed, current_user.id)


@router.get("/", response_model=List[FeedResponse])
def get_feeds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère TOUS les flux pour tous les utilisateurs
    Partage global des flux entre tous les utilisateurs
    """
    feed_service = FeedService(db)
    return feed_service.get_feeds()  # Pas de filtre par user_id


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed(
    feed_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feed_service = FeedService(db)
    feed = feed_service.get_feed_by_id(feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flux non trouvé"
        )
    return feed


@router.put("/{feed_id}", response_model=FeedResponse)
def update_feed(
    feed_id: int,
    feed_update: FeedUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feed_service = FeedService(db)
    feed = feed_service.get_feed_by_id(feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flux non trouvé"
        )
    
    # Vérifier que l'utilisateur est le créateur du flux
    if feed.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas le droit de modifier ce flux"
        )
    
    return feed_service.update_feed(feed_id, feed_update)


@router.delete("/{feed_id}")
def delete_feed(
    feed_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feed_service = FeedService(db)
    feed = feed_service.get_feed_by_id(feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flux non trouvé"
        )
    
    # Vérifier que l'utilisateur est le créateur du flux
    if feed.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas le droit de supprimer ce flux"
        )
    
    ip_address, user_agent = get_client_info(request)
    success = feed_service.delete_feed(feed_id, user_id=current_user.id, ip_address=ip_address, user_agent=user_agent)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du flux"
        )
    
    return {"message": "Flux supprimé avec succès"}


@router.put("/{feed_id}/prompts", response_model=FeedResponse)
def update_feed_prompts(
    feed_id: int,
    prompts_update: NetworkPromptsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour les prompts d'un flux RSS"""
    feed_service = FeedService(db)
    feed = feed_service.get_feed_by_id(feed_id)
    
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flux non trouvé"
        )
    
    # Vérifier que l'utilisateur est le créateur du flux
    if feed.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas le droit de modifier ce flux"
        )
    
    # Mettre à jour les prompts
    feed.network_prompts = prompts_update.network_prompts
    db.commit()
    db.refresh(feed)
    
    return feed


@router.get("/status/collections")
def get_collection_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère le statut des collectes en cours"""
    from app.workers.celery_app import celery_app
    from datetime import datetime, timezone, timedelta
    
    # Récupérer les tâches actives
    active_tasks = celery_app.control.inspect().active()
    scheduled_tasks = celery_app.control.inspect().scheduled()
    
    # Récupérer les flux
    feed_service = FeedService(db)
    feeds = feed_service.get_feeds(current_user.id)
    
    # Analyser le statut de chaque flux
    feed_status = []
    for feed in feeds:
        status = {
            'id': feed.id,
            'name': feed.name,
            'url': feed.url,
            'is_active': feed.is_active,
            'last_fetch': feed.last_fetch.isoformat() if feed.last_fetch else None,
            'frequency_minutes': feed.frequency_minutes,
            'collection_status': 'unknown',
            'next_collection_in': None
        }
        
        # Déterminer le statut de collecte
        if not feed.last_fetch:
            status['collection_status'] = 'never_collected'
        else:
            now = datetime.now(timezone.utc)
            last_fetch = feed.last_fetch
            
            # Convertir last_fetch en UTC si nécessaire
            if last_fetch.tzinfo is None:
                last_fetch = last_fetch.replace(tzinfo=timezone.utc)
            else:
                last_fetch = last_fetch.astimezone(timezone.utc)
            
            time_since_last = now - last_fetch
            required_interval = timedelta(minutes=feed.frequency_minutes)
            
            if time_since_last < required_interval:
                status['collection_status'] = 'recent'
                status['next_collection_in'] = str(required_interval - time_since_last)
            elif time_since_last < required_interval * 2:
                status['collection_status'] = 'overdue'
            else:
                status['collection_status'] = 'stale'
        
        feed_status.append(status)
    
    return {
        'feeds': feed_status,
        'active_tasks': active_tasks,
        'scheduled_tasks': scheduled_tasks,
        'worker_status': {
            'active_workers': len(active_tasks) if active_tasks else 0,
            'total_tasks': sum(len(tasks) for tasks in (active_tasks.values() if active_tasks else []))
        }
    }

