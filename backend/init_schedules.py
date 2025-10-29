#!/usr/bin/env python3
"""
Script d'initialisation des horaires par défaut
"""
import sys
sys.path.insert(0, '/app' if '/app' in __file__ else '.')

from app.core.database import SessionLocal
from app.services.schedule_service import ScheduleService

def init_default_schedules():
    """Initialiser les configurations d'horaires par défaut"""
    db = SessionLocal()
    try:
        print("📅 Initialisation des horaires par défaut...")
        schedule_service = ScheduleService(db)
        schedule_service.create_default_schedules()
        print("✅ Initialisation des horaires terminée")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_default_schedules()
