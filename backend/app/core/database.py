from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Configuration du pool de connexions avec gestion des connexions fermées
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Vérifie si la connexion est valide avant utilisation
    pool_recycle=3600,  # Recycle les connexions après 1 heure
    pool_size=10,  # Nombre de connexions dans le pool
    max_overflow=20,  # Nombre max de connexions supplémentaires
    echo=False  # Mettre à True pour voir les requêtes SQL en debug
)

# pool_pre_ping=True gère automatiquement la vérification et reconnexion des connexions fermées

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur de session DB: {e}")
        raise
    finally:
        db.close()

