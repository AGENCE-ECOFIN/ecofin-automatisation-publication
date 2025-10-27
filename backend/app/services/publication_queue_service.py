from sqlalchemy.orm import Session
from app.models.publication_queue import PublicationQueue
from app.models.post import Post
from app.models.feed import Feed
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import json


class PublicationQueueService:
    def __init__(self, db: Session):
        self.db = db

    def add_post_to_queue(self, post_id: int, networks: List[str] = None) -> List[PublicationQueue]:
        """Ajoute un post à la file d'attente pour les réseaux spécifiés"""
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise ValueError(f"Post {post_id} non trouvé")
        
        if post.status != "validated":
            raise ValueError(f"Le post {post_id} n'est pas validé (statut: {post.status})")
        
        feed = self.db.query(Feed).filter(Feed.id == post.feed_id).first()
        if not feed:
            raise ValueError(f"Feed {post.feed_id} non trouvé")
        
        # Déterminer les réseaux cibles
        if not networks:
            networks = feed.target_networks or ["facebook", "linkedin", "x"]
        
        queue_items = []
        
        for network in networks:
            # Vérifier si l'élément existe déjà
            existing = self.db.query(PublicationQueue).filter(
                PublicationQueue.post_id == post_id,
                PublicationQueue.network == network
            ).first()
            
            if existing:
                continue
            
            # Récupérer le contenu généré pour ce réseau
            generated_content = post.generated_content or {}
            content = generated_content.get(network, post.content)
            
            # Calculer le délai de publication avec vérification des horaires
            publication_timing = feed.publication_timing or {}
            delay_minutes = publication_timing.get(network, 30)
            
            # 🔥 FIFO PAR FEED : Vérifier s'il y a déjà des posts programmés sur CE RÉSEAU pour CE FEED
            last_scheduled = self.db.query(PublicationQueue).filter(
                PublicationQueue.feed_id == post.feed_id,
                PublicationQueue.network == network,
                PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
            ).order_by(PublicationQueue.scheduled_at.desc()).first()
            
            now = datetime.now(timezone.utc)
            
            if last_scheduled and last_scheduled.scheduled_at:
                # Programmer APRÈS le dernier post programmé + le délai (sans ajustement horaire)
                scheduled_at = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                print(f"🔄 FIFO FEED: Dernier post du feed #{post.feed_id} sur {network} programmé à {last_scheduled.scheduled_at.strftime('%H:%M')}")
                print(f"   → Heure calculée: {scheduled_at.strftime('%H:%M')} (après {delay_minutes}min)")
            else:
                # Pas de post en attente pour ce feed, programmer normalement avec ajustement horaire
                base_time = now + timedelta(minutes=delay_minutes)
                from app.services.schedule_service import ScheduleService
                schedule_service = ScheduleService(self.db)
                scheduled_at = schedule_service._adjust_time_to_schedule(network, base_time)
                print(f"✨ Premier post du feed #{post.feed_id} sur {network}")
                print(f"   → Heure calculée: {base_time.strftime('%H:%M')} → Ajustée: {scheduled_at.strftime('%H:%M')}")
            
            print(f"📅 Post #{post_id} programmé pour {network}:")
            print(f"   Heure optimale: {scheduled_at.strftime('%d/%m/%Y %H:%M')}")
            
            # Récupérer la page de destination
            social_pages = feed.social_pages or {}
            target_page_id = social_pages.get(network)
            
            # Déterminer le statut selon l'heure calculée
            now = datetime.now()
            if scheduled_at <= now + timedelta(minutes=5):  # Dans les 5 prochaines minutes
                status = "PENDING"
            else:
                status = "SCHEDULED"
            
            # Créer l'élément de la file d'attente
            queue_item = PublicationQueue(
                post_id=post_id,
                feed_id=post.feed_id,
                network=network,
                target_page_id=target_page_id,
                content=content,
                media_urls=[post.source_image] if post.source_image else None,
                scheduled_at=scheduled_at,
                status=status
            )
            
            self.db.add(queue_item)
            queue_items.append(queue_item)
        
        self.db.commit()
        
        # Rafraîchir les objets pour obtenir les IDs
        for item in queue_items:
            self.db.refresh(item)
        
        return queue_items

    def get_queue_items(self, filters: Dict = None) -> List[PublicationQueue]:
        """Récupère les éléments de la file d'attente avec filtres optionnels"""
        query = self.db.query(PublicationQueue)
        
        if filters:
            if filters.get('status'):
                query = query.filter(PublicationQueue.status == filters['status'])
            if filters.get('network'):
                query = query.filter(PublicationQueue.network == filters['network'])
            if filters.get('feed_id'):
                query = query.filter(PublicationQueue.feed_id == filters['feed_id'])
        
        return query.order_by(PublicationQueue.created_at.desc()).all()

    def get_queue_stats(self) -> Dict:
        """Récupère les statistiques de la file d'attente"""
        from sqlalchemy import func
        
        stats = self.db.query(
            PublicationQueue.status,
            func.count(PublicationQueue.id).label('count')
        ).group_by(PublicationQueue.status).all()
        
        return {
            "by_status": {stat.status.value: stat.count for stat in stats},
            "total": sum(stat.count for stat in stats)
        }

    def pause_item(self, item_id: int) -> bool:
        """Met en pause un élément de la file d'attente"""
        item = self.db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
        if not item:
            return False
        
        if item.status not in ["PENDING", "SCHEDULED"]:
            return False
        
        item.is_paused = True
        item.status = "PENDING"
        self.db.commit()
        return True

    def resume_item(self, item_id: int) -> bool:
        """Reprend un élément de la file d'attente"""
        item = self.db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
        if not item:
            return False
        
        if not item.is_paused:
            return False
        
        item.is_paused = False
        item.status = "PENDING"
        self.db.commit()
        return True

    def cancel_item(self, item_id: int) -> bool:
        """Annule un élément de la file d'attente"""
        item = self.db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
        if not item:
            return False
        
        if item.status in ["PUBLISHED", "CANCELLED"]:
            return False
        
        item.status = "CANCELLED"
        self.db.commit()
        return True

    def retry_item(self, item_id: int) -> bool:
        """Réessaie un élément de la file d'attente"""
        item = self.db.query(PublicationQueue).filter(PublicationQueue.id == item_id).first()
        if not item:
            return False
        
        if item.status != "FAILED":
            return False
        
        if item.retry_count >= item.max_retries:
            return False
        
        item.status = "PENDING"
        item.retry_count += 1
        item.error_message = None
        self.db.commit()
        return True

