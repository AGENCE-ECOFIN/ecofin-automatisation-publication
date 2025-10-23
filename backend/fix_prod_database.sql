-- Script SQL pour corriger la base de données de production
-- À exécuter directement sur le serveur 185.143.103.162

-- 1. Créer la table network_configs
CREATE TABLE IF NOT EXISTS network_configs (
    id SERIAL PRIMARY KEY,
    network VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    default_publication_delay INTEGER DEFAULT 30,
    api_credentials JSONB,
    page_configs JSONB,
    max_posts_per_day INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Créer la table schedule_configs
CREATE TABLE IF NOT EXISTS schedule_configs (
    id SERIAL PRIMARY KEY,
    network VARCHAR(50) NOT NULL,
    day_of_week INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(network, day_of_week)
);

-- 3. Insérer les configurations réseau par défaut
INSERT INTO network_configs (network, is_active, default_publication_delay, max_posts_per_day)
VALUES 
    ('facebook', TRUE, 30, 10),
    ('linkedin', TRUE, 30, 10),
    ('x', TRUE, 30, 10)
ON CONFLICT (network) DO NOTHING;

-- 4. Insérer les configurations de planification par défaut
INSERT INTO schedule_configs (network, day_of_week, start_time, end_time, is_active)
VALUES 
    -- Facebook
    ('facebook', 0, '08:00:00', '18:00:00', TRUE),
    ('facebook', 1, '08:00:00', '18:00:00', TRUE),
    ('facebook', 2, '08:00:00', '18:00:00', TRUE),
    ('facebook', 3, '08:00:00', '18:00:00', TRUE),
    ('facebook', 4, '08:00:00', '18:00:00', TRUE),
    ('facebook', 5, '08:00:00', '18:00:00', TRUE),
    ('facebook', 6, '08:00:00', '18:00:00', TRUE),
    -- LinkedIn
    ('linkedin', 0, '08:00:00', '18:00:00', TRUE),
    ('linkedin', 1, '08:00:00', '18:00:00', TRUE),
    ('linkedin', 2, '08:00:00', '18:00:00', TRUE),
    ('linkedin', 3, '08:00:00', '18:00:00', TRUE),
    ('linkedin', 4, '08:00:00', '18:00:00', TRUE),
    ('linkedin', 5, '08:00:00', '18:00:00', TRUE),
    ('linkedin', 6, '08:00:00', '18:00:00', TRUE),
    -- X (Twitter)
    ('x', 0, '08:00:00', '18:00:00', TRUE),
    ('x', 1, '08:00:00', '18:00:00', TRUE),
    ('x', 2, '08:00:00', '18:00:00', TRUE),
    ('x', 3, '08:00:00', '18:00:00', TRUE),
    ('x', 4, '08:00:00', '18:00:00', TRUE),
    ('x', 5, '08:00:00', '18:00:00', TRUE),
    ('x', 6, '08:00:00', '18:00:00', TRUE)
ON CONFLICT (network, day_of_week) DO NOTHING;

-- 5. Vérifier les tables créées
SELECT 'network_configs' as table_name, COUNT(*) as count FROM network_configs
UNION ALL
SELECT 'schedule_configs' as table_name, COUNT(*) as count FROM schedule_configs;
