from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.api import auth, feeds, posts, test_generation, tasks, networks, users
from app.api import publication_queue as publication_queue_api
from app.api import unified_publication, blotato_accounts, direct_post
from app.core.database import engine
from app.models import user, feed, post, publication
from app.models import network_config
from app.models.publication_queue import PublicationQueue
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer les tables
user.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EcoFin Publication API",
    description="API pour la génération et publication automatisée de posts à partir de flux RSS",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage de l'application"""
    try:
        logger.info("🚀 Démarrage de l'application...")
        
        # Initialiser la base de données (créer les réseaux par défaut)
        from app.init_db import init_database
        init_database()
        
        logger.info("✅ Application démarrée avec succès!")
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        # Ne pas bloquer le démarrage si l'initialisation échoue
        pass

# Configuration CORS - Autoriser tous les origins en production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet tous les origins (dev + prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(auth.router)
app.include_router(feeds.router)
app.include_router(posts.router)
app.include_router(test_generation.router)
app.include_router(test_generation.generation_router)  # Router pour la génération directe
app.include_router(tasks.router)
app.include_router(networks.router, prefix="/networks", tags=["networks"])
app.include_router(publication_queue_api.router, prefix="/publication-queue", tags=["publication-queue"])
app.include_router(unified_publication.router, tags=["unified-publication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(blotato_accounts.router, tags=["blotato-accounts"])
app.include_router(direct_post.router, tags=["direct-post"])


@app.get("/")
def read_root():
    return {"message": "EcoFin Publication API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/celery/status")
def celery_status():
    """Vérifie le statut de Celery"""
    try:
        from app.workers.celery_app import celery_app
        
        # Vérifier les workers actifs
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        # Compter les tâches actives
        active_task_count = 0
        if active_workers:
            for worker_tasks in active_workers.values():
                if isinstance(worker_tasks, list):
                    active_task_count += len(worker_tasks)
        
        return {
            "status": "healthy",
            "workers": active_workers or {},
            "active_tasks": active_workers or {},
            "scheduled_tasks": scheduled_tasks or {},
            "reserved_tasks": reserved_tasks or {},
            "worker_count": len(active_workers) if active_workers else 0,
            "active_task_count": active_task_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "workers": {},
            "active_tasks": {},
            "scheduled_tasks": {},
            "reserved_tasks": {},
            "worker_count": 0,
            "active_task_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
