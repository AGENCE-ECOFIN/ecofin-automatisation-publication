#!/usr/bin/env python3
"""
Script de nettoyage de la base de données sur le serveur de production
À exécuter sur ubuntu@ov-91cb48:~/ecofin-publication-preprod
"""

import psycopg2
import sys
from datetime import datetime

# Configuration de la base de données locale (Docker sur le serveur)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecofin_publication',
    'user': 'ecofin_user',
    'password': 'changeme'
}

def get_db_connection():
    """Établit une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        print(f"🔧 Configuration: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        print("💡 Vérifiez que Docker est démarré et que PostgreSQL est accessible")
        sys.exit(1)

def cleanup_database():
    """Nettoie la base de données en supprimant les données spécifiées"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🧹 Début du nettoyage de la base de données...")
        print(f"📅 Timestamp: {datetime.now()}")
        print(f"🌐 Serveur: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print("-" * 50)
        
        # 1. Supprimer l'historique des publications
        print("🗑️  Suppression de l'historique des publications...")
        cursor.execute("DELETE FROM publications;")
        publications_count = cursor.rowcount
        print(f"   ✅ {publications_count} publications supprimées")
        
        # 2. Supprimer la file d'attente de publication
        print("🗑️  Suppression de la file d'attente...")
        cursor.execute("DELETE FROM publication_queue;")
        queue_count = cursor.rowcount
        print(f"   ✅ {queue_count} éléments de file supprimés")
        
        # 3. Supprimer les posts
        print("🗑️  Suppression des posts...")
        cursor.execute("DELETE FROM posts;")
        posts_count = cursor.rowcount
        print(f"   ✅ {posts_count} posts supprimés")
        
        # 4. Supprimer les feeds
        print("🗑️  Suppression des feeds...")
        cursor.execute("DELETE FROM feeds;")
        feeds_count = cursor.rowcount
        print(f"   ✅ {feeds_count} feeds supprimés")
        
        # 5. Réinitialiser les séquences (IDs auto-incrémentés)
        print("🔄 Réinitialisation des séquences...")
        sequences = [
            'publications_id_seq',
            'publication_queue_id_seq', 
            'posts_id_seq',
            'feeds_id_seq'
        ]
        
        for seq in sequences:
            try:
                cursor.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1;")
                print(f"   ✅ Séquence {seq} réinitialisée")
            except psycopg2.Error as e:
                print(f"   ⚠️  Séquence {seq} non trouvée ou erreur: {e}")
        
        # 6. Valider les changements
        conn.commit()
        
        print("-" * 50)
        print("✅ Nettoyage terminé avec succès !")
        print(f"📊 Résumé:")
        print(f"   - Publications supprimées: {publications_count}")
        print(f"   - Éléments de file supprimés: {queue_count}")
        print(f"   - Posts supprimés: {posts_count}")
        print(f"   - Feeds supprimés: {feeds_count}")
        print(f"   - Séquences réinitialisées: {len(sequences)}")
        
        # 7. Vérifier ce qui reste (configurations et utilisateurs)
        print("\n🔍 Vérification des données conservées:")
        
        cursor.execute("SELECT COUNT(*) FROM users;")
        users_count = cursor.fetchone()[0]
        print(f"   👥 Utilisateurs conservés: {users_count}")
        
        cursor.execute("SELECT COUNT(*) FROM network_configs;")
        network_configs_count = cursor.fetchone()[0]
        print(f"   ⚙️  Configurations réseau conservées: {network_configs_count}")
        
        cursor.execute("SELECT COUNT(*) FROM schedule_configs;")
        schedule_configs_count = cursor.fetchone()[0]
        print(f"   📅 Configurations de planification conservées: {schedule_configs_count}")
        
    except psycopg2.Error as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🧹 Script de nettoyage de la base de données sur le serveur")
    print("=" * 70)
    print("⚠️  Ce script va supprimer TOUTES les données suivantes:")
    print("   - Tous les feeds")
    print("   - Tous les posts")
    print("   - Tout l'historique des publications")
    print("   - Toute la file d'attente de publication")
    print("\n✅ Les données suivantes seront CONSERVÉES:")
    print("   - Utilisateurs")
    print("   - Configurations réseau")
    print("   - Configurations de planification")
    print(f"\n🌐 Base de données cible: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"👤 User: {DB_CONFIG['user']}")
    print(f"🔑 Password: {DB_CONFIG['password']}")
    print(f"🗄️  Database: {DB_CONFIG['database']}")
    print("\n🚀 Exécution automatique en cours...")
    
    # Effectuer le nettoyage
    cleanup_database()
    
    print("\n🎉 Script terminé avec succès !")
