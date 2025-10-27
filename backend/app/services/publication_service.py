"""
Service de publication unifié utilisant Blotato API
Documentation: https://help.blotato.com/api/start
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app.core.config import settings
from app.services.blotato_service import BlotatoService
import logging

logger = logging.getLogger(__name__)

class PublicationService:
    """Service unifié pour la publication via Blotato API"""
    
    def __init__(self):
        # Utiliser le service Blotato centralisé
        self.blotato = BlotatoService()
    
    def publish_to_network(self, network: str, content: str, media_urls: List[str] = None, target_page_id: str = None, is_direct_post: bool = False) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Publie un contenu sur un réseau social via Blotato API
        
        Args:
            network: Nom du réseau ('linkedin', 'x', 'facebook', etc.)
            content: Contenu à publier
            media_urls: URLs des médias (optionnel)
            target_page_id: ID de la page cible (optionnel)
            is_direct_post: True si c'est un post direct, False si post programmé
            
        Returns:
            Tuple[success, message, publication_url, post_submission_id]
        """
        success, message, publication_url, processed_media_urls, post_submission_id = self.blotato.publish_to_network(
            network, content, media_urls, target_page_id=target_page_id, is_direct_post=is_direct_post
        )
        return success, message, publication_url, post_submission_id
    
    
    def publish_to_multiple_networks(self, content: str, networks: List[str], media_urls: List[str] = None) -> Dict[str, Dict]:
        """
        Publie le même contenu sur plusieurs réseaux via Blotato
        
        Args:
            content: Contenu à publier
            networks: Liste des réseaux cibles
            media_urls: URLs des médias (optionnel)
            
        Returns:
            Dict avec les résultats par réseau
        """
        return self.blotato.publish_to_multiple_networks(content, networks, media_urls)
    
    def get_network_status(self) -> Dict[str, Dict]:
        """
        Vérifie le statut de connexion via l'API Blotato
        
        Returns:
            Dict avec le statut de chaque réseau
        """
        return self.blotato.get_network_status()
    
    def get_all_networks_status(self) -> Dict[str, Dict]:
        """
        Récupère le statut détaillé de tous les réseaux configurés
        
        Returns:
            Dict avec le statut de chaque réseau
        """
        return self.blotato.get_all_networks_status()
    
    def schedule_post(self, content: str, networks: List[str], scheduled_at: datetime, media_urls: List[str] = None) -> Dict:
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
        return self.blotato.schedule_post(content, networks, scheduled_at, media_urls)