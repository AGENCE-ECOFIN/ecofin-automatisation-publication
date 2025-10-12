from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ecofin_pub",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.workers.tasks']
)

# Configuration Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    beat_schedule={
        'process-all-feeds': {
            'task': 'app.workers.tasks.process_all_active_feeds',
            'schedule': 300.0,  # Toutes les 5 minutes - Vérifie quels flux doivent être collectés
        },
        'process-publication-queue': {
            'task': 'app.workers.tasks.process_publication_queue',
            'schedule': 60.0,  # Toutes les 1 minute - Traite la file de publication
        },
    },
)

