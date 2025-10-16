#!/bin/bash

# 🔧 Script de correction pour le serveur 185.143.103.162

echo "🔧 Correction des problèmes sur le serveur de production..."
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVER_IP="185.143.103.162"
API_URL="http://${SERVER_IP}:8000"

echo -e "${BLUE}📡 Serveur: ${SERVER_IP}${NC}"
echo ""

# 1. Tester la connexion à l'API
echo -e "${YELLOW}1️⃣ Test de connexion à l'API...${NC}"
response=$(curl -s "${API_URL}/")
if [ -n "$response" ]; then
    echo -e "${GREEN}✅ API accessible${NC}"
    echo "   Response: $response"
else
    echo -e "${RED}❌ API non accessible${NC}"
    exit 1
fi
echo ""

# 2. Copier le script de correction sur le serveur
echo -e "${YELLOW}2️⃣ Copie du script de correction sur le serveur...${NC}"
echo "Exécutez cette commande manuellement :"
echo ""
echo -e "${BLUE}scp backend/fix_production_issues.py user@${SERVER_IP}:/tmp/${NC}"
echo ""

# 3. Instructions pour exécuter sur le serveur
echo -e "${YELLOW}3️⃣ Connexion au serveur et exécution...${NC}"
echo ""
echo "Exécutez ces commandes sur le serveur :"
echo ""
echo -e "${BLUE}# Se connecter au serveur"
echo "ssh user@${SERVER_IP}"
echo ""
echo "# Copier le script dans le conteneur"
echo "docker cp /tmp/fix_production_issues.py ecofin-backend-preprod:/app/fix.py"
echo ""
echo "# Exécuter le script"
echo "docker exec -it ecofin-backend-preprod python /app/fix.py"
echo ""
echo "# Redémarrer le backend"
echo "docker restart ecofin-backend-preprod${NC}"
echo ""

# 4. Alternative : Commandes SQL directes
echo -e "${YELLOW}4️⃣ Alternative : Commandes SQL directes${NC}"
echo ""
echo "Si le script Python ne fonctionne pas, exécutez ces commandes SQL :"
echo ""
echo -e "${BLUE}docker exec -it ecofin-postgres-preprod psql -U ecofin_user -d ecofin_publication << 'SQL'

-- Vérifier les réseaux
SELECT COUNT(*) as nb_reseaux FROM network_configs;

-- Créer les réseaux si absents
INSERT INTO network_configs (network, is_active, default_publication_delay, max_posts_per_day)
SELECT 'facebook', true, 4, 10
WHERE NOT EXISTS (SELECT 1 FROM network_configs WHERE network = 'facebook');

INSERT INTO network_configs (network, is_active, default_publication_delay, max_posts_per_day)
SELECT 'linkedin', true, 5, 8
WHERE NOT EXISTS (SELECT 1 FROM network_configs WHERE network = 'linkedin');

INSERT INTO network_configs (network, is_active, default_publication_delay, max_posts_per_day)
SELECT 'x', true, 3, 15
WHERE NOT EXISTS (SELECT 1 FROM network_configs WHERE network = 'x');

-- Vérifier les posts validés
SELECT id, title, status FROM posts WHERE status = 'validated';

-- Vérifier la file de publication
SELECT COUNT(*) as nb_queue FROM publication_queue;

SQL${NC}"
echo ""

# 5. Tests finaux
echo -e "${YELLOW}5️⃣ Tests après correction (à exécuter après les étapes ci-dessus)${NC}"
echo ""
echo "# Tester l'endpoint des réseaux"
echo -e "${BLUE}curl -X GET ${API_URL}/networks/ | jq${NC}"
echo ""
echo "# Tester la file de publication"
echo -e "${BLUE}curl -X GET ${API_URL}/publication-queue/ | jq${NC}"
echo ""
echo "# Tester les posts validés"
echo -e "${BLUE}curl -X GET ${API_URL}/posts/validated | jq${NC}"
echo ""

echo -e "${GREEN}✅ Instructions générées !${NC}"
echo ""
echo -e "${YELLOW}💡 Note: Vous devrez vous connecter au serveur pour exécuter ces commandes${NC}"

