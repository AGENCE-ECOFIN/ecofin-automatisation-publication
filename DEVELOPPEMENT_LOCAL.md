# 🛠️ Guide de Développement Local

## 🚀 Démarrage Rapide

### 1️⃣ Prérequis

```bash
# Vérifier les installations
python3 --version  # Python 3.12+
node --version     # Node 18+
docker --version   # Docker 24+
```

### 2️⃣ Installation Complète

```bash
# Cloner et accéder au projet
cd /Users/thierryhema/Documents/perso/ecofin/publication

# Lancer le script d'installation automatique
./start_dev.sh
```

Le script va :
- ✅ Créer le fichier `.env` si nécessaire
- ✅ Démarrer PostgreSQL et Redis avec Docker
- ✅ Créer l'environnement virtuel Python
- ✅ Installer toutes les dépendances backend
- ✅ Appliquer les migrations de base de données
- ✅ Installer les dépendances frontend

### 3️⃣ Configuration

Si c'est la première fois, configurez `backend/.env` :

```bash
# Éditer le fichier
nano backend/.env
```

**Minimum requis pour démarrer** :

```env
# Database (déjà configuré par Docker)
DATABASE_URL=postgresql://user:password@localhost:5432/ecofin_pub

# Redis (déjà configuré par Docker)
REDIS_URL=redis://localhost:6379/0

# JWT (générer une clé aléatoire)
SECRET_KEY=votre-secret-key-tres-longue-et-aleatoire-minimum-32-caracteres

# OpenAI (pour la génération de contenu)
OPENAI_API_KEY=sk-your-openai-api-key

# Blotato (pour la publication)
BLOTATO_API_KEY=blt_your-blotato-api-key

# SMTP (pour les emails) - Optionnel
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
SMTP_FROM_EMAIL=votre.email@gmail.com
SMTP_FROM_NAME=EcoFin Publication

# Application
APP_NAME=EcoFin Publication
FRONTEND_URL=http://localhost:3000
```

---

## 🎯 Démarrage Manuel (4 Terminaux)

### Terminal 1 : Backend API

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**URL** : http://localhost:8000  
**Docs** : http://localhost:8000/docs

### Terminal 2 : Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

**Rôle** : Traite les tâches asynchrones (collecte RSS, génération IA, publication)

### Terminal 3 : Celery Beat

```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app beat --loglevel=info
```

**Rôle** : Planificateur de tâches périodiques

### Terminal 4 : Frontend React

```bash
cd frontend
npm start
```

**URL** : http://localhost:3000

---

## 🐛 Résolution des Problèmes Courants

### ❌ Erreur : `email-validator is not installed`

```bash
cd backend
source venv/bin/activate
pip install email-validator pydantic[email]
```

### ❌ Erreur : `Permission denied` pour les logs

```bash
# Créer le dossier logs avec les bonnes permissions
mkdir -p backend/logs
chmod 755 backend/logs
```

### ❌ Erreur : PostgreSQL connection refused

```bash
# Vérifier que Docker tourne
docker ps

# Redémarrer PostgreSQL
docker-compose restart db

# Vérifier les logs
docker logs ecofin_db_local
```

### ❌ Erreur : Redis connection refused

```bash
# Redémarrer Redis
docker-compose restart redis

# Tester la connexion
docker exec -it ecofin_redis_local redis-cli ping
# Doit retourner: PONG
```

### ❌ Module Python introuvable

```bash
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### ❌ Erreur de migration Alembic

```bash
cd backend
source venv/bin/activate

# Voir l'état des migrations
alembic current

# Réinitialiser complètement
alembic downgrade base
alembic upgrade head

# Ou créer une nouvelle migration
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### ❌ Frontend : Module introuvable

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

---

## 🗄️ Gestion de la Base de Données

### Accéder à PostgreSQL

```bash
# Via Docker
docker exec -it ecofin_db_local psql -U user -d ecofin_pub

# Commandes utiles :
\dt              # Liste des tables
\d+ table_name   # Structure d'une table
SELECT * FROM users;
\q               # Quitter
```

### Réinitialiser la base de données

```bash
# Arrêter tous les services
docker-compose down -v

# Redémarrer (supprime toutes les données)
docker-compose up -d

# Réappliquer les migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

### Backup de la base de données

```bash
# Créer un backup
docker exec ecofin_db_local pg_dump -U user ecofin_pub > backup_$(date +%Y%m%d).sql

# Restaurer un backup
cat backup_20251012.sql | docker exec -i ecofin_db_local psql -U user ecofin_pub
```

---

## 🔧 Commandes Utiles

### Docker

```bash
# Voir les conteneurs actifs
docker ps

