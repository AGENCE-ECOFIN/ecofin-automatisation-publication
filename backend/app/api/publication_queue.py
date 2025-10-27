from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.publication_queue import PublicationQueue
from app.schemas.publication_queue import PublicationQueueResponse, PublicationQueueUpdate
from app.services.publication_queue_service import PublicationQueueService

router = APIRouter()

@router.get("/", response_model=List[PublicationQueueResponse])
def get_publication_queue(
    status: Optional[str] = None,
    network: Optional[str] = None,
    feed_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère la file d'attente de publication avec filtres optionnels"""
    queue_service = PublicationQueueService(db)
    filters = {}
    if status:
        filters['status'] = status
    if network:
        filters['network'] = network
    if feed_id:
        filters['feed_id'] = feed_id
    
    queue_items = queue_service.get_queue_items(filters)
    return queue_items

@router.get("/{item_id}", response_model=PublicationQueueResponse)
def get_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère un élément spécifique de la file d'attente"""
    item = db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément de la file d'attente non trouvé"
        )
    return item

@router.put("/{item_id}/pause")
def pause_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met en pause un élément de la file d'attente"""
    from datetime import datetime, timezone
    
    item = db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément de la file d'attente non trouvé"
        )
    
    if item.status not in ["PENDING", "SCHEDULED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de mettre en pause cet élément"
        )
    
    # Calculer le temps restant en secondes
    now = datetime.now(timezone.utc)
    if item.scheduled_at:
        remaining_seconds = int((item.scheduled_at - now).total_seconds())
        
        # Sauvegarder le temps restant dans extra_data
        extra_data = item.extra_data or {}
        extra_data['paused_at'] = now.isoformat()
        extra_data['remaining_seconds'] = max(0, remaining_seconds)  # Pas de valeur négative
        item.extra_data = extra_data
        
        print(f"⏸️ Pause item #{item_id}: {remaining_seconds}s restantes sauvegardées")
    
    item.is_paused = True
    db.commit()
    
    return {"message": "Élément mis en pause avec succès"}

@router.put("/{item_id}/resume")
def resume_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprend un élément de la file d'attente"""
    from datetime import datetime, timezone, timedelta
    
    item = db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément de la file d'attente non trouvé"
        )
    
    if not item.is_paused:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet élément n'est pas en pause"
        )
    
    # Récupérer le temps restant sauvegardé lors de la pause
    extra_data = item.extra_data or {}
    remaining_seconds = extra_data.get('remaining_seconds', 300)  # Default 5 min si pas sauvegardé
    
    # Recalculer scheduled_at = maintenant + temps restant
    now = datetime.now(timezone.utc)
    new_scheduled_time = now + timedelta(seconds=remaining_seconds)
    
    # 🔄 VÉRIFIER LES HORAIRES : Si la reprise est hors horaires, ajuster
    from app.services.schedule_service import ScheduleService
    schedule_service = ScheduleService(db)
    adjusted_time = schedule_service._adjust_time_to_schedule(item.network, new_scheduled_time)
    
    # Si l'heure a été ajustée (hors horaires), recalculer le statut
    if adjusted_time != new_scheduled_time:
        print(f"   🕐 Reprise hors horaires: {new_scheduled_time.strftime('%H:%M')} → {adjusted_time.strftime('%H:%M')}")
        config = schedule_service.get_active_config_for_network_now(item.network)
        if config and config.is_active:
            if config.is_time_in_range(adjusted_time.hour, adjusted_time.minute):
                item.status = "SCHEDULED"
            else:
                item.status = "WAITING_HOURS"
        else:
            item.status = "SCHEDULED"
    else:
        # Reprise dans les horaires, peut être publié immédiatement
        item.status = "PENDING"
    
    item.scheduled_at = adjusted_time
    item.is_paused = False
    
    # Nettoyer les données de pause
    if 'paused_at' in extra_data:
        del extra_data['paused_at']
    if 'remaining_seconds' in extra_data:
        del extra_data['remaining_seconds']
    item.extra_data = extra_data if extra_data else None
    
    db.commit()
    
    print(f"▶️ Reprise item #{item_id}: reprogrammé dans {remaining_seconds}s (à {item.scheduled_at.strftime('%H:%M:%S')})")
    
    return {"message": f"Élément repris avec succès - programmé dans {remaining_seconds//60}min {remaining_seconds%60}s"}

