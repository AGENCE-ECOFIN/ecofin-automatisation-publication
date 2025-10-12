# 📝 Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2025-10-12

### 🎉 Version initiale - Production Ready

#### ✨ Ajouté
- **Collecte automatique RSS** avec fréquence configurable
- **Génération IA de posts** avec OpenAI GPT pour chaque réseau social
- **Publication multi-réseaux** via Blotato API (LinkedIn, Facebook, X)
- **File d'attente FIFO intelligente** avec espacement dynamique
- **Dashboard temps réel** avec statistiques et monitoring
- **Gestion des utilisateurs** avec authentification JWT
- **Emails automatiques** (bienvenue, réinitialisation mot de passe)
- **Post direct** avec génération IA optionnelle
- **Historique complet** avec filtres avancés
- **Configuration dynamique** sans redémarrage requis
- **CI/CD GitHub Actions** pour preprod et production
- **Docker** avec images optimisées multi-stage
- **Documentation complète** (README, DEPLOYMENT, API docs)

#### 🔧 Backend
- FastAPI 0.104.1 avec Gunicorn
- PostgreSQL 15 avec SQLAlchemy 2.0.23
- Celery 5.3.4 + Beat pour tâches asynchrones
- Redis 5.0.1 pour cache et broker
- OpenAI 1.3.8 pour génération de contenu
- Blotato API pour publication centralisée
- SMTP intégré pour envoi d'emails
- Alembic pour migrations de base de données

#### 🎨 Frontend
- React 18 avec Hooks
- React Query pour gestion d'état
- Tailwind CSS pour styling moderne
- Nginx pour production
- Compte à rebours temps réel (1s)
- Rafraîchissement automatique (3s)

#### 🔐 Sécurité
- Authentification JWT
- Hachage bcrypt des mots de passe
- Reset password avec token 1h
- Permissions basées sur les rôles (Admin/User)
- Variables d'environnement sécurisées

#### 📊 Fonctionnalités clés
- **Workflow complet** : RSS → Brouillon → Validation → File → Publication
- **FIFO par feed et réseau** : Publications séquentielles avec espacement
- **Pause/Reprise** : Globale ou individuelle
- **Retry automatique** : En cas d'échec de publication
- **Configuration réseau** : Délais, max posts/jour, heures optimales
- **Prompts personnalisés** : Par flux et par réseau
- **Pages de destination dynamiques** : Sélection depuis configuration Blotato
- **Distinction posts** : RSS vs Direct

#### 🚀 Déploiement
- Docker Compose pour dev et production
- GitHub Actions CI/CD avec 2 workflows
- Dockerfiles multi-stage optimisés
- Nginx reverse proxy configuré
- Health checks automatiques
- Backup base de données intégré
- Documentation déploiement complète

#### 📝 Documentation
- README complet avec instructions détaillées
- Guide de déploiement étape par étape
- Documentation API Swagger/ReDoc
- .editorconfig pour cohérence du code
- .gitignore et .dockerignore optimisés
- Licence MIT

#### 🧹 Nettoyage
- Suppression de 17 fichiers de documentation obsolètes
- Suppression de 5 scripts shell non utilisés
- Nettoyage des caches Python
- Optimisation de la structure du projet
- Ajout des fichiers de configuration standards

---

## Format des changements

- **Ajouté** : Nouvelles fonctionnalités
- **Modifié** : Modifications de fonctionnalités existantes
- **Déprécié** : Fonctionnalités bientôt supprimées
- **Supprimé** : Fonctionnalités supprimées
- **Corrigé** : Corrections de bugs
- **Sécurité** : Corrections de vulnérabilités

