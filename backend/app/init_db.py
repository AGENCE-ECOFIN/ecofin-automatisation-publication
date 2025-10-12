"""
Script d'initialisation de la base de données
Crée automatiquement les configurations de réseaux par défaut
"""
import sys
import time
from app.core.database import SessionLocal, engine
from app.models.network_config import NetworkConfig
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def wait_for_db(max_retries=30, delay=2):
    """Attendre que la base de données soit disponible"""
    logger.info("⏳ Attente de la base de données...")
    
    for attempt in range(max_retries):
        try:
            # Tenter une connexion simple
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✅ Base de données accessible!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"   Tentative {attempt + 1}/{max_retries} - Attente {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"❌ Impossible de se connecter à la base de données après {max_retries} tentatives")
                return False
    return False

def init_networks():
    """Initialiser les configurations de réseaux par défaut"""
    db = SessionLocal()
    try:
        # Vérifier si les réseaux existent déjà
        existing_networks = db.query(NetworkConfig).all()
        
        if len(existing_networks) > 0:
            logger.info(f"✅ {len(existing_networks)} réseaux déjà configurés")
            for network in existing_networks:
                logger.info(f"   - {network.network}: actif={network.is_active}, délai={network.default_publication_delay}min")
            return True
        
        logger.info("📝 Création des configurations de réseaux par défaut...")
        
        # Configuration par défaut des réseaux
        default_networks = [
            {
                'network': 'facebook',
                'is_active': True,
                'default_publication_delay': 4,
                'max_posts_per_day': 10
            },
            {
                'network': 'linkedin',
                'is_active': True,
                'default_publication_delay': 5,
                'max_posts_per_day': 8
            },
            {
                'network': 'x',
                'is_active': True,
                'default_publication_delay': 3,
                'max_posts_per_day': 15
            }
        ]
        
        for config in default_networks:
            network = NetworkConfig(**config)
            db.add(network)
            logger.info(f"   ✅ {config['network']} créé (délai: {config['default_publication_delay']}min, max: {config['max_posts_per_day']}/jour)")
        
        db.commit()
        logger.info("✅ 3 réseaux créés avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation des réseaux: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def init_database():
    """Point d'entrée principal pour l'initialisation de la base de données"""
    logger.info("")
    logger.info("="*60)
    logger.info("🚀 Initialisation de la base de données")
    logger.info("="*60)
    
    # Attendre que la DB soit prête
    if not wait_for_db():
        logger.error("❌ Impossible de continuer sans base de données")
        sys.exit(1)
    
    # Initialiser les réseaux
    logger.info("")
    if init_networks():
        logger.info("")
        logger.info("="*60)
        logger.info("✅ Initialisation terminée avec succès!")
        logger.info("="*60)
        logger.info("")
        return True
    else:
        logger.error("")
        logger.error("="*60)
        logger.error("❌ Erreur lors de l'initialisation")
        logger.error("="*60)
        logger.error("")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

