"""
API unifiée pour la gestion des publications sur plusieurs réseaux sociaux
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.publication_service import PublicationService
from app.models.publication_queue import PublicationQueue
from app.models.network_config import NetworkConfig

router = APIRouter(prefix="/unified-publication", tags=["unified-publication"])

# Schémas Pydantic
class PublicationRequest(BaseModel):
    content: str
    networks: List[str]
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None

class PublicationResponse(BaseModel):
    success: bool
    message: str
    results: Dict[str, Dict]
    publication_id: Optional[int] = None

class NetworkStatusResponse(BaseModel):
    network: str
    status: str
    message: str
    rate_limit: Optional[int] = None
    min_interval: Optional[int] = None

class BulkPublicationRequest(BaseModel):
    publications: List[PublicationRequest]

@router.post("/publish", response_model=PublicationResponse)
def publish_content(
    request: PublicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publie du contenu sur plusieurs réseaux sociaux simultanément
    """
    try:
        publication_service = PublicationService()
        
        # Vérifier que les réseaux sont supportés
        supported_networks = ['linkedin', 'x', 'facebook']
        invalid_networks = [n for n in request.networks if n not in supported_networks]
        if invalid_networks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Réseaux non supportés: {invalid_networks}"
            )
        
        # Publier sur les réseaux demandés
        results = publication_service.publish_to_multiple_networks(
            content=request.content,
            networks=request.networks,
            media_urls=request.media_urls
        )
        
        # Calculer le succès global
        success_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)
        
        if success_count == total_count:
            message = f"Publication réussie sur tous les réseaux ({success_count}/{total_count})"
            success = True
        elif success_count > 0:
            message = f"Publication partielle ({success_count}/{total_count} réseaux)"
            success = True
        else:
            message = "Échec de la publication sur tous les réseaux"
            success = False
        
        return PublicationResponse(
            success=success,
            message=message,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la publication: {str(e)}"
        )

@router.post("/publish-queue-item/{item_id}")
def publish_queue_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publie un élément spécifique de la file d'attente
    """
    try:
        # Récupérer l'élément de la file d'attente
        queue_item = db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
        if not queue_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Élément de la file d'attente non trouvé"
            )
        
        if queue_item.is_paused:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de publier un élément en pause"
            )
        
        # Marquer comme en cours de publication
        queue_item.status = 'PUBLISHING'
        db.commit()
        
        # Publier sur le réseau
        publication_service = PublicationService()
        success, message, url = publication_service.publish_to_network(
            network=queue_item.network,
            content=queue_item.content,
            media_urls=queue_item.media_urls
        )
        
        if success:
            queue_item.status = 'PUBLISHED'
            queue_item.published_at = datetime.utcnow()
            queue_item.publication_url = url
        else:
            queue_item.status = 'FAILED'
            queue_item.error_message = message
        
        db.commit()
        
        return {
            "success": success,
            "message": message,
            "publication_url": url,
            "queue_item_id": item_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # En cas d'erreur, marquer comme échoué
        queue_item.status = 'FAILED'
        queue_item.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la publication: {str(e)}"
        )

@router.get("/networks/status", response_model=List[NetworkStatusResponse])
def get_networks_status(
    current_user: User = Depends(get_current_user)
):
    """
    Vérifie le statut de connexion de tous les réseaux sociaux
    """
    try:
        publication_service = PublicationService()
        status_results = publication_service.get_all_networks_status()
        
        response = []
        for network, status_info in status_results.items():
            response.append(NetworkStatusResponse(
                network=network,
                status=status_info['status'],
                message=status_info['message'],
                rate_limit=status_info.get('rate_limit'),
                min_interval=status_info.get('min_interval')
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification des statuts: {str(e)}"
        )

@router.post("/bulk-publish", response_model=List[PublicationResponse])
def bulk_publish(
    request: BulkPublicationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Publie plusieurs contenus en lot
    """
    try:
        publication_service = PublicationService()
        results = []
        
        for pub_request in request.publications:
            # Publier sur les réseaux demandés
            pub_results = publication_service.publish_to_multiple_networks(
                content=pub_request.content,
                networks=pub_request.networks,
                media_urls=pub_request.media_urls
            )
            
            # Calculer le succès
            success_count = sum(1 for r in pub_results.values() if r['success'])
            total_count = len(pub_results)
            
            if success_count == total_count:
                message = f"Publication réussie sur tous les réseaux ({success_count}/{total_count})"
                success = True
            elif success_count > 0:
                message = f"Publication partielle ({success_count}/{total_count} réseaux)"
                success = True
            else:
                message = "Échec de la publication sur tous les réseaux"
                success = False
            
            results.append(PublicationResponse(
                success=success,
                message=message,
                results=pub_results
            ))
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la publication en lot: {str(e)}"
        )

@router.get("/queue/ready")
def get_ready_queue_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les éléments de la file d'attente prêts pour publication
    """
    try:
        # Récupérer les configurations de réseaux actifs
        active_configs = db.query(NetworkConfig).filter(
            NetworkConfig.is_active == True
        ).all()
        
        ready_items = []
        
        for config in active_configs:
            # Récupérer le prochain élément pour ce réseau
            next_item = db.query(PublicationQueue).filter(
                PublicationQueue.network == config.network,
                PublicationQueue.status == 'PENDING',
                PublicationQueue.is_paused == False
            ).order_by(PublicationQueue.created_at.asc()).first()
            
            if next_item:
                ready_items.append({
                    "id": next_item.id,
                    "network": next_item.network,
                    "content": next_item.content[:100] + "...",
                    "created_at": next_item.created_at.isoformat(),
                    "interval_minutes": config.default_publication_delay or 30
                })
        
        return {
            "ready_items": ready_items,
            "total": len(ready_items),
            "networks": [config.network for config in active_configs]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des éléments prêts: {str(e)}"
        )
