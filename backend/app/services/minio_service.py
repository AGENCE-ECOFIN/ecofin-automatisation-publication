"""
Service MinIO pour le stockage des images des posts directs
Fournit des URLs publiques accessibles par Blotato
"""

import os
import uuid
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from minio import Minio
from minio.error import S3Error
import requests
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class MinIOService:
    """Service pour gérer l'upload des images vers MinIO avec URLs publiques"""
    
    def __init__(self):
        # Configuration MinIO
        self.minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # Bucket pour les images des posts directs
        self.bucket_name = "direct-posts-images"
        
        # URL publique de base (votre DNS)
        self.public_base_url = settings.MINIO_PUBLIC_URL
        
        # Initialiser le bucket s'il n'existe pas
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """S'assurer que le bucket existe et est public"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} créé")
            
            # Configurer le bucket pour être public (lecture seule)
            self._set_bucket_policy()
            
        except S3Error as e:
            logger.error(f"Erreur lors de la création du bucket: {e}")
    
    def _set_bucket_policy(self):
        """Configure le bucket pour être public en lecture"""
        try:
            # Politique pour permettre la lecture publique
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                    }
                ]
            }
            
            import json
            self.minio_client.set_bucket_policy(
                self.bucket_name, 
                json.dumps(policy)
            )
            logger.info(f"Politique publique configurée pour le bucket {self.bucket_name}")
            
        except S3Error as e:
            logger.warning(f"Impossible de configurer la politique publique: {e}")
    
    def upload_image_from_base64(self, base64_data: str, filename: Optional[str] = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Upload une image depuis des données base64 vers MinIO
        
        Args:
            base64_data: Données base64 de l'image (avec ou sans préfixe data:)
            filename: Nom de fichier personnalisé (optionnel)
            
        Returns:
            Tuple[success, message, minio_path, signed_url]
            - success: True si upload réussi
            - message: Message de statut
            - minio_path: Chemin dans MinIO (pour stockage en DB)
            - signed_url: URL signée temporaire (pour affichage client)
        """
        try:
            # Nettoyer les données base64
            if base64_data.startswith('data:'):
                # Enlever le préfixe data:image/...;base64,
                base64_data = base64_data.split(',')[1]
            
            # Décoder les données base64
            try:
                image_data = base64.b64decode(base64_data)
                logger.info(f"Données base64 décodées: {len(image_data)} bytes")
            except Exception as e:
                return False, f"Erreur décodage base64: {str(e)}", None
            
            # Générer un nom de fichier unique
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                filename = f"direct_post_{timestamp}_{unique_id}.jpg"  # Par défaut jpg
            
            # Upload vers MinIO
            from io import BytesIO
            image_stream = BytesIO(image_data)
            
            # Déterminer le content-type depuis l'extension
            ext = os.path.splitext(filename)[1].lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            content_type = content_type_map.get(ext, 'image/jpeg')
            
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=filename,
                data=image_stream,
                length=len(image_data),
                content_type=content_type
            )
            
            # Construire le chemin MinIO (pour stockage en DB)
            minio_path = f"{self.bucket_name}/{filename}"
            
            # Générer une URL signée temporaire (7 jours)
            try:
                signed_url = self.minio_client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=filename,
                    expires=timedelta(days=7)
                )
                logger.info(f"URL signée générée pour {filename}")
            except Exception as e:
                logger.warning(f"Impossible de générer l'URL signée: {e}")
                signed_url = None
            
            logger.info(f"Image base64 uploadée vers MinIO: {minio_path}")
            return True, "Image uploadée avec succès", minio_path, signed_url
            
        except S3Error as e:
            error_msg = f"Erreur MinIO lors de l'upload: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None, None
        except Exception as e:
            error_msg = f"Erreur inattendue lors de l'upload: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None, None
    
    def upload_images_from_base64_list(self, base64_images: List[str]) -> List[str]:
        """
        Upload plusieurs images depuis des données base64 vers MinIO
        
        Args:
            base64_images: Liste des données base64 des images
            
        Returns:
            Liste des URLs publiques des images uploadées
        """
        public_urls = []
        
        for i, base64_data in enumerate(base64_images):
            # Générer un nom de fichier avec index
            filename = f"direct_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jpg"
            
            success, message, minio_path, signed_url = self.upload_image_from_base64(base64_data, filename)
            
            if success and minio_path:
                # Générer l'URL publique
                public_url = self.get_public_url(minio_path)
                public_urls.append(public_url)
                logger.info(f"Image {i+1} uploadée: {public_url}")
            else:
                logger.warning(f"Échec upload image {i+1}: {message}")
                # En cas d'échec, ne pas ajouter d'URL
        
        return public_urls

    def upload_image_from_url(self, image_url: str, filename: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Upload une image depuis une URL vers MinIO (méthode legacy)
        
        Args:
            image_url: URL de l'image à uploader
            filename: Nom de fichier personnalisé (optionnel)
            
        Returns:
            Tuple[success, message, public_url]
        """
        try:
            # Pour les URLs externes, télécharger et uploader
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False, f"Impossible de télécharger l'image: {response.status_code}", None
            
            # Convertir en base64 et utiliser la méthode base64
            import base64
            base64_data = f"data:{response.headers.get('content-type', 'image/jpeg')};base64,{base64.b64encode(response.content).decode('utf-8')}"
            
            success, message, minio_path, signed_url = self.upload_image_from_base64(base64_data, filename)
            
            if success:
                # Retourner l'URL publique pour compatibilité
                public_url = self.get_public_url(minio_path)
                return True, message, public_url
            else:
                return False, message, None
                
        except Exception as e:
            error_msg = f"Erreur upload depuis URL: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def generate_signed_url(self, minio_path: str, expires_days: int = 7) -> Tuple[bool, str, Optional[str]]:
        """
        Génère une URL signée temporaire pour un chemin MinIO
        
        Args:
            minio_path: Chemin MinIO (format: bucket/filename)
            expires_days: Durée de validité en jours
            
        Returns:
            Tuple[success, message, signed_url]
        """
        try:
            # Parser le chemin MinIO
            if '/' not in minio_path:
                return False, "Chemin MinIO invalide", None
            
            bucket_name, object_name = minio_path.split('/', 1)
            
            # Vérifier que l'objet existe
            try:
                self.minio_client.stat_object(bucket_name, object_name)
            except S3Error:
                return False, "Objet non trouvé dans MinIO", None
            
            # Générer l'URL signée
            signed_url = self.minio_client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(days=expires_days)
            )
            
            # Remplacer localhost par l'IP publique dans l'URL signée
            if '127.0.0.1:9000' in signed_url:
                signed_url = signed_url.replace('127.0.0.1:9000', settings.MINIO_ENDPOINT)
                logger.info(f"URL signée corrigée avec IP publique: {settings.MINIO_ENDPOINT}")
            
            logger.info(f"URL signée générée pour {minio_path} (valide {expires_days} jours)")
            return True, "URL signée générée", signed_url
            
        except Exception as e:
            error_msg = f"Erreur génération URL signée: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def get_public_url(self, minio_path: str) -> str:
        """
        Génère l'URL publique pour Blotato (non signée, bucket public)
        
        Args:
            minio_path: Chemin MinIO (format: bucket/filename)
            
        Returns:
            URL publique
        """
        return f"{self.public_base_url}/{minio_path}"

    def upload_images_from_urls(self, image_urls: List[str]) -> List[str]:
        """
        Upload plusieurs images depuis des URLs vers MinIO
        
        Args:
            image_urls: Liste des URLs d'images à uploader
            
        Returns:
            Liste des URLs publiques des images uploadées
        """
        public_urls = []
        
        for image_url in image_urls:
            # Vérifier si c'est déjà une URL publique
            if self._is_public_url(image_url):
                public_urls.append(image_url)
                continue
            
            # Upload vers MinIO
            success, message, public_url = self.upload_image_from_url(image_url)
            
            if success and public_url:
                public_urls.append(public_url)
                logger.info(f"Image uploadée: {image_url} -> {public_url}")
            else:
                logger.warning(f"Échec upload image {image_url}: {message}")
                # En cas d'échec, garder l'URL originale
                public_urls.append(image_url)
        
        return public_urls
    
    def delete_image(self, filename: str) -> Tuple[bool, str]:
        """
        Supprime une image du bucket MinIO
        
        Args:
            filename: Nom du fichier à supprimer
            
        Returns:
            Tuple[success, message]
        """
        try:
            self.minio_client.remove_object(self.bucket_name, filename)
            logger.info(f"Image supprimée: {filename}")
            return True, "Image supprimée avec succès"
            
        except S3Error as e:
            error_msg = f"Erreur lors de la suppression: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur inattendue lors de la suppression: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_images(self) -> List[dict]:
        """
        Liste toutes les images du bucket
        
        Returns:
            Liste des informations sur les images
        """
        try:
            images = []
            objects = self.minio_client.list_objects(self.bucket_name, recursive=True)
            
            for obj in objects:
                images.append({
                    'filename': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'public_url': f"{self.public_base_url}/{self.bucket_name}/{obj.object_name}"
                })
            
            return images
            
        except S3Error as e:
            logger.error(f"Erreur lors de la liste des images: {e}")
            return []
    
    def cleanup_old_images(self, days_old: int = 30) -> Tuple[int, str]:
        """
        Nettoie les images anciennes du bucket
        
        Args:
            days_old: Nombre de jours d'ancienneté pour la suppression
            
        Returns:
            Tuple[nombre_supprimées, message]
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            objects = self.minio_client.list_objects(self.bucket_name, recursive=True)
            
            for obj in objects:
                if obj.last_modified.replace(tzinfo=None) < cutoff_date:
                    self.minio_client.remove_object(self.bucket_name, obj.object_name)
                    deleted_count += 1
                    logger.info(f"Image ancienne supprimée: {obj.object_name}")
            
            message = f"{deleted_count} images anciennes supprimées"
            logger.info(message)
            return deleted_count, message
            
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage: {str(e)}"
            logger.error(error_msg)
            return 0, error_msg
    
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
        
        # Vérifier si c'est déjà une URL MinIO publique
        if self.public_base_url in url:
            return True
        
        return any(url.startswith(domain) for domain in public_domains)
