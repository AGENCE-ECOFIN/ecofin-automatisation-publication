#!/usr/bin/env python3
"""
Migrer l'historique de publication_queue vers publications
Pour récupérer les publications qui ont été faites avant la mise à jour
"""
import sys
sys.path.insert(0, '/app' if '/app' in __file__ else '.')

from app.core.database import SessionLocal
from app.models.publication_queue import PublicationQueue
from app.models.publication import Publication

def migrate_history():
    """Migrer les publications depuis publication_queue vers publications"""
    db = SessionLocal()
    try:
        print("="*60)
        print("🔄 Migration de l'historique")
        print("="*60)
        
        # 1. Vérifier les publications existantes
        existing_pubs = db.query(Publication).all()
        print(f"\n📊 État actuel:")
        print(f"  Publications dans 'publications': {len(existing_pubs)}")
        
        # 2. Récupérer tous les items PUBLISHED et FAILED de publication_queue
        queue_items = db.query(PublicationQueue).filter(
            PublicationQueue.status.in_(['PUBLISHED', 'FAILED'])
        ).all()
        
        print(f"  Items publiés dans 'publication_queue': {len(queue_items)}")
        print()
        
        if len(queue_items) == 0:
            print("⚠️  Aucune publication à migrer")
            return
        
        # 3. Pour chaque item, vérifier s'il existe déjà dans publications
        migrated = 0
        skipped = 0
        
        for item in queue_items:
            # Vérifier si déjà dans publications
            exists = db.query(Publication).filter(
                Publication.post_id == item.post_id,
                Publication.network == item.network,
                Publication.published_at == item.published_at
            ).first()
            
            if exists:
                skipped += 1
                continue
            
            # Créer l'entrée dans publications
            publication = Publication(
                post_id=item.post_id,
                network=item.network,
                content=item.content,
                published_url=item.publication_url,
                is_success=(item.status == 'PUBLISHED'),
                error_message=item.error_message if item.status == 'FAILED' else None,
                published_at=item.published_at or item.created_at
            )
            
            db.add(publication)
            migrated += 1
            
            print(f"{'✅' if item.status == 'PUBLISHED' else '❌'} Migré #{item.id}: {item.network} - {item.status}")
        
        db.commit()
        
        print()
        print("="*60)
        print("📊 RÉSULTAT")
        print("="*60)
        print(f"✅ Migrées: {migrated}")
        print(f"⏭️  Déjà existantes: {skipped}")
        print(f"📚 Total dans publications: {len(existing_pubs) + migrated}")
        print()
        print("✅ Migration terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_history()

