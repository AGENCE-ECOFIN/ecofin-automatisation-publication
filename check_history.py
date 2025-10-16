#!/usr/bin/env python3
"""
Vérifier ce qui est dans la base de données pour l'historique
"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.publication import Publication
from app.models.publication_queue import PublicationQueue

db = SessionLocal()

print("="*60)
print("🔍 DIAGNOSTIC HISTORIQUE DES PUBLICATIONS")
print("="*60)

# 1. Publications (table publications)
print("\n1️⃣ TABLE PUBLICATIONS (historique réel)")
print("-"*60)
publications = db.query(Publication).order_by(Publication.created_at.desc()).all()
print(f"Total: {len(publications)} entrées\n")

for pub in publications:
    print(f"ID #{pub.id}:")
    print(f"  post_id: {pub.post_id if pub.post_id else '📤 POST DIRECT'}")
    print(f"  network: {pub.network}")
    print(f"  is_success: {'✅ Oui' if pub.is_success else '❌ Non'}")
    print(f"  published_url: {pub.published_url if pub.published_url else 'N/A'}")
    print(f"  published_at: {pub.published_at}")
    if pub.error_message:
        print(f"  error: {pub.error_message}")
    print()

# 2. Publication Queue avec statut PUBLISHED/FAILED
print("\n2️⃣ TABLE PUBLICATION_QUEUE (PUBLISHED/FAILED)")
print("-"*60)
queue_history = db.query(PublicationQueue).filter(
    PublicationQueue.status.in_(['PUBLISHED', 'FAILED'])
).order_by(PublicationQueue.published_at.desc()).all()
print(f"Total: {len(queue_history)} entrées\n")

for item in queue_history:
    print(f"ID #{item.id}:")
    print(f"  post_id: {item.post_id}")
    print(f"  feed_id: {item.feed_id}")
    print(f"  network: {item.network}")
    print(f"  status: {item.status}")
    print(f"  published_at: {item.published_at}")
    print()

# 3. Résumé
print("="*60)
print("📊 RÉSUMÉ")
print("="*60)
print(f"Publications (table publications): {len(publications)}")
print(f"  - Succès: {len([p for p in publications if p.is_success])}")
print(f"  - Échecs: {len([p for p in publications if not p.is_success])}")
print(f"  - Posts directs (post_id NULL): {len([p for p in publications if p.post_id is None])}")
print()
print(f"Queue Published/Failed: {len(queue_history)}")
print(f"  - PUBLISHED: {len([q for q in queue_history if q.status == 'PUBLISHED'])}")
print(f"  - FAILED: {len([q for q in queue_history if q.status == 'FAILED'])}")
print()

# 4. Recommandation
print("💡 RECOMMANDATION")
print("-"*60)
print("L'historique devrait afficher les données de:")
print("  ✅ Table 'publications' (posts RSS + posts directs)")
print("  ❌ PAS 'publication_queue' (c'est juste la file d'attente)")
print()

db.close()

