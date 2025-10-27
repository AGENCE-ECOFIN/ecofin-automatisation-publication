"""
Service de publication centralisé utilisant l'API Blotato
Documentation: https://help.blotato.com/api/start
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app.core.config import settings
from app.services.image_service import ImageService
from app.services.minio_service import MinIOService
import logging

logger = logging.getLogger(__name__)


class BlotatoService:
    """Service centralisé pour la publication via l'API Blotato"""
    
    def __init__(self):
        # Configuration de l'API Blotato
        self.api_url = "https://backend.blotato.com/v2"
        self.api_key = settings.BLOTATO_API_KEY
        
        # Mapping des noms de réseaux vers les platforms Blotato (3 réseaux uniquement)
        # Note: Les platforms sont en minuscules dans l'API Blotato
        self.network_mapping = {
            'linkedin': 'linkedin',
            'x': 'twitter',  # X s'appelle 'twitter' dans l'API Blotato
            'twitter': 'twitter',
            'facebook': 'facebook'
        }
        
        # Headers pour l'API Blotato
        self.headers = {
            'blotato-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _get_account_id(self, network: str, target_page_id: str = None) -> Optional[str]:
        """
        Récupère l'ID du compte Blotato pour un réseau donné depuis blotato_accounts.json
        
        Args:
            network: Nom du réseau ('linkedin', 'x', 'facebook', etc.)
            target_page_id: ID de la page/compte spécifique à utiliser (optionnel)
            
        Returns:
            L'ID du compte ou None si non trouvé
        """
        try:
            import os
            from pathlib import Path
            
            # Chemin vers le fichier blotato_accounts.json
            blotato_file = Path(__file__).parent.parent.parent / "blotato_accounts.json"
            
            if not blotato_file.exists():
                logger.warning(f"Fichier blotato_accounts.json non trouvé: {blotato_file}")
                return None
                
            with open(blotato_file, 'r', encoding='utf-8') as f:
                blotato_accounts = json.load(f)
            
            network_accounts = blotato_accounts.get(network.lower(), [])
            if not network_accounts or len(network_accounts) == 0:
                logger.warning(f"Aucun compte trouvé pour {network}")
                return None
            
            # Si un target_page_id est fourni, chercher le compte correspondant
            if target_page_id:
                for account in network_accounts:
                    # Pour X, comparer directement avec accountId
                    if network.lower() == 'x':
                        if account.get('accountId') == target_page_id:
                            logger.info(f"Account ID trouvé pour {network} avec target_page_id {target_page_id}: {account.get('accountId')}")
                            return account.get('accountId')
                    # Pour Facebook/LinkedIn, chercher dans les pages
                    else:
                        pages = account.get('pages', [])
                        for page in pages:
                            if page.get('pageId') == target_page_id:
                                logger.info(f"Account ID trouvé pour {network} avec pageId {target_page_id}: {account.get('accountId')}")
                                return account.get('accountId')
                
                logger.warning(f"Aucun compte trouvé pour {network} avec target_page_id {target_page_id}")
                return None
            
            # Fallback: récupérer le premier compte pour le réseau demandé
            account_id = network_accounts[0].get('accountId')
            logger.info(f"Account ID récupéré pour {network} (fallback): {account_id}")
            return account_id
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'account ID pour {network}: {e}")
            return None
    
    def publish_to_network(
        self, 
        network: str, 
        content: str, 
        media_urls: List[str] = None,
        scheduled_at: Optional[datetime] = None,
        target_page_id: str = None,
        is_direct_post: bool = False
    ) -> Tuple[bool, str, Optional[str], Optional[List[str]], Optional[str]]:
        """
        Publie un contenu sur un réseau social via l'API Blotato
        Documentation: https://help.blotato.com/api/api-reference/publish-post
        
        Args:
            network: Nom du réseau ('linkedin', 'x', 'facebook')
            content: Contenu à publier
            media_urls: URLs des médias (optionnel)
            scheduled_at: Date de publication programmée (optionnel)
            target_page_id: ID de la page cible (optionnel)
            is_direct_post: True si c'est un post direct (upload MinIO), False si post programmé (URLs publiques)
            
        Returns:
            Tuple[success, message, publication_url, processed_media_urls, post_submission_id]
        """
        try:
            # Vérifier que le réseau est supporté
            if network.lower() not in self.network_mapping:
                return False, f"Réseau {network} non supporté par Blotato", None, None, None
            
            # Récupérer l'ID du compte
            account_id = self._get_account_id(network.lower(), target_page_id)
            if not account_id:
                return False, f"Aucun compte configuré pour {network}", None, None, None
            
            # Récupérer le nom de la platform Blotato (lowercase pour l'API)
            platform = self.network_mapping[network.lower()].lower()
            
            # Traiter les images selon le type de post
            processed_media_urls = media_urls if media_urls else []
            if processed_media_urls:
                logger.info(f"Traitement des images pour {network}: {len(processed_media_urls)} images")
                
                if is_direct_post:
                    # Posts directs : Uploader vers MinIO
                    logger.info("Post direct détecté - Upload vers MinIO")
                    minio_service = MinIOService()
                    
                    processed_urls = []
                    for media_url in processed_media_urls:
                        if media_url.startswith('data:'):
                            # Images en base64 - upload vers MinIO
                            logger.info(f"Upload base64 vers MinIO: {media_url[:50]}...")
                            base64_urls = minio_service.upload_images_from_base64_list([media_url])
                            processed_urls.extend(base64_urls)
                            logger.info(f"URLs base64 ajoutées: {len(base64_urls)} URLs")
                        elif media_url.startswith('/uploads/'):
                            # Chemin local - utiliser mapping vers MinIO
                            logger.info(f"Recherche mapping MinIO pour: {media_url}")
                            filename = media_url.split('/')[-1]
                            
                            # Charger le mapping local -> MinIO
                            try:
                                from pathlib import Path
                                mapping_file = Path("local_to_minio_mapping.json")
                                
                                if mapping_file.exists():
                                    with open(mapping_file, 'r') as f:
                                        mapping = json.load(f)
                                    
                                    if filename in mapping:
                                        public_url = mapping[filename]['public_url']
                                        processed_urls.append(public_url)
                                        logger.info(f"URL MinIO trouvée: {public_url}")
                                    else:
                                        logger.warning(f"Mapping non trouvé pour {filename}")
                                        # Fallback: URL publique directe
                                        public_url = f"{minio_service.public_base_url}/direct-posts-images/{filename}"
                                        processed_urls.append(public_url)
                                else:
                                    logger.warning("Fichier mapping non trouvé")
                                    # Fallback: URL publique directe
                                    public_url = f"{minio_service.public_base_url}/direct-posts-images/{filename}"
                                    processed_urls.append(public_url)
                                    
                            except Exception as e:
                                logger.error(f"Erreur chargement mapping: {e}")
                                # Fallback: URL publique directe
                                public_url = f"{minio_service.public_base_url}/direct-posts-images/{filename}"
                                processed_urls.append(public_url)
                        elif media_url.startswith('http'):
                            # URL externe - upload vers MinIO
                            logger.info(f"Upload URL externe vers MinIO: {media_url}")
                            success, message, public_url = minio_service.upload_image_from_url(media_url)
                            if success and public_url:
                                processed_urls.append(public_url)
                            else:
                                logger.warning(f"Échec upload URL externe: {message}")
                                processed_urls.append(media_url)  # Garder l'URL originale
                        else:
                            # Autre format - garder tel quel
                            processed_urls.append(media_url)
                    
                    processed_media_urls = processed_urls
                    logger.info(f"URLs publiques MinIO après traitement: {processed_media_urls}")
                else:
                    # Posts programmés : Utiliser directement les URLs publiques existantes
                    logger.info("Post programmé détecté - Utilisation des URLs publiques existantes")
                    processed_media_urls = media_urls  # Pas de traitement, utiliser tel quel
                    logger.info(f"URLs publiques utilisées directement: {processed_media_urls}")
            
            # Construire l'objet target selon le réseau
            target = {"targetType": platform}
            
            # Utiliser le target_page_id fourni ou celui de la config
            page_id = target_page_id
            
            # Facebook et LinkedIn nécessitent un pageId spécifique
            # X utilise l'accountId comme pageId (pas de pages séparées)
            if platform in ["facebook", "linkedin"]:
                if not page_id and hasattr(settings, 'BLOTATO_FACEBOOK_PAGE_ID') and platform == "facebook":
                    page_id = settings.BLOTATO_FACEBOOK_PAGE_ID
                if page_id:
                    target["pageId"] = page_id
            elif platform == "x":
                # Pour X, utiliser l'accountId comme pageId si pas de target_page_id spécifique
                if not page_id:
                    target["pageId"] = account_id
                else:
                    target["pageId"] = page_id
            
            # Préparer le payload selon la documentation Blotato
            payload = {
                "post": {
                    "accountId": account_id,
                    "content": {
                        "text": content,
                        "mediaUrls": processed_media_urls,
                        "platform": platform
                    },
                    "target": target
                }
            }
            
            # Ajouter scheduledTime au niveau racine si fourni (pas dans post)
            if scheduled_at:
                # Format ISO 8601 requis par Blotato
                payload["scheduledTime"] = scheduled_at.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Log pour debug
            logger.info(f"📤 Publication sur {network} via Blotato - Account ID: {account_id}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Effectuer la publication via l'API Blotato
            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                # L'API Blotato retourne postSubmissionId
                post_submission_id = result.get('postSubmissionId', 'unknown')
                
                # Vérifier si la réponse contient des erreurs malgré le statut 201
                if 'error' in result or 'failed' in str(result).lower():
                    error_msg = result.get('error', 'Publication échouée côté réseau social')
                    logger.error(f"❌ Publication échouée sur {network}: {error_msg}")
                    return False, f"Publication échouée: {error_msg}", None, None, None
                
                message = f"Publication réussie sur {network} via Blotato"
                if scheduled_at:
                    message += f" (programmée pour {scheduled_at.strftime('%Y-%m-%d %H:%M')})"
                
                # Construire l'URL vers la page cible au lieu de Blotato
                publication_url = self._build_page_url(platform, target.get('pageId'))
                
                logger.info(f"✅ {message} - Submission ID: {post_submission_id}")
                return True, message, publication_url, processed_media_urls, post_submission_id
            
            elif response.status_code == 429:
                # Rate limit dépassé
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', 'Rate limit exceeded')
                logger.error(f"⏱️  Rate limit Blotato: {error_msg}")
                return False, f"Rate limit dépassé: {error_msg}", None, None, None
            
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', response.text)
                full_error = f"Erreur Blotato {response.status_code}: {error_msg}"
                logger.error(f"❌ Erreur publication {network}: {full_error}")
                return False, full_error, None, None, None
                
        except requests.exceptions.Timeout:
            error_msg = f"Timeout lors de la publication sur {network}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None, None, None
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur réseau pour {network}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None, None, None
        except Exception as e:
            error_msg = f"Erreur inattendue pour {network}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None, None, None
    
    def publish_to_multiple_networks(
        self, 
        content: str, 
        networks: List[str], 
        media_urls: List[str] = None,
        scheduled_at: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """
        Publie le même contenu sur plusieurs réseaux via Blotato
        
        Note: Avec Blotato, chaque réseau nécessite une publication séparée
        car chaque compte a son propre accountId
        
        Args:
            content: Contenu à publier
            networks: Liste des réseaux cibles
            media_urls: URLs des médias (optionnel)
            scheduled_at: Date de publication programmée (optionnel)
            
        Returns:
            Dict avec les résultats par réseau
        """
        results = {}
        
        for network in networks:
            success, message, publication_url, processed_media_urls = self.publish_to_network(
                network=network,
                content=content,
                media_urls=media_urls,
                scheduled_at=scheduled_at,
                is_direct_post=False  # Posts programmés par défaut
            )
            
            results[network] = {
                'success': success,
                'message': message,
                'publication_url': publication_url,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return results
    
    def get_network_status(self) -> Dict[str, Dict]:
        """
        Vérifie le statut de connexion via l'API Blotato
        
        Returns:
            Dict avec le statut de chaque réseau
        """
        try:
            # Endpoint pour récupérer les comptes connectés
            response = requests.get(
                f"{self.api_url}/accounts",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                accounts = response.json()
                status = {}
                
                # Parser la réponse de Blotato
                if isinstance(accounts, list):
                    for account in accounts:
                        platform = account.get('platform', '').lower()
                        account_id = account.get('id')
                        username = account.get('username', account.get('name', 'N/A'))
                        is_connected = account.get('isConnected', True)
                        
                        status[platform] = {
                            'connected': is_connected,
                            'account_id': account_id,
                            'account_name': username,
                            'last_check': datetime.utcnow().isoformat()
                        }
                
                return status
            else:
                error_msg = f'Erreur API Blotato: {response.status_code}'
                logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            error_msg = f'Erreur de connexion Blotato: {str(e)}'
            logger.error(error_msg)
            return {'error': error_msg}
    
    def get_all_networks_status(self) -> Dict[str, Dict]:
        """
        Récupère le statut détaillé de tous les réseaux configurés
        
        Returns:
            Dict avec le statut de chaque réseau
        """
        network_status = self.get_network_status()
        
        # Construire une réponse formatée
        formatted_status = {}
        supported_networks = ['linkedin', 'x', 'facebook']
        
        for network in supported_networks:
            if 'error' in network_status:
                formatted_status[network] = {
                    'status': 'error',
                    'message': network_status['error'],
                    'connected': False
                }
            elif network in network_status:
                info = network_status[network]
                formatted_status[network] = {
                    'status': 'connected' if info['connected'] else 'disconnected',
                    'message': f"Compte {info['account_name']} connecté" if info['connected'] else 'Compte non connecté',
                    'connected': info['connected'],
                    'account_id': info.get('account_id'),
                    'account_name': info.get('account_name')
                }
            else:
                # Vérifier si un account_id est configuré
                account_id = self._get_account_id(network)
                formatted_status[network] = {
                    'status': 'not_configured' if not account_id else 'unknown',
                    'message': 'Aucun compte configuré' if not account_id else 'Statut inconnu',
                    'connected': False
                }
        
        return formatted_status
    
    def get_x_accounts(self) -> List[Dict]:
        """
        Récupérer la liste des comptes X disponibles
        
        Returns:
            List[Dict] avec les comptes X disponibles
        """
        try:
            from pathlib import Path
            blotato_file = Path("blotato_accounts.json")
            
            if not blotato_file.exists():
                logger.warning("Fichier blotato_accounts.json non trouvé")
                return []
                
            with open(blotato_file, 'r', encoding='utf-8') as f:
                blotato_accounts = json.load(f)
            
            # Récupérer les comptes X
            x_accounts = blotato_accounts.get('x', [])
            
            # Formater pour l'API
            formatted_accounts = []
            for account in x_accounts:
                formatted_accounts.append({
                    'accountId': account.get('accountId'),
                    'accountName': account.get('accountName'),
                    'platform': 'x'
                })
            
            return formatted_accounts
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des comptes X: {e}")
            return []
    
    def check_post_status(self, post_submission_id: str) -> Dict:
        """
        Vérifier le statut d'une publication Blotato
        
        Args:
            post_submission_id: ID de soumission retourné par Blotato
            
        Returns:
            Dict avec le statut de la publication
        """
        try:
            response = requests.get(
                f"{self.api_url}/posts/{post_submission_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'status': 'success',
                    'data': result,
                    'message': 'Statut récupéré avec succès'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Erreur lors de la récupération du statut: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur lors de la vérification du statut: {str(e)}'
            }
    
    def schedule_post(
        self, 
        content: str, 
        networks: List[str], 
        scheduled_at: datetime, 
        media_urls: List[str] = None
    ) -> Dict:
        """
        Programme une publication pour plus tard via Blotato
        
        Args:
            content: Contenu à publier
            networks: Liste des réseaux cibles
            scheduled_at: Date/heure de publication
            media_urls: URLs des médias (optionnel)
            
        Returns:
            Dict avec le résultat de la programmation
        """
        try:
            # Avec Blotato, on utilise la même méthode mais avec scheduled_at
            results = self.publish_to_multiple_networks(
                content=content,
                networks=networks,
                media_urls=media_urls,
                scheduled_at=scheduled_at
            )
            
            # Calculer le succès global
            success_count = sum(1 for r in results.values() if r['success'])
            total_count = len(results)
            
            if success_count == total_count:
                return {
                    'success': True,
                    'message': f'Publications programmées avec succès sur tous les réseaux ({success_count}/{total_count})',
                    'scheduled_at': scheduled_at.isoformat(),
                    'results': results
                }
            elif success_count > 0:
                return {
                    'success': True,
                    'message': f'Publications partiellement programmées ({success_count}/{total_count} réseaux)',
                    'scheduled_at': scheduled_at.isoformat(),
                    'results': results
                }
            else:
                return {
                    'success': False,
                    'message': 'Échec de la programmation sur tous les réseaux',
                    'results': results
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur programmation: {str(e)}'
            }
    
    def delete_scheduled_post(self, post_id: str) -> Tuple[bool, str]:
        """
        Supprime une publication programmée
        
        Args:
            post_id: ID du post à supprimer
            
        Returns:
            Tuple[success, message]
        """
        try:
            response = requests.delete(
                f"{self.api_url}/posts/{post_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                return True, "Publication programmée supprimée avec succès"
            else:
                error_msg = f"Erreur lors de la suppression: {response.status_code}"
                return False, error_msg
                
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def get_scheduled_posts(self) -> List[Dict]:
        """
        Récupère la liste des publications programmées
        
        Returns:
            Liste des publications programmées
        """
        try:
            response = requests.get(
                f"{self.api_url}/posts?status=scheduled",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                posts = response.json()
                return posts if isinstance(posts, list) else []
            else:
                logger.error(f"Erreur lors de la récupération des posts: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des posts: {str(e)}")
            return []
    
    def _build_page_url(self, platform: str, page_id: str = None) -> str:
        """
        Construit l'URL de la page cible où l'article a été publié
        
        Args:
            platform: Plateforme cible (facebook, linkedin, twitter)
            page_id: ID de la page/compte cible
            
        Returns:
            URL de la page cible
        """
        if not page_id:
            return None
        
        if platform == "facebook":
            # URL de la page Facebook
            return f"https://www.facebook.com/{page_id}"
        elif platform == "linkedin":
            # URL du compte LinkedIn (peut être personnel ou entreprise)
            # Pour un compte personnel: https://www.linkedin.com/in/{username}
            # Pour une page entreprise: https://www.linkedin.com/company/{company_id}
            # Ici on retourne vers le feed
            return f"https://www.linkedin.com/feed/"
        elif platform == "twitter":
            # URL du compte X/Twitter
            return f"https://twitter.com/i/user/{page_id}"
        else:
            return None

