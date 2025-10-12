import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { FaCheck, FaTimes, FaExternalLinkAlt, FaCalendarAlt } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { publicationQueueService, postsService } from '../services/api';
import { cleanHtmlContent } from '../utils/htmlUtils';
import SocialNetworkIcon from '../components/SocialNetworkIcon';

const History = () => {
  const [networkFilter, setNetworkFilter] = useState('');
  const [feedFilter, setFeedFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Récupérer tous les items publiés et échoués
  const { data: publishedData = [], isLoading: loadingPublished } = useQuery('history-published', () => 
    publicationQueueService.getQueue({ status: 'PUBLISHED' })
  );
  
  const { data: failedData = [], isLoading: loadingFailed } = useQuery('history-failed', () => 
    publicationQueueService.getQueue({ status: 'FAILED' })
  );
  
  // Récupérer les feeds pour les filtres
  const { data: feedsData } = useQuery('feeds', () => postsService.getFeeds());
  const feeds = feedsData?.data || [];
  
  const isLoading = loadingPublished || loadingFailed;
  const error = null;
  
  // Combiner les deux listes
  const published = Array.isArray(publishedData?.data) ? publishedData.data : [];
  const failed = Array.isArray(failedData?.data) ? failedData.data : [];
  const allHistory = [...published, ...failed].sort((a, b) => {
    const dateA = new Date(a.published_at || a.created_at);
    const dateB = new Date(b.published_at || b.created_at);
    return dateB - dateA; // Plus récent en premier
  });
  
  // Appliquer les filtres
  const history = allHistory.filter(item => {
    if (networkFilter && item.network !== networkFilter) return false;
    if (feedFilter && item.feed_id !== parseInt(feedFilter)) return false;
    if (statusFilter && item.status !== statusFilter) return false;
    return true;
  });

  // Debug logs (réduits)
  console.log('🔍 History Debug:', {
    historyCount: history?.length || 0,
    isLoading,
    hasError: !!error
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Historique</h1>
          <p className="mt-2 text-gray-600">Historique des publications</p>
        </div>

        {/* Filtres */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Filtres</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="feedFilter" className="block text-sm font-medium text-gray-700 mb-1">Flux</label>
              <select
                id="feedFilter"
                value={feedFilter}
                onChange={(e) => setFeedFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Tous les flux</option>
                {feeds.map(feed => (
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
                <option value="facebook">Facebook</option>
                <option value="linkedin">LinkedIn</option>
                <option value="x">X (Twitter)</option>
              </select>
            </div>

            <div>
              <label htmlFor="statusFilter" className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
              <select
                id="statusFilter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Tous les statuts</option>
                <option value="PUBLISHED">✅ Publiés</option>
                <option value="FAILED">❌ Échecs</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={() => {
                  setFeedFilter('');
                  setNetworkFilter('');
                  setStatusFilter('');
                }}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Réinitialiser
              </button>
            </div>
          </div>
          
          {/* Statistiques */}
          <div className="mt-4 flex items-center space-x-6 text-sm text-gray-600">
            <span className="font-medium">
              📊 Total : <strong className="text-gray-900">{history.length}</strong>
            </span>
            <span>
              ✅ Publiés : <strong className="text-green-600">{allHistory.filter(i => i.status === 'PUBLISHED').length}</strong>
            </span>
            <span>
              ❌ Échecs : <strong className="text-red-600">{allHistory.filter(i => i.status === 'FAILED').length}</strong>
            </span>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-4 text-gray-600">Chargement de l'historique...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">
                Erreur lors du chargement: {error.message}
              </p>
            </div>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-12">
            <FaCalendarAlt className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun historique</h3>
            <p className="mt-1 text-sm text-gray-500">Aucune publication dans l'historique.</p>
          </div>
        ) : (
          <div className="bg-white shadow-sm rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Publications récentes</h2>
            </div>
            
            <div className="divide-y divide-gray-200">
              {history.map((item) => (
                <div key={item.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        item.status === 'PUBLISHED' ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {item.status === 'PUBLISHED' ? (
                          <FaCheck className="w-5 h-5 text-green-600" />
                        ) : (
                          <FaTimes className="w-5 h-5 text-red-600" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-sm font-medium text-gray-900 capitalize">
                            {item.network}
                          </h3>
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            item.status === 'PUBLISHED'
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {item.status === 'PUBLISHED' ? 'Publié' : 'Échec'}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-500 mt-1">
                          {item.published_at ? (
                            <>
                              Publié le: {format(new Date(item.published_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}
                            </>
                          ) : item.scheduled_at ? (
                            <>
                              Programmé pour: {format(new Date(item.scheduled_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}
                            </>
                          ) : (
                            'Date inconnue'
                          )}
                        </p>
                        
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {item.content?.substring(0, 100)}...
                        </p>
                        
                        {item.error_message && (
                          <p className="text-sm text-red-600 mt-1">
                            Erreur: {item.error_message}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {item.publication_url && (
                        <a
                          href={item.publication_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-1 text-sm text-primary hover:text-primary/80 transition-colors"
                        >
                          <FaExternalLinkAlt className="w-3 h-3 mr-1" />
                          Voir
                        </a>
                      )}
                      
                      <span className="text-xs text-gray-500">
                        {item.feed_id ? `Flux #${item.feed_id}` : '📤 Post direct'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;