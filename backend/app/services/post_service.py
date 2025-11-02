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
        
        # Plus besoin de charger le mapping MinIO car les URLs sont stockées dans media_urls
        
        result = []
        
        # 1. Récupérer les posts directs dans la queue (programmés/en attente)
        queue_direct_posts = self.db.query(PublicationQueue).filter(
            PublicationQueue.feed_id.is_(None)
        ).order_by(PublicationQueue.created_at.desc()).all()
        
        for queue_item in queue_direct_posts:
            # Extraire les informations du post direct
            extra_data = queue_item.extra_data or {}
            is_direct = extra_data.get('is_direct_post', False)
            
            # Utiliser la première image des media_urls stockées
            associated_image = None
            if queue_item.media_urls and len(queue_item.media_urls) > 0:
                associated_image = queue_item.media_urls[0]
                print(f"🖼️ Image trouvée dans media_urls pour queue item {queue_item.id}: {associated_image}")
            
            # Créer les validations réseau appropriées
            network_validations = {
                queue_item.network: {
                    'status': 'draft' if queue_item.status in ['SCHEDULED', 'PENDING'] else 'published',
                    'validated_by': 'system',
                    'validated_at': queue_item.created_at.isoformat(),
                    'content': queue_item.content
                }
            }
            
            result.append({
                'id': f"direct_{queue_item.id}",
                'title': f"Post direct programmé - {queue_item.network}",
                'content': queue_item.content,
                'source_url': None,
                'source_image': associated_image,  # Utiliser l'image depuis media_urls
                'generated_content': {queue_item.network: queue_item.content},
                'status': 'draft' if queue_item.status in ['SCHEDULED', 'PENDING'] else 'published',
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
                'publication_url': queue_item.publication_url,
                'is_immediate': False,
                'network_validations': network_validations
            })
        
        # 2. Récupérer les posts directs publiés immédiatement depuis l'historique
        # (feed_id = NULL dans Publication)
        immediate_direct_posts = self.db.query(Publication).filter(
            Publication.feed_id.is_(None)
        ).order_by(Publication.published_at.desc()).all()
        
        for pub_item in immediate_direct_posts:
            # Utiliser la première image des media_urls stockées
            associated_image = None
            if pub_item.media_urls and len(pub_item.media_urls) > 0:
                associated_image = pub_item.media_urls[0]
                print(f"🖼️ Image trouvée dans media_urls pour post {pub_item.id}: {associated_image}")
            
            # Créer les validations réseau appropriées
            network_validations = {
                pub_item.network: {
                    'status': 'published' if pub_item.is_success else 'failed',
                    'validated_by': 'system',
                    'validated_at': pub_item.published_at.isoformat(),
                    'content': pub_item.content
                }
            }
            
            result.append({
                'id': f"immediate_{pub_item.id}",
                'title': f"Post direct - {pub_item.network}",
                'content': pub_item.content,
                'source_url': None,
                'source_image': associated_image,  # Utiliser l'image depuis media_urls
                'generated_content': {pub_item.network: pub_item.content},
                'status': 'published' if pub_item.is_success else 'failed',
                'feed_id': None,
                'feed': None,
                'validated_by': None,
                'validated_at': None,
                'created_at': pub_item.published_at,
                'updated_at': pub_item.published_at,
                'network': pub_item.network,
                'scheduled_at': None,
                'published_at': pub_item.published_at,
                'queue_status': 'PUBLISHED' if pub_item.is_success else 'FAILED',
                'is_direct': True,
                'publication_url': pub_item.published_url,
                'is_immediate': True,
                'network_validations': network_validations
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
            print(f"❌ Erreur validation post #{post_id}: {e}")
            self.db.rollback()
            return None

    def validate_network(self, post_id: int, network: str, user_id: int) -> Optional[Post]:
        """Valider un réseau spécifique d'un post"""
        try:
            print(f"🚀 [VALIDATE] Début validation du réseau {network} pour post #{post_id} par user #{user_id}")
            
            db_post = self.get_post_by_id(post_id)
            if not db_post:
                print(f"❌ [VALIDATE] Post #{post_id} non trouvé")
                return None

            print(f"📰 [VALIDATE] Post trouvé: {db_post.title}")
            print(f"🔍 [VALIDATE] Validations actuelles: {db_post.network_validations}")

            # Initialiser network_validations si nécessaire
            if not db_post.network_validations:
                db_post.network_validations = {}
                print(f"🆕 [VALIDATE] Initialisation des validations pour post #{post_id}")

            # Mettre à jour le statut du réseau
            new_validation = {
                "status": "validated",
                "validated_by": user_id,
                "validated_at": datetime.utcnow().isoformat()
            }
            db_post.network_validations[network] = new_validation
            print(f"✅ [VALIDATE] Validation du réseau {network} pour post #{post_id}")
            print(f"🔍 [VALIDATE] Nouvelle validation: {new_validation}")

            # Forcer la mise à jour de l'objet JSON
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(db_post, 'network_validations')

            # Vérifier si tous les réseaux sont validés
            all_networks = list(db_post.generated_content.keys()) if db_post.generated_content else []
            validated_networks = [
                net for net, validation in db_post.network_validations.items() 
                if validation.get("status") == "validated"
            ]

            print(f"🔍 [VALIDATE] Réseaux générés: {all_networks}")
            print(f"🔍 [VALIDATE] Réseaux validés: {validated_networks}")

            # Mettre à jour le statut global du post
            if len(validated_networks) == len(all_networks) and all_networks:
                db_post.status = "validated"
                db_post.validated_by = user_id
                db_post.validated_at = datetime.utcnow()
                print(f"🎯 [VALIDATE] Post #{post_id} entièrement validé!")

            print(f"💾 [VALIDATE] Sauvegarde en base de données...")
            self.db.commit()
            self.db.refresh(db_post)
            
            # Ajouter le réseau validé individuellement à la queue
            self._add_network_to_publication_queue(db_post, network)
            print(f"✅ [VALIDATE] Réseau {network} validé et ajouté à la queue pour post #{post_id}")
            
            # Vérifier si tous les réseaux sont validés pour le statut global
            if len(validated_networks) == len(all_networks) and all_networks:
                print(f"🎯 [VALIDATE] Post #{post_id} entièrement validé!")
            
            print(f"🔍 [VALIDATE] Validations finales: {db_post.network_validations}")
            return db_post
            
        except Exception as e:
            print(f"❌ [VALIDATE] Erreur validation réseau {network} pour post #{post_id}: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return None

    def reject_network(self, post_id: int, network: str, user_id: int, rejection_reason: str = None) -> Optional[Post]:
        """Rejeter un réseau spécifique d'un post"""
        try:
            print(f"🚀 [REJECT] Début rejet du réseau {network} pour post #{post_id} par user #{user_id}")
            print(f"🔍 [REJECT] Raison de rejet: {rejection_reason}")
            
            db_post = self.get_post_by_id(post_id)
            if not db_post:
                print(f"❌ [REJECT] Post #{post_id} non trouvé")
                return None

            print(f"📰 [REJECT] Post trouvé: {db_post.title}")
            print(f"🔍 [REJECT] Validations actuelles: {db_post.network_validations}")

            # Initialiser network_validations si nécessaire
            if not db_post.network_validations:
                db_post.network_validations = {}
                print(f"🆕 [REJECT] Initialisation des validations pour post #{post_id}")

            # Vérifier si c'est une restauration (rejection_reason est None)
            if rejection_reason is None:
                # Restauration : remettre en brouillon
                new_validation = {
                    "status": "draft",
                    "validated_by": user_id,
                    "validated_at": datetime.utcnow().isoformat(),
                    "rejection_reason": None
                }
                db_post.network_validations[network] = new_validation
                print(f"🔄 [REJECT] Restauration du réseau {network} pour post #{post_id}")
                print(f"🔍 [REJECT] Nouvelle validation: {new_validation}")
            else:
                # Vrai rejet
                new_validation = {
                    "status": "rejected",
                    "validated_by": user_id,
                    "validated_at": datetime.utcnow().isoformat(),
                    "rejection_reason": rejection_reason
                }
                db_post.network_validations[network] = new_validation
                print(f"❌ [REJECT] Rejet du réseau {network} pour post #{post_id}")
                print(f"🔍 [REJECT] Nouvelle validation: {new_validation}")

            # Forcer la mise à jour de l'objet JSON
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(db_post, 'network_validations')

            print(f"💾 [REJECT] Sauvegarde en base de données...")
            self.db.commit()
            self.db.refresh(db_post)
            
            print(f"✅ [REJECT] Réseau {network} traité pour post #{post_id}")
            print(f"🔍 [REJECT] Validations finales: {db_post.network_validations}")
            
            return db_post
            
        except Exception as e:
            print(f"❌ [REJECT] Erreur traitement réseau {network} pour post #{post_id}: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return None

    def restore_network(self, post_id: int, network: str, user_id: int) -> Optional[Post]:
        """Restaurer un réseau spécifique d'un post (remettre en brouillon)"""
        try:
            print(f"🔄 [RESTORE] Début restauration du réseau {network} pour post #{post_id} par user #{user_id}")
            
            db_post = self.get_post_by_id(post_id)
            if not db_post:
                print(f"❌ [RESTORE] Post #{post_id} non trouvé")
                return None

            print(f"📰 [RESTORE] Post trouvé: {db_post.title}")
            print(f"🔍 [RESTORE] Validations actuelles: {db_post.network_validations}")

            # Initialiser network_validations si nécessaire
            if not db_post.network_validations:
                db_post.network_validations = {}
                print(f"🆕 [RESTORE] Initialisation des validations pour post #{post_id}")

            # Remettre le réseau en brouillon
            new_validation = {
                "status": "draft",
                "validated_by": user_id,
                "validated_at": datetime.utcnow().isoformat(),
                "rejection_reason": None
            }
            db_post.network_validations[network] = new_validation
            print(f"🔄 [RESTORE] Restauration du réseau {network} pour post #{post_id}")
            print(f"🔍 [RESTORE] Nouvelle validation: {new_validation}")

            # Forcer la mise à jour de l'objet JSON
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(db_post, 'network_validations')
            
            print(f"💾 [RESTORE] Sauvegarde en base de données...")
            self.db.commit()
            self.db.refresh(db_post)
            
            print(f"✅ [RESTORE] Réseau {network} restauré pour post #{post_id}")
            print(f"🔍 [RESTORE] Validations finales: {db_post.network_validations}")
            
            return db_post
            
        except Exception as e:
            print(f"❌ [RESTORE] Erreur restauration réseau {network} pour post #{post_id}: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return None

    def _add_network_to_publication_queue(self, post: Post, network: str):
        """
        Ajouter un réseau spécifique validé à la file d'attente de publication
        """
        try:
            print(f"🚀 [QUEUE] Ajout du réseau {network} à la queue pour post #{post.id}")
            from app.models.publication_queue import PublicationQueue
            from datetime import timedelta, timezone
            
            # Vérifier si le contenu généré existe pour ce réseau
            generated_content = post.generated_content if isinstance(post.generated_content, dict) else {}
            if network not in generated_content:
                print(f"❌ [QUEUE] Aucun contenu généré pour le réseau {network}")
                return
            
            # Récupérer la configuration du réseau pour le délai
            from app.models.network_config import NetworkConfig
            network_config = self.db.query(NetworkConfig).filter(
                NetworkConfig.network == network,
                NetworkConfig.is_active == True
            ).first()
            
            if not network_config:
                print(f"❌ [QUEUE] Configuration réseau {network} non trouvée")
                return
            
            # Calculer l'heure de publication avec délais cumulés par feed et réseau
            now = datetime.now(timezone.utc)
            delay_minutes = network_config.default_publication_delay
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
                # Optimisation : utiliser limit(1) et seulement les colonnes nécessaires
                from app.models.publication import Publication
                last_published = self.db.query(Publication).filter(
                    Publication.feed_id == post.feed_id,
                    Publication.network == network,
                    Publication.is_success == True,
                    Publication.published_at.isnot(None)
                ).order_by(Publication.published_at.desc()).limit(1).first()
                
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
            
            # Récupérer les pages sociales du flux
            social_pages = post.feed.social_pages or {}
            page_id = social_pages.get(network)
            
            if not page_id:
                print(f"❌ [QUEUE] Aucune page configurée pour le réseau {network}")
                return
            
            # Vérifier si ce POST spécifique n'est pas déjà en queue pour ce réseau
            # (vérification rapide : si on a déjà des posts en file, on vérifie aussi ce post_id)
            if existing_queue_posts and any(q.post_id == post.id for q in existing_queue_posts):
                print(f"⚠️ [QUEUE] Post #{post.id} déjà en queue pour {network}")
                return
            
            # Créer l'entrée dans la queue
            queue_entry = PublicationQueue(
                post_id=post.id,
                feed_id=post.feed_id,
                network=network,
                target_page_id=page_id,
                content=generated_content[network],
                media_urls=[post.source_image] if post.source_image else [],
                scheduled_at=scheduled_at,
                status='SCHEDULED'
            )
            
            self.db.add(queue_entry)
            self.db.commit()
            
            print(f"✅ [QUEUE] Réseau {network} ajouté à la queue pour le {scheduled_at}")
            
        except Exception as e:
            print(f"❌ [QUEUE] Erreur ajout réseau {network} à la queue: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()

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
                    
                    # 🔥 DÉLAI PAR FEED ET RÉSEAU : Vérifier s'il y a des posts en file d'attente
                    existing_queue_posts = self.db.query(PublicationQueue).filter(
                        PublicationQueue.feed_id == post.feed_id,
                        PublicationQueue.network == network,
                        PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
                    ).order_by(PublicationQueue.scheduled_at.desc()).all()
                    
                    if existing_queue_posts:
                        # Il y a des posts en file d'attente → appliquer le délai cumulatif
                        last_scheduled = existing_queue_posts[0]  # Le plus récent
                        scheduled_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                        print(f"🔄 DÉLAI CUMULATIF: {len(existing_queue_posts)} post(s) en file pour feed #{post.feed_id} sur {network}")
                        print(f"   → Dernier post programmé: {last_scheduled.scheduled_at.strftime('%H:%M')}")
                        print(f"   → Nouveau post: {scheduled_time.strftime('%H:%M')} (après {delay_minutes}min)")
                    else:
                        # File d'attente vide → vérifier le dernier post publié
                        from app.models.publication import Publication
                        last_published = self.db.query(Publication).filter(
                            Publication.feed_id == post.feed_id,
                            Publication.network == network,
                            Publication.is_success == True,
                            Publication.published_at.isnot(None)
                        ).order_by(Publication.published_at.desc()).first()
                        
                        if last_published and last_published.published_at:
                            # Vérifier si le délai est dépassé depuis le dernier post publié
                            time_since_last = now - last_published.published_at
                            delay_seconds = delay_minutes * 60
                            
                            if time_since_last.total_seconds() >= delay_seconds:
                                # Délai dépassé → publication immédiate
                                scheduled_time = schedule_service._adjust_time_to_schedule(network, now)
                                print(f"✨ DÉLAI DÉPASSÉ: Dernier post publié à {last_published.published_at.strftime('%H:%M')}")
                                print(f"   → Publication immédiate: {scheduled_time.strftime('%H:%M')}")
                            else:
                                # Délai pas encore dépassé → programmer à la fin du délai
                                scheduled_time = last_published.published_at + timedelta(minutes=delay_minutes)
                                scheduled_time = schedule_service._adjust_time_to_schedule(network, scheduled_time)
                                remaining_minutes = int((delay_seconds - time_since_last.total_seconds()) / 60)
                                print(f"⏳ DÉLAI EN COURS: Dernier post publié à {last_published.published_at.strftime('%H:%M')}")
                                print(f"   → Délai restant: {remaining_minutes}min")
                                print(f"   → Programmé à: {scheduled_time.strftime('%H:%M')}")
                        else:
                            # Premier post du feed → programmer normalement avec ajustement horaire
                            base_time = now + timedelta(minutes=delay_minutes)
                            scheduled_time = schedule_service._adjust_time_to_schedule(network, base_time)
                            print(f"✨ Premier post du feed #{post.feed_id} sur {network}")
                            print(f"   → Heure calculée: {base_time.strftime('%H:%M')} → Ajustée: {scheduled_time.strftime('%H:%M')}")
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
                
                # 3. Calculer l'heure de programmation avec FIFO
                delay_minutes = network_config.default_publication_delay
                
                # DÉLAI PAR FEED ET RÉSEAU : Vérifier le dernier post du même feed sur le même réseau
                last_scheduled = self.db.query(PublicationQueue).filter(
                    PublicationQueue.feed_id == post.feed_id,
                    PublicationQueue.network == network,
                    PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
                ).order_by(PublicationQueue.scheduled_at.desc()).first()
                
                if last_scheduled and last_scheduled.scheduled_at:
                    # Programmer APRÈS le dernier post + délai (sans ajustement horaire)
                    scheduled_time = last_scheduled.scheduled_at + timedelta(minutes=delay_minutes)
                    print(f"   🔄 DÉLAI FEED+RÉSEAU: Après post #{last_scheduled.id} à {last_scheduled.scheduled_at.strftime('%H:%M')}")
                    print(f"   → Heure calculée: {scheduled_time.strftime('%H:%M')} (après {delay_minutes}min)")
                else:
                    # Premier post du feed - ajuster aux horaires puis appliquer délai
                    base_time = now + timedelta(minutes=delay_minutes)
                    scheduled_time = schedule_service._adjust_time_to_schedule(network, base_time)
                    print(f"   ✨ Premier post du feed #{post.feed_id} sur {network}")
                    print(f"   → Heure calculée: {base_time.strftime('%H:%M')} → Ajustée: {scheduled_time.strftime('%H:%M')}")
                
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
        """Récupère les posts qui ont des réseaux validés en attente de publication"""
        from app.models.publication_queue import PublicationQueue
        
        # Récupérer les feed_ids qui ont des éléments en queue
        queue_feed_ids = self.db.query(PublicationQueue.feed_id).filter(
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
        ).distinct().all()
        
        feed_ids = [feed_id[0] for feed_id in queue_feed_ids if feed_id[0] is not None]
        
        if not feed_ids:
            return []
        
        # Récupérer les posts correspondants
        posts = self.db.query(Post).options(joinedload(Post.feed)).filter(
            Post.feed_id.in_(feed_ids)
        ).order_by(Post.created_at.desc()).all()
        
        # Enrichir chaque post avec les informations de queue (tous réseaux confondus pour affichage)
        for post in posts:
            queue_items = self.db.query(PublicationQueue).filter(
                PublicationQueue.feed_id == post.feed_id,
                PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
            ).all()
            
            # Ajouter les informations de queue au post
            post.queue_items = queue_items
        
        return posts

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
        return self.db.query(Publication).order_by(Publication.published_at.desc()).limit(limit).all()

    def reject_post(self, post_id: int, user_id: int, rejection_reason: str = None) -> Post:
        """Rejeter un post globalement (rejette tous les réseaux et retire de la queue)"""
        post = self.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post non trouvé")
        
        # Initialiser network_validations si nécessaire
        if not post.network_validations:
            post.network_validations = {}
        
        # Rejeter tous les réseaux générés
        generated_content = post.generated_content if isinstance(post.generated_content, dict) else {}
        all_networks = list(generated_content.keys()) if generated_content else []
        
        for network in all_networks:
            post.network_validations[network] = {
                "status": "rejected",
                "validated_by": user_id,
                "validated_at": datetime.utcnow().isoformat(),
                "rejection_reason": rejection_reason
            }
        
        # Forcer la mise à jour de l'objet JSON
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(post, 'network_validations')
        
        # Retirer tous les éléments de ce post de la queue de publication
        from app.models.publication_queue import PublicationQueue
        queue_items = self.db.query(PublicationQueue).filter(
            PublicationQueue.post_id == post_id,
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING', 'PUBLISHING'])
        ).all()
        
        if queue_items:
            for item in queue_items:
                item.status = 'CANCELLED'
                print(f"🗑️ [REJECT] Élément de queue #{item.id} annulé pour post #{post_id}")
        
        # Marquer le post comme rejeté globalement
        post.status = "rejected"
        post.validated_by = user_id
        post.validated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(post)
        print(f"✅ [REJECT] Post #{post_id} rejeté globalement avec {len(all_networks)} réseau(x)")
        return post

    def restore_post(self, post_id: int) -> Post:
        """Restaurer un post rejeté globalement (restaure tous les réseaux rejetés en brouillon)"""
        post = self.get_post_by_id(post_id)
        if not post:
            raise ValueError("Post non trouvé")
        
        # Initialiser network_validations si nécessaire
        if not post.network_validations:
            post.network_validations = {}
        
        # Restaurer tous les réseaux rejetés en brouillon
        generated_content = post.generated_content if isinstance(post.generated_content, dict) else {}
        all_networks = list(generated_content.keys()) if generated_content else []
        
        for network in all_networks:
            # Si le réseau est rejeté, le restaurer en brouillon
            network_validation = post.network_validations.get(network, {})
            if network_validation.get("status") == "rejected":
                post.network_validations[network] = {
                    "status": "draft",
                    "validated_by": None,
                    "validated_at": None,
                    "rejection_reason": None
                }
            elif network not in post.network_validations:
                # Si le réseau n'a pas de validation, l'initialiser en brouillon
                post.network_validations[network] = {
                    "status": "draft"
                }
        
        # Forcer la mise à jour de l'objet JSON
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(post, 'network_validations')
        
        # Remettre le post en brouillon
        post.status = "draft"
        post.validated_by = None
        post.validated_at = None
        
        self.db.commit()
        self.db.refresh(post)
        print(f"✅ [RESTORE] Post #{post_id} restauré globalement avec {len(all_networks)} réseau(x)")
        return post

