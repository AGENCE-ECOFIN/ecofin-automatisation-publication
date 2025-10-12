#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin par défaut
Utiliser ce script au premier déploiement ou pour réinitialiser l'admin
"""
import sys
from app.core.database import SessionLocal
from app.models.user import User
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe brut contre son hash"""
    try:
        return pwd_context.verify(plain_password[:72], hashed_password)
    except Exception as e:
        print(f"Erreur vérification mot de passe: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash un mot de passe (tronqué à 72 bytes pour bcrypt)"""
    try:
        password = password[:72]
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Erreur hash mot de passe: {e}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Vérifie et décode un JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
def create_admin():
    """Créer un utilisateur admin par défaut"""
    db = SessionLocal()
    
    try:
        # Vérifier si l'admin existe déjà
        existing_admin = db.query(User).filter(User.email == "admin@ecofin.com").first()
        
        if existing_admin:
            print("❌ Un utilisateur admin existe déjà avec cet email.")
            print(f"   Email: {existing_admin.email}")
            print(f"   Username: {existing_admin.username}")
            return
        
        # Créer l'admin
        admin = User(
            email="admin@ecofin.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_admin=True,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ Utilisateur admin créé avec succès !")
        print("")
        print("📧 Email:    admin@ecofin.com")
        print("👤 Username: admin")
        print("🔑 Password: admin123")
        print("")
        print("⚠️  IMPORTANT: Changez ce mot de passe dès la première connexion !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()


