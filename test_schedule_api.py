#!/usr/bin/env python3
"""
Test simple de l'API des horaires
"""
import requests
import json

# URL de l'API
BASE_URL = "http://localhost:8000"

def test_schedule_api():
    """Tester l'API des horaires"""
    
    # 1. Se connecter pour obtenir un token
    login_data = {
        "email": "admin@ecofin.com",
        "password": "admin123"
    }
    
    print("🔐 Connexion...")
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Erreur de connexion: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Connexion réussie")
    
    # 2. Récupérer les horaires pour LinkedIn
    print("\n📅 Test récupération horaires LinkedIn...")
    response = requests.get(f"{BASE_URL}/schedule/?network=linkedin", headers=headers)
    
    if response.status_code == 200:
        configs = response.json()
        print(f"✅ {len(configs)} configuration(s) trouvée(s)")
        for config in configs:
            print(f"  - {config['day_type']}: {config['start_time']}-{config['end_time']} (intervalle: {config['interval_minutes']}min)")
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
    
    # 3. Tester le statut pour LinkedIn
    print("\n⏰ Test statut actuel LinkedIn...")
    response = requests.get(f"{BASE_URL}/schedule/status/linkedin", headers=headers)
    
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Publication autorisée maintenant: {status['is_active_now']}")
        print(f"  Raison: {status['reason']}")
        if status['next_available_time']:
            print(f"  Prochaine publication: {status['next_available_time']}")
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
    
    # 4. Générer un planning
    print("\n📊 Test planning de publication...")
    response = requests.get(f"{BASE_URL}/schedule/planning/linkedin", headers=headers)
    
    if response.status_code == 200:
        planning = response.json()
        print(f"✅ Planning généré: {planning['total_slots']} créneaux")
        for slot in planning['planning'][:5]:  # Afficher les 5 premiers
            print(f"  - {slot['time']} ({slot['day_type']})")
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_schedule_api()
