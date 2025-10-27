from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostValidate, NetworkValidationRequest
from app.schemas.publication import PublicationResponse
from app.services.post_service import PostService
from app.api.dependencies import get_current_user
from app.models.user import User
from typing import List

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    return post_service.create_post(post)


@router.get("/drafts", response_model=List[PostResponse])
def get_draft_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    return post_service.get_posts(status="draft")


@router.get("/validated", response_model=List[PostResponse])
def get_validated_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    return post_service.get_posts(status="validated")


@router.get("/queue", response_model=List[PostResponse])
def get_posts_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    return post_service.get_posts_queue()


@router.get("/rejected", response_model=List[PostResponse])
def get_rejected_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    return post_service.get_posts(status="rejected")


@router.get("/direct", response_model=List[dict])
def get_direct_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer les posts directs"""
    post_service = PostService(db)
    return post_service.get_direct_posts()


@router.get("/history", response_model=List[PostResponse])
def get_posts_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère l'historique de tous les posts"""
    post_service = PostService(db)
    return post_service.get_posts()


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    return post_service.update_post(post_id, post_update)


@router.post("/{post_id}/validate", response_model=PostResponse)
def validate_post(
    post_id: int,
    post_validate: PostValidate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    return post_service.validate_post(post_id, post_validate, current_user.id)


@router.post("/{post_id}/reject")
def reject_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    if post.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les brouillons peuvent être rejetés"
        )
    
    # Marquer le post comme rejeté
    post_service.reject_post(post_id, current_user.id)
    
    return {"message": "Post rejeté avec succès"}


@router.post("/{post_id}/restore")
def restore_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    if post.status != "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les posts rejetés peuvent être restaurés"
        )
    
    # Remettre le post en brouillon
    post_service.restore_post(post_id)
    
    return {"message": "Post restauré en brouillon avec succès"}


@router.post("/{post_id}/publish-now")
def publish_post_now(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    if post.status != "validated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le post doit être validé avant publication"
        )
    
    # Marquer le post comme publié
    post_service.mark_post_published(post_id)
    
    # Ici, vous pourriez déclencher une tâche Celery pour publier immédiatement
    # publish_post_task.delay(post_id)
    
    return {"message": "Post programmé pour publication immédiate"}


@router.get("/history/publications", response_model=List[PublicationResponse])
def get_publication_history(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    return post_service.get_publication_history(limit)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    updated_post = post_service.update_post(post_id, post_update)
    if not updated_post:
        raise HTTPException(status_code=404, detail="Post non trouvé")
    return updated_post


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post non trouvé")
    return post


@router.post("/{post_id}/networks/{network}/validate")
def validate_network(
    post_id: int,
    network: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Valider un réseau spécifique d'un post"""
    print(f"🌐 [API] Validation réseau {network} pour post {post_id} par user {current_user.id}")
    post_service = PostService(db)
    post = post_service.validate_network(post_id, network, current_user.id)
    if not post:
        print(f"❌ [API] Post {post_id} non trouvé")
        raise HTTPException(status_code=404, detail="Post non trouvé")
    print(f"✅ [API] Réseau {network} validé avec succès")
    return {"message": f"Réseau {network} validé", "post": post}


@router.post("/{post_id}/networks/{network}/reject")
def reject_network(
    post_id: int,
    network: str,
    request: NetworkValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rejeter un réseau spécifique d'un post"""
    print(f"🌐 [API] Rejet réseau {network} pour post {post_id} par user {current_user.id}")
    print(f"🔍 [API] Raison de rejet: {request.rejection_reason}")
    post_service = PostService(db)
    post = post_service.reject_network(
        post_id, 
        network, 
        current_user.id, 
        request.rejection_reason
    )
    if not post:
        print(f"❌ [API] Post {post_id} non trouvé")
        raise HTTPException(status_code=404, detail="Post non trouvé")
    print(f"✅ [API] Réseau {network} rejeté avec succès")
    return {"message": f"Réseau {network} rejeté", "post": post}


@router.post("/{post_id}/networks/{network}/restore")
def restore_network(
    post_id: int,
    network: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restaurer un réseau spécifique d'un post (remettre en brouillon)"""
    print(f"🌐 [API] Restauration réseau {network} pour post {post_id} par user {current_user.id}")
    post_service = PostService(db)
    post = post_service.restore_network(
        post_id, 
        network, 
        current_user.id
    )
    if not post:
        print(f"❌ [API] Post {post_id} non trouvé")
        raise HTTPException(status_code=404, detail="Post non trouvé")
    print(f"✅ [API] Réseau {network} restauré avec succès")
    return {"message": f"Réseau {network} restauré", "post": post}

