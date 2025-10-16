#!/usr/bin/env python3
"""
Script pour tester l'endpoint /schedule/bulk-update
"""
import requests
import json

# Configuration
BASE_URL = "http://185.143.103.162"
LOGIN_URL = f"{BASE_URL}/auth/token"
SCHEDULE_URL = f"{BASE_URL}/schedule/bulk-update"

def test_schedule_endpoint():
    """Tester l'endpoint de mise à jour des horaires"""
    
    # 1. Se connecter pour obtenir un token
    print("🔐 Connexion...")
    login_data = {
        "username": "admin@ecofin.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code != 200:
            print(f"❌ Erreur de connexion: {response.status_code}")
            print(f"Réponse: {response.text}")
            return
        
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"✅ Connexion réussie, token: {access_token[:20]}...")
        
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        return
    
    # 2. Tester l'endpoint bulk-update
    print("\n📅 Test de l'endpoint bulk-update...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    test_data = {
        "network": "facebook",
        "configs": [
            {
                "day_type": "weekday",
                "start_time": "09:00",
                "end_time": "18:00",
                "is_active": True,
                "max_posts_per_day": 5,
                "specific_days": [0, 1, 2, 3, 4]
            }
        ]
    }
    
    try:
        response = requests.post(SCHEDULE_URL, headers=headers, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Endpoint fonctionne correctement!")
            print(f"Réponse: {response.json()}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    # 3. Tester d'autres endpoints pour comparaison
    print("\n🔍 Test des autres endpoints...")
    
    # Test GET /schedule/
    try:
        get_response = requests.get(f"{BASE_URL}/schedule/", headers=headers)
        print(f"GET /schedule/ - Status: {get_response.status_code}")
        if get_response.status_code == 200:
            print("✅ GET endpoint fonctionne")
        else:
            print(f"❌ GET endpoint erreur: {get_response.text}")
    except Exception as e:
        print(f"❌ Erreur GET: {e}")

if __name__ == "__main__":
    test_schedule_endpoint()
