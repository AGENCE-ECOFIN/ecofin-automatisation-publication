"""
Script d'initialisation de la base de données
Crée automatiquement les configurations de réseaux par défaut
"""
from app.core.database import SessionLocal
from app.models.network_config import NetworkConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_networks():
    """Initialiser les configurations de réseaux par défaut"""
    db = SessionLocal()
    try:
        # Vérifier si les réseaux existent déjà
        existing_networks = db.query(NetworkConfig).all()
        
        if len(existing_networks) > 0:
            logger.info(f"✅ {len(existing_networks)} réseaux déjà configurés")
            for network in existing_networks:
                logger.info(f"   - {network.network}: actif={network.is_active}")
            return
        
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
            logger.info(f"   ✅ {config['network']} créé")
        
        db.commit()
        logger.info("✅ Configurations de réseaux créées avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation des réseaux: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Point d'entrée principal pour l'initialisation de la base de données"""
    logger.info("🚀 Initialisation de la base de données...")
    init_networks()
    logger.info("✅ Initialisation terminée!")

if __name__ == "__main__":
    init_database()

