"""
API pour récupérer les comptes Blotato disponibles
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from pydantic import BaseModel
import json
import os
from pathlib import Path

from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/blotato-accounts", tags=["blotato-accounts"])


class BlotatoPage(BaseModel):
    """Page ou sous-compte"""
    pageId: str
    pageName: str


class BlotatoAccount(BaseModel):
    """Compte Blotato"""
    accountId: str
    accountName: str
    platform: str
    pages: List[BlotatoPage] = []


class BlotatoAccountsResponse(BaseModel):
    """Réponse avec tous les comptes"""
    linkedin: List[BlotatoAccount]
    facebook: List[BlotatoAccount]
    x: List[BlotatoAccount]
    last_updated: str


def load_blotato_accounts() -> Dict:
    """Charge les comptes Blotato depuis le fichier JSON"""
    json_path = Path(__file__).parent.parent.parent / "blotato_accounts.json"
    
    if not json_path.exists():
        # Retourner une structure vide si le fichier n'existe pas
        return {
            "linkedin": [],
            "facebook": [],
            "x": [],
            "last_updated": "2025-01-01T00:00:00Z"
        }
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture des comptes Blotato: {str(e)}"
        )


@router.get("/", response_model=BlotatoAccountsResponse)
def get_all_blotato_accounts(
    current_user: User = Depends(get_current_user)
):
    """
    Récupère tous les comptes et pages Blotato disponibles
    
    Ces informations sont utilisées pour afficher des listes déroulantes
    lors de la création d'un flux RSS, au lieu de saisir manuellement les IDs.
    """
    accounts = load_blotato_accounts()
    return BlotatoAccountsResponse(**accounts)


@router.get("/{network}")
def get_network_accounts(
    network: str,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les comptes d'un réseau spécifique
    
    Args:
        network: 'linkedin', 'facebook' ou 'x'
    """
    if network not in ['linkedin', 'facebook', 'x']:
        raise HTTPException(
            status_code=400,
            detail=f"Réseau '{network}' non supporté. Utilisez: linkedin, facebook ou x"
        )
    
    accounts = load_blotato_accounts()
    return {
        "network": network,
        "accounts": accounts.get(network, []),
        "last_updated": accounts.get("last_updated")
    }


@router.get("/{network}/{account_id}/pages")
def get_account_pages(
    network: str,
    account_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les pages d'un compte spécifique
    
    Utile pour Facebook et LinkedIn qui peuvent avoir plusieurs pages
    """
    if network not in ['linkedin', 'facebook', 'x']:
        raise HTTPException(
            status_code=400,
            detail=f"Réseau '{network}' non supporté"
        )
    
    accounts = load_blotato_accounts()
    network_accounts = accounts.get(network, [])
    
    # Trouver le compte
    for account in network_accounts:
        if account.get('accountId') == account_id:
            return {
                "accountId": account_id,
                "accountName": account.get('accountName'),
                "pages": account.get('pages', [])
            }
    
    raise HTTPException(
        status_code=404,
        detail=f"Compte {account_id} non trouvé pour {network}"
    )


@router.post("/refresh")
def refresh_blotato_accounts(
    current_user: User = Depends(get_current_user)
):
    """
    Rafraîchit la liste des comptes depuis l'API Blotato
    
    Note: Nécessite que le script get_all_blotato_accounts.py soit exécuté
    ou que les comptes soient ajoutés manuellement dans blotato_accounts.json
    """
    import subprocess
    import sys
    
    try:
        # Chemin vers le script
        script_path = Path(__file__).parent.parent.parent / "get_all_blotato_accounts.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Script de récupération non trouvé"
            )
        
        # Exécuter le script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Recharger les comptes
            accounts = load_blotato_accounts()
            return {
                "success": True,
                "message": "Comptes rafraîchis avec succès",
                "accounts": accounts
            }
        else:
            return {
                "success": False,
                "message": "Erreur lors du rafraîchissement",
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Timeout lors du rafraîchissement des comptes"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )

