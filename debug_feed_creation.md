# 🔍 Debug Création/Modification de Feed

## Problème Identifié

**Symptôme** : Lorsqu'on crée ou modifie un feed et qu'on sélectionne une page, le `social_pages` n'est pas sauvegardé.

---

## 🧪 Test Étape par Étape

### 1. Frontend - Vérifier ce qui est envoyé

Dans `FeedCreationModal.js` ligne 106, ajoutez un log :

```javascript
console.log('📤 Envoi des données du flux:', formData);
await onSave(formData);
```

**Ce qu'on doit voir dans la console du navigateur (F12)** :
```javascript
{
  name: "Mon Flux",
  url: "https://example.com/feed.xml",
  frequency_minutes: 120,
  target_networks: ["facebook", "linkedin"],
  social_pages: {
    facebook: "722025697671791",  ← DOIT ÊTRE LÀ !
    linkedin: "7297"
  },
  network_prompts: {},
  is_active: true
}
```

**Si `social_pages` est vide `{}` → Problème Frontend**
**Si `social_pages` est rempli → Problème Backend**

---

### 2. Backend - Vérifier la réception

Dans `backend/app/services/feed_service.py`, ajoutez des logs :

```python
def create_feed(self, feed: FeedCreate, user_id: int) -> Feed:
    print(f"\n🔍 DEBUG CREATE FEED:")
    print(f"   name: {feed.name}")
    print(f"   target_networks: {feed.target_networks}")
    print(f"   social_pages: {feed.social_pages}")  ← LOG ICI
    
    db_feed = Feed(
        name=feed.name,
        url=str(feed.url),
        frequency_minutes=feed.frequency_minutes,
        custom_prompt=feed.custom_prompt,
        target_networks=feed.target_networks,
        social_pages=feed.social_pages,  ← Vérifier que c'est là
        network_prompts=feed.network_prompts,
        created_by=user_id
    )
    
    self.db.add(db_feed)
    self.db.commit()
    self.db.refresh(db_feed)
    
    print(f"\n✅ Feed créé:")
    print(f"   id: {db_feed.id}")
    print(f"   social_pages APRÈS commit: {db_feed.social_pages}")  ← LOG APRÈS
    
    return db_feed
```

---

### 3. Vérifier dans la Base de Données

```sql
-- Dans PostgreSQL
SELECT id, name, target_networks, social_pages 
FROM feeds 
ORDER BY id DESC 
LIMIT 1;
```

**Si social_pages est NULL ou {} après création → Problème dans feed_service.py**

---

## 🔧 Solutions Potentielles

### Solution 1 : Ajouter social_pages explicitement

Dans `backend/app/services/feed_service.py` :

```python
def create_feed(self, feed: FeedCreate, user_id: int) -> Feed:
    # Log pour debug
    print(f"🔍 Création feed - social_pages reçu: {feed.social_pages}")
    
    db_feed = Feed(
        name=feed.name,
        url=str(feed.url),
        frequency_minutes=feed.frequency_minutes,
        custom_prompt=feed.custom_prompt,
        target_networks=feed.target_networks,
        publication_timing=feed.publication_timing,
        social_pages=feed.social_pages,  # ← Doit être là !
        network_prompts=feed.network_prompts,
        created_by=user_id
    )
    
    self.db.add(db_feed)
    self.db.commit()
    self.db.refresh(db_feed)
    
    # Vérifier après commit
    print(f"✅ Feed créé - social_pages sauvegardé: {db_feed.social_pages}")
    
    return db_feed
```

### Solution 2 : Vérifier le Schema Pydantic

Dans `backend/app/schemas/feed.py` :

```python
class FeedBase(BaseModel):
    name: str
    url: Union[HttpUrl, str]
    frequency_minutes: int = 60
    custom_prompt: Optional[str] = None
    network_prompts: Optional[Dict[str, str]] = None
    target_networks: Optional[List[str]] = None
    publication_timing: Optional[Dict[str, int]] = None
    social_pages: Optional[Dict[str, str]] = None  ← Doit être là !
```

**Si ce champ manque → Les données ne sont pas validées**

---

## 🎯 Test Rapide

### Dans la console navigateur (F12) :

```javascript
// Ouvrir la création de flux
// À l'étape 3, sélectionner des pages
// Puis ouvrir la console et taper :

// Vérifier l'état du formulaire
console.log('FormData:', window.formData);  // Si accessible
```

### Dans les logs backend :

```bash
# Chercher les logs de création
docker logs ecofin-backend-preprod | grep -i "social_pages\|création feed"

# Ou en local
tail -f backend/logs/*.log | grep -i social_pages
```

---

## 🚨 Points de Vérification

1. ✅ Frontend envoie `social_pages` dans la requête POST/PUT
2. ✅ Backend reçoit `social_pages` dans FeedCreate/FeedUpdate schema
3. ✅ FeedService.create_feed assigne `social_pages` au modèle
4. ✅ SQLAlchemy sauvegarde le JSON dans la colonne
5. ✅ La valeur est bien dans la DB après commit

---

<div align="center">

**💡 Prochaine étape** : Ajoutons des logs de debug pour identifier exactement où le problème se situe

</div>

