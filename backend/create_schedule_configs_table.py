#!/usr/bin/env python3
"""
Script pour créer la table schedule_configs directement en SQL
Utilisé en cas de problème avec les migrations Alembic
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def create_schedule_configs_table():
    """Créer la table schedule_configs directement"""
    try:
        # Connexion à la base de données
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Vérifier si la table existe déjà
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schedule_configs'
                );
            """))
            
            table_exists = result.fetchone()[0]
            
            if table_exists:
                print("✅ Table schedule_configs existe déjà")
                return True
            
            # Créer la table
            print("🔧 Création de la table schedule_configs...")
            conn.execute(text("""
                CREATE TABLE schedule_configs (
                    id SERIAL PRIMARY KEY,
                    network VARCHAR(50) NOT NULL,
                    day_type VARCHAR(20) NOT NULL,
                    start_time VARCHAR(5) NOT NULL,
                    end_time VARCHAR(5) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_posts_per_day INTEGER DEFAULT 5,
                    specific_days JSON,
                    period_start TIMESTAMP WITH TIME ZONE,
                    period_end TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            # Créer les index
            conn.execute(text("""
                CREATE INDEX ix_schedule_configs_id ON schedule_configs (id);
                CREATE INDEX ix_schedule_configs_network ON schedule_configs (network);
                CREATE INDEX ix_schedule_configs_day_type ON schedule_configs (day_type);
            """))
            
            conn.commit()
            print("✅ Table schedule_configs créée avec succès")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")
        return False

if __name__ == "__main__":
    success = create_schedule_configs_table()
    sys.exit(0 if success else 1)
