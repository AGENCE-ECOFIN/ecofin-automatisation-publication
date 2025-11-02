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
            
            # Calculer le délai de publication depuis NetworkConfig (délai global par réseau)
            from app.models.network_config import NetworkConfig
            network_config = self.db.query(NetworkConfig).filter(
                NetworkConfig.network == network,
                NetworkConfig.is_active == True
            ).first()
            delay_minutes = network_config.default_publication_delay if network_config else 30
            
            now = datetime.now(timezone.utc)
            from app.services.schedule_service import ScheduleService
            schedule_service = ScheduleService(self.db)
            
            # 🔥 ÉTAPE 1: Vérifier s'il y a des posts en file d'attente pour ce feed/réseau
            existing_queue_posts = self.db.query(PublicationQueue).filter(
                PublicationQueue.feed_id == post.feed_id,
                PublicationQueue.network == network,
                PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
            ).order_by(PublicationQueue.scheduled_at.desc()).all()
            
            if existing_queue_posts:
                # Il y a des posts en file d'attente → appliquer le délai cumulatif
                last_scheduled = existing_queue_posts[0]  # Le plus récent
                scheduled_at = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                print(f"🔄 DÉLAI CUMULATIF: {len(existing_queue_posts)} post(s) en file pour feed #{post.feed_id} sur {network}")
                print(f"   → Dernier post programmé: {last_scheduled.scheduled_at.strftime('%H:%M')}")
                print(f"   → Nouveau post: {scheduled_at.strftime('%H:%M')} (après {delay_minutes}min)")
            else:
                # File d'attente vide → vérifier le dernier post publié pour décider immédiat ou délai restant
                from app.models.publication import Publication
                last_published = self.db.query(Publication).filter(
                    Publication.feed_id == post.feed_id,
                    Publication.network == network,
                    Publication.is_success == True,
                    Publication.published_at.isnot(None)
                ).order_by(Publication.published_at.desc()).first()

                if last_published and last_published.published_at:
                    time_since_last = now - last_published.published_at
                    if time_since_last >= timedelta(minutes=delay_minutes):
                        # Délai dépassé → publication immédiate (ajustée aux horaires)
                        scheduled_at = schedule_service._adjust_time_to_schedule(network, now)
                        print(f"✨ File vide & délai dépassé (dernier à {last_published.published_at.strftime('%H:%M')}) → immédiat: {scheduled_at.strftime('%H:%M')}")
                    else:
                        # Délai restant → programmer à fin du délai (ajustée aux horaires)
                        scheduled_at = schedule_service._adjust_time_to_schedule(
                            network,
                            last_published.published_at + timedelta(minutes=delay_minutes)
                        )
                        remaining = int(((timedelta(minutes=delay_minutes) - time_since_last).total_seconds()) // 60)
                        print(f"⏳ File vide & délai en cours (reste ~{remaining}min) → {scheduled_at.strftime('%H:%M')}")
                else:
                    # Aucun historique publié → publication immédiate (ajustée aux horaires)
                    scheduled_at = schedule_service._adjust_time_to_schedule(network, now)
                    print(f"✨ File vide & aucun publié → immédiat: {scheduled_at.strftime('%H:%M')}")
            
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

