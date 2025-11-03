from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user, get_client_info
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    
    # Vérifier si l'utilisateur existe déjà
    if auth_service.get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom d'utilisateur est déjà utilisé"
        )
    
    # Créer l'utilisateur
    db_user = auth_service.create_user(user)
    return db_user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    
    ip_address, user_agent = get_client_info(request)
    
    user = auth_service.authenticate_user(
        user_credentials.username, 
        user_credentials.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user



