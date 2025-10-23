#!/usr/bin/env python3
"""
Script pour corriger la base de données de production
Applique les migrations et initialise les tables manquantes
"""

import psycopg2
import sys
from datetime import datetime

# Configuration de la base de données de production
DB_CONFIG = {
    'host': '185.143.103.162',
    'port': 5432,
    'database': 'ecofin_pub',  # Nom correct de la DB selon le .env
    'user': 'user',
    'password': 'password'
}

def get_db_connection():
    """Établit une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        print(f"🔧 Configuration: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        sys.exit(1)

def create_missing_tables():
    """Crée les tables manquantes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🔧 Création des tables manquantes...")
        print(f"📅 Timestamp: {datetime.now()}")
        print(f"🌐 Serveur: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print("-" * 50)
        
        # 1. Créer la table network_configs
        print("📋 Création de la table network_configs...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_configs (
                id SERIAL PRIMARY KEY,
                network VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                default_publication_delay INTEGER DEFAULT 30,
                api_credentials JSONB,
                page_configs JSONB,
                max_posts_per_day INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ Table network_configs créée")
        
        # 2. Créer la table schedule_configs
        print("📋 Création de la table schedule_configs...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_configs (
                id SERIAL PRIMARY KEY,
                network VARCHAR(50) NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ Table schedule_configs créée")
        
        # 3. Insérer les configurations par défaut
        print("⚙️  Insertion des configurations par défaut...")
        
        # Network configs
        networks = ['facebook', 'linkedin', 'x']
        for network in networks:
            cursor.execute("""
                INSERT INTO network_configs (network, is_active, default_publication_delay, max_posts_per_day)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (network) DO NOTHING;
            """, (network, True, 30, 10))
        
        print("   ✅ Configurations réseau insérées")
        
        # Schedule configs (horaires de publication)
        schedule_data = [
            (0, '08:00:00', '18:00:00'),  # Dimanche
            (1, '08:00:00', '18:00:00'),  # Lundi
            (2, '08:00:00', '18:00:00'),  # Mardi
            (3, '08:00:00', '18:00:00'),  # Mercredi
            (4, '08:00:00', '18:00:00'),  # Jeudi
            (5, '08:00:00', '18:00:00'),  # Vendredi
            (6, '08:00:00', '18:00:00'),  # Samedi
        ]
        
        for network in networks:
            for day, start_time, end_time in schedule_data:
                cursor.execute("""
                    INSERT INTO schedule_configs (network, day_of_week, start_time, end_time, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (network, day_of_week) DO NOTHING;
                """, (network, day, start_time, end_time, True))
        
        print("   ✅ Configurations de planification insérées")
        
        # 4. Valider les changements
        conn.commit()
        
        print("-" * 50)
        print("✅ Tables créées avec succès !")
        
        # 5. Vérifier les tables créées
        print("\n🔍 Vérification des tables:")
        
        cursor.execute("SELECT COUNT(*) FROM network_configs;")
        network_count = cursor.fetchone()[0]
        print(f"   📋 network_configs: {network_count} entrées")
        
        cursor.execute("SELECT COUNT(*) FROM schedule_configs;")
        schedule_count = cursor.fetchone()[0]
        print(f"   📅 schedule_configs: {schedule_count} entrées")
        
    except psycopg2.Error as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔧 Script de correction de la base de données de production")
    print("=" * 70)
    print("⚠️  Ce script va créer les tables manquantes:")
    print("   - network_configs")
    print("   - schedule_configs")
    print("   - Configurations par défaut")
    print(f"\n🌐 Base de données cible: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("\n🚀 Exécution en cours...")
    
    # Créer les tables
    create_missing_tables()
    
    print("\n🎉 Script terminé avec succès !")
    print("💡 Vous pouvez maintenant redémarrer les services Docker")
