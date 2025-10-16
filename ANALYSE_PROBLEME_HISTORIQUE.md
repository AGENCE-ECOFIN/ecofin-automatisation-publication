# 🔍 Analyse Problème Historique

## Problème Identifié

**Symptôme** : 12 posts validés et publiés, mais seulement 1-2 visibles dans l'historique

---

## 🔎 Analyse du Code

### Backend

**Endpoint** : `GET /posts/history/publications?limit=100`

```python
def get_publication_history(limit: int = 100):
    return db.query(Publication).order_by(Publication.created_at.desc()).limit(limit).all()
```

✅ Retourne TOUTES les publications de la table `publications`

---

### Frontend

**Récupération** :
```javascript
const { data: historyData } = useQuery('history', () => postsService.getHistory(100));

const allHistory = Array.isArray(historyData?.data) 
    ? historyData.data 
    : Array.isArray(historyData) 
      ? historyData 
      : [];
```

**Filtrage** :
```javascript
const history = allHistory.filter(item => {
  if (networkFilter && item.network !== networkFilter) return false;
  if (feedFilter) {
    if (feedFilter === 'direct') {
      if (item.post_id !== null) return false;  ← Problème potentiel?
    } else if (item.post_id === null || item.feed_id !== parseInt(feedFilter)) {
      return false;  ← item.feed_id n'existe PAS dans Publication!
    }
  }
  if (statusFilter) {
    const itemStatus = item.is_success ? 'PUBLISHED' : 'FAILED';
    if (itemStatus !== statusFilter) return false;
  }
  return true;
});
```

---

## 🐛 PROBLÈME TROUVÉ !

**Ligne critique** :
```javascript
} else if (item.post_id === null || item.feed_id !== parseInt(feedFilter)) {
  return false;
}
```

**Publications n'a PAS de colonne `feed_id` !**

Structure de `publications`:
```sql
publications
├── id
├── post_id (peut être NULL)
├── network
├── content
├── published_url
├── is_success
├── error_message
├── published_at
└── created_at
```

**Pas de `feed_id` !**

Donc quand on filtre, `item.feed_id` est toujours `undefined`, ce qui fait que le filtre retourne `false` et cache tous les posts !

---

## ✅ Solution

Il faut soit :

### Option 1 : Ajouter feed_id à publications (recommandé)

```sql
ALTER TABLE publications ADD COLUMN feed_id INTEGER;
```

Puis dans `direct_post.py` et `tasks.py`, ajouter :
```python
publication = Publication(
    post_id=item.post_id,
    feed_id=item.feed_id,  ← AJOUTER
    network=item.network,
    ...
)
```

### Option 2 : Corriger le filtre pour ne pas utiliser feed_id

```javascript
if (feedFilter) {
  if (feedFilter === 'direct') {
    if (item.post_id !== null) return false;
  } else {
    // Ne pas filtrer par feed_id car il n'existe pas dans publications
    // On pourrait filtrer par post_id qui appartient au feed...
    // Mais c'est compliqué
  }
}
```

---

## 💡 Recommandation

**Option 1** est meilleure car :
- ✅ Permet de filtrer par flux dans l'historique
- ✅ Plus cohérent avec la structure des données
- ✅ Facile à implémenter

---

## 🚀 Implémentation

1. Migration Alembic pour ajouter `feed_id`
2. Mise à jour du modèle `Publication`
3. Mise à jour du schema `PublicationResponse`
4. Mise à jour de `tasks.py` pour passer `feed_id`
5. Mise à jour de `direct_post.py` (feed_id = NULL)

