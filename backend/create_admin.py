#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin par défaut
Utiliser ce script au premier déploiement ou pour réinitialiser l'admin
"""
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

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