# Logs d'un conteneur
docker logs -f ecofin_db_local
docker logs -f ecofin_redis_local

# Redémarrer un service
docker-compose restart db
docker-compose restart redis

# Arrêter tout
docker-compose down

# Arrêter et supprimer les volumes (⚠️ supprime les données)
docker-compose down -v
```

### Backend Python

```bash
cd backend
source venv/bin/activate

# Lancer l'API
uvicorn app.main:app --reload

# Tests (quand disponibles)
pytest

# Formatter le code
black app/
isort app/

# Créer un nouvel utilisateur admin
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
user = User(
    email='admin@ecofin.com',
    full_name='Admin',
    hashed_password=get_password_hash('admin123'),
    is_admin=True
)
db.add(user)
db.commit()
print('✅ Admin créé : admin@ecofin.com / admin123')
"
```

### Frontend React

```bash
cd frontend

# Démarrer
npm start

# Build de production
npm run build

# Analyser le bundle
npm run build && npx source-map-explorer 'build/static/js/*.js'
```

---

## 📊 Monitoring en Développement

### Celery Flower (Interface de monitoring)

```bash
cd backend
source venv/bin/activate
pip install flower
celery -A app.workers.celery_app flower --port=5555
```

**URL** : http://localhost:5555

### Logs en temps réel

```bash
# Backend
tail -f backend/logs/*.log

# Docker
docker-compose logs -f

# Celery Worker
# Les logs s'affichent directement dans le terminal
```

---

## 🎨 Structure des Fichiers de Dev

```
📁 ecofin-publication/
├── 📄 .env                        # ❌ Ne pas commiter !
├── 📄 docker-compose.yml          # PostgreSQL + Redis
├── 📄 start_dev.sh               # Script de démarrage rapide
├── 📄 stop_dev.sh                # Script d'arrêt
│
├── 📁 backend/
│   ├── 📄 .env                    # Configuration locale
│   ├── 📁 venv/                   # Environnement virtuel Python
│   ├── 📁 logs/                   # Logs de l'application
│   ├── 📁 app/                    # Code source
│   └── 📄 requirements.txt
│
└── 📁 frontend/
    ├── 📁 node_modules/           # Dépendances npm
    ├── 📁 src/                    # Code source React
    └── 📄 package.json
```

---

## 🚦 Workflow de Développement

### 1. Démarrer la journée

```bash
# Terminal 1
./start_dev.sh  # Configure tout automatiquement

# Terminal 2 (Backend)
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3 (Celery)
cd backend && source venv/bin/activate
celery -A app.workers.celery_app worker -l info &
celery -A app.workers.celery_app beat -l info

# Terminal 4 (Frontend)
cd frontend && npm start
```

### 2. Développer

- Backend : Modifiez les fichiers dans `backend/app/`, l'API redémarre automatiquement
- Frontend : Modifiez les fichiers dans `frontend/src/`, le navigateur se recharge automatiquement

### 3. Tester

```bash
# Accéder à l'application
open http://localhost:3000

# Tester l'API
open http://localhost:8000/docs

# Connexion par défaut (créer un admin d'abord)
# Email: admin@ecofin.com
# Password: admin123
```

### 4. Arrêter proprement

```bash
# Dans chaque terminal : Ctrl+C

# Arrêter Docker
./stop_dev.sh
```

---

## 🔄 Synchroniser avec la Production

### Récupérer les dernières modifications

```bash
git pull origin main
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

### Créer une nouvelle migration après modification des modèles

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Description du changement"
alembic upgrade head
```

---

## 📞 Aide

- 📖 **Documentation principale** : `README.md`
- 🚀 **Déploiement** : `DEPLOYMENT.md`
- 📝 **Changelog** : `CHANGELOG.md`
- 🌐 **API Docs** : http://localhost:8000/docs

---

## ✅ Checklist de Démarrage

- [ ] Docker installé et démarré
- [ ] Python 3.12+ installé
- [ ] Node 18+ installé
- [ ] `./start_dev.sh` exécuté avec succès
- [ ] `backend/.env` configuré avec les clés API
- [ ] PostgreSQL accessible (port 5432)
- [ ] Redis accessible (port 6379)
- [ ] Backend API tourne (port 8000)
- [ ] Celery Worker tourne
- [ ] Celery Beat tourne
- [ ] Frontend tourne (port 3000)
- [ ] Connexion réussie à l'application

---

<div align="center">

**🎉 Bon développement ! 🚀**

</div>

