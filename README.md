# 📰 EcoFin Publication

Application automatisée de collecte, génération et publication de contenus sur les réseaux sociaux.

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)

</div>

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Technologies](#-technologies)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Déploiement](#-déploiement)
- [API Documentation](#-api-documentation)

## ✨ Fonctionnalités

### 🤖 Automatisation Complète
- **Collecte RSS automatique** : Surveillance continue de flux RSS avec fréquence configurable (minutes)
- **Génération IA de posts** : Création de contenu optimisé par réseau social avec OpenAI GPT
- **Publication planifiée** : File d'attente intelligente FIFO avec espacement dynamique
- **Multi-réseaux** : Publication simultanée sur LinkedIn, Facebook et X (Twitter) via Blotato
- **Retry automatique** : Nouvelle tentative en cas d'échec avec gestion intelligente des erreurs

### 📊 Gestion et Contrôle
- **Validation manuelle** : Révision des brouillons avant publication
- **Personnalisation par réseau** : Prompts spécifiques pour chaque plateforme sociale
- **Historique complet** : Suivi détaillé avec filtres (réseau, flux, statut)
- **Dashboard en temps réel** : Statistiques actualisées toutes les 3 secondes
- **Compte à rebours** : Timer dynamique jusqu'à la prochaine publication (refresh 1s)

### 👥 Gestion des Utilisateurs
- **Authentification sécurisée** : JWT + bcrypt pour les mots de passe
- **Rôles et permissions** : Admin (gestion complète) et utilisateurs standards
- **Emails automatiques** : Bienvenue avec identifiants, réinitialisation de mot de passe
- **Gestion des comptes** : CRUD complet avec validation et sécurité
- **SMTP intégré** : Envoi d'emails avec design professionnel HTML

### 🎯 Fonctionnalités Avancées
- **Post direct** : Création manuelle hors flux RSS avec génération IA optionnelle
- **Prompts personnalisés** : Contrôle fin de la tonalité et du style par réseau
- **File FIFO intelligente** : Publication séquentielle par feed et réseau avec espacement
- **Pause/Reprise globale ou individuelle** : Contrôle granulaire de chaque publication
- **Configuration dynamique** : Délais, max posts/jour, sans redémarrage
- **Pages de destination** : Sélection dynamique des pages Facebook/comptes pour chaque flux

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │──────┐
└─────────────────┘      │
                         │
                         ↓
┌─────────────────────────────────────────┐
│          Backend API (FastAPI)          │
├─────────────────────────────────────────┤
│  • Auth & Users                         │
│  • Feeds Management                     │
│  • Posts Generation                     │
│  • Publication Queue                    │
└─────────────────────────────────────────┘
           │                │
           ↓                ↓
┌──────────────────┐  ┌─────────────┐
│   PostgreSQL     │  │    Redis    │
│   (Database)     │  │   (Cache)   │
└──────────────────┘  └─────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│         Celery Workers & Beat           │
├─────────────────────────────────────────┤
│  • RSS Fetching                         │
│  • Content Generation (OpenAI)          │
│  • Social Media Publishing (Blotato)    │
└─────────────────────────────────────────┘
```

## 🛠️ Technologies

### Backend
- **FastAPI** 0.104.1 - Framework API moderne et performant
- **SQLAlchemy** 2.0.23 - ORM Python avec PostgreSQL
- **Celery** 5.3.4 - File de tâches asynchrones + Beat pour la planification
- **Redis** 5.0.1 - Cache et broker Celery
- **OpenAI** 1.3.8 - Génération de contenu IA (GPT)
- **Pydantic** 2.5.0 - Validation des données
- **Gunicorn** 21.2.0 - Serveur WSGI production
- **Alembic** 1.13.1 - Migrations de base de données
- **Feedparser** 6.0.10 - Parsing de flux RSS
- **BeautifulSoup4** 4.12.2 - Extraction de contenu HTML
- **Python-Jose** 3.3.0 - JWT pour l'authentification
- **Passlib** 1.7.4 - Hachage de mots de passe bcrypt

### Frontend
- **React** 18 - Interface utilisateur moderne
- **React Query** - Gestion d'état et cache
- **Tailwind CSS** - Styling utility-first
- **React Router** - Navigation
- **Axios** - Requêtes HTTP

### Infrastructure
- **Docker** & **Docker Compose** - Conteneurisation
- **PostgreSQL** 15 - Base de données relationnelle
- **GitHub Actions** - CI/CD
- **Nginx** - Reverse proxy (production)

## 🚀 Installation

### Prérequis

- **Docker** 24.0+ et **Docker Compose** v2
- **Node.js** 18+ et **npm** (pour développement frontend)
- **Python** 3.12+ (pour développement backend)

### Installation rapide avec Docker

```bash
# Cloner le repository
git clone https://github.com/yourusername/ecofin-publication.git
cd ecofin-publication

# Copier et configurer les variables d'environnement
cp backend/env.example backend/.env
# Éditer backend/.env avec vos clés API

# Lancer tous les services
docker-compose up -d

# Créer l'utilisateur admin initial
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    email='admin@example.com',
    username='admin',
    hashed_password=get_password_hash('admin123'),
    is_admin=True
)
db.add(admin)
db.commit()
print('✅ Admin créé : admin@example.com / admin123')
"
```

L'application sera accessible sur :
- **Frontend** : http://localhost:3000
- **API** : http://localhost:8000
- **API Docs** : http://localhost:8000/docs

### Installation en développement

#### Backend

```bash
cd backend

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp env.example .env
# Éditer .env avec vos configurations

# Lancer la base de données et Redis
docker-compose up -d postgres redis

# Appliquer les migrations
alembic upgrade head

# Lancer le serveur de développement
uvicorn app.main:app --reload --port 8000

# Dans un autre terminal, lancer Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Dans un troisième terminal, lancer Celery Beat
celery -A app.workers.celery_app beat --loglevel=info
```

#### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm start
```

## ⚙️ Configuration

### Variables d'environnement principales

Voir `backend/env.example` pour la liste complète. Les plus importantes :

```env
# OpenAI (requis)
OPENAI_API_KEY=sk-votre_cle_openai

# Blotato (requis pour publication)
BLOTATO_API_KEY=blt_votre_cle_blotato
BLOTATO_LINKEDIN_ACCOUNT_ID=votre_id_linkedin
BLOTATO_X_ACCOUNT_ID=votre_id_x
BLOTATO_FACEBOOK_ACCOUNT_ID=votre_id_facebook

# SMTP (requis pour emails)
SMTP_HOST=votre_smtp_host
SMTP_USER=votre_smtp_user
SMTP_PASSWORD=votre_smtp_password

# JWT (à changer en production)
SECRET_KEY=votre_secret_key_tres_longue_et_aleatoire
```

### Configuration Blotato

1. **Créez un compte** sur [Blotato](https://blotato.com)
2. **Connectez vos réseaux sociaux** :
   - LinkedIn (compte personnel ou page entreprise)
   - X / Twitter
   - Facebook (pages uniquement, pas de profils personnels)
3. **Récupérez votre clé API** :
   - Allez dans Settings → API
   - Créez une clé API avec les permissions de publication
   - Copiez la clé (format: `blt_...`)
4. **Notez les IDs de vos comptes** :
   - Les IDs sont disponibles dans les paramètres de chaque réseau connecté
   - Ou utilisez l'API : `curl -H "blotato-api-key: YOUR_KEY" https://backend.blotato.com/v2/accounts`
5. **Configurez `backend/blotato_accounts.json`** avec vos comptes et pages :
   ```json
   {
     "facebook": {
       "account_id": "11315",
       "pages": [
         {"id": "722025697671791", "name": "Page 1"},
         {"id": "1982525425350969", "name": "Page 2"}
       ]
     },
     "linkedin": {
       "account_id": "7297",
       "pages": [{"id": "7297", "name": "Profil LinkedIn"}]
     },
     "x": {
       "account_id": "8067",
       "pages": [{"id": "8067", "name": "Compte X"}]
     }
   }
   ```

## 📖 Utilisation

### 1. Ajouter un flux RSS

```
Dashboard → Flux RSS → ➕ Ajouter un flux
```

**Étape 1 - Informations de base** :
- 📰 **Nom** : Nom d'affichage du flux
- 🔗 **URL RSS** : URL complète du flux (ex: https://example.com/feed.xml)
- ⏱️ **Fréquence** : Intervalle de collecte en minutes (ex: 120 = toutes les 2h)

**Étape 2 - Réseaux cibles** :
- Sélectionnez les réseaux où publier (LinkedIn, Facebook, X)

**Étape 3 - Pages de destination** :
- Pour chaque réseau sélectionné, choisissez la page/compte cible dans la liste
- Les pages sont chargées dynamiquement depuis votre configuration Blotato

**Étape 4 - Configuration avancée (optionnel)** :
- 💬 **Prompts personnalisés par réseau** : Instructions spécifiques pour l'IA
- Exemple : "Crée un post professionnel avec des emojis et 3 hashtags"

### 2. Valider les posts

```
Dashboard → Posts → Onglet "Brouillons"
```

**Workflow de validation** :
1. Les articles RSS collectés apparaissent automatiquement en brouillon
2. Le contenu est généré par l'IA pour chaque réseau configuré
3. Cliquez sur un post pour voir :
   - 📰 Titre et extrait de l'article source
   - 📝 Contenu généré pour chaque réseau
   - 🔗 Lien vers l'article original
   - 🌐 Réseaux et pages de destination

**Actions disponibles** :
- ✏️ **Éditer** : Modifier le contenu généré avant validation
- ✅ **Valider** : Ajouter à la file de publication (calcul automatique de l'heure)
- ❌ **Rejeter** : Marquer comme rejeté (n'apparaît plus dans les brouillons)

### 3. Gérer la file de publication

```
Dashboard → File d'attente → Onglet "File d'attente"
```

**Vue en temps réel** :
- 🔄 **Rafraîchissement automatique** : Toutes les 3 secondes
- ⏱️ **Compte à rebours dynamique** : Mise à jour chaque seconde
- 📊 **Statistiques** : 
  - 📅 Programmés (≤ 10 min)
  - ⏳ En attente (+ de 10 min)
  - ⏸️ En pause
  - 🔄 En cours de publication
  - ✅ Publiés
  - ❌ Échecs

**Actions disponibles** :
- ⏸️ **Pause** : Mettre en pause une publication (avec confirmation)
- ▶️ **Reprendre** : Reprendre une publication en pause
- ❌ **Annuler** : Annuler définitivement une publication
- ⏸️ **Pause tout** : Mettre en pause toute la file
- ▶️ **Reprendre tout** : Reprendre toutes les publications

**Filtres** :
- 🗂️ **Par flux** : Afficher uniquement un flux spécifique
- 🌐 **Par réseau** : Filtrer par plateforme sociale
- ⚡ **Par statut** : Pending, Paused, Publishing, Published, Failed

### 4. Post direct

```
File d'attente → 📤 Post direct
```

**Création manuelle de posts** (hors flux RSS) :

**Étape 1 - Sélection** :
- 🌐 **Réseau** : Choisissez Facebook, LinkedIn ou X
- 📄 **Page** : Sélectionnez la page de destination

**Étape 2 - Création du contenu** :

**Mode manuel** :
- Cochez ☐ Utiliser l'IA
- Écrivez directement votre contenu
- Publication tel quel

**Mode IA** (recommandé) :
- Cochez ☑ Utiliser l'IA
- 💬 **Prompt personnalisé** (optionnel) : "Crée un post engageant avec des emojis..."
- 📝 **Contenu source** : Texte brut à transformer
- Cliquez sur **✨ Générer le contenu avec l'IA**
- Éditez le résultat si nécessaire
- Publiez

**Avantages** :
- Rapide pour des annonces ponctuelles
- Contrôle total sur le contenu
- Génération IA optionnelle
- Respect de la file FIFO
- Espacement automatique selon la config globale

### 5. Configuration des réseaux sociaux

```
File d'attente → ⚙️ Configuration des réseaux
```

**Paramètres globaux par réseau** :
- ✅/❌ **Actif** : Activer/désactiver le réseau
- ⏱️ **Délai par défaut** : Espacement entre publications (minutes)
- 📊 **Max posts/jour** : Limite quotidienne de publications
- 🎯 **Heures optimales** : Heures préférées (ex: 9, 14, 18)

**Effet** :
- S'applique à tous les flux utilisant ce réseau
- Modifiable en temps réel sans redémarrage
- Respect du FIFO avec espacement configuré

### 6. Historique des publications

```
Dashboard → Historique
```

**Suivi complet** :
- 📅 Toutes les publications passées (réussies et échouées)
- 🔍 **Filtres** :
  - Par réseau social
  - Par flux RSS
  - Par statut (Published, Failed)
- 📊 Statistiques : Date, heure, réseau, statut
- 🔗 Lien vers l'article publié sur le réseau social
- 📤 Distinction posts RSS vs posts directs

### 7. Gestion des utilisateurs (Admin uniquement)

```
Page Utilisateurs (accès admin)
```

**Fonctionnalités admin** :
- ➕ **Créer** des utilisateurs avec email automatique de bienvenue
- ✏️ **Modifier** : Nom, email, mot de passe, statut admin
- 🗑️ **Supprimer** des utilisateurs (sauf soi-même)
- 📧 **Renvoyer email** de bienvenue avec nouveau mot de passe

**Pour tous** :
- 🔐 **Mot de passe oublié** : Reset par email avec token 1h
- 👤 **Mon profil** : Modifier ses propres informations

## 🚢 Déploiement

### CI/CD GitHub Actions

Deux workflows sont configurés :

1. **Preprod** : Se déclenche sur push vers `preprod`
2. **Production** : Se déclenche sur push vers `main`

#### Configuration GitHub Secrets

```
DOCKER_HUB_USERNAME       # Docker Hub username
DOCKER_HUB_PASSWORD       # Docker Hub password
VPS_IP_PREPROD           # IP serveur preprod
VPS_IP_PROD              # IP serveur production
VPS_USERNAME             # User SSH
SSH_PRIVATE_KEY          # Clé privée SSH
REACT_APP_API_URL_PREPROD    # URL API preprod
REACT_APP_API_URL_PROD       # URL API production
```

#### Déploiement automatique

```bash
# Déployer en preprod
git push origin preprod

# Déployer en production
git push origin main
```

### Guide complet

Consultez [DEPLOYMENT.md](./DEPLOYMENT.md) pour le guide complet de déploiement.

## 📚 API Documentation

L'API est documentée avec Swagger UI et ReDoc :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints principaux

#### Authentification
- `POST /auth/login` - Connexion
- `POST /auth/register` - Inscription

#### Flux RSS
- `GET /feeds/` - Lister les flux
- `POST /feeds/` - Créer un flux
- `PUT /feeds/{id}` - Modifier un flux
- `DELETE /feeds/{id}` - Supprimer un flux

#### Posts
- `GET /posts/drafts` - Posts brouillons
- `GET /posts/validated` - Posts validés
- `PUT /posts/{id}` - Modifier un post
- `POST /posts/{id}/validate` - Valider un post
- `POST /posts/{id}/reject` - Rejeter un post

#### File de publication
- `GET /publication-queue/` - Lister la file
- `POST /publication-queue/{id}/pause` - Mettre en pause
- `POST /publication-queue/{id}/resume` - Reprendre
- `POST /publication-queue/{id}/cancel` - Annuler

#### Post direct
- `POST /direct-post` - Créer un post direct

#### Utilisateurs
- `GET /users/` - Lister les utilisateurs (Admin)
- `POST /users/` - Créer un utilisateur (Admin)
- `PUT /users/{id}` - Modifier un utilisateur
- `DELETE /users/{id}` - Supprimer un utilisateur (Admin)
- `POST /users/forgot-password` - Mot de passe oublié
- `POST /users/reset-password` - Réinitialiser mot de passe

## 🧪 Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📝 Changelog

Voir [CHANGELOG.md](./CHANGELOG.md) pour l'historique des versions.

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez [CONTRIBUTING.md](./CONTRIBUTING.md).

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](./LICENSE) pour plus de détails.

## 👤 Auteur

**EcoFin Team**

## 🙏 Remerciements

- OpenAI pour l'API GPT
- Blotato pour l'API de publication multi-réseaux
- Toutes les bibliothèques open-source utilisées

---

<div align="center">
Fait avec ❤️ par l'équipe EcoFin
</div>
