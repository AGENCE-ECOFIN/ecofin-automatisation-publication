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
    
    item.is_paused = True
    # Garder le statut actuel mais marquer comme en pause
    # Le statut visuel sera géré par l'interface
    db.commit()
    
    return {"message": "Élément mis en pause avec succès"}

@router.put("/{item_id}/resume")
def resume_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprend un élément de la file d'attente"""
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
    
    item.is_paused = False
    item.status = "PENDING"
    db.commit()
    
    return {"message": "Élément repris avec succès"}

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

@router.get("/stats/summary")
def get_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques de la file d'attente"""
    queue_service = PublicationQueueService(db)
    return queue_service.get_queue_stats()
