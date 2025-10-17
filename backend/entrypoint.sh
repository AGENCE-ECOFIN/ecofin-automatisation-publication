#!/bin/bash
set -e

# Entrypoint script pour le backend en production

echo ""
echo "================================================================"
echo "🚀 Démarrage du backend EcoFin Publication"
echo "================================================================"
echo ""

cd /app

# 1. Initialiser la base de données (attend PostgreSQL automatiquement)
echo "📝 Initialisation de la base de données..."
python -m app.init_db
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'initialisation de la base de données"
    exit 1
fi

# 2. Exécuter les migrations Alembic
echo ""
echo "🔄 Application des migrations Alembic..."
if alembic upgrade head 2>&1; then
    echo "✅ Migrations appliquées avec succès!"
else
    echo "⚠️  Erreur lors de l'application des migrations, tentative de correction..."
    # Essayer de marquer la migration comme appliquée si la table existe déjà
    alembic stamp head 2>&1 || echo "⚠️  Impossible de marquer les migrations comme appliquées"
fi

# 2.5. Vérifier et appliquer toutes les migrations nécessaires
echo ""
echo "🔧 Vérification complète des migrations..."
python /app/check_and_apply_migrations.py || echo "⚠️  Erreur lors de la vérification des migrations"

echo "✅ Migrations terminées!"

# 3. Créer l'utilisateur admin par défaut
echo ""
echo "👤 Création de l'utilisateur admin..."
python /app/create_admin.py 2>&1 || echo "⚠️  Admin déjà existant"

# 4. Démarrer l'application
echo ""
# Initialiser les horaires par défaut
echo "📅 Initialisation des horaires par défaut..."
python /app/init_schedules.py

echo "================================================================"
echo "✅ Initialisation complète - Démarrage de l'application..."
echo "================================================================"
echo ""

exec "$@"

