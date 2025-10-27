#!/usr/bin/env python3
"""
Script pour recalculer les heures de publication des posts existants
en appliquant le système de délais cumulés par feed et par réseau
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.publication_queue import PublicationQueue
from app.models.feed import Feed
from app.services.schedule_service import ScheduleService
from datetime import datetime, timedelta, timezone

def recalculate_queue_schedule():
    """Recalculer les heures de publication en respectant les délais cumulés"""
    db = SessionLocal()
    try:
        print("🔄 Recalcul des heures de publication avec délais cumulés...")
        
        # Récupérer tous les posts programmés, groupés par feed et réseau
        scheduled_posts = db.query(PublicationQueue).filter(
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING'])
        ).order_by(PublicationQueue.feed_id, PublicationQueue.network, PublicationQueue.created_at).all()
        
        # Grouper par feed_id et network
        posts_by_feed_network = {}
        for post in scheduled_posts:
            key = (post.feed_id, post.network)
            if key not in posts_by_feed_network:
                posts_by_feed_network[key] = []
            posts_by_feed_network[key].append(post)
        
        schedule_service = ScheduleService(db)
        now = datetime.now(timezone.utc)
        
        for (feed_id, network), posts in posts_by_feed_network.items():
            print(f"\n📊 Feed #{feed_id} - {network}: {len(posts)} posts à recalculer")
            
            # Récupérer le délai configuré pour ce feed/réseau
            feed = db.query(Feed).filter(Feed.id == feed_id).first()
            if feed and feed.publication_timing:
                delay_minutes = feed.publication_timing.get(network, 30)
            else:
                delay_minutes = 30  # Délai par défaut
            
            print(f"   Délai configuré: {delay_minutes} minutes")
            
            # Calculer les nouvelles heures en respectant les délais cumulés
            base_time = now + timedelta(minutes=delay_minutes)
            
            for i, post in enumerate(posts):
                old_time = post.scheduled_at
                
                if i == 0:
                    # Premier post du feed/réseau
                    new_time = base_time
                else:
                    # Posts suivants : après le post précédent + délai
                    prev_post = posts[i-1]
                    new_time = prev_post.scheduled_at + timedelta(minutes=delay_minutes)
                
                # Ajuster aux horaires d'ouverture si nécessaire
                adjusted_time = schedule_service._adjust_time_to_schedule(network, new_time)
                
                # Mettre à jour
                post.scheduled_at = adjusted_time
                
                print(f"   📅 Post #{post.id}: {old_time.strftime('%d/%m %H:%M')} → {adjusted_time.strftime('%d/%m %H:%M')}")
        
        # Sauvegarder les changements
        db.commit()
        print(f"\n✅ Recalcul terminé pour {len(scheduled_posts)} posts")
        
    except Exception as e:
        print(f"❌ Erreur lors du recalcul: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    recalculate_queue_schedule()
