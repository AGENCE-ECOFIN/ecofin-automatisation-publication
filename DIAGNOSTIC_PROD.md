# 🔍 Diagnostic Problèmes Production

## Problèmes Identifiés

### 1. ❌ Modal "Configuration des réseaux" vide
**Symptôme** : Le modal s'ouvre mais n'affiche aucun réseau

**Causes possibles** :
- Les réseaux ne sont pas créés dans la base de données
- L'endpoint `/networks/` ne retourne rien
- Erreur CORS ou authentification

### 2. ❌ Posts validés (2) non visibles dans la file
**Symptôme** : File d'attente vide malgré 2 posts validés

**Causes possibles** :
- Les posts sont validés mais pas ajoutés à `publication_queue`
- L'endpoint `/publication-queue/` ne retourne rien
- Problème de migration de base de données

---

## 🔧 Diagnostic à Effectuer sur le Serveur

### Étape 1 : Vérifier la base de données

```bash
# Se connecter au serveur
ssh user@votre-serveur

# Accéder à PostgreSQL
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication

# Vérifier les posts validés
SELECT id, title, status, validated_at FROM posts WHERE status = 'validated';

# Vérifier la file de publication
SELECT id, post_id, network, status, scheduled_time FROM publication_queue;

# Vérifier les réseaux configurés
SELECT id, network, is_active, default_publication_delay, max_posts_per_day FROM network_configs;

# Quitter
\q
```

### Étape 2 : Vérifier les logs du backend

```bash
# Logs du backend
docker logs ecofin-backend-preprod --tail=100

# Rechercher des erreurs
docker logs ecofin-backend-preprod 2>&1 | grep -i error

# Vérifier les requêtes API
docker logs ecofin-backend-preprod 2>&1 | grep -E "GET|POST|PUT"
```

### Étape 3 : Tester les endpoints API

```bash
# Depuis le serveur

# 1. Tester l'endpoint des réseaux
curl -X GET http://localhost:8000/networks/ \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  | jq

# 2. Tester la file de publication
curl -X GET http://localhost:8000/publication-queue/ \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  | jq

# 3. Tester les posts validés
curl -X GET http://localhost:8000/posts/validated \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  | jq

# 4. Vérifier la santé de l'API
curl http://localhost:8000/health
```

---

## 🚑 Solutions Rapides

### Solution 1 : Créer les configurations de réseaux

```bash
# Se connecter au conteneur backend
docker exec -it ecofin-backend-preprod bash

# Lancer Python
python

# Créer les réseaux
from app.core.database import SessionLocal
from app.models.network_config import NetworkConfig

db = SessionLocal()

# Vérifier si les réseaux existent
networks = db.query(NetworkConfig).all()
print(f"Réseaux existants: {len(networks)}")
for net in networks:
    print(f"  - {net.network}: actif={net.is_active}")

# Si vide, créer les réseaux
if len(networks) == 0:
    print("Création des réseaux...")
    
    facebook = NetworkConfig(
        network='facebook',
        is_active=True,
        default_publication_delay=4,
        max_posts_per_day=10
    )
    
    linkedin = NetworkConfig(
        network='linkedin',
        is_active=True,
        default_publication_delay=5,
        max_posts_per_day=8
    )
    
    x = NetworkConfig(
        network='x',
        is_active=True,
        default_publication_delay=3,
        max_posts_per_day=15
    )
    
    db.add(facebook)
    db.add(linkedin)
    db.add(x)
    db.commit()
    print("✅ Réseaux créés avec succès!")

db.close()
exit()

# Sortir du conteneur
exit
```

### Solution 2 : Ajouter manuellement les posts validés à la file

```bash
# Se connecter au conteneur backend
docker exec -it ecofin-backend-preprod python

# Ajouter à la file
from app.core.database import SessionLocal
from app.models.post import Post
from app.models.publication_queue import PublicationQueue
from app.models.network_config import NetworkConfig
from datetime import datetime, timedelta, timezone

db = SessionLocal()

# Récupérer les posts validés
validated_posts = db.query(Post).filter(Post.status == 'validated').all()
print(f"Posts validés trouvés: {len(validated_posts)}")

for post in validated_posts:
    print(f"\n📝 Post: {post.title[:50]}")
    print(f"   Feed: {post.feed.name if post.feed else 'N/A'}")
    print(f"   Réseaux cibles: {post.feed.target_networks if post.feed else []}")
    
    # Vérifier s'il est déjà dans la file
    existing = db.query(PublicationQueue).filter(
        PublicationQueue.post_id == post.id
    ).count()
    
    if existing > 0:
        print(f"   ⚠️  Déjà dans la file ({existing} entrées)")
        continue
    
    # Récupérer les réseaux cibles
    target_networks = post.feed.target_networks if post.feed and post.feed.target_networks else ['facebook', 'linkedin', 'x']
    social_pages = post.feed.social_pages if post.feed and post.feed.social_pages else {}
    
    # Ajouter à la file pour chaque réseau
    now = datetime.now(timezone.utc)
    
    for network in target_networks:
        if network in post.generated_content:
            # Récupérer le délai du réseau
            network_config = db.query(NetworkConfig).filter(
                NetworkConfig.network == network
            ).first()
            
            delay_minutes = network_config.default_publication_delay if network_config else 5
            
            # Calculer l'heure de publication
            scheduled_time = now + timedelta(minutes=delay_minutes)
            
            # Récupérer la page de destination
            target_page_id = social_pages.get(network) if social_pages else None
            
            queue_item = PublicationQueue(
                post_id=post.id,
                feed_id=post.feed_id,
                network=network,
                content=post.generated_content[network],
                scheduled_time=scheduled_time,
                status='pending',
                target_page_id=target_page_id
            )
            
            db.add(queue_item)
            print(f"   ✅ Ajouté à la file: {network} -> {scheduled_time}")

db.commit()
print("\n✅ Terminé!")

db.close()
exit()

# Sortir
exit
```

