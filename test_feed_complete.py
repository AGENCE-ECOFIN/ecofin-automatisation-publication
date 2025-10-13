#!/usr/bin/env python3
"""
Script de test complet pour vérifier les feeds et social_pages
"""
import requests
import json
import sys

API_URL = "http://localhost:8000"

def login():
    """Se connecter et obtenir un token"""
    print("🔐 Connexion...")
    response = requests.post(
        f"{API_URL}/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        print(f"✅ Connecté avec succès!")
        return token
    else:
        print(f"❌ Erreur de connexion: {response.text}")
        sys.exit(1)

def test_feeds(token):
    """Tester les feeds"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "="*60)
    print("1️⃣ RÉCUPÉRATION DES FEEDS")
    print("="*60)
    
    response = requests.get(f"{API_URL}/feeds/", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Erreur: {response.text}")
        return None
    
    feeds = response.json()
    print(f"✅ {len(feeds)} feeds trouvés\n")
    
    for feed in feeds:
        print(f"📰 Feed #{feed['id']}: {feed['name']}")
        print(f"   URL: {feed['url']}")
        print(f"   Réseaux cibles: {feed.get('target_networks', [])}")
        print(f"   Pages sociales: {feed.get('social_pages', {})}")
        print(f"   Prompts réseau: {feed.get('network_prompts', {})}")
        
        # Vérifier si des pages manquent
        target_networks = feed.get('target_networks', [])
        social_pages = feed.get('social_pages', {})
        
        missing_pages = []
        for network in target_networks:
            if network not in social_pages or not social_pages[network]:
                missing_pages.append(network)
        
        if missing_pages:
            print(f"   ⚠️  PAGES MANQUANTES: {', '.join(missing_pages)}")
        else:
            print(f"   ✅ Toutes les pages configurées")
        print()
    
    return feeds

def test_update_feed(token, feed_id):
    """Tester la mise à jour d'un feed"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "="*60)
    print(f"2️⃣ TEST DE MISE À JOUR DU FEED #{feed_id}")
    print("="*60)
    
    update_data = {
        "target_networks": ["facebook", "linkedin"],
        "social_pages": {
            "facebook": "722025697671791",
            "linkedin": "7297"
        },
        "network_prompts": {
            "facebook": "Crée un post engageant avec des emojis",
            "linkedin": "Crée un post professionnel"
        }
    }
    
    print(f"\nDonnées envoyées:")
    print(json.dumps(update_data, indent=2))
    
    response = requests.put(
        f"{API_URL}/feeds/{feed_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        updated_feed = response.json()
        print(f"✅ Feed mis à jour!")
        print(f"\nRésultat:")
        print(f"  target_networks: {updated_feed.get('target_networks')}")
        print(f"  social_pages: {updated_feed.get('social_pages')}")
        print(f"  network_prompts: {updated_feed.get('network_prompts')}")
        
        # Vérifier que les données sont bien sauvegardées
        if updated_feed.get('social_pages') == update_data['social_pages']:
            print("\n✅ social_pages correctement sauvegardé!")
        else:
            print("\n❌ social_pages NON sauvegardé!")
            print(f"   Attendu: {update_data['social_pages']}")
            print(f"   Reçu: {updated_feed.get('social_pages')}")
    else:
        print(f"❌ Erreur: {response.text}")

def test_direct_db_check(token):
    """Vérifier directement dans la base de données"""
    print("\n" + "="*60)
    print("3️⃣ VÉRIFICATION BASE DE DONNÉES")
    print("="*60)
    
    print("\nExécutez cette commande pour vérifier dans PostgreSQL:")
    print("\npsql -U user -d ecofin_pub -c \"SELECT id, name, target_networks, social_pages FROM feeds;\"")

def main():
    print("="*60)
    print("🧪 TEST COMPLET DES FEEDS ET SOCIAL_PAGES")
    print("="*60)
    print()
    
    # 1. Se connecter
    token = login()
    
    # 2. Récupérer les feeds
    feeds = test_feeds(token)
    
    if not feeds or len(feeds) == 0:
        print("\n⚠️  Aucun feed à tester. Créez d'abord un feed via l'interface.")
        return
    
    # 3. Tester la mise à jour du premier feed
    test_update_feed(token, feeds[0]['id'])
    
    # 4. Instructions DB
    test_direct_db_check(token)
    
    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
    print()

if __name__ == "__main__":
    main()

