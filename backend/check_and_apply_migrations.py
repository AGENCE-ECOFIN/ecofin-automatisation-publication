#!/usr/bin/env python3
"""
Script pour vérifier et appliquer toutes les migrations nécessaires
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def check_and_apply_migrations():
    """Vérifier et appliquer toutes les migrations nécessaires"""
    try:
        # Connexion à la base de données
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("🔍 Vérification des tables et colonnes...")
            
            # 1. Vérifier si la table publications existe et a la colonne feed_id
            print("\n📋 Vérification table publications...")
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'publications' 
                    AND column_name = 'feed_id'
                );
            """))
            feed_id_exists = result.fetchone()[0]
            
            if not feed_id_exists:
                print("❌ Colonne feed_id manquante dans publications")
                print("🔧 Ajout de la colonne feed_id...")
                conn.execute(text("""
                    ALTER TABLE publications 
                    ADD COLUMN feed_id INTEGER;
                """))
                conn.execute(text("""
                    ALTER TABLE publications 
                    ADD CONSTRAINT fk_publications_feed_id 
                    FOREIGN KEY (feed_id) REFERENCES feeds(id);
                """))
                print("✅ Colonne feed_id ajoutée")
            else:
                print("✅ Colonne feed_id existe déjà")
            
            # 2. Vérifier si la table schedule_configs existe
            print("\n📅 Vérification table schedule_configs...")
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schedule_configs'
                );
            """))
            schedule_table_exists = result.fetchone()[0]
            
            if not schedule_table_exists:
                print("❌ Table schedule_configs manquante")
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
                conn.execute(text("""
                    CREATE INDEX ix_schedule_configs_id ON schedule_configs (id);
                    CREATE INDEX ix_schedule_configs_network ON schedule_configs (network);
                    CREATE INDEX ix_schedule_configs_day_type ON schedule_configs (day_type);
                """))
                print("✅ Table schedule_configs créée")
            else:
                print("✅ Table schedule_configs existe déjà")
            
            # 3. Vérifier si la table feeds a la colonne network_prompts
            print("\n🔗 Vérification colonne network_prompts dans feeds...")
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'feeds' 
                    AND column_name = 'network_prompts'
                );
            """))
            network_prompts_exists = result.fetchone()[0]
            
            if not network_prompts_exists:
                print("❌ Colonne network_prompts manquante dans feeds")
                print("🔧 Ajout de la colonne network_prompts...")
                conn.execute(text("""
                    ALTER TABLE feeds 
                    ADD COLUMN network_prompts JSON;
                """))
                print("✅ Colonne network_prompts ajoutée")
            else:
                print("✅ Colonne network_prompts existe déjà")
            
            # 4. Vérifier les contraintes de clés étrangères dans publication_queue
            print("\n🔗 Vérification contraintes publication_queue...")
            result = conn.execute(text("""
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = 'publication_queue' 
                AND constraint_type = 'FOREIGN KEY';
            """))
            fk_constraints = result.fetchall()
            
            print(f"Contraintes FK trouvées: {[c[0] for c in fk_constraints]}")
            
            # 5. Vérifier la colonne metadata dans publication_queue
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'publication_queue' 
                    AND column_name = 'metadata'
                );
            """))
            metadata_exists = result.fetchone()[0]
            
            if metadata_exists:
                print("⚠️  Colonne metadata trouvée dans publication_queue (à supprimer)")
                print("🔧 Suppression de la colonne metadata...")
                conn.execute(text("""
                    ALTER TABLE publication_queue DROP COLUMN metadata;
                """))
                print("✅ Colonne metadata supprimée")
            else:
                print("✅ Colonne metadata n'existe pas (correct)")
            
            conn.commit()
            print("\n🎉 Toutes les vérifications et corrections terminées!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    success = check_and_apply_migrations()
    sys.exit(0 if success else 1)
