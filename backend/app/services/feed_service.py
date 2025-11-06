from sqlalchemy.orm import Session
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate
from app.services.audit_service import AuditService
from typing import List, Optional
import feedparser
from datetime import datetime
from app.services.llm_service import LLMService


class FeedService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_feed(self, feed: FeedCreate, user_id: int) -> Feed:
        # Log pour debug
        print(f"\n🔍 DEBUG CREATE FEED:")
        print(f"   name: {feed.name}")
        print(f"   target_networks: {feed.target_networks}")
        print(f"   social_pages: {feed.social_pages}")
        print(f"   network_prompts: {feed.network_prompts}")
        print(f"   publication_timing: {feed.publication_timing}")
        
        db_feed = Feed(
            name=feed.name,
            url=str(feed.url),
            frequency_minutes=feed.frequency_minutes,
            custom_prompt=feed.custom_prompt,
            target_networks=feed.target_networks,
            social_pages=feed.social_pages,  # ← Explicitement ajouté
            network_prompts=feed.network_prompts,  # ← Explicitement ajouté
            publication_timing=feed.publication_timing,  # ← Explicitement ajouté
            created_by=user_id
        )
        
        self.db.add(db_feed)
        self.db.commit()
        self.db.refresh(db_feed)
        
        print(f"\n✅ Feed créé - Vérification:")
        print(f"   id: {db_feed.id}")
        print(f"   social_pages APRÈS commit: {db_feed.social_pages}")
        print(f"   network_prompts APRÈS commit: {db_feed.network_prompts}")
        
        # Logger la création du feed
        self.audit_service.log_action(
            action="FEED_CREATE",
            entity_type="feed",
            user_id=user_id,
            entity_id=db_feed.id,
            description=f"Création du flux RSS '{db_feed.name}'",
            metadata={
                "feed_name": db_feed.name,
                "feed_url": str(db_feed.url),
                "target_networks": db_feed.target_networks
            },
            ip_address=None,
            user_agent=None
        )
        
        return db_feed

    def get_feeds(self, user_id: Optional[int] = None) -> List[Feed]:
        """
        Récupère tous les flux
        Si user_id fourni, filtre par créateur (non utilisé actuellement)
        Par défaut: TOUS les flux visibles par tous
        """
        query = self.db.query(Feed)
        # Ne plus filtrer par user_id - partage global
        # if user_id:
        #     query = query.filter(Feed.created_by == user_id)
        return query.all()

    def get_feed_by_id(self, feed_id: int) -> Optional[Feed]:
        feed = self.db.query(Feed).filter(Feed.id == feed_id).first()
        if feed:
            # Debug: Vérifier que les prompts sont bien chargés depuis la BDD
            print(f"🔍 [FEED_SERVICE] Feed #{feed_id} récupéré:")
            print(f"   network_prompts type: {type(feed.network_prompts)}")
            print(f"   network_prompts valeur: {feed.network_prompts}")
            print(f"   network_prompts est None: {feed.network_prompts is None}")
            if feed.network_prompts:
                print(f"   network_prompts contient: {list(feed.network_prompts.keys())}")
                for network, prompt in feed.network_prompts.items():
                    print(f"   - {network}: {prompt[:50] if prompt else 'VIDE'}...")
        return feed

    def update_feed(self, feed_id: int, feed_update: FeedUpdate) -> Optional[Feed]:
        db_feed = self.get_feed_by_id(feed_id)
        if not db_feed:
            return None

        update_data = feed_update.model_dump(exclude_unset=True)
        
        # Log pour debug
        print(f"\n🔍 DEBUG UPDATE FEED #{feed_id}:")
        print(f"   Données reçues: {update_data}")
        print(f"   social_pages AVANT: {db_feed.social_pages}")
        print(f"   network_prompts AVANT: {db_feed.network_prompts}")
        
        # Colonnes JSON qui nécessitent flag_modified
        json_fields = ['network_prompts', 'target_networks', 'publication_timing', 'social_pages']
        
        for field, value in update_data.items():
            print(f"   Mise à jour {field}: {value}")
            setattr(db_feed, field, value)
            
            # Forcer la mise à jour pour les colonnes JSON
            if field in json_fields:
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(db_feed, field)
                print(f"   ✅ flag_modified appliqué pour {field}")

        self.db.commit()
        self.db.refresh(db_feed)
        
        print(f"\n✅ Feed mis à jour - Vérification:")
        print(f"   social_pages APRÈS commit: {db_feed.social_pages}")
        print(f"   network_prompts APRÈS commit: {db_feed.network_prompts}")
        
        return db_feed

    def delete_feed(self, feed_id: int, user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Supprime un flux et tous les éléments associés en cascade"""
        db_feed = self.get_feed_by_id(feed_id)
        if not db_feed:
            return False
        
        # Sauvegarder le nom du flux avant suppression
        feed_name = db_feed.name
        feed_url = str(db_feed.url) if db_feed.url else None
        
        # Compter les éléments avant suppression pour l'audit
        from app.models.post import Post
        from app.models.publication_queue import PublicationQueue
        from app.models.publication import Publication
        
        publications_count = self.db.query(Publication).filter(Publication.feed_id == feed_id).count()
        queue_count = self.db.query(PublicationQueue).filter(PublicationQueue.feed_id == feed_id).count()
        posts_count = self.db.query(Post).filter(Post.feed_id == feed_id).count()
        
        try:
            # 1. Supprimer toutes les publications associées (EN PREMIER car référencées)
            if publications_count > 0:
                # Utiliser synchronize_session=False pour forcer la suppression SQL
                self.db.query(Publication).filter(Publication.feed_id == feed_id).delete(synchronize_session=False)
                print(f"🗑️ Supprimé {publications_count} publication(s) associée(s) au flux #{feed_id}")
            
            # 2. Supprimer tous les éléments de la file d'attente associés
            if queue_count > 0:
                self.db.query(PublicationQueue).filter(PublicationQueue.feed_id == feed_id).delete(synchronize_session=False)
                print(f"🗑️ Supprimé {queue_count} élément(s) de la file d'attente associé(s) au flux #{feed_id}")
            
            # 3. Nettoyer le cache Redis pour les articles de ce flux
            try:
                import redis
                from app.core.config import settings
                redis_client = redis.from_url(settings.REDIS_URL)
                
                # Récupérer tous les posts avant suppression pour obtenir leurs source_url
                posts_to_delete = self.db.query(Post).filter(Post.feed_id == feed_id).all()
                cache_keys_deleted = 0
                
                import hashlib
                
                # Méthode 1: Essayer avec hashlib.md5() (nouveau système déterministe)
                for post in posts_to_delete:
                    if post.source_url:
                        article_hash = hashlib.md5(post.source_url.encode('utf-8')).hexdigest()
                        cache_key = f"article:{article_hash}"
                        
                        if redis_client.delete(cache_key):
                            cache_keys_deleted += 1
                
                # Méthode 2: Supprimer TOUTES les clés article:*
                # Nécessaire car les anciennes clés créées avec hash() non-déterministe
                # ne peuvent pas être retrouvées avec le nouveau système
                # Le cache sera recréé automatiquement lors des prochaines collectes
                try:
                    # Utiliser SCAN pour éviter de bloquer Redis avec KEYS sur de grandes bases
                    cursor = 0
                    all_article_keys = []
                    
                    while True:
                        cursor, keys = redis_client.scan(cursor, match='article:*', count=1000)
                        all_article_keys.extend(keys)
                        if cursor == 0:
                            break
                    
                    if all_article_keys:
                        # Supprimer toutes les clés par batch pour éviter les problèmes de mémoire
                        batch_size = 100
                        for i in range(0, len(all_article_keys), batch_size):
                            batch = all_article_keys[i:i + batch_size]
                            deleted = redis_client.delete(*batch)
                            cache_keys_deleted += deleted
                        
                        print(f"🗑️ Nettoyage complet: supprimé {len(all_article_keys)} clé(s) article:* (cache vidé)")
                except Exception as scan_error:
                    print(f"⚠️ Erreur lors du scan Redis (ignorée): {scan_error}")
                    # Fallback: essayer avec KEYS si SCAN échoue (moins efficace mais fonctionne sur petites bases)
                    try:
                        all_article_keys = redis_client.keys('article:*')
                        if all_article_keys:
                            deleted = redis_client.delete(*all_article_keys)
                            cache_keys_deleted += deleted
                            print(f"🗑️ Nettoyage complet (KEYS fallback): supprimé {len(all_article_keys)} clé(s)")
                    except Exception as keys_error:
                        print(f"⚠️ Erreur lors du nettoyage global Redis (ignorée): {keys_error}")
                
                if cache_keys_deleted > 0:
                    print(f"🗑️ Total nettoyé: {cache_keys_deleted} entrée(s) de cache Redis pour le flux #{feed_id}")
                elif posts_to_delete:
                    print(f"ℹ️ Aucune clé de cache Redis trouvée pour le flux #{feed_id} ({len(posts_to_delete)} posts)")
            except Exception as redis_error:
                # Ne pas bloquer la suppression si Redis échoue
                print(f"⚠️ Erreur lors du nettoyage du cache Redis (ignorée): {redis_error}")
            
            # 4. Supprimer tous les posts associés (draft, validated, rejected)
            if posts_count > 0:
                self.db.query(Post).filter(Post.feed_id == feed_id).delete(synchronize_session=False)
                print(f"🗑️ Supprimé {posts_count} post(s) associé(s) au flux #{feed_id}")
            
            # Commit intermédiaire pour s'assurer que tout est supprimé
            self.db.flush()
            
            # 5. Supprimer le flux lui-même
            self.db.delete(db_feed)
            self.db.commit()
            
            print(f"✅ Flux #{feed_id} '{feed_name}' supprimé avec succès (cascade)")
            
            # Logger la suppression du feed
            self.audit_service.log_action(
                action="FEED_DELETE",
                entity_type="feed",
                user_id=user_id,
                entity_id=feed_id,
                description=f"Suppression du flux RSS '{feed_name}'",
                metadata={
                    "feed_name": feed_name,
                    "feed_url": feed_url,
                    "publications_count": publications_count,
                    "queue_count": queue_count,
                    "posts_count": posts_count
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Erreur lors de la suppression du flux #{feed_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def fetch_feed_articles(self, feed: Feed) -> List[dict]:
        """Récupère les nouveaux articles d'un flux RSS"""
        try:
            import requests
            import ssl
            from datetime import timedelta
            
            # Vérifier si le flux doit être collecté selon sa fréquence
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
                    print(f"Flux {feed.name} collecté récemment, attente de {required_interval - time_since_last_fetch}")
                    return []
            
            # Configuration pour contourner les problèmes SSL
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Télécharger le flux avec requests
            response = requests.get(feed.url, verify=False, timeout=30)
            response.raise_for_status()
            
            # Parser le contenu avec feedparser
            parsed_feed = feedparser.parse(response.content)
            articles = []
            
            # Filtrer les articles récents (dernières 24h par défaut)
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            for entry in parsed_feed.entries:
                # Vérifier la date de publication
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        published_time = None
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        published_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        published_time = None
                
                # Si pas de date, accepter l'article
                if published_time is None or published_time > cutoff_time:
                    source_url = entry.get('link', '')
                    
                    # Vérifier si l'article existe déjà dans la base de données
                    if source_url and self._article_exists(source_url):
                        print(f"Article déjà existant: {source_url}")
                        continue
                    
                    # Extraire le contenu (summary ou description)
                    content = entry.get('summary', '') or entry.get('description', '')
                    
                    articles.append({
                        'title': entry.get('title', ''),
                        'content': content,
                        'source_url': source_url,
                        'source_image': self._extract_image(entry),
                        'published': entry.get('published_parsed')
                    })
            
            # Mettre à jour la dernière récupération
            feed.last_fetch = datetime.now(timezone.utc)
            self.db.commit()
            
            print(f"Flux {feed.name}: {len(articles)} nouveaux articles trouvés")
            return articles
        except Exception as e:
            print(f"Erreur lors de la récupération du flux {feed.name}: {e}")
            return []

    def _article_exists(self, source_url: str) -> bool:
        """Vérifie si un article avec cette URL existe déjà"""
        from app.models.post import Post
        existing_post = self.db.query(Post).filter(Post.source_url == source_url).first()
        return existing_post is not None

    def _extract_image(self, entry) -> Optional[str]:
        """Extrait l'URL de l'image de l'article"""
        from bs4 import BeautifulSoup
        import re
        
        # Rechercher dans différents champs possibles
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    return media.get('url')
        
        # Vérifier les enclosures (comme dans les flux La Tribune)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            print(f"🔍 DEBUG La Tribune: enclosures trouvés: {len(entry.enclosures)}")
            for i, enclosure in enumerate(entry.enclosures):
                print(f"🔍 DEBUG La Tribune: enclosure[{i}] = {enclosure}, type = {type(enclosure)}")
                # feedparser peut stocker l'enclosure comme dict ou objet
                if isinstance(enclosure, dict):
                    print(f"🔍 DEBUG La Tribune: dict keys = {list(enclosure.keys())}")
                    print(f"🔍 DEBUG La Tribune: dict values = {enclosure}")
                    enclosure_type = enclosure.get('type', '')
                    print(f"🔍 DEBUG La Tribune: type = {enclosure_type}")
                    # Vérifier si c'est une image (ou si le type n'est pas spécifié mais qu'il y a une URL)
                    if (enclosure_type and enclosure_type.startswith('image/')) or not enclosure_type:
                        # feedparser peut stocker l'URL dans 'href', 'url', ou 'link'
                        # Essayer dans cet ordre: url (RSS 2.0 standard), href (feedparser normalisé), link
                        image_url = enclosure.get('url') or enclosure.get('href') or enclosure.get('link')
                        print(f"🔍 DEBUG La Tribune: image_url = {image_url}")
                        if image_url:
                            print(f"🖼️ Image trouvée via enclosure (dict): {image_url}")
                            return image_url
                else:
                    # Si c'est un objet, essayer d'accéder aux attributs directement
                    try:
                        attrs = [a for a in dir(enclosure) if not a.startswith('_')]
                        print(f"🔍 DEBUG La Tribune: objet attributes = {attrs}")
                        enclosure_type = getattr(enclosure, 'type', None)
                        print(f"🔍 DEBUG La Tribune: type = {enclosure_type}")
                        # Vérifier si c'est une image (ou si le type n'est pas spécifié mais qu'il y a une URL)
                        if (enclosure_type and str(enclosure_type).startswith('image/')) or not enclosure_type:
                            # Essayer dans cet ordre: url (RSS 2.0 standard), href (feedparser normalisé), link
                            image_url = getattr(enclosure, 'url', None) or getattr(enclosure, 'href', None) or getattr(enclosure, 'link', None)
                            print(f"🔍 DEBUG La Tribune: image_url = {image_url}")
                            if image_url:
                                print(f"🖼️ Image trouvée via enclosure (objet): {image_url}")
                                return image_url
                    except Exception as e:
                        print(f"⚠️ Erreur lors de l'extraction d'enclosure (objet): {e}")
                        continue
        
        # Rechercher dans les liens (feedparser peut aussi stocker les enclosures ici)
        if hasattr(entry, 'links') and entry.links:
            print(f"🔍 DEBUG La Tribune: links trouvés: {len(entry.links)}")
            for i, link in enumerate(entry.links):
                print(f"🔍 DEBUG La Tribune: link[{i}] = {link}")
                link_type = link.get('type', '') if isinstance(link, dict) else getattr(link, 'type', '')
                if link_type and link_type.startswith('image/'):
                    image_url = link.get('href') or link.get('url') if isinstance(link, dict) else getattr(link, 'href', None) or getattr(link, 'url', None)
                    print(f"🔍 DEBUG La Tribune: image_url dans links = {image_url}")
                    if image_url:
                        print(f"🖼️ Image trouvée via links: {image_url}")
                        return image_url
        
        # Rechercher dans le contenu HTML pour des images avec BeautifulSoup
        if hasattr(entry, 'summary') and entry.summary:
            try:
                soup = BeautifulSoup(entry.summary, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    return img_tag.get('src')
            except Exception:
                pass
            
            # Fallback avec regex
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            matches = re.findall(img_pattern, entry.summary, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Rechercher dans le contenu
        if hasattr(entry, 'content') and entry.content:
            content_value = entry.content[0].value if isinstance(entry.content, list) and entry.content else entry.content
            if isinstance(content_value, str):
                try:
                    soup = BeautifulSoup(content_value, 'html.parser')
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        return img_tag.get('src')
                except Exception:
                    pass
                
                # Fallback avec regex
                img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
                matches = re.findall(img_pattern, content_value, re.IGNORECASE)
                if matches:
                    return matches[0]
        
        # Rechercher dans le contenu HTML pour des images avec des patterns plus larges
        if hasattr(entry, 'summary') and entry.summary:
            # Pattern plus large pour capturer plus d'images
            img_pattern = r'<img[^>]+src=["\']([^"\']*\.(?:jpg|jpeg|png|gif|webp|svg))["\'][^>]*>'
            matches = re.findall(img_pattern, entry.summary, re.IGNORECASE)
            if matches:
                return matches[0]
        
        if hasattr(entry, 'content') and entry.content:
            content_value = entry.content[0].value if isinstance(entry.content, list) and entry.content else entry.content
            if isinstance(content_value, str):
                img_pattern = r'<img[^>]+src=["\']([^"\']*\.(?:jpg|jpeg|png|gif|webp|svg))["\'][^>]*>'
                matches = re.findall(img_pattern, content_value, re.IGNORECASE)
                if matches:
                    return matches[0]
        
        # Aucune image trouvée
        print(f"⚠️ Aucune image trouvée pour l'article: {entry.get('title', 'N/A')[:50]}...")
        return None

    def generate_posts_for_article(self, feed: Feed, article: dict, target_networks: List[str] = None) -> dict:
        """
        Génère des posts pour tous les réseaux définis à partir d'un article
        """
        if target_networks is None:
            # Définir les réseaux par défaut
            target_networks = ["facebook", "linkedin", "x"]
        
        llm_service = LLMService()
        
        # Construire le contenu de l'article pour le LLM
        article_content = f"""
        Titre: {article['title']}
        Contenu: {article['content']}
        URL source: {article['source_url']}
        """
        
        # Générer les posts pour tous les réseaux en utilisant les prompts spécifiques
        generated_posts = llm_service.generate_social_media_posts(
            article_content=article_content,
            custom_prompt=feed.custom_prompt,
            network_prompts=feed.network_prompts,
            target_networks=target_networks,
            source_url=article.get('source_url'),
            title=article.get('title'),
            source_image=article.get('source_image')
        )
        
        return {
            "article": article,
            "generated_posts": generated_posts,
            "target_networks": target_networks,
            "feed_id": feed.id,
            "feed_name": feed.name
        }
