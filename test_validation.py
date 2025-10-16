#!/usr/bin/env python3
"""
Script de test pour vérifier la validation des posts et l'ajout à la queue
"""

import sys
import os
sys.path.append('/Users/thierryhema/Documents/perso/ecofin/publication/backend')

from app.core.database import SessionLocal
from app.services.post_service import PostService
from app.schemas.post import PostValidate
from app.models.publication_queue import PublicationQueue

def test_validation():
    """Test de validation d'un post"""
    db = SessionLocal()
    try:
        # 1. Récupérer un post en brouillon
        post_service = PostService(db)
        posts = post_service.get_posts(status="draft")
        
        if not posts:
            print("❌ Aucun post en brouillon trouvé")
            return
            
        post = posts[0]
        print(f"📰 Test avec le post #{post.id}: {post.title[:50]}...")
        print(f"   Feed: {post.feed_id}")
        print(f"   Status: {post.status}")
        
        # 2. Simuler une validation
        generated_content = {
            "facebook": f"Test post Facebook pour {post.title[:30]}...",
            "linkedin": f"Test post LinkedIn pour {post.title[:30]}...",
            "x": f"Test post X pour {post.title[:30]}..."
        }
        
        post_validate = PostValidate(generated_content=generated_content)
        
        print(f"🚀 Validation du post #{post.id}...")
        result = post_service.validate_post(post.id, post_validate, 1)  # user_id = 1
        
        if result:
            print(f"✅ Post validé avec succès")
            print(f"   Status: {result.status}")
            
            # 3. Vérifier la queue
            queue_items = db.query(PublicationQueue).filter(
                PublicationQueue.post_id == post.id
            ).all()
            
            print(f"📊 Éléments dans la queue pour ce post: {len(queue_items)}")
            for item in queue_items:
                print(f"   - {item.network} - {item.status} - {item.scheduled_at}")
        else:
            print("❌ Échec de la validation")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_validation()
