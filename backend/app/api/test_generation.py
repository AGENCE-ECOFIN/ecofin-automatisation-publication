from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.feed_service import FeedService
from app.services.llm_service import LLMService
from app.api.dependencies import get_current_user
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter(prefix="/test", tags=["test"])

# Router séparé pour la génération directe (sans prefix)
generation_router = APIRouter(tags=["generation"])


class TestArticleRequest(BaseModel):
    title: str
    content: str
    source_url: Optional[str] = None
    custom_prompt: Optional[str] = None
    network_prompts: Optional[Dict[str, str]] = None
    target_networks: Optional[List[str]] = None


class TestArticleResponse(BaseModel):
    article: dict
    generated_posts: dict
    target_networks: List[str]


@router.post("/generate-posts", response_model=TestArticleResponse)
def test_generate_posts(
    request: TestArticleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Teste la génération de posts pour un article sur tous les réseaux définis
    """
    try:
        llm_service = LLMService()
        
        # Définir les réseaux cibles
        target_networks = request.target_networks or ["facebook", "linkedin", "x"]
        
        # Construire le contenu de l'article
        article_content = f"""
        Titre: {request.title}
        Contenu: {request.content}
        URL source: {request.source_url or 'Non spécifiée'}
        """
        
        # Générer les posts pour tous les réseaux
        generated_posts = llm_service.generate_social_media_posts(
            article_content=article_content,
            custom_prompt=request.custom_prompt,
            network_prompts=request.network_prompts,
            target_networks=target_networks,
            source_url=request.source_url,
            title=request.title,
            source_image=None
        )
        
        return TestArticleResponse(
            article={
                "title": request.title,
                "content": request.content,
                "source_url": request.source_url
            },
            generated_posts=generated_posts,
            target_networks=target_networks
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}"
        )


@router.post("/generate-posts-for-feed/{feed_id}", response_model=TestArticleResponse)
def test_generate_posts_for_feed(
    feed_id: int,
    request: TestArticleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Teste la génération de posts pour un article en utilisant la configuration d'un flux
    """
    try:
        feed_service = FeedService(db)
        feed = feed_service.get_feed_by_id(feed_id)
        
        if not feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flux non trouvé"
            )
        
        # Vérifier que l'utilisateur a accès au flux
        if feed.created_by != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce flux"
            )
        
        # Utiliser la méthode du service de flux
        article = {
            "title": request.title,
            "content": request.content,
            "source_url": request.source_url or "http://example.com"
        }
        
        result = feed_service.generate_posts_for_article(
            feed=feed,
            article=article,
            target_networks=request.target_networks
        )
        
        return TestArticleResponse(
            article=result["article"],
            generated_posts=result["generated_posts"],
            target_networks=result["target_networks"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}"
        )


class DirectGenerationRequest(BaseModel):
    network: str
    content: str
    custom_prompt: Optional[str] = None


class DirectGenerationResponse(BaseModel):
    generated_content: str
    network: str


@generation_router.post("/test-generation", response_model=DirectGenerationResponse)
def generate_direct_content(
    request: DirectGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Génère du contenu pour un post direct en utilisant l'IA
    """
    try:
        llm_service = LLMService()
        
        # Générer le post pour le réseau spécifique
        generated_posts = llm_service.generate_social_media_posts(
            article_content=request.content,
            custom_prompt=request.custom_prompt,
            network_prompts=None,
            target_networks=[request.network],
            source_url=None,
            title=None,
            source_image=None
        )
        
        # Récupérer le contenu généré pour le réseau
        generated_content = generated_posts.get(request.network, request.content)
        
        return DirectGenerationResponse(
            generated_content=generated_content,
            network=request.network
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}"
        )
