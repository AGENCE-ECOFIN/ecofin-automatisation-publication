from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import secrets
from app.core.database import get_db
from app.api.auth import get_current_user
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.email_service import EmailService
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False

class UserUpdateRequest(BaseModel):
    username: str = None
    email: str = None
    password: str = None
    is_admin: bool = None

@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouvel utilisateur (admin seulement)"""
    # Vérifier que l'utilisateur actuel est admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent créer des utilisateurs"
        )
    
    # Vérifier que l'email n'existe pas déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Vérifier que le nom d'utilisateur n'existe pas déjà
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec ce nom d'utilisateur existe déjà"
        )
    
    # Créer le nouvel utilisateur
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Envoyer l'email de bienvenue avec le mot de passe
    email_service = EmailService()
    email_service.send_welcome_email(
        to_email=new_user.email,
        username=new_user.username,
        password=user_data.password
    )
    
    return new_user

@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer la liste des utilisateurs (admin seulement)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent voir la liste des utilisateurs"
        )
    
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un utilisateur par ID"""
    # L'utilisateur peut voir son propre profil ou être admin
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez voir que votre propre profil"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un utilisateur"""
    # L'utilisateur peut modifier son propre profil ou être admin
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez modifier que votre propre profil"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Mettre à jour les champs fournis
    if user_data.username is not None:
        # Vérifier que le nom d'utilisateur n'existe pas déjà
        existing_username = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce nom d'utilisateur est déjà utilisé"
            )
        user.username = user_data.username
    
    if user_data.email is not None:
        # Vérifier que l'email n'existe pas déjà
        existing_email = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé"
            )
        user.email = user_data.email
    
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    # Seuls les admins peuvent modifier le statut admin
    if user_data.is_admin is not None and current_user.is_admin:
        user.is_admin = user_data.is_admin
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un utilisateur (admin seulement)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent supprimer des utilisateurs"
        )
    
    # Empêcher la suppression de son propre compte
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "Utilisateur supprimé avec succès"}

@router.get("/me/profile", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Récupérer le profil de l'utilisateur connecté"""
    return current_user


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SendWelcomeEmailRequest(BaseModel):
    user_id: int


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Demander la réinitialisation du mot de passe"""
    # Chercher l'utilisateur
    user = db.query(User).filter(User.email == request.email).first()
    
    # Ne pas révéler si l'utilisateur existe ou non
    if not user:
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}
    
    # Générer un token de réinitialisation
    reset_token = secrets.token_urlsafe(32)
    reset_expiry = datetime.utcnow() + timedelta(hours=1)
    
    # Enregistrer le token dans la base de données
    user.reset_token = reset_token
    user.reset_token_expiry = reset_expiry
    db.commit()
    
    # Envoyer l'email
    email_service = EmailService()
    email_service.send_password_reset_email(
        to_email=user.email,
        username=user.username,
        reset_token=reset_token
    )
    
    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Réinitialiser le mot de passe avec un token"""
    # Chercher l'utilisateur avec ce token
    user = db.query(User).filter(User.reset_token == request.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation invalide"
        )
    
    # Vérifier que le token n'a pas expiré
    if not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation expiré"
        )
    
    # Mettre à jour le mot de passe
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    
    return {"message": "Mot de passe réinitialisé avec succès"}


@router.post("/send-welcome-email")
def send_welcome_email(
    request: SendWelcomeEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Renvoyer l'email de bienvenue (admin seulement)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent envoyer des emails de bienvenue"
        )
    
    # Chercher l'utilisateur
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Générer un mot de passe temporaire
    temp_password = secrets.token_urlsafe(12)
    user.hashed_password = get_password_hash(temp_password)
    db.commit()
    
    # Envoyer l'email
    email_service = EmailService()
    success = email_service.send_welcome_email(
        to_email=user.email,
        username=user.username,
        password=temp_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'envoi de l'email"
        )
    
    return {"message": f"Email de bienvenue envoyé à {user.email}"}
