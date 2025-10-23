#!/usr/bin/env python3
"""
Script pour corriger les contraintes de la table schedule_configs
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

def fix_schedule_configs_constraints():
    """Corrige les contraintes de la table schedule_configs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🔧 Correction des contraintes de la table schedule_configs...")
        print(f"📅 Timestamp: {datetime.now()}")
        print("-" * 50)
        
        # 1. Vérifier la structure actuelle
        print("🔍 Vérification de la structure actuelle...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'schedule_configs'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("   Colonnes actuelles:")
        for col in columns:
            print(f"     📋 {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # 2. Modifier la contrainte NOT NULL sur day_of_week
        print("\n🔧 Modification des contraintes...")
        
        # Rendre day_of_week nullable
        try:
            cursor.execute("ALTER TABLE schedule_configs ALTER COLUMN day_of_week DROP NOT NULL;")
            print("   ✅ Contrainte NOT NULL supprimée sur day_of_week")
        except psycopg2.Error as e:
            print(f"   ⚠️  Erreur avec day_of_week: {e}")
        
        # 3. Mettre à jour les données existantes
        print("\n🔄 Mise à jour des données existantes...")
        
        # Mettre à jour les enregistrements existants avec day_of_week = 0 (dimanche) par défaut
        cursor.execute("""
            UPDATE schedule_configs 
            SET day_of_week = 0 
            WHERE day_of_week IS NULL;
        """)
        updated_rows = cursor.rowcount
        print(f"   ✅ {updated_rows} lignes mises à jour avec day_of_week=0")
        
        # 4. Ajouter une valeur par défaut pour day_of_week
        try:
            cursor.execute("ALTER TABLE schedule_configs ALTER COLUMN day_of_week SET DEFAULT 0;")
            print("   ✅ Valeur par défaut ajoutée pour day_of_week")
        except psycopg2.Error as e:
            print(f"   ⚠️  Erreur avec la valeur par défaut: {e}")
        
        # 5. Valider les changements
        conn.commit()
        
        print("-" * 50)
        print("✅ Correction des contraintes terminée avec succès !")
        
        # 6. Vérifier la nouvelle structure
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
    print("🔧 Script de correction des contraintes schedule_configs")
    print("=" * 60)
    print("⚠️  Ce script va corriger les contraintes de la table schedule_configs")
    print("   - Rendre day_of_week nullable")
    print("   - Ajouter une valeur par défaut")
    print("   - Mettre à jour les données existantes")
    print(f"\n🌐 Base de données: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("\n🚀 Exécution de la correction...")
    
    fix_schedule_configs_constraints()
    
    print("\n🎉 Correction terminée avec succès !")
    print("💡 Les configurations de planification devraient maintenant fonctionner")