---

## 🔍 Vérification Finale

```bash
# 1. Vérifier dans la base de données
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication \
  -c "SELECT COUNT(*) as total FROM network_configs;" \
  -c "SELECT COUNT(*) as total FROM publication_queue;"

# 2. Redémarrer le backend pour rafraîchir
docker restart ecofin-backend-preprod

# 3. Vérifier l'API
sleep 5
curl http://localhost:8000/health
curl -X GET http://localhost:8000/networks/ | jq

# 4. Dans le navigateur, rafraîchir la page (Ctrl+F5)
```

---

## 📝 Script Automatique de Correction

Créer un fichier `fix_production.sh` :

```bash
#!/bin/bash

echo "🔧 Correction des problèmes de production..."

# Créer les réseaux si absents
docker exec -it ecofin-backend-preprod python << 'PYTHON'
from app.core.database import SessionLocal
from app.models.network_config import NetworkConfig

db = SessionLocal()
networks = db.query(NetworkConfig).all()

if len(networks) == 0:
    print("📝 Création des réseaux...")
    for net_name, delay, max_posts in [('facebook', 4, 10), ('linkedin', 5, 8), ('x', 3, 15)]:
        network = NetworkConfig(
            network=net_name,
            is_active=True,
            default_publication_delay=delay,
            max_posts_per_day=max_posts
        )
        db.add(network)
    db.commit()
    print("✅ Réseaux créés!")
else:
    print(f"✅ {len(networks)} réseaux déjà configurés")

db.close()
PYTHON

# Ajouter les posts validés à la file
docker exec -it ecofin-backend-preprod python << 'PYTHON'
from app.core.database import SessionLocal
from app.services.post_service import PostService

db = SessionLocal()
post_service = PostService(db)

# Récupérer et traiter les posts validés
validated_posts = post_service.get_posts(status='validated')
print(f"📝 {len(validated_posts)} posts validés trouvés")

for post in validated_posts:
    try:
        post_service._add_to_publication_queue(post)
        print(f"✅ {post.title[:50]} ajouté à la file")
    except Exception as e:
        print(f"❌ Erreur: {e}")

db.close()
PYTHON

# Redémarrer le backend
docker restart ecofin-backend-preprod

echo "✅ Correction terminée! Attendez 10 secondes puis rafraîchissez la page."
```

---

## 🎯 Checklist de Vérification

- [ ] Les 3 réseaux (facebook, linkedin, x) existent dans `network_configs`
- [ ] Les posts validés existent dans la table `posts` avec `status='validated'`
- [ ] Les posts validés sont présents dans `publication_queue`
- [ ] L'endpoint `/networks/` retourne 3 réseaux
- [ ] L'endpoint `/publication-queue/` retourne des items
- [ ] Le token JWT est valide (pas expiré)
- [ ] Le frontend affiche l'URL API correcte dans les logs console
- [ ] Pas d'erreurs CORS dans la console du navigateur

---

## 📞 Obtenir Plus d'Informations

### Dans la console du navigateur (F12)

```javascript
// Vérifier l'URL de l'API
console.log('API URL:', process.env.REACT_APP_API_URL || 'http://localhost:8000');

// Vérifier le token
console.log('Token:', localStorage.getItem('token') ? 'Présent' : 'Absent');

// Tester l'API manuellement
fetch('http://votre-serveur:8000/networks/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
.then(r => r.json())
.then(data => console.log('Networks:', data))
.catch(err => console.error('Error:', err));

fetch('http://votre-serveur:8000/publication-queue/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
.then(r => r.json())
.then(data => console.log('Queue:', data))
.catch(err => console.error('Error:', err));
```

---

<div align="center">

**💡 Conseil** : Commencez par la "Solution 1" pour créer les réseaux, puis la "Solution 2" pour ajouter les posts à la file.

</div>

