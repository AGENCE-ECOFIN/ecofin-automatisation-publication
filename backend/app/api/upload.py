from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from app.api.dependencies import get_current_user
from app.models.user import User
import os
import uuid
from pathlib import Path
import shutil
from typing import Optional

router = APIRouter(prefix="/upload", tags=["upload"])

# Définir le dossier uploads
UPLOAD_DIR = Path("uploads/images")

def ensure_upload_dir():
    """Créer le dossier uploads s'il n'existe pas"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Extensions autorisées
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload une image et retourne l'URL
    """
    try:
        # S'assurer que le dossier existe
        ensure_upload_dir()
        
        # Vérifier l'extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Extension non autorisée. Utilisez: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Lire le contenu du fichier
        contents = await file.read()
        
        # Vérifier la taille
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Générer un nom de fichier unique
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Construire l'URL accessible
        # Note: En production, utilisez un CDN ou serveur de fichiers statiques
        file_url = f"/uploads/images/{unique_filename}"
        
        return {
            "url": file_url,
            "filename": file.filename,
            "size": len(contents),
            "message": "Image uploadée avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload: {str(e)}"
        )

@router.delete("/image/{filename}")
async def delete_image(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Supprime une image uploadée
    """
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Image non trouvée"
            )
        
        # Supprimer le fichier
        os.remove(file_path)
        
        return {"message": "Image supprimée avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )

