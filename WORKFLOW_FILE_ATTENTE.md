# 📋 Workflow File d'Attente - Comment ça Marche ?

## 🎯 Vue d'Ensemble

Lorsque vous **validez un post**, il est **automatiquement ajouté** à la file de publication pour **chaque réseau configuré** dans le flux RSS.

---

## 🔄 Workflow Complet

### 1️⃣ Configuration du Flux RSS

Quand vous créez un flux RSS, vous configurez :

```
Flux RSS "TechCrunch"
├── 📡 Réseaux cibles : Facebook, LinkedIn, X
└── 📄 Pages de destination :
    ├── Facebook → Page "Ma Page Facebook"
    ├── LinkedIn → Profil "Mon Profil LinkedIn"  
    └── X → Compte "Mon Compte X"
```

### 2️⃣ Configuration Globale des Réseaux

Dans **File d'attente → ⚙️ Configuration des réseaux** :

```
Facebook
├── ✅ Actif
├── ⏱️ Délai : 4 minutes
└── 📊 Max posts/jour : 10

LinkedIn  
├── ✅ Actif
├── ⏱️ Délai : 5 minutes
└── 📊 Max posts/jour : 8

X (Twitter)
├── ✅ Actif
├── ⏱️ Délai : 3 minutes
└── 📊 Max posts/jour : 15
```

### 3️⃣ Article Collecté → Brouillon

```
🤖 Celery collecte automatiquement l'article RSS
    ↓
📝 Génération IA du contenu pour chaque réseau
    ↓
📄 Post créé en "BROUILLON" avec :
    ├── Titre
    ├── Contenu original
    ├── Contenu généré pour Facebook
    ├── Contenu généré pour LinkedIn
    └── Contenu généré pour X
```

### 4️⃣ Validation du Post ✅

Quand vous cliquez sur **"Valider"** :

```python
# Ce qui se passe automatiquement :

1. Post marqué comme "validated" ✅
2. Pour CHAQUE réseau configuré dans le flux :
   
   a) Vérifie si le réseau est ACTIF globalement
   b) Récupère le DÉLAI depuis la config globale
   c) Récupère la PAGE depuis la config du flux
   d) Calcule l'heure de publication (FIFO)
   e) Crée une entrée dans publication_queue
```

### 5️⃣ Calcul FIFO Intelligent 🧠

```
Exemple avec un flux "TechCrunch" :

Post 1 validé à 10:00
├── Facebook → programmé à 10:04 (maintenant + 4 min)
├── LinkedIn → programmé à 10:05 (maintenant + 5 min)
└── X → programmé à 10:03 (maintenant + 3 min)

Post 2 validé à 10:02 (même flux)
├── Facebook → programmé à 10:08 (après Post1 + 4 min) ✅ FIFO
├── LinkedIn → programmé à 10:10 (après Post1 + 5 min) ✅ FIFO  
└── X → programmé à 10:06 (après Post1 + 3 min) ✅ FIFO

Post 3 d'un AUTRE flux validé à 10:02
├── Facebook → programmé à 10:06 (maintenant + 4 min) ← Pas de FIFO avec Post1/2
├── LinkedIn → programmé à 10:07 (maintenant + 5 min)
└── X → programmé à 10:05 (maintenant + 3 min)
```

**Règle FIFO** : Les posts du **même flux** sur le **même réseau** sont espacés automatiquement.

---

## 📊 Structure de la File d'Attente

### Table `publication_queue`

```sql
id  | post_id | feed_id | network    | status   | scheduled_at        | target_page_id
----|---------|---------|------------|----------|---------------------|----------------
1   | 42      | 5       | facebook   | PENDING  | 2025-10-12 10:04:00 | 722025697671791
2   | 42      | 5       | linkedin   | PENDING  | 2025-10-12 10:05:00 | 7297
3   | 42      | 5       | x          | PENDING  | 2025-10-12 10:03:00 | 8067
```

Chaque **ligne** = **1 publication** sur **1 réseau**

---

## ⚙️ Configuration : Où est Quoi ?

### 🌐 Configuration GLOBALE (network_configs)
**Emplacement** : File d'attente → Configuration des réseaux

**Ce qui est configuré ici** :
- ✅/❌ Réseau actif ou non
- ⏱️ **Délai entre publications** (minutes)
- 📊 **Max posts par jour**
- 🎯 **Heures optimales** de publication

**S'applique à** : TOUS les flux RSS

```sql
SELECT * FROM network_configs;

id | network  | is_active | default_publication_delay | max_posts_per_day
---|----------|-----------|---------------------------|------------------
1  | facebook | true      | 4                         | 10
2  | linkedin | true      | 5                         | 8
3  | x        | true      | 3                         | 15
```

### 📡 Configuration PAR FLUX (feeds)
**Emplacement** : Flux RSS → Créer/Éditer un flux

**Ce qui est configuré ici** :
- 📡 **Réseaux cibles** : Sur quels réseaux publier ?
- 📄 **Pages de destination** : Quelle page pour chaque réseau ?
- 💬 **Prompts personnalisés** : Instructions IA par réseau (optionnel)

**S'applique à** : CE flux uniquement

```sql
SELECT id, name, target_networks, social_pages FROM feeds;

id | name       | target_networks              | social_pages
---|------------|------------------------------|---------------------
5  | TechCrunch | ["facebook","linkedin","x"]  | {"facebook":"722025697671791",...}
```

---

## 🔥 Ce Qui Est Automatique

✅ **Collecte RSS** → Celery toutes les X minutes (fréquence du flux)
✅ **Génération IA** → Automatique à la collecte
✅ **Ajout à la file** → Automatique à la validation
✅ **Calcul FIFO** → Automatique (espacement intelligent)
✅ **Publication** → Celery au moment programmé
✅ **Retry** → Automatique si échec

---

## 🎮 Ce Que VOUS Contrôlez

### Via l'Interface

#### Dashboard "File d'attente"
- 👀 **Voir** tous les posts programmés
- ⏸️ **Pause** : Mettre un post en pause
- ▶️ **Reprendre** : Reprendre un post en pause
- ❌ **Annuler** : Annuler une publication
- 🔄 **Retry** : Republier un post échoué
- 📊 **Filtres** : Par flux, réseau, statut

#### Configuration des Réseaux
- ✅/❌ **Activer/Désactiver** un réseau
- ⏱️ **Modifier le délai** entre publications
- 📊 **Changer le max posts/jour**

#### Flux RSS
- 📡 **Choisir les réseaux** cibles
- 📄 **Sélectionner les pages** de destination
- 💬 **Personnaliser les prompts** IA

---

## 📈 Statuts des Publications

| Statut | Description | Icône | Action possible |
|--------|-------------|-------|-----------------|
| **PENDING** | En attente (> 10 min) | ⏳ | Pause, Annuler |
| **SCHEDULED** | Programmé (≤ 10 min) | 📅 | Pause, Annuler |
| **PUBLISHING** | En cours de publication | 🔄 | Attendre |
| **PUBLISHED** | Publié avec succès | ✅ | Voir lien |
| **FAILED** | Échec de publication | ❌ | Retry |
| **PAUSED** | En pause | ⏸️ | Reprendre, Annuler |
| **CANCELLED** | Annulé | ❌ | Aucune |

---

## 🚀 Exemple Complet

### Configuration

**Flux "Blog Tech"**
- URL RSS : https://blog.tech/feed.xml
- Fréquence : 120 minutes (2h)
- Réseaux : Facebook, LinkedIn
- Pages :
  - Facebook → "Page Tech News" (ID: 123456)
  - LinkedIn → "Profil John Doe" (ID: 7297)

**Config Globale**
- Facebook : Délai 4 min, Max 10/jour
- LinkedIn : Délai 5 min, Max 8/jour

### Scénario

**10:00** - Celery collecte 2 nouveaux articles
```
📰 Article 1 : "Les nouveautés React 19"
📰 Article 2 : "TypeScript 5.5 released"
```

**10:01** - IA génère le contenu pour Facebook et LinkedIn

**10:05** - Vous validez Article 1
```
File d'attente créée :
├── Facebook → 10:09 (dans 4 min)
└── LinkedIn → 10:10 (dans 5 min)
```

**10:07** - Vous validez Article 2
```
File d'attente mise à jour :
├── Facebook → 10:13 (après Article 1 + 4 min) ← FIFO !
└── LinkedIn → 10:15 (après Article 1 + 5 min) ← FIFO !
```

**10:09** - 🤖 Celery publie Article 1 sur Facebook
**10:10** - 🤖 Celery publie Article 1 sur LinkedIn  
**10:13** - 🤖 Celery publie Article 2 sur Facebook
**10:15** - 🤖 Celery publie Article 2 sur LinkedIn

**Résultat** : Publications espacées, pas de spam ! ✅

---

## 💡 Conseils

### Pour un flux à fort volume
```
✅ Augmentez le délai (ex: 10 min au lieu de 4)
✅ Réduisez le max posts/jour
✅ Utilisez les pauses stratégiquement
```

### Pour plusieurs flux
```
✅ Chaque flux a son propre FIFO
✅ Pas d'interférence entre flux
✅ Publications peuvent être en parallèle
```

### Pour tester
```
✅ Créez un flux test avec délai court (1 min)
✅ Validez 1-2 posts
✅ Observez dans la file d'attente
✅ Vérifiez les publications
```

---

## 🔍 Debug / Vérification

### Dans la base de données

```sql
-- Voir la file d'attente
SELECT 
    pq.id,
    p.title,
    f.name as feed_name,
    pq.network,
    pq.status,
    pq.scheduled_at,
    pq.target_page_id
FROM publication_queue pq
JOIN posts p ON pq.post_id = p.id
JOIN feeds f ON pq.feed_id = f.id
ORDER BY pq.scheduled_at;

-- Statistiques par réseau
SELECT 
    network,
    status,
    COUNT(*) as total
FROM publication_queue
GROUP BY network, status;
```

### Dans les logs

```bash
# Backend
docker logs ecofin-backend-preprod | grep -i "validation\|queue\|fifo"

# Celery Worker
docker logs ecofin-celery-worker-preprod | grep -i "publish\|queue"
```

---

<div align="center">

**✨ Le système gère tout automatiquement ! ✨**

Vous n'avez qu'à :
1. Configurer les flux RSS (une fois)
2. Configurer les réseaux globalement (une fois)  
3. Valider les posts
4. 🎉 La magie opère !

</div>

