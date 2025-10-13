# Test de mise à jour d'un feed
import requests
import json

# Configuration
API_URL = "http://localhost:8000"
token = "VOTRE_TOKEN"  # À remplacer

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Récupérer les feeds
print("1️⃣ Récupération des feeds...")
response = requests.get(f"{API_URL}/feeds/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    feeds = response.json()
    print(f"✅ {len(feeds)} feeds trouvés")
    for feed in feeds:
        print(f"\nFeed #{feed['id']}: {feed['name']}")
        print(f"  target_networks: {feed.get('target_networks')}")
        print(f"  social_pages: {feed.get('social_pages')}")
else:
    print(f"❌ Erreur: {response.text}")
    exit(1)

# 2. Tester la mise à jour
if feeds:
    feed_id = feeds[0]['id']
    print(f"\n2️⃣ Test de mise à jour du feed #{feed_id}...")
    
    update_data = {
        "target_networks": ["facebook", "linkedin"],
        "social_pages": {
            "facebook": "722025697671791",
            "linkedin": "7297"
        }
    }
    
    print(f"Données envoyées: {json.dumps(update_data, indent=2)}")
    
    response = requests.put(
        f"{API_URL}/feeds/{feed_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        updated_feed = response.json()
        print(f"✅ Feed mis à jour")
        print(f"  target_networks: {updated_feed.get('target_networks')}")
        print(f"  social_pages: {updated_feed.get('social_pages')}")
    else:
        print(f"❌ Erreur: {response.text}")
        
    # 3. Vérifier dans la DB
    print(f"\n3️⃣ Re-vérification...")
    response = requests.get(f"{API_URL}/feeds/{feed_id}", headers=headers)
    if response.status_code == 200:
        feed = response.json()
        print(f"  social_pages: {feed.get('social_pages')}")
        
        if feed.get('social_pages') == update_data['social_pages']:
            print("✅ social_pages correctement sauvegardé!")
        else:
            print("❌ social_pages NON sauvegardé!")
            print(f"   Attendu: {update_data['social_pages']}")
            print(f"   Reçu: {feed.get('social_pages')}")
