from sqlalchemy.orm import Session
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate
from typing import List, Optional
import feedparser
from datetime import datetime
from app.services.llm_service import LLMService


class FeedService:
    def __init__(self, db: Session):
        self.db = db

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
        return self.db.query(Feed).filter(Feed.id == feed_id).first()

    def update_feed(self, feed_id: int, feed_update: FeedUpdate) -> Optional[Feed]:
        db_feed = self.get_feed_by_id(feed_id)
        if not db_feed:
            return None

        update_data = feed_update.model_dump(exclude_unset=True)
        
        # Log pour debug
        print(f"\n🔍 DEBUG UPDATE FEED #{feed_id}:")
        print(f"   Données reçues: {update_data}")
        print(f"   social_pages AVANT: {db_feed.social_pages}")
        
        for field, value in update_data.items():
            print(f"   Mise à jour {field}: {value}")
            setattr(db_feed, field, value)

        self.db.commit()
        self.db.refresh(db_feed)
        
        print(f"\n✅ Feed mis à jour - Vérification:")
        print(f"   social_pages APRÈS commit: {db_feed.social_pages}")
        print(f"   network_prompts APRÈS commit: {db_feed.network_prompts}")
        
        return db_feed

    def delete_feed(self, feed_id: int) -> bool:
        """Supprime un flux et tous les éléments associés en cascade"""
        db_feed = self.get_feed_by_id(feed_id)
        if not db_feed:
            return False
        
        # Sauvegarder le nom du flux avant suppression
        feed_name = db_feed.name
        
        try:
            # Importer les modèles nécessaires
            from app.models.post import Post
            from app.models.publication_queue import PublicationQueue
            from app.models.publication import Publication
            
            # 1. Supprimer toutes les publications associées (EN PREMIER car référencées)
            publications_count = self.db.query(Publication).filter(Publication.feed_id == feed_id).count()
            if publications_count > 0:
                # Utiliser synchronize_session=False pour forcer la suppression SQL
                self.db.query(Publication).filter(Publication.feed_id == feed_id).delete(synchronize_session=False)
                print(f"🗑️ Supprimé {publications_count} publication(s) associée(s) au flux #{feed_id}")
            
            # 2. Supprimer tous les éléments de la file d'attente associés
            queue_count = self.db.query(PublicationQueue).filter(PublicationQueue.feed_id == feed_id).count()
            if queue_count > 0:
                self.db.query(PublicationQueue).filter(PublicationQueue.feed_id == feed_id).delete(synchronize_session=False)
                print(f"🗑️ Supprimé {queue_count} élément(s) de la file d'attente associé(s) au flux #{feed_id}")
            
            # 3. Supprimer tous les posts associés (draft, validated, rejected)
            posts_count = self.db.query(Post).filter(Post.feed_id == feed_id).count()
            if posts_count > 0:
                self.db.query(Post).filter(Post.feed_id == feed_id).delete(synchronize_session=False)
                print(f"🗑️ Supprimé {posts_count} post(s) associé(s) au flux #{feed_id}")
            
            # Commit intermédiaire pour s'assurer que tout est supprimé
            self.db.flush()
            
            # 4. Supprimer le flux lui-même
            self.db.delete(db_feed)
            self.db.commit()
            
            print(f"✅ Flux #{feed_id} '{feed_name}' supprimé avec succès (cascade)")
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
            for enclosure in entry.enclosures:
                # feedparser peut stocker l'enclosure comme dict ou objet
                if isinstance(enclosure, dict):
                    enclosure_type = enclosure.get('type', '')
                    if enclosure_type and enclosure_type.startswith('image/'):
                        # feedparser peut stocker l'URL dans 'href', 'url', ou 'link'
                        image_url = enclosure.get('href') or enclosure.get('url') or enclosure.get('link')
                        if image_url:
                            print(f"🖼️ Image trouvée via enclosure (dict): {image_url}")
                            return image_url
                else:
                    # Si c'est un objet, essayer d'accéder aux attributs directement
                    try:
                        if hasattr(enclosure, 'type') and str(enclosure.type).startswith('image/'):
                            image_url = getattr(enclosure, 'href', None) or getattr(enclosure, 'url', None) or getattr(enclosure, 'link', None)
                            if image_url:
                                print(f"🖼️ Image trouvée via enclosure (objet): {image_url}")
                                return image_url
                    except Exception as e:
                        print(f"⚠️ Erreur lors de l'extraction d'enclosure (objet): {e}")
                        continue
        
        # Rechercher dans les liens
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('image/'):
                    return link.get('href')
        
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
            target_networks=target_networks
        )
        
        return {
            "article": article,
            "generated_posts": generated_posts,
            "target_networks": target_networks,
            "feed_id": feed.id,
            "feed_name": feed.name
        }
