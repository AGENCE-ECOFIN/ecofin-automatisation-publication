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

    def get_direct_posts(self) -> List[dict]:
        """Récupérer les posts directs depuis la publication_queue ET l'historique"""
        from app.models.publication_queue import PublicationQueue
        from app.models.publication import Publication
        
        result = []
        
        # 1. Récupérer les posts directs dans la queue (programmés/en attente)
        queue_direct_posts = self.db.query(PublicationQueue).filter(
            PublicationQueue.post_id.is_(None)
        ).order_by(PublicationQueue.created_at.desc()).all()
        
        for queue_item in queue_direct_posts:
            # Extraire les informations du post direct
            extra_data = queue_item.extra_data or {}
            is_direct = extra_data.get('is_direct_post', False)
            
            result.append({
                'id': f"direct_{queue_item.id}",
                'title': f"Post direct - {queue_item.network}",
                'content': queue_item.content,
                'source_url': None,
                'source_image': queue_item.media_urls[0] if queue_item.media_urls else None,
                'generated_content': {queue_item.network: queue_item.content},
                'status': 'direct',
                'feed_id': None,
                'feed': None,
                'validated_by': None,
                'validated_at': None,
                'created_at': queue_item.created_at,
                'updated_at': queue_item.updated_at,
                'network': queue_item.network,
                'scheduled_at': queue_item.scheduled_at,
                'published_at': queue_item.published_at,
                'queue_status': queue_item.status,
                'is_direct': True,
                'publication_url': queue_item.publication_url
            })
        
        # 2. Récupérer les posts directs publiés immédiatement depuis l'historique
        # (post_id = NULL ET feed_id = NULL dans Publication)
        immediate_direct_posts = self.db.query(Publication).filter(
            Publication.post_id.is_(None),
            Publication.feed_id.is_(None)
        ).order_by(Publication.published_at.desc()).all()
        
        for pub_item in immediate_direct_posts:
            result.append({
                'id': f"immediate_{pub_item.id}",
                'title': f"Post direct - {pub_item.network}",
                'content': pub_item.content,
                'source_url': None,
                'source_image': None,
                'generated_content': {pub_item.network: pub_item.content},
                'status': 'direct',
                'feed_id': None,
                'feed': None,
                'validated_by': None,
                'validated_at': None,
                'created_at': pub_item.published_at,  # Utiliser published_at comme created_at
                'updated_at': pub_item.published_at,
                'network': pub_item.network,
                'scheduled_at': None,  # Pas de programmation pour les posts immédiats
                'published_at': pub_item.published_at,
                'queue_status': 'PUBLISHED' if pub_item.is_success else 'FAILED',
                'is_direct': True,
                'publication_url': pub_item.published_url,
                'is_immediate': True  # Marquer comme post immédiat
            })
        
        # Trier par date de création (plus récent en premier)
        result.sort(key=lambda x: x['created_at'], reverse=True)
        
        return result

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
            print(f"🚀 DÉBUT validate_post pour post #{post_id} par user #{user_id}")
            db_post = self.get_post_by_id(post_id)
            if not db_post:
                print(f"❌ Post #{post_id} non trouvé")
                return None

            db_post.generated_content = post_validate.generated_content
            db_post.status = "validated"
            db_post.validated_by = user_id
            db_post.validated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_post)
            
            # ✅ PROGRAMMER IMMÉDIATEMENT selon la logique complète
            self._schedule_validated_post(db_post)
            print(f"✅ Post #{post_id} validé et programmé selon les critères")
            
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
            print(f"🚀 DÉBUT _add_to_publication_queue pour post #{post.id} - Feed #{post.feed_id}")
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
                    
                    # ✅ Vérifier les horaires configurés pour ce réseau
                    from app.services.schedule_service import ScheduleService
                    schedule_service = ScheduleService(self.db)
                    schedule_status = schedule_service.is_publication_allowed_now(network)
                    
                    print(f"📊 Statut horaires pour {network}: {schedule_status}")
                    
                    # Délai : depuis la config GLOBALE
                    delay_minutes = network_config.default_publication_delay
                    
                    # 🔥 FIFO PAR FEED : Vérifier s'il y a déjà des posts programmés sur CE RÉSEAU pour CE FEED
                    last_scheduled = self.db.query(PublicationQueue).filter(
                        PublicationQueue.feed_id == post.feed_id,
                        PublicationQueue.network == network,
                        PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
                    ).order_by(PublicationQueue.scheduled_at.desc()).first()
                    
                    if last_scheduled and last_scheduled.scheduled_at:
                        # Programmer APRÈS le dernier post programmé + le délai
                        base_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                        print(f"🔄 FIFO FEED: Dernier post du feed #{post.feed_id} sur {network} programmé à {last_scheduled.scheduled_at.strftime('%H:%M')}")
                        print(f"   → Heure calculée: {base_time.strftime('%H:%M')} (après {delay_minutes}min)")
                    else:
                        # Pas de post en attente pour ce feed, programmer normalement
                        base_time = now + timedelta(minutes=delay_minutes)
                        print(f"✨ Premier post du feed #{post.feed_id} sur {network}, heure calculée: {base_time.strftime('%H:%M')}")
                    
                    # Vérifier si cette heure est dans un créneau autorisé et ajuster si nécessaire
                    scheduled_time = schedule_service._adjust_time_to_schedule(network, base_time)
                    print(f"📅 Heure finale programmée: {scheduled_time.strftime('%H:%M')}")
                    
                    # Déterminer le statut selon l'heure programmée et les horaires configurés
                    # Vérifier si l'heure programmée est dans un créneau autorisé
                    config = schedule_service.get_active_config_for_network_now(network)
                    if config and config.is_active:
                        # Si configuré, vérifier si l'heure programmée est dans les horaires
                        scheduled_hour = scheduled_time.hour
                        scheduled_minute = scheduled_time.minute
                        if config.is_time_in_range(scheduled_hour, scheduled_minute):
                            status = "SCHEDULED"  # Programmé dans les horaires autorisés
                        else:
                            status = "WAITING_HOURS"  # Programmé hors horaires autorisés
                    else:
                        # Pas de configuration horaire, toujours SCHEDULED
                        status = "SCHEDULED"
                    
                    # Page : depuis la config DU FLUX
                    destination_id = social_pages.get(network, '')
                    
                    # ⚠️ Facebook nécessite OBLIGATOIREMENT un pageId
                    # Utiliser la page du flux ou fallback vers blotato_accounts.json
                    if network == 'facebook' and not destination_id:
                        import json
                        import os
                        try:
                            blotato_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blotato_accounts.json')
                            with open(blotato_file, 'r') as f:
                                blotato_accounts = json.load(f)
                                facebook_accounts = blotato_accounts.get('facebook', [])
                                if facebook_accounts and len(facebook_accounts) > 0:
                                    facebook_pages = facebook_accounts[0].get('pages', [])
                                    if facebook_pages and len(facebook_pages) > 0:
                                        destination_id = facebook_pages[0]['pageId']
                                        print(f"   ⚠️  Page Facebook manquante pour ce flux, utilisation du fallback: {facebook_pages[0]['pageName']}")
                        except Exception as e:
                            print(f"   ❌ Impossible de charger blotato_accounts.json: {e}")
                    
                    # Si toujours pas de page pour Facebook, skip
                    if network == 'facebook' and not destination_id:
                        print(f"   ❌ Facebook nécessite un pageId - Skip ce réseau")
                        continue
                    
                    queue_item = PublicationQueue(
                        post_id=post.id,
                        feed_id=post.feed_id,
                        network=network,
                        content=generated_content[network],
                        media_urls=media_urls,
                        scheduled_at=scheduled_time,  # ✅ Délai depuis config GLOBALE
                        target_page_id=destination_id,  # ✅ Page depuis config DU FLUX (ou fallback)
                        status=status,
                        is_paused=False
                    )
                    self.db.add(queue_item)
                    
                    print(f"✅ AJOUTÉ À LA QUEUE: {network} - Statut: {status} - Programmé: {scheduled_time.strftime('%H:%M')} - Page: {destination_id}")
            
            self.db.commit()
            print(f"✅ Post ajouté à la file de publication pour {len(target_networks)} réseau(x)")
            
        except Exception as e:
            self.db.rollback()
            raise

    def _schedule_validated_post(self, post: Post):
        """Programmer un post validé selon la logique complète"""
        from app.models.publication_queue import PublicationQueue
        from app.models.network_config import NetworkConfig
        from app.services.schedule_service import ScheduleService
        from datetime import datetime, timezone, timedelta
        
        try:
            print(f"🚀 PROGRAMMATION post #{post.id} - {post.title[:50]}...")
            
            # Récupérer les réseaux cibles du flux
            target_networks = post.feed.target_networks if post.feed.target_networks else ['facebook', 'linkedin', 'x']
            
            # S'assurer que generated_content est un dictionnaire
            generated_content = post.generated_content if isinstance(post.generated_content, dict) else {}
            
            # Récupérer la configuration du flux pour les pages
            social_pages = post.feed.social_pages or {}
            media_urls = [post.source_image] if post.source_image else []
            
            now = datetime.now(timezone.utc)
            schedule_service = ScheduleService(self.db)
            
            for network in target_networks:
                # Vérifier si le contenu généré existe pour ce réseau
                if network not in generated_content:
                    print(f"   ⚠️ Pas de contenu généré pour {network}")
                    continue
                
                # 1. Vérifier la configuration du réseau
                network_config = self.db.query(NetworkConfig).filter(
                    NetworkConfig.network == network,
                    NetworkConfig.is_active == True
                ).first()
                
                if not network_config:
                    print(f"   ⚠️ Réseau {network} non configuré, skip")
                    continue
                
                # 2. Vérifier les horaires d'ouverture
                schedule_status = schedule_service.is_publication_allowed_now(network)
                print(f"   📊 Horaires {network}: {schedule_status}")
                
                # 3. Calculer l'heure de programmation
                delay_minutes = network_config.default_publication_delay
                
                # FIFO PAR FEED : Vérifier le dernier post du même feed
                last_scheduled = self.db.query(PublicationQueue).filter(
                    PublicationQueue.feed_id == post.feed_id,
                    PublicationQueue.network == network,
                    PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
                ).order_by(PublicationQueue.scheduled_at.desc()).first()
                
                if last_scheduled and last_scheduled.scheduled_at:
                    # Programmer APRÈS le dernier post + délai
                    base_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                    print(f"   🔄 FIFO: Après post #{last_scheduled.id} à {last_scheduled.scheduled_at.strftime('%H:%M')}")
                else:
                    # Premier post du feed
                    base_time = now + timedelta(minutes=delay_minutes)
                    print(f"   ✨ Premier post du feed #{post.feed_id} sur {network}")
                
                # 4. Ajuster selon les horaires configurés
                scheduled_time = schedule_service._adjust_time_to_schedule(network, base_time)
                print(f"   📅 Heure calculée: {base_time.strftime('%H:%M')} → Ajustée: {scheduled_time.strftime('%H:%M')}")
                
                # 5. Déterminer le statut initial
                config = schedule_service.get_active_config_for_network_now(network)
                if config and config.is_active:
                    if config.is_time_in_range(scheduled_time.hour, scheduled_time.minute):
                        status = "SCHEDULED"  # Programmé dans les horaires
                    else:
                        status = "WAITING_HOURS"  # En attente d'horaires
                else:
                    status = "SCHEDULED"  # Pas de config horaire
                
                # 6. Page de destination
                destination_id = social_pages.get(network, '')
                
                # Fallback Facebook si nécessaire
                if network == 'facebook' and not destination_id:
                    import json
                    import os
                    try:
                        blotato_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blotato_accounts.json')
                        with open(blotato_file, 'r') as f:
                            blotato_accounts = json.load(f)
                            facebook_accounts = blotato_accounts.get('facebook', [])
                            if facebook_accounts and len(facebook_accounts) > 0:
                                facebook_pages = facebook_accounts[0].get('pages', [])
                                if facebook_pages:
                                    destination_id = facebook_pages[0]['pageId']
                                print(f"   ⚠️ Fallback Facebook: {facebook_pages[0]['pageName']}")
                    except Exception as e:
                        print(f"   ❌ Erreur fallback Facebook: {e}")
                
                if network == 'facebook' and not destination_id:
                    print(f"   ❌ Pas de page Facebook, skip")
                    continue
                
                # 7. Créer l'entrée de queue
                queue_item = PublicationQueue(
                    post_id=post.id,
                    feed_id=post.feed_id,
                    network=network,
                    content=generated_content[network],
                    media_urls=media_urls,
                    scheduled_at=scheduled_time,
                    target_page_id=destination_id,
                    status=status,
                    is_paused=False
                )
                self.db.add(queue_item)
                
                print(f"   ✅ PROGRAMMÉ {network}: {status} à {scheduled_time.strftime('%H:%M')} - Page: {destination_id}")
            
            self.db.commit()
            print(f"✅ Post #{post.id} programmé pour {len(target_networks)} réseau(x)")
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Erreur programmation post #{post.id}: {e}")
            raise

    def _check_if_post_ready_for_queue(self, post: Post, network: str) -> dict:
        """Vérifier si un post validé est prêt à être ajouté à la queue de publication"""
        from app.models.network_config import NetworkConfig
        from app.services.schedule_service import ScheduleService
        from app.models.publication_queue import PublicationQueue
        from datetime import datetime, timezone, timedelta
        
        try:
            # 1. Vérifier la configuration du réseau
            network_config = self.db.query(NetworkConfig).filter(
                NetworkConfig.network == network,
                NetworkConfig.is_active == True
            ).first()
            
            if not network_config:
                return {"ready": False, "reason": f"Réseau {network} non configuré"}
            
            # 2. Vérifier les horaires
            schedule_service = ScheduleService(self.db)
            schedule_status = schedule_service.is_publication_allowed_now(network)
            
            if not schedule_status["allowed"]:
                return {"ready": False, "reason": f"Horaires fermés: {schedule_status['reason']}"}
            
            # 3. Vérifier le délai depuis le dernier post du même feed
            delay_minutes = network_config.default_publication_delay
            now = datetime.now(timezone.utc)
            
            last_scheduled = self.db.query(PublicationQueue).filter(
                PublicationQueue.feed_id == post.feed_id,
                PublicationQueue.network == network,
                PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
            ).order_by(PublicationQueue.scheduled_at.desc()).first()
            
            if last_scheduled and last_scheduled.scheduled_at:
                # Calculer l'heure minimum pour le prochain post
                min_next_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                
                if now < min_next_time:
                    remaining = min_next_time - now
                    return {"ready": False, "reason": f"Délai insuffisant, reste {remaining}"}
            
            # 4. Vérifier la page de destination (pour Facebook)
            if network == 'facebook':
                social_pages = post.feed.social_pages or {}
                destination_id = social_pages.get(network, '')
                
                if not destination_id:
                    # Vérifier le fallback
                    import json
                    import os
                    try:
                        blotato_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blotato_accounts.json')
                        with open(blotato_file, 'r') as f:
                            blotato_accounts = json.load(f)
                            facebook_accounts = blotato_accounts.get('facebook', [])
                            if not facebook_accounts or len(facebook_accounts) == 0:
                                return {"ready": False, "reason": "Pas de compte Facebook configuré"}
                            facebook_pages = facebook_accounts[0].get('pages', [])
                            if not facebook_pages:
                                return {"ready": False, "reason": "Pas de page Facebook configurée"}
                    except:
                        return {"ready": False, "reason": "Configuration Facebook manquante"}
            
            # Tous les critères sont OK
            return {"ready": True, "reason": "Prêt à publier"}
            
        except Exception as e:
            return {"ready": False, "reason": f"Erreur: {str(e)}"}

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

