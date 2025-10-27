"""
API endpoints pour la gestion des horaires de publication
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.services.schedule_service import ScheduleService
from app.schemas.schedule_config import (
    ScheduleConfigCreate, 
    ScheduleConfigUpdate, 
    ScheduleConfigResponse,
    ScheduleConfigBulkUpdate,
    ScheduleStatusResponse
)

router = APIRouter()


@router.post("/", response_model=ScheduleConfigResponse)
def create_schedule_config(
    config: ScheduleConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle configuration d'horaires"""
    schedule_service = ScheduleService(db)
    return schedule_service.create_schedule_config(config)


@router.get("/", response_model=List[ScheduleConfigResponse])
def get_schedule_configs(
    network: Optional[str] = Query(None, description="Filtrer par réseau"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les configurations d'horaires"""
    schedule_service = ScheduleService(db)
    configs = schedule_service.get_schedule_configs(network)
    return configs


@router.get("/{config_id}", response_model=ScheduleConfigResponse)
def get_schedule_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer une configuration d'horaires par ID"""
    schedule_service = ScheduleService(db)
    config = schedule_service.get_schedule_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.put("/{config_id}", response_model=ScheduleConfigResponse)
def update_schedule_config(
    config_id: int,
    config_update: ScheduleConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour une configuration d'horaires"""
    schedule_service = ScheduleService(db)
    config = schedule_service.update_schedule_config(config_id, config_update)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.delete("/{config_id}")
def delete_schedule_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprimer une configuration d'horaires"""
    schedule_service = ScheduleService(db)
    success = schedule_service.delete_schedule_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return {"message": "Configuration supprimée avec succès"}


@router.post("/bulk-update", response_model=List[ScheduleConfigResponse])
def bulk_update_schedule_configs(
    bulk_update: ScheduleConfigBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour plusieurs configurations en une fois"""
    schedule_service = ScheduleService(db)
    
    # Utiliser la nouvelle méthode qui gère la reprogrammation automatique
    created_configs = schedule_service.bulk_update_schedules(bulk_update.network, bulk_update.configs)
    
    return created_configs


@router.post("/recalculate-posts/{network}")
def recalculate_posts_for_network(
    network: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Forcer le recalcul de tous les posts programmés pour un réseau"""
    schedule_service = ScheduleService(db)
    
    # Forcer le recalcul
    schedule_service._recalculate_posts_schedule(network)
    
    return {"message": f"Posts recalculés pour {network}"}


@router.get("/status/{network}", response_model=ScheduleStatusResponse)
def get_schedule_status(
    network: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vérifier le statut actuel des horaires pour un réseau"""
    schedule_service = ScheduleService(db)
    status = schedule_service.is_publication_allowed_now(network)
    
    return ScheduleStatusResponse(
        network=status["network"],
        is_active_now=status["allowed"],
        current_config=status["config"],
        next_available_time=status["next_available"],
        reason=status["reason"]
    )


@router.get("/planning/{network}")
def get_publication_planning(
    network: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Générer un planning de publication pour un réseau"""
    schedule_service = ScheduleService(db)
    planning = schedule_service.get_publication_schedule_for_network(network)
    return {
        "network": network,
        "planning": planning,
        "total_slots": len(planning)
    }


@router.post("/init-defaults")
def initialize_default_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialiser les configurations d'horaires par défaut"""
    schedule_service = ScheduleService(db)
    schedule_service.create_default_schedules()
    return {"message": "Configurations par défaut créées avec succès"}

@router.post("/recalculate-queue/{network}")
async def recalculate_queue_for_network(
    network: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculer les horaires des posts en attente pour un réseau"""
    try:
        schedule_service = ScheduleService(db)
        updated_count = schedule_service.recalculate_queue_for_network(network)
        return {
            "message": f"Recalcul effectué pour {updated_count} posts en attente",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du recalcul: {str(e)}")
