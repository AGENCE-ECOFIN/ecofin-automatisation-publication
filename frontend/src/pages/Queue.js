import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaPlay, FaClock } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { postsService } from '../services/api';
import { cleanHtmlContent } from '../utils/htmlUtils';

const Queue = () => {
  const [activeTab, setActiveTab] = useState('queue');
  const queryClient = useQueryClient();
  
  // Debug logs pour confirmer le chargement
  console.log('🚀 Queue component loaded!', new Date().toISOString());
  console.log('🔍 Active tab:', activeTab);
  
  

  // Récupérer les posts de la queue (programmés)
  const { data: queueData = [], isLoading: queueLoading, error: queueError } = useQuery('queue', postsService.getQueue, {
    staleTime: 0,
    cacheTime: 0,
  });
  
  // Récupérer les posts directs immédiats
  const { data: directPostsData = [], isLoading: directLoading, error: directError } = useQuery('direct-posts', postsService.getDirectPosts, {
    staleTime: 0,
    cacheTime: 0,
  });
  
  // Utiliser seulement les données de la queue (PublicationQueue)
  const queue = Array.isArray(queueData?.data) ? queueData.data : Array.isArray(queueData) ? queueData : [];
  const directPosts = Array.isArray(directPostsData?.data) ? directPostsData.data : Array.isArray(directPostsData) ? directPostsData : [];
  
  // Debug logs
  console.log('🔍 Queue Debug:', { queue: queue.length, directPosts: directPosts.length, activeTab });
  console.log('📊 Queue data:', queue);
  console.log('📊 Direct posts data:', directPosts);
  
  const isLoading = queueLoading || directLoading;
  const error = queueError || directError;
  
  const publishNowMutation = useMutation(
    (id) => postsService.publishNow(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('queue');
        queryClient.invalidateQueries('direct-posts');
        queryClient.invalidateQueries('history');
      }
    }
  );

  const handlePublishNow = (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir publier ce post maintenant ?')) {
      publishNowMutation.mutate(id);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Gestion des publications</h1>
              <p className="mt-2 text-gray-600">Gérez votre file d'attente de publication et vos posts directs</p>
              <div className="mt-2 p-2 bg-green-100 text-green-800 text-sm rounded">
                ✅ Composant Queue avec onglets chargé - {new Date().toLocaleTimeString()}
              </div>
            </div>
                        <button
                          onClick={() => {
                            queryClient.invalidateQueries('queue');
                            queryClient.invalidateQueries('direct-posts');
                            queryClient.refetchQueries('queue');
                            queryClient.refetchQueries('direct-posts');
                          }}
                          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        >
                          🔄 Rafraîchir
                        </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'queue', label: 'File d\'attente', count: queue.length },
                { id: 'direct', label: 'Posts directs', count: directPosts.length }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-4 text-gray-600">Chargement...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">
                Erreur lors du chargement: {error.message}
              </p>
            </div>
          </div>
        ) : activeTab === 'queue' ? (
          queue.length === 0 ? (
            <div className="text-center py-12">
              <FaClock className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">File d'attente vide</h3>
              <p className="mt-1 text-sm text-gray-500">
                Aucun élément en attente. Allez dans "Brouillons" pour valider des réseaux.
              </p>
            </div>
          ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {queue.map((item) => {
                          const itemStatus = item.status || 'UNKNOWN';
                          
                          return (
                            <div key={item.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                              <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                  <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                                    {item.content.substring(0, 100)}...
                                  </h3>
                                  <p className="text-sm text-gray-500 mt-1">
                                    Réseau: <span className="capitalize font-medium">{item.network === 'x' ? 'X (Twitter)' : item.network}</span>
                                    {item.feed_id === null && (
                                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                        Post direct programmé
                                      </span>
                                    )}
                                  </p>
                                </div>
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  itemStatus === 'SCHEDULED' ? 'bg-blue-100 text-blue-800' :
                                  itemStatus === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                                  itemStatus === 'PUBLISHING' ? 'bg-purple-100 text-purple-800' :
                                  itemStatus === 'PUBLISHED' ? 'bg-green-100 text-green-800' :
                                  itemStatus === 'FAILED' ? 'bg-red-100 text-red-800' :
                                  itemStatus === 'CANCELLED' ? 'bg-gray-100 text-gray-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {itemStatus === 'SCHEDULED' ? 'Programmé' :
                                   itemStatus === 'PENDING' ? 'En attente' :
                                   itemStatus === 'PUBLISHING' ? 'En cours' :
                                   itemStatus === 'PUBLISHED' ? 'Publié' :
                                   itemStatus === 'FAILED' ? 'Échec' :
                                   itemStatus === 'CANCELLED' ? 'Annulé' :
                                   'Inconnu'}
                                </span>
                              </div>

                              <p className="text-gray-600 text-sm line-clamp-3 mb-4">
                                {item.content}
                              </p>

                              <div className="mb-4">
                                <h4 className="text-sm font-medium text-gray-700 mb-2">Planification:</h4>
                                <p className="text-sm text-gray-600">
                                  {item.scheduled_at ? 
                                    `Programmé le: ${format(new Date(item.scheduled_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}` :
                                    'Pas de date programmée'
                                  }
                                </p>
                              </div>

                              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                                <div className="text-xs text-gray-500">
                                  <p>Créé le: {format(new Date(item.created_at), 'dd/MM à HH:mm', { locale: fr })}</p>
                                  {item.target_page_id && (
                                    <p>Page ID: {item.target_page_id}</p>
                                  )}
                                  {item.published_at && (
                                    <p>Publié le: {format(new Date(item.published_at), 'dd/MM à HH:mm', { locale: fr })}</p>
                                  )}
                                </div>
                                
                                {/* Afficher les actions seulement pour les posts non publiés */}
                                {itemStatus !== 'PUBLISHED' && itemStatus !== 'FAILED' && (
                                  <div className="flex space-x-2">
                                    <button
                                      onClick={() => handlePublishNow(item.id)}
                                      disabled={publishNowMutation.isLoading}
                                      className="inline-flex items-center px-3 py-1 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                                    >
                                      <FaPlay className="w-3 h-3 mr-1" />
                                      Publier
                                    </button>
                                  </div>
                                )}
                                
                                {/* Afficher le lien de publication pour les posts publiés */}
                                {itemStatus === 'PUBLISHED' && item.publication_url && (
                                  <div className="flex space-x-2">
                                    <a
                                      href={item.publication_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                                    >
                                      Voir la publication
                                    </a>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
          )
        ) : (
          directPosts.length === 0 ? (
            <div className="text-center py-12">
              <FaClock className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun post direct</h3>
              <p className="mt-1 text-sm text-gray-500">
                Aucun post direct créé pour le moment.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {directPosts.map((post) => {
                const postStatus = post.status || 'UNKNOWN';
                
                return (
                  <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                          {post.title}
                        </h3>
                        <p className="text-sm text-gray-500 mt-1">
                          Réseau: <span className="capitalize font-medium">{post.network === 'x' ? 'X (Twitter)' : post.network}</span>
                          <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                            Post direct
                          </span>
                        </p>
                      </div>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        postStatus === 'published' ? 'bg-green-100 text-green-800' :
                        postStatus === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {postStatus === 'published' ? 'Publié' :
                         postStatus === 'failed' ? 'Échec' :
                         'Inconnu'}
                      </span>
                    </div>

                    <p className="text-gray-600 text-sm line-clamp-3 mb-4">
                      {post.content}
                    </p>

                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Publication:</h4>
                      <p className="text-sm text-gray-600">
                        {post.published_at ? 
                          `Publié le: ${format(new Date(post.published_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}` :
                          'Non publié'
                        }
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                      <div className="text-xs text-gray-500">
                        <p>Créé le: {format(new Date(post.created_at), 'dd/MM à HH:mm', { locale: fr })}</p>
                        {post.publication_url && (
                          <p>URL: {post.publication_url}</p>
                        )}
                      </div>
                      
                      {/* Afficher le lien de publication pour les posts publiés */}
                      {postStatus === 'published' && post.publication_url && (
                        <div className="flex space-x-2">
                          <a
                            href={post.publication_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                          >
                            Voir la publication
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default Queue;