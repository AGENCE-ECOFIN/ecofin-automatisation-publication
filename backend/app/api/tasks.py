from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from typing import List, Dict, Any
from datetime import datetime, timedelta
import redis
from app.core.config import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Connexion Redis pour récupérer l'historique des tâches
redis_client = redis.from_url(settings.REDIS_URL)

@router.get("/history")
def get_tasks_history(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Récupère l'historique des tâches Celery"""
    try:
        from app.workers.celery_app import celery_app
        
        # Récupérer les informations des workers
        inspect = celery_app.control.inspect()
        
        # Récupérer les statistiques des workers
        stats = inspect.stats()
        
        # Récupérer les tâches actives
        active_tasks = inspect.active()
        
        # Récupérer les tâches programmées
        scheduled_tasks = inspect.scheduled()
        
        # Récupérer les tâches réservées
        reserved_tasks = inspect.reserved()
        
        # Récupérer les workers enregistrés
        registered = inspect.registered()
        
        # Construire l'historique avec des données par défaut
        history = {
            'workers': {},
            'active_tasks': active_tasks or {},
            'scheduled_tasks': scheduled_tasks or {},
            'reserved_tasks': reserved_tasks or {},
            'stats': stats or {},
            'registered': registered or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Ajouter des informations sur les workers
        if stats:
            for worker_name, worker_stats in stats.items():
                history['workers'][worker_name] = {
                    'status': 'online',
                    'total_tasks': worker_stats.get('total', 0),
                    'pool': worker_stats.get('pool', {}),
                    'rusage': worker_stats.get('rusage', {}),
                    'clock': worker_stats.get('clock', 0)
                }
        elif registered:
            # Si pas de stats mais des workers enregistrés
            for worker_name in registered.keys():
                history['workers'][worker_name] = {
                    'status': 'online',
                    'total_tasks': 0,
                    'pool': {},
                    'rusage': {},
                    'clock': 0
                }
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )

@router.get("/stats")
def get_tasks_stats(
    current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques des tâches"""
    try:
        from app.workers.celery_app import celery_app
        
        # Récupérer les statistiques
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        # Récupérer les tâches actives
        active_tasks = inspect.active()
        
        # Compter le nombre total de tâches
        total_active = sum(len(tasks) for tasks in (active_tasks.values() if active_tasks else []))
        
        # Récupérer les informations sur les workers
        workers_info = []
        if stats:
            for worker_name, worker_stats in stats.items():
                workers_info.append({
                    'name': worker_name,
                    'status': 'online',
                    'total_tasks': worker_stats.get('total', 0),
                    'active_tasks': len(active_tasks.get(worker_name, [])) if active_tasks else 0,
                    'pool_size': worker_stats.get('pool', {}).get('max-concurrency', 0),
                    'current_load': worker_stats.get('pool', {}).get('current-load', 0)
                })
        
        return {
            'total_workers': len(workers_info),
            'total_active_tasks': total_active,
            'workers': workers_info,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )
