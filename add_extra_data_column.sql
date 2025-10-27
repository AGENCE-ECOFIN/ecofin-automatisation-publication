-- Script SQL pour ajouter la colonne extra_data à la table publications
-- À exécuter sur le serveur de production

-- Ajouter la colonne extra_data
ALTER TABLE publications ADD COLUMN extra_data JSON;

-- Mettre à jour la version Alembic
UPDATE alembic_version SET version_num = '2f0fe8c89379';

-- Vérifier que la colonne a été ajoutée
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'publications' 
AND column_name = 'extra_data';
