from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.minio_service import MinIOService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload-image")
async def upload_image_to_minio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload une image vers MinIO et retourne l'URL publique
    Pour tester l'intégration MinIO avec les posts directs
    """
    try:
        # Vérifier que c'est une image
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        # Lire le contenu du fichier
        content = await file.read()
        
        # Créer le service MinIO
        minio_service = MinIOService()
        
        # Upload vers MinIO
        from io import BytesIO
        success, message, public_url = minio_service.upload_image_from_url(
            image_url=f"data:{file.content_type};base64,{content.decode('base64')}"
        )
        
        if success and public_url:
            return {
                "success": True,
                "message": "Image uploadée avec succès",
                "public_url": public_url,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content)
            }
        else:
            raise HTTPException(status_code=500, detail=f"Erreur upload: {message}")
            
    except Exception as e:
        logger.error(f"Erreur upload image: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/upload-base64-with-path")
async def upload_base64_with_path(
    base64_images: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload des images base64 vers MinIO et retourne les chemins + URLs signées
    Pour le flux complet : base64 → MinIO → chemin (DB) + URL signée (affichage)
    """
    try:
        if not base64_images:
            raise HTTPException(status_code=400, detail="Aucune image base64 fournie")
        
        # Créer le service MinIO
        minio_service = MinIOService()
        
        results = []
        for i, base64_data in enumerate(base64_images):
            success, message, minio_path, signed_url = minio_service.upload_image_from_base64(base64_data)
            
            if success and minio_path:
                # Générer l'URL publique pour Blotato
                public_url = minio_service.get_public_url(minio_path)
                
                results.append({
                    "index": i,
                    "success": True,
                    "minio_path": minio_path,  # Pour stockage en DB
                    "signed_url": signed_url,  # Pour affichage client
                    "public_url": public_url   # Pour Blotato
                })
            else:
                results.append({
                    "index": i,
                    "success": False,
                    "error": message
                })
        
        successful_uploads = [r for r in results if r["success"]]
        
        return {
            "success": True,
            "message": f"{len(successful_uploads)}/{len(base64_images)} images uploadées",
            "results": results,
            "summary": {
                "total": len(base64_images),
                "successful": len(successful_uploads),
                "failed": len(base64_images) - len(successful_uploads)
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur upload base64 avec chemin: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/generate-signed-url")
async def generate_signed_url(
    minio_path: str,
    expires_days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Génère une URL signée temporaire pour un chemin MinIO stocké en DB
    """
    try:
        minio_service = MinIOService()
        success, message, signed_url = minio_service.generate_signed_url(minio_path, expires_days)
        
        if success:
            return {
                "success": True,
                "message": message,
                "minio_path": minio_path,
                "signed_url": signed_url,
                "expires_days": expires_days
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Erreur génération URL signée: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/upload-base64")
async def upload_base64_to_minio(
    base64_images: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload des images base64 vers MinIO et retourne les URLs publiques
    Pour tester l'intégration MinIO avec les posts directs
    """
    try:
        if not base64_images:
            raise HTTPException(status_code=400, detail="Aucune image base64 fournie")
        
        # Créer le service MinIO
        minio_service = MinIOService()
        
        # Upload vers MinIO
        public_urls = minio_service.upload_images_from_base64_list(base64_images)
        
        return {
            "success": True,
            "message": f"{len(public_urls)} images uploadées",
            "original_count": len(base64_images),
            "public_urls": public_urls,
            "uploaded_count": len(public_urls)
        }
        
    except Exception as e:
        logger.error(f"Erreur upload base64: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/upload-images-from-urls")
async def upload_images_from_urls(
    image_urls: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload plusieurs images depuis des URLs vers MinIO
    Pour tester l'intégration avec les posts directs
    """
    try:
        if not image_urls:
            raise HTTPException(status_code=400, detail="Aucune URL d'image fournie")
        
        # Créer le service MinIO
        minio_service = MinIOService()
        
        # Upload vers MinIO
        public_urls = minio_service.upload_images_from_urls(image_urls)
        
        return {
            "success": True,
            "message": f"{len(public_urls)} images traitées",
            "original_urls": image_urls,
            "public_urls": public_urls,
            "uploaded_count": len([url for url in public_urls if minio_service.public_base_url in url])
        }
        
    except Exception as e:
        logger.error(f"Erreur upload images: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.get("/list-images")
async def list_minio_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste toutes les images stockées dans MinIO
    """
    try:
        minio_service = MinIOService()
        images = minio_service.list_images()
        
        return {
            "success": True,
            "message": f"{len(images)} images trouvées",
            "images": images
        }
        
    except Exception as e:
        logger.error(f"Erreur liste images: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.delete("/delete-image/{filename}")
async def delete_minio_image(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime une image de MinIO
    """
    try:
        minio_service = MinIOService()
        success, message = minio_service.delete_image(filename)
        
        if success:
            return {
                "success": True,
                "message": message
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Erreur suppression image: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/cleanup-old-images")
async def cleanup_old_images(
    days_old: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Nettoie les images anciennes de MinIO
    """
    try:
        minio_service = MinIOService()
        deleted_count, message = minio_service.cleanup_old_images(days_old)
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Erreur nettoyage: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
