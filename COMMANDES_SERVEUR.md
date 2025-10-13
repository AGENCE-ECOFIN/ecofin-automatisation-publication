# 🚀 Commandes à Exécuter sur le Serveur

## 📍 Connexion au Serveur

```bash
ssh user@185.143.103.162
```

---

## 1️⃣ Créer les Réseaux (Facebook, LinkedIn, X)

```bash
# Exécuter cette commande en UNE SEULE FOIS
docker exec -it ecofin-backend-preprod python << 'PYTHON'
from app.core.database import SessionLocal
from app.models.network_config import NetworkConfig

db = SessionLocal()

# Vérifier si les réseaux existent
existing = db.query(NetworkConfig).all()
print(f"Réseaux existants: {len(existing)}")

if len(existing) == 0:
    print("\n📝 Création des réseaux...")
    
    # Créer Facebook
    facebook = NetworkConfig(
        network='facebook',
        is_active=True,
        default_publication_delay=4,
        max_posts_per_day=10
    )
    db.add(facebook)
    print("✅ Facebook créé")
    
    # Créer LinkedIn
    linkedin = NetworkConfig(
        network='linkedin',
        is_active=True,
        default_publication_delay=5,
        max_posts_per_day=8
    )
    db.add(linkedin)
    print("✅ LinkedIn créé")
    
    # Créer X (Twitter)
    x = NetworkConfig(
        network='x',
        is_active=True,
        default_publication_delay=3,
        max_posts_per_day=15
    )
    db.add(x)
    print("✅ X (Twitter) créé")
    
    db.commit()
    print("\n✅ 3 réseaux créés avec succès!")
else:
    print("\n⚠️  Les réseaux existent déjà:")
    for net in existing:
        print(f"  - {net.network}: actif={net.is_active}, délai={net.default_publication_delay}min")

db.close()
PYTHON
```

---

## 2️⃣ Vérifier que les Réseaux Sont Créés

```bash
# Vérifier dans la base de données
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication -c "SELECT id, network, is_active, default_publication_delay, max_posts_per_day FROM network_configs;"
```

**Résultat attendu :**
```
 id | network  | is_active | default_publication_delay | max_posts_per_day 
----+----------+-----------+---------------------------+-------------------
  1 | facebook | t         |                         4 |                10
  2 | linkedin | t         |                         5 |                 8
  3 | x        | t         |                         3 |                15
```

---

## 3️⃣ Tester l'API

```bash
# Tester l'endpoint des réseaux
curl -s http://localhost:8000/networks/ | jq
```

**Résultat attendu :**
```json
[
  {
    "id": 1,
    "network": "facebook",
    "is_active": true,
    "default_publication_delay": 4,
    "max_posts_per_day": 10
  },
  {
    "id": 2,
    "network": "linkedin",
    "is_active": true,
    "default_publication_delay": 5,
    "max_posts_per_day": 8
  },
  {
    "id": 3,
    "network": "x",
    "is_active": true,
    "default_publication_delay": 3,
    "max_posts_per_day": 15
  }
]
```

---

## 4️⃣ Redémarrer le Backend (Important)

```bash
docker restart ecofin-backend-preprod
```

Attendre 15 secondes puis vérifier :

```bash
docker logs ecofin-backend-preprod --tail=20
```

---

## 5️⃣ Vérifier dans le Navigateur

1. **Rafraîchir la page** avec `Ctrl + F5` (ou `Cmd + Shift + R` sur Mac)
2. Aller dans **File d'attente**
3. Cliquer sur **⚙️ Configuration des réseaux**
4. Vous devriez voir **3 cartes** : Facebook, LinkedIn, X

---

## 🔍 Si les Posts Validés N'Apparaissent Pas

### Vérifier les posts validés

```bash
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication -c "SELECT id, title, status, validated_at FROM posts WHERE status = 'validated';"
```

### Ajouter les posts validés à la file

```bash
docker exec -it ecofin-backend-preprod python << 'PYTHON'
from app.core.database import SessionLocal
from app.services.post_service import PostService

db = SessionLocal()
post_service = PostService(db)

# Récupérer les posts validés
validated = post_service.get_posts(status='validated')
print(f"\n📝 {len(validated)} posts validés trouvés")

if len(validated) == 0:
    print("⚠️  Aucun post validé")
else:
    for post in validated:
        try:
            # Vérifier s'il est déjà dans la file
            from app.models.publication_queue import PublicationQueue
            existing = db.query(PublicationQueue).filter(
                PublicationQueue.post_id == post.id
            ).count()
            
            if existing > 0:
                print(f"⚠️  Post #{post.id} déjà dans la file")
            else:
                # Ajouter à la file
                post_service._add_to_publication_queue(post)
                print(f"✅ Post #{post.id}: {post.title[:50]}")
        except Exception as e:
            print(f"❌ Erreur: {e}")

db.close()
print("\n✅ Terminé!")
PYTHON
```

### Vérifier la file de publication

```bash
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication -c "SELECT id, post_id, network, status, scheduled_time FROM publication_queue ORDER BY scheduled_time;"
```

---

## 📊 Commandes de Diagnostic Rapide

### Tout en Une Commande

```bash
echo "=== DIAGNOSTIC COMPLET ===" && \
echo "" && \
echo "1. Réseaux configurés:" && \
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication -c "SELECT COUNT(*) as total FROM network_configs;" && \
echo "" && \
echo "2. Posts validés:" && \
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication -c "SELECT COUNT(*) as total FROM posts WHERE status = 'validated';" && \
echo "" && \
echo "3. File de publication:" && \
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication -c "SELECT COUNT(*) as total FROM publication_queue;" && \
echo "" && \
echo "4. Backend status:" && \
curl -s http://localhost:8000/health | jq
```

---

## 🚑 En Cas de Problème

### Le backend ne répond pas

```bash
# Vérifier le statut
docker ps | grep ecofin

# Voir les logs
docker logs ecofin-backend-preprod --tail=50

# Redémarrer
docker restart ecofin-backend-preprod
```

### PostgreSQL ne répond pas

```bash
# Vérifier
docker logs ecofin-postgres-preprod --tail=20

# Redémarrer
docker restart ecofin-postgres-preprod
```

### Tout réinitialiser (⚠️ Supprime les données)

```bash
cd ~/ecofin-publication-preprod
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

---

## ✅ Checklist Finale

- [ ] Les 3 réseaux sont créés (Facebook, LinkedIn, X)
- [ ] L'endpoint `/networks/` retourne 3 réseaux
- [ ] Le backend est redémarré
- [ ] La page est rafraîchie avec Ctrl+F5
- [ ] Le modal "Configuration des réseaux" affiche 3 cartes
- [ ] Les posts validés apparaissent dans la file

---

<div align="center">

**💡 Astuce** : Copiez-collez les commandes une par une dans votre terminal SSH

**🔗 Serveur** : ssh user@185.143.103.162

</div>

