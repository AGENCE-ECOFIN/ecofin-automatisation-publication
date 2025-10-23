"""
Service pour uploader les images vers un CDN public
pour que LinkedIn puisse y accéder
"""

import requests
import base64
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ImageService:
    """Service pour gérer l'upload des images vers un CDN public"""
    
    def __init__(self):
        # Configuration pour différents CDN
        self.cdn_configs = {
            'imgur': {
                'upload_url': 'https://api.imgur.com/3/image',
                'headers': {
                    'Authorization': 'Client-ID 546c25a59c58ad7'  # Client ID public d'Imgur
                }
            },
            'cloudinary': {
                'upload_url': 'https://api.cloudinary.com/v1_1/demo/image/upload',
                'cloud_name': 'demo'
            }
        }
    
    def upload_to_imgur(self, image_url: str) -> Optional[str]:
        """
        Upload une image vers Imgur et retourne l'URL publique
        
        Args:
            image_url: URL locale de l'image
            
        Returns:
            URL publique de l'image ou None si échec
        """
        try:
            # Télécharger l'image depuis l'URL locale
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Impossible de télécharger l'image {image_url}: {response.status_code}")
                return None
            
            # Encoder l'image en base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            
            # Upload vers Imgur avec headers corrects
            upload_data = {
                'image': image_data,
                'type': 'base64'
            }
            
            headers = {
                'Authorization': 'Client-ID 546c25a59c58ad7',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            upload_response = requests.post(
                'https://api.imgur.com/3/image',
                headers=headers,
                data=upload_data,
                timeout=30
            )
            
            logger.info(f"Imgur response: {upload_response.status_code} - {upload_response.text[:200]}")
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                if result.get('success'):
                    public_url = result['data']['link']
                    logger.info(f"Image uploadée vers Imgur: {public_url}")
                    return public_url
                else:
                    logger.error(f"Erreur Imgur: {result.get('data', {}).get('error', 'Unknown error')}")
                    return None
            else:
                logger.error(f"Erreur upload Imgur: {upload_response.status_code} - {upload_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'upload vers Imgur: {e}")
            return None
    
    def upload_images_to_cdn(self, image_urls: List[str]) -> List[str]:
        """
        Upload plusieurs images vers un CDN et retourne les URLs publiques
        
        Args:
            image_urls: Liste des URLs locales des images
            
        Returns:
            Liste des URLs publiques des images
        """
        public_urls = []
        
        for image_url in image_urls:
            # Vérifier si c'est déjà une URL publique
            if self._is_public_url(image_url):
                public_urls.append(image_url)
                continue
            
            # Pour les réseaux sociaux, utiliser des URLs d'images optimisées
            optimized_url = self._get_optimized_image_url(image_url)
            if optimized_url:
                public_urls.append(optimized_url)
            else:
                # Upload vers Imgur en dernier recours
                public_url = self.upload_to_imgur(image_url)
                if public_url:
                    public_urls.append(public_url)
                else:
                    logger.warning(f"Impossible d'uploader l'image {image_url}")
                    # Garder l'URL originale en cas d'échec
                    public_urls.append(image_url)
        
        return public_urls
    
    def _get_optimized_image_url(self, image_url: str) -> Optional[str]:
        """
        Retourne une URL d'image optimisée pour les réseaux sociaux
        Utilise des services d'images publiques fiables
        """
        try:
            # Utiliser des services d'images publiques fiables
            if "localhost" in image_url or "127.0.0.1" in image_url:
                # Pour les images locales, utiliser un service de proxy d'images
                # ou convertir en base64 et utiliser data URI
                return self._convert_to_data_uri(image_url)
            
            return None
        except Exception as e:
            logger.error(f"Erreur optimisation image: {e}")
            return None
    
    def _convert_to_data_uri(self, image_url: str) -> Optional[str]:
        """
        Convertit une image locale en data URI pour éviter les problèmes d'URL
        """
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                # Détecter le type MIME
                content_type = response.headers.get('content-type', 'image/png')
                
                # Encoder en base64
                image_data = base64.b64encode(response.content).decode('utf-8')
                
                # Créer data URI
                data_uri = f"data:{content_type};base64,{image_data}"
                
                logger.info(f"Image convertie en data URI: {len(data_uri)} caractères")
                return data_uri
            else:
                logger.error(f"Impossible de télécharger l'image: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erreur conversion data URI: {e}")
            return None
    
    def _is_public_url(self, url: str) -> bool:
        """
        Vérifie si une URL est déjà publique (accessible depuis l'extérieur)
        
        Args:
            url: URL à vérifier
            
        Returns:
            True si l'URL est publique, False sinon
        """
        # URLs considérées comme publiques
        public_domains = [
            'https://',
            'http://',
            'https://images.unsplash.com',
            'https://picsum.photos',
            'https://via.placeholder.com',
            'https://imgur.com',
            'https://i.imgur.com',
            'https://cloudinary.com'
        ]
        
        return any(url.startswith(domain) for domain in public_domains)
