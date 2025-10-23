#!/usr/bin/env python3
"""
Script de test de connexion à la base de données de production
"""

import psycopg2
import socket

# Configuration de la base de données de production
DB_CONFIGS = [
    {
        'host': '185.143.103.162',
        'port': 5432,
        'database': 'ecofin_publication',
        'user': 'postgres',
        'password': 'admin123'
    },
    {
        'host': '185.143.103.162',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'admin123'
    },
    {
        'host': '185.143.103.162',
        'port': 5433,
        'database': 'ecofin_publication',
        'user': 'postgres',
        'password': 'admin123'
    }
]

def test_port(host, port):
    """Teste si un port est ouvert"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_db_connection(config):
    """Teste une configuration de base de données"""
    try:
        conn = psycopg2.connect(**config)
        conn.close()
        return True, "Connexion réussie"
    except psycopg2.Error as e:
        return False, str(e)

if __name__ == "__main__":
    print("🔍 Test de connexion à la base de données de production")
    print("=" * 60)
    
    host = "185.143.103.162"
    print(f"🌐 Test du serveur: {host}")
    
    # Tester les ports courants
    ports_to_test = [5432, 5433, 3306, 1433, 1521]
    print(f"\n🔌 Test des ports: {ports_to_test}")
    
    for port in ports_to_test:
        if test_port(host, port):
            print(f"   ✅ Port {port} ouvert")
        else:
            print(f"   ❌ Port {port} fermé")
    
    # Tester les configurations de base de données
    print(f"\n🗄️  Test des configurations de base de données:")
    
    for i, config in enumerate(DB_CONFIGS, 1):
        print(f"\n   Configuration {i}:")
        print(f"   Host: {config['host']}")
        print(f"   Port: {config['port']}")
        print(f"   Database: {config['database']}")
        print(f"   User: {config['user']}")
        
        success, message = test_db_connection(config)
        if success:
            print(f"   ✅ {message}")
        else:
            print(f"   ❌ {message}")
    
    print("\n🎯 Recommandations:")
    print("   - Vérifiez que PostgreSQL est en cours d'exécution sur le serveur")
    print("   - Vérifiez que le port est correct (généralement 5432)")
    print("   - Vérifiez les credentials (utilisateur/mot de passe)")
    print("   - Vérifiez que le firewall autorise les connexions sur ce port")
