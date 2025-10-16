#!/bin/bash
# Script pour corriger les permissions sur le serveur
echo '🔧 Correction des permissions des dossiers...'

# Arrêter les conteneurs
docker-compose -f docker-compose.prod.yml down

# Supprimer les dossiers problématiques créés par root
sudo rm -rf uploads logs

# Créer les dossiers avec les bonnes permissions
mkdir -p uploads/images logs

# Redémarrer les conteneurs
docker-compose -f docker-compose.prod.yml up --build -d

echo '✅ Permissions corrigées et application redémarrée!'
