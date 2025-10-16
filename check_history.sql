-- Vérifier ce qui est dans la base de données

-- 1. Publications (historique réel)
\echo '=== TABLE PUBLICATIONS (Historique réel) ==='
SELECT 
    id,
    CASE WHEN post_id IS NULL THEN '📤 POST DIRECT' ELSE 'Flux #' || post_id::text END as type,
    network,
    CASE WHEN is_success THEN '✅ Succès' ELSE '❌ Échec' END as resultat,
    CASE WHEN published_url IS NOT NULL THEN 'Oui' ELSE 'Non' END as has_url,
    published_at
FROM publications
ORDER BY created_at DESC;

\echo ''
\echo '=== COMPTEURS ==='
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) as succes,
    SUM(CASE WHEN NOT is_success THEN 1 ELSE 0 END) as echecs,
    SUM(CASE WHEN post_id IS NULL THEN 1 ELSE 0 END) as posts_directs
FROM publications;

\echo ''
\echo '=== PAR RÉSEAU ==='
SELECT 
    network,
    COUNT(*) as total,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) as succes
FROM publications
GROUP BY network;

