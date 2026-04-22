from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostValidate, NetworkValidationRequest, PostRejectRequest, PaginatedPostsResponse, PaginatedDirectPostsResponse, SourceHintsResponse
from app.schemas.publication import PublicationResponse, PaginatedPublicationsResponse
from app.services.post_service import PostService
from app.api.dependencies import get_current_user, get_client_info
from app.models.user import User
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    ip_address, user_agent = get_client_info(request)
    return post_service.create_post(post, user_id=current_user.id, ip_address=ip_address, user_agent=user_agent)


@router.get("/drafts", response_model=PaginatedPostsResponse)
def get_draft_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    search: Optional[str] = None,
    source: Optional[str] = None,
    created_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    items, total = post_service.get_posts_paginated(
        status="draft",
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        created_on=created_date,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/validated", response_model=PaginatedPostsResponse)
def get_validated_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    search: Optional[str] = None,
    source: Optional[str] = None,
    created_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    items, total = post_service.get_posts_paginated(
        status="validated",
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        created_on=created_date,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/queue", response_model=PaginatedPostsResponse)
def get_posts_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    items, total = post_service.get_posts_queue_paginated(page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/rejected", response_model=PaginatedPostsResponse)
def get_rejected_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    search: Optional[str] = None,
    source: Optional[str] = None,
    created_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    items, total = post_service.get_posts_paginated(
        status="rejected",
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        created_on=created_date,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/direct", response_model=PaginatedDirectPostsResponse)
def get_direct_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer les posts directs"""
    post_service = PostService(db)
    items, total = post_service.get_direct_posts_paginated(page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/history", response_model=PaginatedPostsResponse)
def get_posts_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère l'historique de tous les posts"""
    post_service = PostService(db)
    items, total = post_service.get_posts_paginated(page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/meta/source-hints", response_model=SourceHintsResponse)
def get_post_source_hints(
    limit: int = Query(500, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Noms des flux RSS créés dans Flux (table feeds), pour le filtre Source."""
    post_service = PostService(db)
    sources = post_service.list_source_filter_hints(limit=limit)
    return {"sources": sources}


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
    request: Request,
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
    
    ip_address, user_agent = get_client_info(request)
    return post_service.update_post(post_id, post_update, user_id=current_user.id, ip_address=ip_address, user_agent=user_agent)


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
    request_body: Optional[PostRejectRequest] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rejeter un post globalement (rejette tous les réseaux et retire de la queue) - motif optionnel"""
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    # Permettre le rejet même si le post a des réseaux validés
    # Motif de rejet optionnel (pas nécessaire) - peut être None ou non fourni
    rejection_reason = None
    if request_body is not None and hasattr(request_body, 'rejection_reason'):
        rejection_reason = request_body.rejection_reason
    
    # Marquer le post comme rejeté globalement (l'audit est fait dans reject_post)
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    post_service.reject_post(post_id, current_user.id, rejection_reason, ip_address=ip_address, user_agent=user_agent)
    
    return {"message": "Post rejeté globalement avec succès (tous les réseaux rejetés et retirés de la queue)"}


@router.post("/{post_id}/restore")
def restore_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restaurer un post rejeté globalement (restaure tous les réseaux rejetés en brouillon)"""
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post non trouvé"
        )
    
    # Permettre la restauration même si le post n'est pas strictement "rejected"
    # (certains posts peuvent avoir des réseaux rejetés mais un statut différent)
    # if post.status != "rejected":
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Seuls les posts rejetés peuvent être restaurés"
    #     )
    
    # Restaurer globalement le post (tous les réseaux rejetés)
    post_service.restore_post(post_id)
    
    return {"message": "Post restauré globalement avec succès (tous les réseaux rejetés restaurés en brouillon)"}


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


@router.get("/history/publications", response_model=PaginatedPublicationsResponse)
def get_publication_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    network: Optional[str] = None,
    feed: Optional[str] = Query(None, description='Vide, "direct", ou identifiant numérique de flux'),
    pub_status: Optional[str] = Query(None, description="PUBLISHED ou FAILED"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_service = PostService(db)
    items, total = post_service.get_publication_history_paginated(
        page=page,
        page_size=page_size,
        network=network,
        feed=feed,
        pub_status=pub_status,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


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
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Valider un réseau spécifique d'un post"""
    print(f"🌐 [API] Validation réseau {network} pour post {post_id} par user {current_user.id}")
    post_service = PostService(db)
    ip_address, user_agent = get_client_info(request)
    post = post_service.validate_network(post_id, network, current_user.id, ip_address=ip_address, user_agent=user_agent)
    if not post:
        print(f"❌ [API] Post {post_id} non trouvé")
        raise HTTPException(status_code=404, detail="Post non trouvé")
    print(f"✅ [API] Réseau {network} validé avec succès")
    return {"message": f"Réseau {network} validé", "post": post}


@router.post("/{post_id}/networks/{network}/reject")
def reject_network(
    post_id: int,
    network: str,
    request_body: NetworkValidationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rejeter un réseau spécifique d'un post"""
    print(f"🌐 [API] Rejet réseau {network} pour post {post_id} par user {current_user.id}")
    print(f"🔍 [API] Raison de rejet: {request_body.rejection_reason}")
    post_service = PostService(db)
    ip_address, user_agent = get_client_info(request)
    post = post_service.reject_network(
        post_id, 
        network, 
        current_user.id, 
        request_body.rejection_reason,
        ip_address=ip_address,
        user_agent=user_agent
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
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restaurer un réseau spécifique d'un post (remettre en brouillon)"""
    print(f"🌐 [API] Restauration réseau {network} pour post {post_id} par user {current_user.id}")
    post_service = PostService(db)
    ip_address, user_agent = get_client_info(request)
    post = post_service.restore_network(
        post_id, 
        network, 
        current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    if not post:
        print(f"❌ [API] Post {post_id} non trouvé")
        raise HTTPException(status_code=404, detail="Post non trouvé")
    print(f"✅ [API] Réseau {network} restauré avec succès")
    return {"message": f"Réseau {network} restauré", "post": post}