@router.put("/{item_id}/cancel")
def cancel_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annule un élément de la file d'attente"""
    item = db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément de la file d'attente non trouvé"
        )
    
    if item.status in ["PUBLISHED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'annuler cet élément"
        )
    
    item.status = "CANCELLED"
    db.commit()
    
    return {"message": "Élément annulé avec succès"}

@router.put("/{item_id}/retry")
def retry_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Réessaie un élément de la file d'attente"""
    item = db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément de la file d'attente non trouvé"
        )
    
    if item.status != "FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les éléments en échec peuvent être réessayés"
        )
    
    if item.retry_count >= item.max_retries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre maximum de tentatives atteint"
        )
    
    item.status = "PENDING"
    item.retry_count += 1
    item.error_message = None
    db.commit()
    
    return {"message": "Élément programmé pour un nouvel essai"}

@router.post("/add-validated-posts")
def add_validated_posts_to_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajoute automatiquement tous les posts validés à la file d'attente"""
    from app.models.post import Post
    
    # Récupérer tous les posts validés qui ne sont pas déjà dans la file d'attente
    validated_posts = db.query(Post).filter(Post.status == "validated").all()
    
    queue_service = PublicationQueueService(db)
    added_items = []
    
    for post in validated_posts:
        try:
            items = queue_service.add_post_to_queue(post.id)
            added_items.extend(items)
        except Exception as e:
            print(f"Erreur lors de l'ajout du post {post.id}: {e}")
            continue
    
    return {
        "message": f"{len(added_items)} éléments ajoutés à la file d'attente",
        "added_count": len(added_items)
    }

@router.post("/recalculate-schedule")
def recalculate_queue_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculer les heures de publication en respectant les délais cumulés par feed et réseau"""
    try:
        from app.models.feed import Feed
        from app.services.schedule_service import ScheduleService
        from datetime import datetime, timedelta, timezone
        
        print("🔄 Recalcul des heures de publication avec délais cumulés...")
        
        # Récupérer tous les posts programmés, groupés par feed et réseau
        scheduled_posts = db.query(PublicationQueue).filter(
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING'])
        ).order_by(PublicationQueue.feed_id, PublicationQueue.network, PublicationQueue.created_at).all()
        
        # Grouper par feed_id et network
        posts_by_feed_network = {}
        for post in scheduled_posts:
            key = (post.feed_id, post.network)
            if key not in posts_by_feed_network:
                posts_by_feed_network[key] = []
            posts_by_feed_network[key].append(post)
        
        schedule_service = ScheduleService(db)
        now = datetime.now(timezone.utc)
        recalculated_count = 0
        
        for (feed_id, network), posts in posts_by_feed_network.items():
            print(f"\n📊 Feed #{feed_id} - {network}: {len(posts)} posts à recalculer")
            
            # Récupérer le délai configuré pour ce réseau (depuis NetworkConfig)
            from app.models.network_config import NetworkConfig
            network_config = db.query(NetworkConfig).filter(
                NetworkConfig.network == network,
                NetworkConfig.is_active == True
            ).first()
            delay_minutes = network_config.default_publication_delay if network_config else 30
            
            print(f"   Délai configuré: {delay_minutes} minutes")
            
            # Calculer les nouvelles heures en respectant les délais cumulés par feed et réseau
            base_time = now + timedelta(minutes=delay_minutes)
            
            for i, post in enumerate(posts):
                old_time = post.scheduled_at
                
                if i == 0:
                    # Premier post du feed/réseau - ajuster aux horaires
                    new_time = schedule_service._adjust_time_to_schedule(network, base_time)
                else:
                    # Posts suivants : après le post précédent + délai (sans ajustement horaire)
                    prev_post = posts[i-1]
                    new_time = prev_post.scheduled_at + timedelta(minutes=delay_minutes)
                
                adjusted_time = new_time
                
                # Mettre à jour
                post.scheduled_at = adjusted_time
                recalculated_count += 1
                
                print(f"   📅 Post #{post.id}: {old_time.strftime('%d/%m %H:%M')} → {adjusted_time.strftime('%d/%m %H:%M')}")
        
        # Sauvegarder les changements
        db.commit()
        
        return {
            "success": True,
            "message": f"Recalcul terminé pour {recalculated_count} posts",
            "recalculated_count": recalculated_count
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du recalcul: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors du recalcul: {str(e)}")

@router.get("/stats/summary")
def get_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques de la file d'attente"""
    queue_service = PublicationQueueService(db)
    return queue_service.get_queue_stats()
