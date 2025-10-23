#!/usr/bin/env python3
"""
Script pour corriger le schéma de la table schedule_configs
"""

import psycopg2
import sys
from datetime import datetime

# Configuration de la base de données de production
DB_CONFIG = {
    'host': '185.143.103.162',
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
        sys.exit(1)

def fix_schedule_configs_schema():
    """Corrige le schéma de la table schedule_configs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🔧 Correction du schéma de la table schedule_configs...")
        print(f"📅 Timestamp: {datetime.now()}")
        print("-" * 50)
        
        # 1. Vérifier la structure actuelle
        print("🔍 Vérification de la structure actuelle...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'schedule_configs'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"   Colonnes actuelles: {[col[0] for col in columns]}")
        
        # 2. Ajouter les colonnes manquantes si nécessaire
        print("🔧 Ajout des colonnes manquantes...")
        
        # Ajouter day_type si elle n'existe pas
        try:
            cursor.execute("ALTER TABLE schedule_configs ADD COLUMN day_type VARCHAR(20) DEFAULT 'weekday';")
            print("   ✅ Colonne day_type ajoutée")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("   ✅ Colonne day_type existe déjà")
            else:
                print(f"   ⚠️  Erreur avec day_type: {e}")
        
        # Ajouter max_posts_per_day si elle n'existe pas
        try:
            cursor.execute("ALTER TABLE schedule_configs ADD COLUMN max_posts_per_day INTEGER DEFAULT 10;")
            print("   ✅ Colonne max_posts_per_day ajoutée")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("   ✅ Colonne max_posts_per_day existe déjà")
            else:
                print(f"   ⚠️  Erreur avec max_posts_per_day: {e}")
        
        # Ajouter specific_days si elle n'existe pas
        try:
            cursor.execute("ALTER TABLE schedule_configs ADD COLUMN specific_days JSONB;")
            print("   ✅ Colonne specific_days ajoutée")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("   ✅ Colonne specific_days existe déjà")
            else:
                print(f"   ⚠️  Erreur avec specific_days: {e}")
        
        # Ajouter period_start si elle n'existe pas
        try:
            cursor.execute("ALTER TABLE schedule_configs ADD COLUMN period_start TIME;")
            print("   ✅ Colonne period_start ajoutée")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("   ✅ Colonne period_start existe déjà")
            else:
                print(f"   ⚠️  Erreur avec period_start: {e}")
        
        # Ajouter period_end si elle n'existe pas
        try:
            cursor.execute("ALTER TABLE schedule_configs ADD COLUMN period_end TIME;")
            print("   ✅ Colonne period_end ajoutée")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("   ✅ Colonne period_end existe déjà")
            else:
                print(f"   ⚠️  Erreur avec period_end: {e}")
        
        # 3. Mettre à jour les données existantes
        print("🔄 Mise à jour des données existantes...")
        cursor.execute("""
            UPDATE schedule_configs 
            SET day_type = 'weekday' 
            WHERE day_type IS NULL;
        """)
        updated_rows = cursor.rowcount
        print(f"   ✅ {updated_rows} lignes mises à jour avec day_type='weekday'")
        
        # 4. Valider les changements
        conn.commit()
        
        print("-" * 50)
        print("✅ Correction du schéma terminée avec succès !")
        
        # 5. Vérifier la nouvelle structure
        print("\n🔍 Vérification de la nouvelle structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'schedule_configs'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"   📋 {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
    except psycopg2.Error as e:
        print(f"❌ Erreur lors de la correction: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔧 Script de correction du schéma schedule_configs")
    print("=" * 60)
    print("⚠️  Ce script va corriger la structure de la table schedule_configs")
    print("   - Ajouter les colonnes manquantes")
    print("   - Mettre à jour les données existantes")
    print(f"\n🌐 Base de données: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("\n🚀 Exécution de la correction...")
    
    fix_schedule_configs_schema()
    
    print("\n🎉 Correction terminée avec succès !")
    print("💡 Les services devraient maintenant fonctionner sans erreur")
