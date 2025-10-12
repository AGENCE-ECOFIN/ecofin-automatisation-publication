from sqlalchemy.orm import Session, joinedload
from app.models.post import Post
from app.models.publication import Publication
from app.models.publication_queue import PublicationQueue
from app.models.network_config import NetworkConfig
from app.schemas.post import PostCreate, PostUpdate, PostValidate
from typing import List, Optional
from datetime import datetime, timezone, timedelta


class PostService:
    def __init__(self, db: Session):
        self.db = db

    def create_post(self, post: PostCreate) -> Post:
        db_post = Post(
            title=post.title,
            content=post.content,
            source_url=str(post.source_url) if post.source_url else None,
            source_image=post.source_image,
            feed_id=post.feed_id,
            status="draft"
        )
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def get_posts(self, status: Optional[str] = None, feed_id: Optional[int] = None) -> List[Post]:
        query = self.db.query(Post).options(joinedload(Post.feed))
        if status:
            query = query.filter(Post.status == status)
        if feed_id:
            query = query.filter(Post.feed_id == feed_id)
        return query.order_by(Post.created_at.desc()).all()

    def get_post_by_id(self, post_id: int) -> Optional[Post]:
        return self.db.query(Post).options(joinedload(Post.feed)).filter(Post.id == post_id).first()

    def update_post(self, post_id: int, post_update: PostUpdate) -> Optional[Post]:
        db_post = self.get_post_by_id(post_id)
        if not db_post:
            return None

        update_data = post_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)

        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def validate_post(self, post_id: int, post_validate: PostValidate, user_id: int) -> Optional[Post]:
        try:
            db_post = self.get_post_by_id(post_id)
            if not db_post:
                return None

            db_post.generated_content = post_validate.generated_content
            db_post.status = "validated"
            db_post.validated_by = user_id
            db_post.validated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_post)
            
            # Ajouter automatiquement à la file d'attente pour chaque réseau
            self._add_to_publication_queue(db_post)
            
            return db_post
            
        except Exception as e:
            self.db.rollback()
            raise

    def _add_to_publication_queue(self, post: Post):
        """
        Ajouter un post validé à la file d'attente de publication
        Utilise les délais et pages configurés dans le flux (DYNAMIQUE)
        """
        try:
            from app.models.publication_queue import PublicationQueue
            from datetime import timedelta, timezone
            
            # Récupérer les réseaux cibles du flux
            target_networks = post.feed.target_networks if post.feed.target_networks else ['facebook', 'linkedin', 'x']
            
            # S'assurer que generated_content est un dictionnaire
            generated_content = post.generated_content if isinstance(post.generated_content, dict) else {}
            
            # Récupérer la configuration du flux pour les pages
            social_pages = post.feed.social_pages or {}
            media_urls = [post.source_image] if post.source_image else []
            
            now = datetime.now(timezone.utc)
            
            for network in target_networks:
                # Vérifier si le contenu généré existe pour ce réseau
                if network in generated_content:
                    # ✅ Récupérer la configuration GLOBALE du réseau (pour le délai)
                    network_config = self.db.query(NetworkConfig).filter(
                        NetworkConfig.network == network,
                        NetworkConfig.is_active == True
                    ).first()
                    
                    if not network_config:
                        print(f"⚠️ Réseau {network} non configuré ou inactif, skip")
                        continue
                    
                    # Délai : depuis la config GLOBALE
                    delay_minutes = network_config.default_publication_delay
                    
                    # 🔥 FIFO : Vérifier s'il y a déjà des posts de CE FEED sur CE RÉSEAU en attente
                    last_scheduled = self.db.query(PublicationQueue).filter(
                        PublicationQueue.feed_id == post.feed_id,
                        PublicationQueue.network == network,
                        PublicationQueue.status.in_(['PENDING', 'PUBLISHING'])
                    ).order_by(PublicationQueue.scheduled_at.desc()).first()
                    
                    if last_scheduled and last_scheduled.scheduled_at:
                        # Programmer APRÈS le dernier post programmé + le délai
                        scheduled_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                        print(f"🔄 FIFO: Dernier post de ce feed sur {network} programmé à {last_scheduled.scheduled_at.strftime('%H:%M')}")
                        print(f"   → Nouveau post programmé à {scheduled_time.strftime('%H:%M')} (après {delay_minutes}min)")
                    else:
                        # Pas de post en attente, programmer normalement
                        scheduled_time = now + timedelta(minutes=delay_minutes)
                        print(f"✨ Premier post de ce feed sur {network}, programmé à {scheduled_time.strftime('%H:%M')}")
                    
                    # Page : depuis la config DU FLUX
                    destination_id = social_pages.get(network, '')
                    
                    queue_item = PublicationQueue(
                        post_id=post.id,
                        feed_id=post.feed_id,
                        network=network,
                        content=generated_content[network],
                        media_urls=media_urls,
                        scheduled_at=scheduled_time,  # ✅ Délai depuis config GLOBALE
                        target_page_id=destination_id,  # ✅ Page depuis config DU FLUX
                        status="PENDING",
                        is_paused=False
                    )
                    self.db.add(queue_item)
                    
                    print(f"📅 Validation: Programmé {network} pour {scheduled_time.strftime('%H:%M')} (délai global: {delay_minutes} min) sur page du flux: {destination_id or 'non configurée'}")
            
            self.db.commit()
            print(f"✅ Post ajouté à la file de publication pour {len(target_networks)} réseau(x)")
            
        except Exception as e:
            self.db.rollback()
            raise

    def get_posts_queue(self) -> List[Post]:
        """Récupère les posts validés en attente de publication"""
        return self.db.query(Post).options(joinedload(Post.feed)).filter(Post.status == "validated").order_by(Post.validated_at.asc()).all()

    def mark_post_published(self, post_id: int) -> Optional[Post]:
        db_post = self.get_post_by_id(post_id)
        if not db_post:
            return None

        db_post.status = "published"
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def create_publication(self, post_id: int, network: str, content: str, published_url: str = None, is_success: bool = True, error_message: str = None) -> Publication:
        db_publication = Publication(
            post_id=post_id,
            network=network,
            content=content,
            published_url=published_url,
            is_success=is_success,
            error_message=error_message,
            published_at=datetime.utcnow() if is_success else None
        )
        self.db.add(db_publication)
        self.db.commit()
        self.db.refresh(db_publication)
        return db_publication

    def get_publication_history(self, limit: int = 100) -> List[Publication]:
        return self.db.query(Publication).order_by(Publication.created_at.desc()).limit(limit).all()

    def reject_post(self, post_id: int, user_id: int) -> Post:
        """Rejeter un post"""
        post = self.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post non trouvé")
        
        post.status = "rejected"
        post.validated_by = user_id
        post.validated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(post)
        return post

    def restore_post(self, post_id: int) -> Post:
        """Restaurer un post rejeté en brouillon"""
        post = self.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post non trouvé")
        
        post.status = "draft"
        post.validated_by = None
        post.validated_at = None
        
        self.db.commit()
        self.db.refresh(post)
        return post

