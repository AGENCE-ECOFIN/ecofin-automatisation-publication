from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.blotato_service import BlotatoService
from datetime import datetime

router = APIRouter()

class DirectPostRequest(BaseModel):
    network: str
    content: str
    target_page_id: str
    media_urls: Optional[List[str]] = []

@router.post("/direct-post/")
async def create_direct_post(
    post_data: DirectPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer et publier IMMÉDIATEMENT un post direct (sans flux RSS)
    Publication IMMÉDIATE, ne passe PAS par la file d'attente
    """
    try:
        # Initialiser le service Blotato
        blotato_service = BlotatoService()
        
        print(f"\n📤 Publication directe IMMÉDIATE sur {post_data.network}")
        print(f"   Contenu: {post_data.content[:100]}...")
        print(f"   Page: {post_data.target_page_id}")
        print(f"   Médias: {len(post_data.media_urls) if post_data.media_urls else 0} image(s)")
        
        # Publier IMMÉDIATEMENT via Blotato
        success, message, publication_url = blotato_service.publish_to_network(
            network=post_data.network,
            content=post_data.content,
            media_urls=post_data.media_urls or [],
            target_page_id=post_data.target_page_id
        )
        
        if success:
            print(f"✅ Publication réussie: {publication_url}")
            
            # Enregistrer dans l'historique
            from app.models.publication import Publication
            publication = Publication(
                post_id=None,  # Post direct, pas de post associé
                feed_id=None,  # Post direct, pas de flux associé
                network=post_data.network,
                content=post_data.content,
                published_url=publication_url,
                is_success=True,
                published_at=datetime.utcnow()
            )
            db.add(publication)
            db.commit()
            
            return {
                "message": "✅ Post publié IMMÉDIATEMENT avec succès !",
                "success": True,
                "publication_url": publication_url,
                "network": post_data.network,
                "published_at": datetime.utcnow().isoformat()
            }
        else:
            print(f"❌ Échec publication: {message}")
            
            # Enregistrer l'échec dans l'historique
            from app.models.publication import Publication
            publication = Publication(
                post_id=None,
                feed_id=None,  # Post direct, pas de flux associé
                network=post_data.network,
                content=post_data.content,
                published_url=None,
                is_success=False,
                error_message=message,
                published_at=datetime.utcnow()
            )
            db.add(publication)
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail=f"Erreur de publication: {message}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
