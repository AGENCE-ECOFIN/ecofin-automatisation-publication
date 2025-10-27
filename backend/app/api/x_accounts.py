from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.blotato_service import BlotatoService

router = APIRouter()

@router.get("/x-accounts")
def get_x_accounts(
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer la liste des comptes X disponibles pour la publication
    """
    try:
        blotato_service = BlotatoService()
        x_accounts = blotato_service.get_x_accounts()
        
        return {
            "success": True,
            "data": x_accounts,
            "message": f"{len(x_accounts)} comptes X disponibles"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des comptes X: {str(e)}"
        )
