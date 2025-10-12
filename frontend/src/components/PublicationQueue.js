import React, { useState } from 'react';
import { FaPlay, FaPause, FaTrash, FaClock, FaCheck, FaTimes, FaExclamationTriangle, FaPlus } from 'react-icons/fa';

const PublicationQueue = ({ queueItems, onPauseItem, onResumeItem, onCancelItem, onRetryItem, onAddValidatedPosts, isAddingValidatedPosts }) => {
  // S'assurer que queueItems est toujours un tableau
  const queueItemsList = Array.isArray(queueItems) ? queueItems : [];
  const [filters, setFilters] = useState({
    status: 'all',
    network: 'all',
    feed: 'all'
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <FaClock className="text-yellow-500" />;
      case 'scheduled': return <FaClock className="text-blue-500" />;
      case 'publishing': return <FaPlay className="text-indigo-500" />;
      case 'published': return <FaCheck className="text-green-500" />;
      case 'failed': return <FaTimes className="text-red-500" />;
      case 'cancelled': return <FaExclamationTriangle className="text-gray-500" />;
      default: return <FaClock className="text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'publishing': return 'bg-indigo-100 text-indigo-800';
      case 'published': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
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

  const filteredItems = queueItemsList.filter(item => {
    if (filters.status !== 'all' && item.status !== filters.status) return false;
    if (filters.network !== 'all' && item.network !== filters.network) return false;
    if (filters.feed !== 'all' && item.feed_id !== parseInt(filters.feed)) return false;
    return true;
  });

  const statusCounts = queueItemsList.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header avec statistiques */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">File d'attente de publication</h2>
          <div className="flex space-x-2">
            {onAddValidatedPosts && (
              <button 
                onClick={onAddValidatedPosts}
                disabled={isAddingValidatedPosts}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                <FaPlus className="inline mr-2" />
                {isAddingValidatedPosts ? 'Ajout...' : 'Ajouter posts validés'}
              </button>
            )}
            <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              <FaPlay className="inline mr-2" />
              Reprendre tout
            </button>
            <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors">
              <FaPause className="inline mr-2" />
              Pause tout
            </button>
          </div>
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{queueItemsList.length}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{statusCounts.pending || 0}</div>
            <div className="text-sm text-yellow-600">En attente</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{statusCounts.scheduled || 0}</div>
            <div className="text-sm text-blue-600">Programmés</div>
          </div>
          <div className="text-center p-3 bg-indigo-50 rounded-lg">
            <div className="text-2xl font-bold text-indigo-600">{statusCounts.publishing || 0}</div>
            <div className="text-sm text-indigo-600">En cours</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{statusCounts.published || 0}</div>
            <div className="text-sm text-green-600">Publiés</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{statusCounts.failed || 0}</div>
            <div className="text-sm text-red-600">Échecs</div>
          </div>
        </div>
      </div>

      {/* Filtres */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Statut</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">Tous les statuts</option>
              <option value="pending">En attente</option>
              <option value="scheduled">Programmé</option>
              <option value="publishing">En cours</option>
              <option value="published">Publié</option>
              <option value="failed">Échec</option>
              <option value="cancelled">Annulé</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Réseau</label>
            <select
              value={filters.network}
              onChange={(e) => setFilters(prev => ({ ...prev, network: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">Tous les réseaux</option>
              <option value="facebook">Facebook</option>
              <option value="linkedin">LinkedIn</option>
              <option value="x">X (Twitter)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Flux</label>
            <select
              value={filters.feed}
              onChange={(e) => setFilters(prev => ({ ...prev, feed: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">Tous les flux</option>
              {/* Ici on pourrait ajouter la liste des flux */}
            </select>
          </div>
        </div>
      </div>

      {/* Liste des éléments */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
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
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
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
                      <span className="ml-1 capitalize">{item.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.scheduled_at ? new Date(item.scheduled_at).toLocaleString('fr-FR') : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {item.status === 'pending' && (
                        <button
                          onClick={() => onPauseItem(item.id)}
                          className="text-yellow-600 hover:text-yellow-900"
                          title="Mettre en pause"
                        >
                          <FaPause className="w-4 h-4" />
                        </button>
                      )}
                      {item.status === 'paused' && (
                        <button
                          onClick={() => onResumeItem(item.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Reprendre"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      )}
                      {item.status === 'failed' && (
                        <button
                          onClick={() => onRetryItem(item.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Réessayer"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => onCancelItem(item.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Annuler"
                      >
                        <FaTrash className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FaClock className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun élément dans la file d'attente</h3>
          <p className="mt-1 text-sm text-gray-500">
            Les publications programmées apparaîtront ici.
          </p>
        </div>
      )}
    </div>
  );
};

export default PublicationQueue;
