from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from typing import Optional, Tuple

security = HTTPBearer()


def get_client_info(request: Request) -> Tuple[Optional[str], Optional[str]]:
    """
    Récupère l'adresse IP et le user agent depuis la requête
    
    Returns:
        Tuple (ip_address, user_agent)
    """
    # Récupérer l'IP (gérer les proxies)
    ip_address = request.client.host if request.client else None
    if "x-forwarded-for" in request.headers:
        ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Récupérer le user agent
    user_agent = request.headers.get("user-agent")
    
    return ip_address, user_agent


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    auth_service = AuthService(db)
    user = auth_service.verify_token_and_get_user(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits administrateur requis"
        )
    return current_user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    return current_user



