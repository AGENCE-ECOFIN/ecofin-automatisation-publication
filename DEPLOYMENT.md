# 🚀 Guide de Déploiement - EcoFin Publication

Ce guide explique comment déployer l'application EcoFin Publication en environnement de production (preprod).

## 📋 Prérequis

### Sur votre machine locale
- Git
- Compte GitHub avec accès au repository
- Compte Docker Hub

### Sur le serveur VPS
- Ubuntu 20.04+ / Debian 11+
- Docker Engine 24.0+
- Docker Compose v2
- Accès SSH avec clé
- Ports ouverts: 80, 443 (si reverse proxy), ou ports personnalisés

## 🔧 Configuration Initiale

### 1. Configuration GitHub Secrets

Dans votre repository GitHub, allez dans **Settings → Secrets and variables → Actions** et ajoutez :

#### Docker Hub
- `DOCKER_HUB_USERNAME` : Votre nom d'utilisateur Docker Hub
- `DOCKER_HUB_PASSWORD` : Votre mot de passe ou token Docker Hub

#### VPS
- `VPS_IP_PREPROD` : L'IP de votre serveur preprod
- `VPS_USERNAME` : Nom d'utilisateur SSH (ex: `root` ou `ubuntu`)
- `SSH_PRIVATE_KEY` : Votre clé privée SSH complète

#### Application
- `REACT_APP_API_URL_PREPROD` : URL de votre API (ex: `https://api-preprod.ecofin.com`)

### 2. Préparation du VPS

Connectez-vous à votre VPS :

```bash
ssh user@your-vps-ip
```

#### Installation de Docker

```bash
# Mettre à jour les paquets
sudo apt-get update && sudo apt-get upgrade -y

# Installer les dépendances
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Ajouter la clé GPG Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Ajouter le repository Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installer Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Vérifier l'installation
sudo docker --version
sudo docker compose version

# Ajouter votre utilisateur au groupe docker (optionnel)
sudo usermod -aG docker $USER
newgrp docker
```

#### Créer le répertoire de déploiement

```bash
mkdir -p ~/ecofin-publication-preprod
cd ~/ecofin-publication-preprod
```

#### Créer le fichier `.env`

```bash
nano .env
```

Copiez le contenu de `.env.prod.example` et remplissez avec vos vraies valeurs :

```env
# Docker Hub
DOCKER_HUB_USERNAME=your_dockerhub_username

# Database
POSTGRES_USER=ecofin_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=ecofin_publication

# Redis
REDIS_PASSWORD=your_redis_password_here

# JWT
SECRET_KEY=your_very_long_random_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-your_openai_api_key

# Blotato
BLOTATO_API_KEY=blt_your_blotato_key
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
FRONTEND_URL=https://preprod.ecofin.com
BACKEND_DOMAIN=api-preprod.ecofin.com
FRONTEND_DOMAIN=preprod.ecofin.com
```

Sauvegarder et quitter (`Ctrl+X`, puis `Y`, puis `Enter`).

### 3. Configuration du firewall (optionnel)

```bash
# Permettre SSH
sudo ufw allow 22/tcp

# Permettre HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activer le firewall
sudo ufw enable
```

## 🚀 Déploiement

### Déploiement automatique via GitHub Actions

1. **Pousser vers la branche `preprod`** :

```bash
git checkout preprod
git merge main  # ou votre branche de développement
git push origin preprod
```

2. Le workflow GitHub Actions se déclenche automatiquement et :
   - ✅ Build les images Docker (backend et frontend)
   - ✅ Push les images sur Docker Hub
   - ✅ Se connecte au VPS
   - ✅ Pull les nouvelles images
   - ✅ Redémarre les conteneurs

3. **Suivre le déploiement** :
   - Allez dans l'onglet **Actions** de votre repository GitHub
   - Cliquez sur le workflow en cours d'exécution
   - Suivez les logs en temps réel

### Déploiement manuel (si nécessaire)

Sur le VPS :

```bash
cd ~/ecofin-publication-preprod

# Pull les dernières images
docker compose pull

# Arrêter les conteneurs actuels
docker compose down

# Démarrer les nouveaux conteneurs
docker compose up -d

# Vérifier le statut
docker compose ps

# Voir les logs
docker compose logs -f
```

## 🔍 Vérification du Déploiement

### 1. Vérifier les conteneurs

```bash
docker compose ps
```

