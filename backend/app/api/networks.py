from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.dependencies import get_current_user, get_client_info
from app.services.audit_service import AuditService
from app.models.user import User
from app.models.network_config import NetworkConfig
from app.schemas.network_config import NetworkConfigResponse, NetworkConfigCreate, NetworkConfigUpdate

router = APIRouter()

@router.get("/", response_model=List[NetworkConfigResponse])
def get_networks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère la liste des configurations de réseaux"""
    networks = db.query(NetworkConfig).all()
    return networks

@router.get("/{network_id}", response_model=NetworkConfigResponse)
def get_network(
    network_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère une configuration de réseau spécifique"""
    network = db.query(NetworkConfig).filter(NetworkConfig.id == network_id).first()
    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration réseau non trouvée"
        )
    return network

@router.post("/", response_model=NetworkConfigResponse)
def create_network(
    network_data: NetworkConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée une nouvelle configuration de réseau"""
    # Vérifier si le réseau existe déjà
    existing_network = db.query(NetworkConfig).filter(
        NetworkConfig.network == network_data.network
    ).first()
    
    if existing_network:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce réseau est déjà configuré"
        )
    
    network = NetworkConfig(**network_data.model_dump())
    db.add(network)
    db.commit()
    db.refresh(network)
    
    return network

@router.put("/{network_id}", response_model=NetworkConfigResponse)
def update_network(
    network_id: int,
    network_data: NetworkConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour une configuration de réseau"""
    network = db.query(NetworkConfig).filter(NetworkConfig.id == network_id).first()
    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration réseau non trouvée"
        )
    
    # Sauvegarder les anciennes valeurs pour l'audit
    old_values = {
        "network": network.network,
        "default_publication_delay": network.default_publication_delay,
        "is_active": network.is_active
    }
    
    # Mettre à jour uniquement les champs fournis et non-None
    update_data = network_data.model_dump(exclude_unset=True)
    modified_fields = list(update_data.keys())
    for field, value in update_data.items():
        if value is not None:  # Ne mettre à jour que si la valeur n'est pas None
            setattr(network, field, value)
    
    db.commit()
    db.refresh(network)
    
    # Logger la mise à jour de la config réseau
    ip_address, user_agent = get_client_info(request)
    audit_service = AuditService(db)
    audit_service.log_action(
        action="CONFIG_UPDATE",
        entity_type="network_config",
        user_id=current_user.id,
        entity_id=network_id,
        description=f"Modification de la configuration réseau '{network.network}'",
        metadata={
            "network": network.network,
            "modified_fields": modified_fields,
            "old_values": old_values,
            "new_values": {field: getattr(network, field, None) for field in modified_fields}
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return network

@router.delete("/{network_id}")
def delete_network(
    network_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprime une configuration de réseau"""
    network = db.query(NetworkConfig).filter(NetworkConfig.id == network_id).first()
    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration réseau non trouvée"
        )
    
    db.delete(network)
    db.commit()
    
    return {"message": "Configuration réseau supprimée avec succès"}
