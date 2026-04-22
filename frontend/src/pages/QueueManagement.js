import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaClock, FaPlay, FaPause, FaCheck, FaTimes, FaPlus, FaGlobe, FaEdit } from 'react-icons/fa';
import { publicationQueueService, feedsService, DEFAULT_PAGE_SIZE } from '../services/api';
import Pagination from '../components/Pagination';

const QueueManagement = () => {
  const [feedFilter, setFeedFilter] = useState('');
  const [networkFilter, setNetworkFilter] = useState('');
  const [page, setPage] = useState(1);
  const [showGlobalConfig, setShowGlobalConfig] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);

  const queryClient = useQueryClient();

  useEffect(() => {
    setPage(1);
  }, [feedFilter, networkFilter]);

  const { data: queueData, isLoading: queueLoading } = useQuery(
    ['publication-queue-qm', page, feedFilter, networkFilter],
    () =>
      publicationQueueService.getQueue(
        {
          network: networkFilter || undefined,
          feed: feedFilter || undefined,
        },
        { page, pageSize: DEFAULT_PAGE_SIZE }
      ),
    { keepPreviousData: true }
  );
  const queueItems = queueData?.data || [];
  const queueMeta = queueData?.pagination || {};

  // Récupération des flux pour les filtres
  const { data: feedsData } = useQuery('queue-management-feeds', () =>
    feedsService.getFeeds({ page: 1, pageSize: 500 })
  );
  const feeds = feedsData?.data || [];

  // Mutations pour les actions individuelles
  const pauseItemMutation = useMutation(publicationQueueService.pauseItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
    }
  });

  const resumeItemMutation = useMutation(publicationQueueService.resumeItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
    }
  });

  const cancelItemMutation = useMutation(publicationQueueService.cancelItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
    }
  });

  const retryItemMutation = useMutation(publicationQueueService.retryItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
    }
  });

  // Mutations pour les actions groupées
  const pauseAllMutation = useMutation(
    () => Promise.all(queueItems.map(item => publicationQueueService.pauseItem(item.id))),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('publication-queue');
      }
    }
  );

  const resumeAllMutation = useMutation(
    () => Promise.all(queueItems.map(item => publicationQueueService.resumeItem(item.id))),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('publication-queue');
      }
    }
  );

  // Gestion des sélections
  const handleSelectItem = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSelectAll = () => {
    setSelectedItems(
      selectedItems.length === queueItems.length
        ? []
        : queueItems.map((item) => item.id)
    );
  };

  // Actions individuelles
  const handlePauseItem = (itemId) => {
    pauseItemMutation.mutate(itemId);
  };

  const handleResumeItem = (itemId) => {
    resumeItemMutation.mutate(itemId);
  };

  const handleCancelItem = (itemId) => {
    if (window.confirm('Êtes-vous sûr de vouloir annuler cet élément ?')) {
      cancelItemMutation.mutate(itemId);
    }
  };

  const handleRetryItem = (itemId) => {
    retryItemMutation.mutate(itemId);
  };

  // Actions groupées
  const handlePauseAll = () => {
    if (window.confirm('Êtes-vous sûr de vouloir mettre en pause tous les éléments ?')) {
      pauseAllMutation.mutate();
    }
  };

  const handleResumeAll = () => {
    if (window.confirm('Êtes-vous sûr de vouloir reprendre tous les éléments ?')) {
      resumeAllMutation.mutate();
    }
  };

  const handlePauseSelected = () => {
    if (selectedItems.length === 0) return;
    if (window.confirm(`Êtes-vous sûr de vouloir mettre en pause ${selectedItems.length} élément(s) ?`)) {
      Promise.all(selectedItems.map(id => publicationQueueService.pauseItem(id)))
        .then(() => {
          queryClient.invalidateQueries('publication-queue');
          setSelectedItems([]);
        });
    }
  };

  const handleResumeSelected = () => {
    if (selectedItems.length === 0) return;
    if (window.confirm(`Êtes-vous sûr de vouloir reprendre ${selectedItems.length} élément(s) ?`)) {
      Promise.all(selectedItems.map(id => publicationQueueService.resumeItem(id)))
        .then(() => {
          queryClient.invalidateQueries('publication-queue');
          setSelectedItems([]);
        });
    }
  };

  // Fonctions utilitaires
  const getStatusIcon = (status) => {
    switch (status) {
      case 'PENDING': return <FaClock className="text-yellow-500" />;
      case 'SCHEDULED': return <FaClock className="text-blue-500" />;
      case 'PUBLISHING': return <FaPlay className="text-indigo-500" />;
      case 'PUBLISHED': return <FaCheck className="text-green-500" />;
      case 'FAILED': return <FaTimes className="text-red-500" />;
      case 'CANCELLED': return <FaPause className="text-gray-500" />;
      default: return <FaClock className="text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'PENDING': return 'bg-yellow-100 text-yellow-800';
      case 'SCHEDULED': return 'bg-blue-100 text-blue-800';
      case 'PUBLISHING': return 'bg-indigo-100 text-indigo-800';
      case 'PUBLISHED': return 'bg-green-100 text-green-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      case 'CANCELLED': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getNetworkIcon = (network) => {
    switch (network) {
      case 'facebook': return '📘';
      case 'linkedin': return '💼';
      case 'x': return '🐦';
      default: return '🌐';
    }
  };

  if (queueLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Chargement de la file d'attente...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header avec actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">File d'attente de publication</h2>
          <div className="flex space-x-2">
            <button 
              onClick={() => setShowGlobalConfig(true)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <FaEdit className="inline mr-2" />
              Config globale
            </button>
          </div>
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{queueMeta.total ?? queueItems.length}</div>
            <div className="text-sm text-gray-600">Total (filtres)</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg" title="Répartition sur la page courante">
            <div className="text-2xl font-bold text-yellow-600">{queueItems.filter(item => item.status === 'PENDING').length}</div>
            <div className="text-sm text-yellow-600">En attente</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg" title="Répartition sur la page courante">
            <div className="text-2xl font-bold text-blue-600">{queueItems.filter(item => item.status === 'SCHEDULED').length}</div>
            <div className="text-sm text-blue-600">Programmés</div>
          </div>
          <div className="text-center p-3 bg-indigo-50 rounded-lg" title="Répartition sur la page courante">
            <div className="text-2xl font-bold text-indigo-600">{queueItems.filter(item => item.status === 'PUBLISHING').length}</div>
            <div className="text-sm text-indigo-600">En cours</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg" title="Répartition sur la page courante">
            <div className="text-2xl font-bold text-green-600">{queueItems.filter(item => item.status === 'PUBLISHED').length}</div>
            <div className="text-sm text-green-600">Publiés</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg" title="Répartition sur la page courante">
            <div className="text-2xl font-bold text-red-600">{queueItems.filter(item => item.status === 'FAILED').length}</div>
            <div className="text-sm text-red-600">Échecs</div>
          </div>
        </div>

        {/* Filtres */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Filtres</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="feedFilter" className="block text-sm font-medium text-gray-700 mb-1">Flux</label>
              <select
                id="feedFilter"
                value={feedFilter}
                onChange={(e) => setFeedFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Tous les flux</option>
                <option value="direct">Posts directs</option>
                {feeds.map((feed) => (
                  <option key={feed.id} value={feed.id}>{feed.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="networkFilter" className="block text-sm font-medium text-gray-700 mb-1">Réseau</label>
              <select
                id="networkFilter"
                value={networkFilter}
                onChange={(e) => setNetworkFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Tous les réseaux</option>
                <option value="x">X (Twitter)</option>
                <option value="linkedin">LinkedIn</option>
                <option value="facebook">Facebook</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={() => {
                  setFeedFilter('');
                  setNetworkFilter('');
                  setPage(1);
                }}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Effacer filtres
              </button>
            </div>
          </div>
        </div>

        {/* Actions globales */}
        <div className="mt-6 flex flex-wrap gap-2">
          <button 
            onClick={handleResumeAll}
            disabled={resumeAllMutation.isLoading}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            <FaPlay className="inline mr-2" />
            {resumeAllMutation.isLoading ? 'Reprise...' : 'Reprendre tout'}
          </button>
          <button 
            onClick={handlePauseAll}
            disabled={pauseAllMutation.isLoading}
            className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50"
          >
            <FaPause className="inline mr-2" />
            {pauseAllMutation.isLoading ? 'Pause...' : 'Pause tout'}
          </button>
          <button 
            onClick={handleResumeSelected}
            disabled={selectedItems.length === 0}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
          >
            <FaPlay className="inline mr-2" />
            Reprendre sélectionnés ({selectedItems.length})
          </button>
          <button 
            onClick={handlePauseSelected}
            disabled={selectedItems.length === 0}
            className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors disabled:opacity-50"
          >
            <FaPause className="inline mr-2" />
            Pause sélectionnés ({selectedItems.length})
          </button>
        </div>
      </div>

      {/* Liste des éléments */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedItems.length === queueItems.length && queueItems.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contenu
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Réseau
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Planifié
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {queueItems.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.id)}
                      onChange={() => handleSelectItem(item.id)}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="max-w-xs">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.content.substring(0, 100)}...
                      </p>
                      <p className="text-xs text-gray-500">Flux #{item.feed_id}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{getNetworkIcon(item.network)}</span>
                      <span className="text-sm font-medium text-gray-900 capitalize">
                        {item.network}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                      {getStatusIcon(item.status)}
                      <span className="ml-1">{item.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.scheduled_at ? new Date(item.scheduled_at).toLocaleString('fr-FR') : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {item.is_paused ? (
                        <button
                          onClick={() => handleResumeItem(item.id)}
                          disabled={resumeItemMutation.isLoading}
                          className="text-green-600 hover:text-green-900 disabled:opacity-50"
                          title="Reprendre"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handlePauseItem(item.id)}
                          disabled={pauseItemMutation.isLoading}
                          className="text-yellow-600 hover:text-yellow-900 disabled:opacity-50"
                          title="Mettre en pause"
                        >
                          <FaPause className="w-4 h-4" />
                        </button>
                      )}
                      
                      {item.status === 'FAILED' && (
                        <button
                          onClick={() => handleRetryItem(item.id)}
                          disabled={retryItemMutation.isLoading}
                          className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                          title="Réessayer"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      )}
                      
                      {!['PUBLISHED', 'CANCELLED'].includes(item.status) && (
                        <button
                          onClick={() => handleCancelItem(item.id)}
                          disabled={cancelItemMutation.isLoading}
                          className="text-red-600 hover:text-red-900 disabled:opacity-50"
                          title="Annuler"
                        >
                          <FaTimes className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {queueMeta.total > 0 && (
          <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
            <Pagination meta={queueMeta} onPageChange={setPage} />
          </div>
        )}
      </div>

      {(queueMeta.total ?? 0) === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FaClock className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun élément dans la file d'attente</h3>
          <p className="mt-1 text-sm text-gray-500">
            Les publications programmées apparaîtront ici.
          </p>
        </div>
      )}

      {/* Modal de configuration globale */}
      {showGlobalConfig && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Configuration globale des publications</h3>
                <button
                  onClick={() => setShowGlobalConfig(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <FaTimes className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {globalConfigs.map((config) => (
                  <div key={config.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-lg font-semibold text-gray-800 capitalize">
                        {config.network === 'x' ? 'X (Twitter)' : config.network}
                      </h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        config.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {config.is_active ? 'Actif' : 'Inactif'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Intervalle (minutes)
                        </label>
                        <input
                          type="number"
                          className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                          defaultValue={config.interval_minutes}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Heures optimales (séparées par des virgules)
                        </label>
                        <input
                          type="text"
                          className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                          defaultValue={config.optimal_times?.join(',') || ''}
                        />
                      </div>
                    </div>

                    <div className="flex space-x-2 mt-4">
                      <button className="flex-1 px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors text-sm">
                        <FaCheck className="inline mr-1" />
                        Sauvegarder
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QueueManagement;