Vous devriez voir :
- ✅ `ecofin-postgres-preprod` (healthy)
- ✅ `ecofin-redis-preprod` (healthy)
- ✅ `ecofin-backend-preprod` (healthy)
- ✅ `ecofin-celery-worker-preprod` (up)
- ✅ `ecofin-celery-beat-preprod` (up)
- ✅ `ecofin-frontend-preprod` (healthy)

### 2. Tester l'API

```bash
curl http://localhost:8000/health
# Devrait retourner: {"status":"healthy"}
```

### 3. Vérifier les logs

```bash
# Tous les services
docker compose logs -f

# Backend uniquement
docker compose logs -f backend

# Celery worker
docker compose logs -f celery-worker

# Frontend
docker compose logs -f frontend
```

### 4. Accéder à l'application

- **Frontend** : `https://preprod.ecofin.com` (ou votre domaine)
- **API** : `https://api-preprod.ecofin.com/docs` (Swagger UI)
- **Health Check** : `https://api-preprod.ecofin.com/health`

## 🛠️ Commandes Utiles

### Gestion des conteneurs

```bash
# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Redémarrer
docker compose restart

# Redémarrer un service spécifique
docker compose restart backend

# Voir les logs en temps réel
docker compose logs -f

# Voir les stats de ressources
docker stats
```

### Maintenance

```bash
# Nettoyer les images inutilisées
docker image prune -af

# Nettoyer tous les volumes non utilisés
docker volume prune -f

# Nettoyer tout le système Docker
docker system prune -af --volumes
```

### Base de données

```bash
# Accéder à PostgreSQL
docker compose exec postgres psql -U ecofin_user -d ecofin_publication

# Backup de la base de données
docker compose exec postgres pg_dump -U ecofin_user ecofin_publication > backup.sql

# Restaurer depuis un backup
docker compose exec -T postgres psql -U ecofin_user ecofin_publication < backup.sql
```

### Migrations de base de données

```bash
# Accéder au conteneur backend
docker compose exec backend bash

# Créer une nouvelle migration
alembic revision --autogenerate -m "Description de la migration"

# Appliquer les migrations
alembic upgrade head

# Revenir à une migration précédente
alembic downgrade -1
```

## 🔐 Sécurité

### Recommandations

1. **Changez tous les mots de passe par défaut**
   - PostgreSQL
   - Redis
   - SECRET_KEY (JWT)

2. **Utilisez HTTPS en production**
   - Configurez un reverse proxy (Traefik, Nginx, Caddy)
   - Obtenez des certificats SSL (Let's Encrypt)

3. **Limitez l'accès SSH**
   - Utilisez uniquement des clés SSH
   - Désactivez l'authentification par mot de passe
   - Changez le port SSH par défaut

4. **Configurez un pare-feu**
   - N'ouvrez que les ports nécessaires
   - Utilisez `ufw` ou `iptables`

5. **Mettez en place des sauvegardes automatiques**
   - Base de données
   - Volumes Docker
   - Configuration

## 🚨 Dépannage

### Les conteneurs ne démarrent pas

```bash
# Vérifier les logs
docker compose logs

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -m
```

### Problèmes de connexion à la base de données

```bash
# Vérifier que PostgreSQL est accessible
docker compose exec postgres pg_isready -U ecofin_user

# Vérifier les variables d'environnement
docker compose exec backend env | grep DATABASE
```

### Celery ne traite pas les tâches

```bash
# Vérifier les workers Celery
docker compose logs celery-worker

# Vérifier Redis
docker compose exec redis redis-cli ping
```

### L'application ne répond pas

```bash
# Vérifier le statut des conteneurs
docker compose ps

# Redémarrer tous les services
docker compose restart

# Si nécessaire, recréer les conteneurs
docker compose down && docker compose up -d
```

## 📞 Support

Pour toute question ou problème :
- Consultez les logs : `docker compose logs -f`
- Vérifiez la documentation de l'API : `/docs`
- Contactez l'équipe de développement

## 📝 Notes

- **Backup réguliers** : Configurez des sauvegardes automatiques quotidiennes
- **Monitoring** : Envisagez d'installer un outil de monitoring (Prometheus, Grafana)
- **Logs centralisés** : Utilisez une solution de gestion des logs (ELK Stack, Loki)
- **Alertes** : Configurez des alertes pour les erreurs critiques

---

🎉 **Félicitations !** Votre application EcoFin Publication est maintenant déployée !

