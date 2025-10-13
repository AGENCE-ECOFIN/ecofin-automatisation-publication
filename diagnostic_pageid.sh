#!/bin/bash

# 🔍 Diagnostic complet du problème pageId

echo "================================================================"
echo "🔍 DIAGNOSTIC COMPLET - Problème PageId"
echo "================================================================"
echo ""

SERVER="185.143.103.162"

echo "📡 Serveur: $SERVER"
echo ""

# Fonction pour exécuter sur le serveur
exec_remote() {
    echo "💡 Exécutez cette commande sur le serveur:"
    echo ""
    echo "ssh user@$SERVER << 'REMOTE'"
    echo "$1"
    echo "REMOTE"
    echo ""
}

# 1. Vérifier les feeds dans la DB
echo "1️⃣ VÉRIFIER LES FEEDS DANS LA BASE DE DONNÉES"
echo "-----------------------------------------------------------"
exec_remote "
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication << 'SQL'

-- Liste complète des feeds avec leurs configurations
SELECT 
    id,
    name,
    target_networks,
    social_pages,
    network_prompts
FROM feeds
ORDER BY id;

SQL
"

# 2. Vérifier la file de publication
echo "2️⃣ VÉRIFIER LA FILE DE PUBLICATION"
echo "-----------------------------------------------------------"
exec_remote "
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication << 'SQL'

-- Liste de la file avec le pageId
SELECT 
    pq.id,
    pq.post_id,
    p.title,
    f.name as feed_name,
    pq.network,
    pq.target_page_id,
    pq.status,
    pq.error_message
FROM publication_queue pq
LEFT JOIN posts p ON pq.post_id = p.id
LEFT JOIN feeds f ON pq.feed_id = f.id
ORDER BY pq.id DESC
LIMIT 10;

SQL
"

# 3. Vérifier les posts validés
echo "3️⃣ VÉRIFIER LES POSTS VALIDÉS"
echo "-----------------------------------------------------------"
exec_remote "
docker exec ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication << 'SQL'

-- Posts validés avec leur feed
SELECT 
    p.id,
    p.title,
    p.status,
    p.feed_id,
    f.name as feed_name,
    f.social_pages as feed_social_pages
FROM posts p
LEFT JOIN feeds f ON p.feed_id = f.id
WHERE p.status = 'validated'
ORDER BY p.id DESC;

SQL
"

# 4. Tester l'API
echo "4️⃣ TESTER L'API"
echo "-----------------------------------------------------------"
exec_remote "
# Test endpoint feeds
curl -s http://localhost:8000/feeds/ | jq '.[] | {id, name, social_pages}'

# Test endpoint publication queue
curl -s http://localhost:8000/publication-queue/ | jq '.[] | {id, network, target_page_id, status}' | head -20
"

# 5. Vérifier les logs backend
echo "5️⃣ VÉRIFIER LES LOGS BACKEND"
echo "-----------------------------------------------------------"
exec_remote "
# Logs récents du backend
docker logs ecofin-backend-preprod --tail=100 | grep -i 'social_pages\|target_page_id\|pageId'

# Ou tous les logs
docker logs ecofin-backend-preprod --tail=200
"

echo ""
echo "================================================================"
echo "✅ Commandes de diagnostic générées!"
echo "================================================================"
echo ""
echo "💡 Copiez-collez les commandes une par une sur le serveur"
echo ""

