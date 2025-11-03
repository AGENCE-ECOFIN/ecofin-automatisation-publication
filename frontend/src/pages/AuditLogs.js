import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { auditService } from '../services/api';

const AuditLogs = () => {
  const [filters, setFilters] = useState({
    user_id: '',
    entity_type: '',
    entity_id: '',
    action: '',
  });
  const [page, setPage] = useState(0);
  const [limit, setLimit] = useState(50);

  const { data: logsData, isLoading, error, refetch } = useQuery(
    ['auditLogs', filters, page, limit],
    () => auditService.getLogs({
      ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== '')),
      limit,
      offset: page * limit,
    }),
    {
      keepPreviousData: true,
    }
  );

  const { data: summaryData } = useQuery(
    'auditSummary',
    () => auditService.getSummary(),
    {
      enabled: false, // Optionnel, on peut l'activer si on veut afficher le résumé
    }
  );

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(0); // Reset to first page when filter changes
  };

  const handleResetFilters = () => {
    setFilters({
      user_id: '',
      entity_type: '',
      entity_id: '',
      action: '',
    });
    setPage(0);
  };

  const getActionBadgeColor = (action) => {
    const colors = {
      'POST_VALIDATE': 'bg-green-100 text-green-800',
      'POST_REJECT': 'bg-red-100 text-red-800',
      'POST_RESTORE': 'bg-blue-100 text-blue-800',
      'POST_MODIFY': 'bg-yellow-100 text-yellow-800',
      'POST_CREATE': 'bg-purple-100 text-purple-800',
      'POST_DELETE': 'bg-red-100 text-red-800',
      'FEED_CREATE': 'bg-green-100 text-green-800',
      'FEED_DELETE': 'bg-red-100 text-red-800',
      'CONFIG_UPDATE': 'bg-orange-100 text-orange-800',
      'USER_LOGIN': 'bg-indigo-100 text-indigo-800',
      'USER_LOGOUT': 'bg-gray-100 text-gray-800',
    };
    return colors[action] || 'bg-gray-100 text-gray-800';
  };

  const getEntityTypeBadgeColor = (entityType) => {
    const colors = {
      'post': 'bg-blue-100 text-blue-800',
      'feed': 'bg-green-100 text-green-800',
      'network_config': 'bg-orange-100 text-orange-800',
      'schedule_config': 'bg-purple-100 text-purple-800',
      'user': 'bg-indigo-100 text-indigo-800',
    };
    return colors[entityType] || 'bg-gray-100 text-gray-800';
  };

  const logs = logsData?.data?.logs || [];
  const total = logsData?.data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📋 Logs d'Audit</h1>
        <p className="text-gray-600">Traçabilité des actions importantes dans le système</p>
      </div>

      {/* Filtres */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filtres</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Action
            </label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Toutes</option>
              <option value="POST_VALIDATE">Validation Post</option>
              <option value="POST_REJECT">Rejet Post</option>
              <option value="POST_RESTORE">Restauration Post</option>
              <option value="POST_MODIFY">Modification Post</option>
              <option value="POST_CREATE">Création Post</option>
              <option value="POST_DELETE">Suppression Post</option>
              <option value="FEED_CREATE">Création Flux</option>
              <option value="FEED_DELETE">Suppression Flux</option>
              <option value="CONFIG_UPDATE">Mise à jour Config</option>
              <option value="USER_LOGIN">Connexion</option>
              <option value="USER_LOGOUT">Déconnexion</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type d'entité
            </label>
            <select
              value={filters.entity_type}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tous</option>
              <option value="post">Post</option>
              <option value="feed">Flux RSS</option>
              <option value="network_config">Config Réseau</option>
              <option value="schedule_config">Config Horaires</option>
              <option value="user">Utilisateur</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ID Entité
            </label>
            <input
              type="number"
              value={filters.entity_id}
              onChange={(e) => handleFilterChange('entity_id', e.target.value)}
              placeholder="ID de l'entité"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ID Utilisateur
            </label>
            <input
              type="number"
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              placeholder="ID de l'utilisateur"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleResetFilters}
            className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
          >
            Réinitialiser les filtres
          </button>
        </div>
      </div>

      {/* Statistiques */}
      {logs.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              Total: <strong>{total}</strong> logs
            </span>
            <span className="text-sm text-gray-600">
              Page {page + 1} sur {totalPages}
            </span>
          </div>
        </div>
      )}

      {/* Liste des logs */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Chargement des logs...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">
            Erreur lors du chargement des logs: {error.message}
          </p>
        </div>
      )}

      {!isLoading && !error && logs.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-600">Aucun log d'audit trouvé</p>
        </div>
      )}

      {!isLoading && !error && logs.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date/Heure
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Utilisateur
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entité
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(log.created_at), 'dd MMM yyyy HH:mm:ss', { locale: fr })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.username || 'Système'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionBadgeColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getEntityTypeBadgeColor(log.entity_type)}`}>
                          {log.entity_type}
                        </span>
                        {log.entity_id && (
                          <span className="text-sm text-gray-600">#{log.entity_id}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {log.description || '-'}
                      {log.action_metadata && Object.keys(log.action_metadata).length > 0 && (
                        <details className="mt-1">
                          <summary className="text-xs text-blue-600 cursor-pointer hover:underline">
                            Voir détails
                          </summary>
                          <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                            {JSON.stringify(log.action_metadata, null, 2)}
                          </pre>
                        </details>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {!isLoading && !error && logs.length > 0 && totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setPage(prev => Math.max(0, prev - 1))}
            disabled={page === 0}
            className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Précédent
          </button>
          <span className="text-sm text-gray-600">
            Page {page + 1} sur {totalPages}
          </span>
          <button
            onClick={() => setPage(prev => Math.min(totalPages - 1, prev + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;

