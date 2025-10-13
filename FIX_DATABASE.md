# 🔧 Correction Problème Base de Données

## ❌ Erreur Observée
```
FATAL:  database "ecofin_user" does not exist
```

PostgreSQL cherche la base **`ecofin_user`** au lieu de **`ecofin_publication`**.

---

## 🎯 Solution Rapide

### Sur le serveur VPS :

```bash
# 1. Arrêter les services
cd ~/ecofin-publication-preprod  # ou votre répertoire
docker-compose -f docker-compose.prod.yml down

# 2. Éditer le fichier .env
nano .env
```

### Vérifier ces lignes dans `.env` :

```bash
# ✅ Correct
POSTGRES_USER=ecofin_user
POSTGRES_PASSWORD=votre_mot_de_passe_securise
POSTGRES_DB=ecofin_publication    # ⚠️ IMPORTANT : doit être "ecofin_publication"

# Dans DATABASE_URL, vérifier que ça correspond
DATABASE_URL=postgresql://ecofin_user:votre_mot_de_passe@postgres:5432/ecofin_publication
```

**❌ Erreur commune** :
```bash
POSTGRES_DB=ecofin_user    # ❌ FAUX - c'est le nom de la DB, pas de l'user
```

### 3. Nettoyer et redémarrer

```bash
# Supprimer les volumes (⚠️ supprime les données)
docker-compose -f docker-compose.prod.yml down -v

# Redémarrer proprement
docker-compose -f docker-compose.prod.yml up -d

# Vérifier les logs
docker logs ecofin-postgres-preprod
docker logs ecofin-backend-preprod
```

---

## 🔍 Vérification Détaillée

### 1. Vérifier les variables d'environnement dans le conteneur backend

```bash
docker exec ecofin-backend-preprod env | grep DATABASE
```

**Attendu** :
```
DATABASE_URL=postgresql://ecofin_user:mot_de_passe@postgres:5432/ecofin_publication
```

**Si vous voyez** :
```
DATABASE_URL=postgresql://ecofin_user:mot_de_passe@postgres:5432/ecofin_user
```
❌ **C'est ça le problème !**

### 2. Vérifier PostgreSQL

```bash
# Se connecter au conteneur PostgreSQL
docker exec -it ecofin-postgres-preprod psql -U ecofin_user

# Lister les bases de données
\l

# Vous devriez voir :
# ecofin_publication  | ecofin_user | UTF8 | ...
```

### 3. Si la base n'existe pas, la créer

```bash
# Depuis le conteneur PostgreSQL
docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d postgres

# Créer la base
CREATE DATABASE ecofin_publication OWNER ecofin_user;

# Vérifier
\l

# Quitter
\q
```

---

## 🚀 Commandes Complètes de Correction

```bash
# Sur le serveur VPS
cd ~/ecofin-publication-preprod

# 1. Arrêter tout
docker-compose -f docker-compose.prod.yml down

# 2. Supprimer les volumes (⚠️ efface les données)
docker volume rm ecofin-publication-preprod_postgres_data

# 3. Vérifier le .env
cat .env | grep POSTGRES

# Doit afficher :
# POSTGRES_USER=ecofin_user
# POSTGRES_PASSWORD=...
# POSTGRES_DB=ecofin_publication

# 4. Si incorrect, corriger
nano .env

# 5. Redémarrer
docker-compose -f docker-compose.prod.yml up -d

# 6. Vérifier les logs
docker logs ecofin-postgres-preprod -f

# 7. Attendre que PostgreSQL soit prêt (environ 10 secondes)
# Puis vérifier le backend
docker logs ecofin-backend-preprod -f

# 8. Créer l'utilisateur admin
docker exec -it ecofin-backend-preprod python create_admin.py
```

---

## 📝 Template .env Correct

Copiez ce template dans votre `.env` sur le serveur :

```bash
# Database (PostgreSQL)
POSTGRES_USER=ecofin_user
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
POSTGRES_DB=ecofin_publication

# Redis
REDIS_PASSWORD=VotreMotDePasseRedisSecurise456!

# JWT Security
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire-32-caracteres-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI API
OPENAI_API_KEY=sk-votre-cle-openai

# Blotato API
BLOTATO_API_KEY=blt_votre-cle-blotato
BLOTATO_LINKEDIN_ACCOUNT_ID=7297
BLOTATO_X_ACCOUNT_ID=8067
BLOTATO_FACEBOOK_ACCOUNT_ID=11315

# SMTP
SMTP_HOST=sequencemedia.smtp.com
SMTP_PORT=587
SMTP_USER=n8n_mediamania
SMTP_PASSWORD=W44MptRw9ww63C
SMTP_FROM_EMAIL=n8n_mediamania@sequencemedia.smtp.com
SMTP_FROM_NAME=EcoFin Publication

# Application
APP_NAME=EcoFin Publication
FRONTEND_URL=https://votre-domaine.com

# Docker Hub
DOCKER_HUB_USERNAME=noname1705
```

---

## ✅ Vérification Finale

```bash
# 1. Tous les conteneurs sont en cours d'exécution
docker ps

# 2. Backend accessible
curl http://localhost:8000/health
# Doit retourner : {"status":"healthy"}

# 3. Frontend accessible
curl http://localhost/
# Doit retourner du HTML

# 4. Base de données accessible
docker exec ecofin-postgres-preprod pg_isready -U ecofin_user -d ecofin_publication
# Doit retourner : accepting connections

# 5. Vérifier les migrations
docker exec ecofin-backend-preprod alembic current
# Doit afficher la dernière révision
```

---

## 🆘 Si le Problème Persiste

### Dernière solution : Recréer complètement

```bash
# ⚠️ Attention : supprime TOUTES les données

# 1. Tout arrêter et supprimer
cd ~/ecofin-publication-preprod
docker-compose -f docker-compose.prod.yml down -v
docker volume prune -f

# 2. Supprimer les images (optionnel)
docker-compose -f docker-compose.prod.yml pull

# 3. Vérifier .env (IMPORTANT)
cat .env | grep POSTGRES_DB
# DOIT afficher : POSTGRES_DB=ecofin_publication

# 4. Redémarrer de zéro
docker-compose -f docker-compose.prod.yml up -d

# 5. Suivre les logs
docker-compose -f docker-compose.prod.yml logs -f

# 6. Une fois démarré (attendre ~30 secondes)
docker exec -it ecofin-backend-preprod alembic upgrade head
docker exec -it ecofin-backend-preprod python create_admin.py
```

---

## 📊 Résumé des Noms

| Variable | Valeur | Description |
|----------|--------|-------------|
| **POSTGRES_USER** | `ecofin_user` | Nom de l'utilisateur PostgreSQL |
| **POSTGRES_DB** | `ecofin_publication` | Nom de la base de données ⚠️ |
| **Container** | `ecofin-postgres-preprod` | Nom du conteneur |

**⚠️ Ne pas confondre USER et DB !**

---

<div align="center">

**💡 Astuce** : Toujours vérifier le fichier `.env` en premier !

</div>

