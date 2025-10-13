# 🐛 Erreur PageId Blotato

## ❌ Problème

```
Erreur Blotato 400: body.post.target must have required property 'pageId'
```

**Cause** : Le `target_page_id` n'est pas défini pour Facebook lors de l'ajout à la file de publication.

---

## 🔍 Diagnostic

### Vérifier les Feeds en Production

Sur le serveur :

```bash
# Se connecter
ssh user@185.143.103.162

# Vérifier les feeds et leurs configurations de pages
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication << 'SQL'

-- Voir les flux et leurs pages configurées
SELECT 
    id, 
    name, 
    target_networks,
    social_pages
FROM feeds;

SQL
```

**Résultat attendu** :
```
 id | name       | target_networks              | social_pages
----|------------|------------------------------|------------------
  1 | TechCrunch | ["facebook","linkedin","x"]  | {"facebook":"722025697671791",...}
```

**Si `social_pages` est `NULL` ou `{}` → C'EST LE PROBLÈME !**

---

## ✅ Solution 1 : Mettre à Jour les Feeds

### Sur le serveur

```bash
docker exec -it ecofin-backend-preprod python << 'PYTHON'
from app.core.database import SessionLocal
from app.models.feed import Feed
import json

db = SessionLocal()

# Charger les IDs depuis blotato_accounts.json
with open('/app/blotato_accounts.json', 'r') as f:
    blotato_accounts = json.load(f)

# Récupérer les feeds
feeds = db.query(Feed).all()
print(f"\n🔍 {len(feeds)} flux trouvés\n")

for feed in feeds:
    print(f"📰 Flux #{feed.id}: {feed.name}")
    print(f"   Réseaux: {feed.target_networks}")
    print(f"   Pages actuelles: {feed.social_pages}")
    
    # Si social_pages est vide, le configurer avec les comptes par défaut
    if not feed.social_pages or feed.social_pages == {}:
        print(f"   ⚠️  Aucune page configurée!")
        
        # Créer la configuration par défaut
        social_pages = {}
        
        if feed.target_networks:
            for network in feed.target_networks:
                if network == 'facebook' and 'facebook' in blotato_accounts:
                    # Prendre la première page Facebook
                    pages = blotato_accounts['facebook'].get('pages', [])
                    if pages and len(pages) > 0:
                        social_pages['facebook'] = pages[0]['id']
                        print(f"   ✅ Facebook: {pages[0]['id']} ({pages[0]['name']})")
                
                elif network == 'linkedin' and 'linkedin' in blotato_accounts:
                    pages = blotato_accounts['linkedin'].get('pages', [])
                    if pages and len(pages) > 0:
                        social_pages['linkedin'] = pages[0]['id']
                        print(f"   ✅ LinkedIn: {pages[0]['id']}")
                
                elif network == 'x' and 'x' in blotato_accounts:
                    pages = blotato_accounts['x'].get('pages', [])
                    if pages and len(pages) > 0:
                        social_pages['x'] = pages[0]['id']
                        print(f"   ✅ X: {pages[0]['id']}")
        
        # Mettre à jour le feed
        feed.social_pages = social_pages
        db.commit()
        print(f"   ✅ Pages configurées!")
    else:
        print(f"   ✅ Pages déjà configurées")
    
    print("")

print("\n✅ Terminé!")
db.close()
PYTHON
```

---

## ✅ Solution 2 : Rendre pageId Obligatoire dans Blotato Service

### Modifier le code (déjà fait en local)

`backend/app/services/blotato_service.py` :

```python
# Facebook nécessite TOUJOURS un pageId
if platform == "facebook":
    if not page_id:
        # Essayer de récupérer depuis la config
        if hasattr(settings, 'BLOTATO_FACEBOOK_PAGE_ID'):
            page_id = settings.BLOTATO_FACEBOOK_PAGE_ID
    
    if not page_id:
        # ERREUR : Facebook nécessite un pageId
        return False, f"Facebook nécessite un pageId (target_page_id manquant)", None
    
    target["pageId"] = page_id
```

---

## ✅ Solution 3 : Vérifier lors de la Validation

### Dans `post_service.py`

Ajouter une vérification lors de l'ajout à la file :

```python
# Page : depuis la config DU FLUX
destination_id = social_pages.get(network, '')

# ⚠️ Facebook nécessite OBLIGATOIREMENT un pageId
if network == 'facebook' and not destination_id:
    print(f"⚠️  Facebook nécessite un pageId pour ce flux - Skip")
    continue

queue_item = PublicationQueue(
    ...
    target_page_id=destination_id,
    ...
)
```

---

## 🚀 Solution Rapide (Recommandée)

### 1. Exécuter la Solution 1 sur le serveur

```bash
ssh user@185.143.103.162

# Copier le script de mise à jour
# (voir Solution 1 ci-dessus)
```

### 2. Vérifier que ça fonctionne

```bash
# Vérifier les feeds
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication \
  -c "SELECT id, name, social_pages FROM feeds;"

# Devrait afficher les pages configurées pour chaque flux
```

### 3. Retry les publications échouées

```bash
# Dans l'interface web
# File d'attente → Chercher les publications "Failed"
# Cliquer sur "Retry" pour chaque publication échouée
```

---

## 🔧 Prevention : Rendre le pageId Obligatoire

### Dans le Frontend (Création de Flux)

S'assurer que l'utilisateur DOIT sélectionner une page pour chaque réseau :

```javascript
// frontend/src/components/FeedCreationModal.js
// Étape 3 : Pages de destination

// Validation avant de passer à l'étape suivante
const validateStep3 = () => {
  for (const network of selectedNetworks) {
    if (network === 'facebook' && !socialPages[network]) {
      alert('Veuillez sélectionner une page Facebook');
      return false;
    }
  }
  return true;
};
```

---

## 📊 Commande de Diagnostic Complète

```bash
# Sur le serveur
ssh user@185.143.103.162

# Tout vérifier d'un coup
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication << 'SQL'

-- Feeds sans pages configurées
SELECT id, name, target_networks, social_pages
FROM feeds
WHERE social_pages IS NULL OR social_pages = '{}';

-- Publications échouées à cause de pageId
SELECT id, post_id, network, status, error_message
FROM publication_queue
WHERE error_message LIKE '%pageId%';

-- Count par statut
SELECT status, COUNT(*) 
FROM publication_queue 
GROUP BY status;

SQL
```

---

<div align="center">

**💡 Astuce** : Toujours configurer les pages de destination lors de la création d'un flux !

</div>

