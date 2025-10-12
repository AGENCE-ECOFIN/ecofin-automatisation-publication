#!/bin/bash

# Entrypoint script pour le backend en production

echo "🚀 Démarrage du backend EcoFin Publication..."

# Attendre que PostgreSQL soit prêt (attente simple)
echo "⏳ Attente de PostgreSQL (15 secondes)..."
sleep 15
echo "✅ PostgreSQL devrait être prêt!"

# Exécuter les migrations Alembic
echo "🔄 Application des migrations..."
cd /app
alembic upgrade head 2>&1 || echo "⚠️  Migrations déjà appliquées ou erreur"
echo "✅ Migrations terminées!"

# Initialiser la base de données (créer l'admin)
echo "📝 Tentative de création de l'admin..."
python /app/create_admin.py 2>&1 || echo "⚠️  Admin déjà existant ou erreur"
echo "✅ Initialisation terminée!"

# Démarrer l'application
echo "🚀 Lancement de l'application..."
exec "$@"

