from celery import current_task
from app.workers.celery_app import celery_app
from app.services.feed_service import FeedService
from app.services.post_service import PostService
from app.services.llm_service import LLMService
from app.core.database import SessionLocal
from app.schemas.post import PostCreate
import redis
from app.core.config import settings
import json


# Connexion Redis pour le cache
redis_client = redis.from_url(settings.REDIS_URL)


@celery_app.task
def fetch_and_process_feed(feed_id: int):
    """Tâche pour récupérer et traiter les articles d'un flux RSS"""
    db = SessionLocal()
    try:
        feed_service = FeedService(db)
        post_service = PostService(db)
        llm_service = LLMService()
        
        # Récupérer le flux
        feed = feed_service.get_feed_by_id(feed_id)
        if not feed or not feed.is_active:
            return {"status": "skipped", "reason": "feed_not_active"}
        
        # Récupérer les articles
        articles = feed_service.fetch_feed_articles(feed)
        
        processed_count = 0
        for article in articles:
            try:
                # Vérifier si l'article a déjà été traité
                article_hash = hash(article['source_url'])
                if redis_client.get(f"article:{article_hash}"):
                    print(f"⏭️  Article déjà traité (cache): {article['title'][:50]}...")
                    continue
                
                # Définir les réseaux cibles pour ce flux
                target_networks = []
                if feed.target_networks and len(feed.target_networks) > 0:
                    # Si des réseaux spécifiques sont définis, les utiliser
                    target_networks = feed.target_networks
                else:
                    # Sinon, générer pour tous les réseaux
                    target_networks = ["facebook", "linkedin", "x"]
            
                # Préparer le contenu de l'article avec le lien source
                article_content_with_link = f"Titre: {article['title']}\nContenu: {article['content']}"
                if article.get('source_url'):
                    article_content_with_link += f"\n\nLien de l'article: {article['source_url']}"
                
                # Générer les posts pour tous les réseaux définis en utilisant les prompts spécifiques
                generated_content = llm_service.generate_social_media_posts(
                    article_content=article_content_with_link,
                    custom_prompt=feed.custom_prompt,
                    network_prompts=feed.network_prompts,
                    target_networks=target_networks,
                    source_url=article.get('source_url')  # Passer le lien séparément aussi
                )
                
                # Créer le post
                post_data = PostCreate(
                    title=article['title'],
                    content=article['content'],
                    source_url=article['source_url'],
                    source_image=article['source_image'],
                    feed_id=feed_id
                )
                
                post = post_service.create_post(post_data)
                
                # Mettre à jour le contenu généré pour tous les réseaux
                post.generated_content = generated_content
                post.status = "draft"  # Toujours en brouillon - validation manuelle requise
                
                db.commit()
                print(f"📝 Post créé en brouillon: {post.title[:50]}...")
                
                # Marquer l'article comme traité
                redis_client.setex(f"article:{article_hash}", 86400 * 30, "processed")  # 30 jours
                processed_count += 1
                print(f"✅ Article traité: {article['title'][:50]}...")
                
            except Exception as article_error:
                print(f"❌ Erreur traitement article '{article.get('title', 'Unknown')[:50]}': {article_error}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue
        
        print(f"\n📊 Résumé: {processed_count}/{len(articles)} articles traités")
        return {"status": "success", "processed_count": processed_count}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def publish_post(post_id: int, networks: list = None):
    """Tâche pour publier un post sur les réseaux sociaux"""
    db = SessionLocal()
    try:
        post_service = PostService(db)
        
        post = post_service.get_post_by_id(post_id)
        if not post or post.status != "validated":
            return {"status": "error", "message": "Post not found or not validated"}
        
        if not post.generated_content:
            return {"status": "error", "message": "No generated content"}
        
        networks_to_publish = networks or ["facebook", "linkedin", "x"]
        results = []
        
        for network in networks_to_publish:
            if network in post.generated_content:
                content = post.generated_content[network]
                
                # Ici, vous intégreriez les APIs des réseaux sociaux
                # Pour l'instant, on simule la publication
                success = simulate_social_media_publish(network, content)
                
                if success:
                    published_url = f"https://{network}.com/post/{post_id}"
                    post_service.create_publication(
                        post_id=post_id,
                        network=network,
                        content=content,
                        published_url=published_url,
                        is_success=True
                    )
                    results.append({"network": network, "status": "success"})
                else:
                    post_service.create_publication(
                        post_id=post_id,
                        network=network,
                        content=content,
                        is_success=False,
                        error_message="Publication failed"
                    )
                    results.append({"network": network, "status": "failed"})
        
        # Marquer le post comme publié si au moins une publication a réussi
        if any(r["status"] == "success" for r in results):
            post_service.mark_post_published(post_id)
        
        return {"status": "completed", "results": results}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def simulate_social_media_publish(network: str, content: str) -> bool:
    """Simule la publication sur un réseau social"""
    # Dans une vraie implémentation, vous utiliseriez les APIs officielles
    # Twitter API, LinkedIn API, Facebook API, etc.
    print(f"Publishing to {network}: {content[:100]}...")
    return True  # Simuler un succès


@celery_app.task
def process_all_active_feeds():
    """Tâche périodique pour traiter tous les flux actifs"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        feed_service = FeedService(db)
        feeds = feed_service.get_feeds()
        
        active_feeds = [feed for feed in feeds if feed.is_active]
        scheduled_count = 0
        
        for feed in active_feeds:
            # Vérifier si le flux doit être collecté selon sa fréquence
            should_collect = True
            if feed.last_fetch:
                # Utiliser datetime.now() avec timezone UTC
                from datetime import timezone
                now = datetime.now(timezone.utc)
                last_fetch = feed.last_fetch
                
                # Convertir last_fetch en UTC si nécessaire
                if last_fetch.tzinfo is None:
                    # Si last_fetch est naif, l'assumer UTC
                    last_fetch = last_fetch.replace(tzinfo=timezone.utc)
                else:
                    # Convertir en UTC
                    last_fetch = last_fetch.astimezone(timezone.utc)
                
                time_since_last_fetch = now - last_fetch
                required_interval = timedelta(minutes=feed.frequency_minutes)
                
                if time_since_last_fetch < required_interval:
                    print(f"Flux {feed.name} collecté récemment, prochaine collecte dans {required_interval - time_since_last_fetch}")
                    should_collect = False
            
            if should_collect:
                # Programmer le traitement du flux
                fetch_and_process_feed.delay(feed.id)
                scheduled_count += 1
                print(f"Flux {feed.name} programmé pour collecte")
        
        return {"status": "scheduled", "feeds_count": len(active_feeds), "scheduled_count": scheduled_count}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def manage_post_state_transitions():
    """Gérer les transitions de statut des posts : SCHEDULED → WAITING_HOURS → PENDING → PUBLISHING"""
    from app.models.publication_queue import PublicationQueue
    from app.services.schedule_service import ScheduleService
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        print("🔄 Gestion des transitions de statut...")
        schedule_service = ScheduleService(db)
        now = datetime.now(timezone.utc)
        
        # 1. SCHEDULED → PENDING si l'heure est atteinte et horaires OK
        scheduled_items = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'SCHEDULED',
            PublicationQueue.is_paused == False,
            PublicationQueue.scheduled_at <= now
        ).all()
        
        for item in scheduled_items:
            schedule_status = schedule_service.is_publication_allowed_now(item.network)
            if schedule_status["allowed"]:
                item.status = 'PENDING'
                print(f"   ✅ #{item.id} SCHEDULED → PENDING (heure atteinte + horaires OK)")
            else:
                # Reporter au prochain créneau autorisé
                config = schedule_service.get_active_config_for_network_now(item.network)
                if config:
                    next_time = schedule_service._calculate_next_available_time(config)
                    if next_time != "Maintenant":
                        try:
                            hour, minute = map(int, next_time.split(':'))
                            new_scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            item.scheduled_at = new_scheduled
                            item.status = 'WAITING_HOURS'
                            print(f"   🕐 #{item.id} reporté à {next_time} (WAITING_HOURS)")
                        except:
                            pass
        
        # 2. WAITING_HOURS → SCHEDULED si horaires ouverts
        waiting_items = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'WAITING_HOURS',
            PublicationQueue.is_paused == False
        ).all()
        
        for item in waiting_items:
            schedule_status = schedule_service.is_publication_allowed_now(item.network)
            if schedule_status["allowed"]:
                # Vérifier si l'heure programmée est dans le futur
                if item.scheduled_at > now:
                    item.status = 'SCHEDULED'
                    print(f"   🕐 #{item.id} WAITING_HOURS → SCHEDULED (horaires OK)")
                elif item.scheduled_at <= now:
                    item.status = 'PENDING'
                    print(f"   ⏰ #{item.id} WAITING_HOURS → PENDING (heure dépassée + horaires OK)")
        
        db.commit()
        print(f"✅ Transitions gérées: {len(scheduled_items)} SCHEDULED, {len(waiting_items)} WAITING_HOURS")
        
    except Exception as e:
        print(f"❌ Erreur transitions de statut: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task
def recovery_failed_publications():
    """Tâche de rattrapage pour les posts qui n'ont pas été publiés"""
    from app.models.publication_queue import PublicationQueue
    from app.services.schedule_service import ScheduleService
    from datetime import datetime, timezone, timedelta
    
    db = SessionLocal()
    try:
        print("🔧 Tâche de rattrapage...")
        now = datetime.now(timezone.utc)
        
        # Posts PENDING depuis plus de 5 minutes (probablement bloqués)
        stuck_pending = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'PENDING',
            PublicationQueue.is_paused == False,
            PublicationQueue.created_at <= now - timedelta(minutes=5)
        ).all()
        
        for item in stuck_pending:
            print(f"   🔧 Post #{item.id} bloqué en PENDING depuis {item.created_at}")
            # Forcer la publication
            item.status = 'PENDING'  # Reste PENDING pour être repris par process_publication_queue
            print(f"   ✅ Post #{item.id} marqué pour reprise")
        
        # Posts PUBLISHING depuis plus de 10 minutes (probablement en erreur)
        stuck_publishing = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'PUBLISHING',
            PublicationQueue.created_at <= now - timedelta(minutes=10)
        ).all()
        
        for item in stuck_publishing:
            print(f"   🔧 Post #{item.id} bloqué en PUBLISHING depuis {item.created_at}")
            # Marquer comme échec et reprogrammer
            item.status = 'FAILED'
            item.error_message = "Timeout - Publication bloquée plus de 10 minutes"
            print(f"   ❌ Post #{item.id} marqué comme échec")
        
        if stuck_pending or stuck_publishing:
            db.commit()
            print(f"✅ Rattrapage: {len(stuck_pending)} PENDING, {len(stuck_publishing)} PUBLISHING traités")
        else:
            print("✅ Aucun post bloqué détecté")
        
    except Exception as e:
        print(f"❌ Erreur tâche de rattrapage: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task
def process_publication_queue():
    """
    Tâche pour traiter la file d'attente de publication
    Utilise les délais configurés PAR FLUX (publication_timing)
    Complètement DYNAMIQUE - lit la config depuis la BDD
    """
    from app.models.publication_queue import PublicationQueue
    from app.services.publication_service import PublicationService
    from app.services.schedule_service import ScheduleService
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        schedule_service = ScheduleService(db)
        
        # Récupérer tous les posts en attente dont l'heure de publication est passée
        # 1. Mettre à jour les statuts SCHEDULED vers PENDING si l'heure est atteinte
        scheduled_items = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'SCHEDULED',
            PublicationQueue.is_paused == False,
            PublicationQueue.scheduled_at <= now
        ).all()
        
        for item in scheduled_items:
            # Vérifier si on est dans les horaires autorisés
            schedule_status = schedule_service.is_publication_allowed_now(item.network)
            if schedule_status["allowed"]:
                item.status = 'PENDING'
                print(f"⏰ Statut mis à jour: {item.network} #{item.id} SCHEDULED → PENDING (horaires OK)")
            else:
                # Reporter au prochain créneau autorisé
                config = schedule_service.get_active_config_for_network_now(item.network)
                next_time = schedule_service._calculate_next_available_time(config)
                if next_time != "Maintenant":
                    from datetime import datetime
                    # Parser next_time et mettre à jour scheduled_at
                    try:
                        hour, minute = map(int, next_time.split(':'))
                        new_scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        item.scheduled_at = new_scheduled
                        print(f"🕐 Repoussé: {item.network} #{item.id} vers {next_time}")
                    except:
                        pass
        
        # 2. Mettre à jour les statuts WAITING_HOURS vers SCHEDULED si horaires atteints
        waiting_items = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'WAITING_HOURS',
            PublicationQueue.is_paused == False
        ).all()
        
        for item in waiting_items:
            schedule_status = schedule_service.is_publication_allowed_now(item.network)
            if schedule_status["allowed"] and item.scheduled_at <= now:
                item.status = 'PENDING'
                print(f"🕐 Statut mis à jour: {item.network} #{item.id} WAITING_HOURS → PENDING (horaires atteints)")
            elif schedule_status["allowed"]:
                item.status = 'SCHEDULED'
                print(f"🕐 Statut mis à jour: {item.network} #{item.id} WAITING_HOURS → SCHEDULED (horaires OK)")
        
        db.commit()
        
        # 3. Récupérer les items PENDING prêts à publier
        pending_items = db.query(PublicationQueue).filter(
            PublicationQueue.status == 'PENDING',
            PublicationQueue.is_paused == False,
            PublicationQueue.scheduled_at <= now
        ).order_by(PublicationQueue.scheduled_at.asc()).limit(10).all()
        
        processed_count = 0
        publication_service = PublicationService()
        
        for item in pending_items:
            try:
                print(f"📤 Publication #{item.id} sur {item.network} (programmée pour {item.scheduled_at})")
                
                # Les posts PENDING sont prêts à publier, pas besoin de vérifier les horaires
                # (ils ont déjà été vérifiés lors de la transition SCHEDULED -> PENDING)
                
                print(f"🚀 DÉBUT publication #{item.id} sur {item.network}")
                
                # Marquer comme en cours de publication
                item.status = 'PUBLISHING'
                db.commit()
                
                # Publier via Blotato en utilisant le destination_id configuré
                success, message, url = publication_service.publish_to_network(
                    network=item.network,
                    content=item.content,
                    media_urls=item.media_urls,
                    target_page_id=item.target_page_id  # Passer la page cible
                )
                
                if success:
                    item.status = 'PUBLISHED'
                    item.published_at = now
                    item.publication_url = url
                    print(f"✅ Publication réussie sur {item.network}: {url}")
                    
                    # Enregistrer dans la table publications pour l'historique
                    from app.models.publication import Publication
                    publication = Publication(
                        post_id=item.post_id,
                        feed_id=item.feed_id,  # Pour filtrage par flux dans l'historique
                        network=item.network,
                        content=item.content,
                        published_url=url,
                        is_success=True,
                        published_at=now
                    )
                    db.add(publication)
                    
                else:
                    item.status = 'FAILED'
                    item.error_message = message
                    print(f"❌ Échec de publication sur {item.network}: {message}")
                    
                    # Enregistrer l'échec dans la table publications
                    from app.models.publication import Publication
                    publication = Publication(
                        post_id=item.post_id,
                        feed_id=item.feed_id,  # Pour filtrage par flux dans l'historique
                        network=item.network,
                        content=item.content,
                        published_url=None,
                        is_success=False,
                        error_message=message,
                        published_at=now
                    )
                    db.add(publication)
                
                db.commit()
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Erreur publication item {item.id}: {e}")
                item.status = 'FAILED'
                item.error_message = str(e)
                db.commit()
        
        if processed_count > 0:
            print(f"✅ {processed_count} publication(s) traitée(s)")
        
        return {
            "status": "success", 
            "processed_count": processed_count,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement de la file d'attente: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
