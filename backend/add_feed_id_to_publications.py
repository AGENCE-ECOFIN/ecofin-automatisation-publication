#!/usr/bin/env python3
"""
Script pour ajouter la colonne feed_id à la table publications
Utilisé en cas de problème avec les migrations Alembic
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def add_feed_id_to_publications():
    """Ajouter la colonne feed_id à la table publications"""
    try:
        # Connexion à la base de données
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Vérifier si la colonne existe déjà
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'publications' 
                    AND column_name = 'feed_id'
                );
            """))
            
            column_exists = result.fetchone()[0]
            
            if column_exists:
                print("✅ Colonne feed_id existe déjà dans la table publications")
                return True
            
            # Ajouter la colonne feed_id
            print("🔧 Ajout de la colonne feed_id à la table publications...")
            conn.execute(text("""
                ALTER TABLE publications 
                ADD COLUMN feed_id INTEGER;
            """))
            
            # Créer la clé étrangère
            print("🔧 Création de la clé étrangère...")
            conn.execute(text("""
                ALTER TABLE publications 
                ADD CONSTRAINT fk_publications_feed_id 
                FOREIGN KEY (feed_id) REFERENCES feeds(id);
            """))
            
            conn.commit()
            print("✅ Colonne feed_id ajoutée avec succès à la table publications")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
        return False

if __name__ == "__main__":
    success = add_feed_id_to_publications()
    sys.exit(0 if success else 1)
