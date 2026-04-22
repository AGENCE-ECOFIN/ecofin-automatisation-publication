import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaTimes } from 'react-icons/fa';
import { postsService, DEFAULT_PAGE_SIZE } from '../services/api';
import { log } from '../utils/logger';
import PostFeedCard from '../components/PostFeedCard';
import Pagination from '../components/Pagination';

const Posts = () => {
  const [activeTab, setActiveTab] = useState('drafts');
  const [pageDrafts, setPageDrafts] = useState(1);
  const [pageValidated, setPageValidated] = useState(1);
  const [pageRejected, setPageRejected] = useState(1);
  const [selectedPost, setSelectedPost] = useState(null);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generatedContent, setGeneratedContent] = useState({});
  const [sourceFilter, setSourceFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const queryClient = useQueryClient();

  const { data: sourceHintsRes } = useQuery(
    'posts-source-hints',
    () => postsService.getSourceHints(),
    { staleTime: 5 * 60 * 1000 }
  );
  const sourceSuggestions = sourceHintsRes?.data?.sources ?? [];

  const listQueryOptions = {
    search: searchTerm.trim() || undefined,
    source: sourceFilter.trim() || undefined,
    createdDate: dateFilter || undefined,
  };

  useEffect(() => {
    setPageDrafts(1);
    setPageValidated(1);
    setPageRejected(1);
  }, [searchTerm, sourceFilter, dateFilter]);

  // Queries (pagination + filtres côté serveur)
  const { data: draftQuery, isLoading: draftsLoading, error: draftsError } = useQuery(
    ['drafts', pageDrafts, searchTerm, sourceFilter, dateFilter],
    () =>
      postsService.getDrafts({
        page: pageDrafts,
        pageSize: DEFAULT_PAGE_SIZE,
        ...listQueryOptions,
      }),
    { select: (response) => ({ items: response.data || [], meta: response.pagination || {} }) }
  );

  const { data: validatedQuery, isLoading: validatedLoading, error: validatedError } = useQuery(
    ['validated', pageValidated, searchTerm, sourceFilter, dateFilter],
    () =>
      postsService.getValidated({
        page: pageValidated,
        pageSize: DEFAULT_PAGE_SIZE,
        ...listQueryOptions,
      }),
    { select: (response) => ({ items: response.data || [], meta: response.pagination || {} }) }
  );

  const { data: rejectedQuery, isLoading: rejectedLoading, error: rejectedError } = useQuery(
    ['rejected', pageRejected, searchTerm, sourceFilter, dateFilter],
    () =>
      postsService.getRejected({
        page: pageRejected,
        pageSize: DEFAULT_PAGE_SIZE,
        ...listQueryOptions,
      }),
    { select: (response) => ({ items: response.data || [], meta: response.pagination || {} }) }
  );

  const safeDrafts = draftQuery?.items || [];
  const safeValidated = validatedQuery?.items || [];
  const safeRejected = rejectedQuery?.items || [];
  const draftMeta = draftQuery?.meta || {};
  const validatedMeta = validatedQuery?.meta || {};
  const rejectedMeta = rejectedQuery?.meta || {};

  const currentPaginationMeta =
    activeTab === 'drafts' ? draftMeta : activeTab === 'validated' ? validatedMeta : rejectedMeta;

  const handlePageChange = (p) => {
    if (activeTab === 'drafts') setPageDrafts(p);
    else if (activeTab === 'validated') setPageValidated(p);
    else setPageRejected(p);
  };

  const isLoading = draftsLoading || validatedLoading || rejectedLoading;

  // Mutations
  const saveMutation = useMutation(
    ({ id, data }) => postsService.updatePost(id, data),
    {
      onSuccess: (data) => {
        log.debug('Posts', 'Post sauvegardé', { id: data?.data?.id });
        queryClient.invalidateQueries(['drafts']);
        setIsModalOpen(false);
      },
      onError: (error) => {
        log.error('Posts', 'Sauvegarde post', { message: error?.message });
      }
    }
  );

  // Mutations pour la validation granulaire
  const validateNetworkMutation = useMutation(
    ({ postId, network }) => {
      log.debug('Posts', 'Validation réseau', { postId, network });
      return postsService.validateNetwork(postId, network);
    },
    {
      onSuccess: (data) => {
        log.debug('Posts', 'Réseau validé', { postId: data?.data?.id });
        // Forcer le rechargement des données
        queryClient.invalidateQueries(['drafts']);
        queryClient.invalidateQueries(['validated']);
        queryClient.invalidateQueries(['rejected']);
        queryClient.invalidateQueries('queue');
        queryClient.refetchQueries(['drafts']);
      },
      onError: (error) => {
        log.error('Posts', 'Validation réseau', { message: error?.message });
      }
    }
  );

  const rejectNetworkMutation = useMutation(
    ({ postId, network, rejectionReason }) => {
      log.debug('Posts', 'Rejet réseau', { postId, network });
      return postsService.rejectNetwork(postId, network, rejectionReason);
    },
    {
      onSuccess: (data) => {
        log.debug('Posts', 'Réseau rejeté', { postId: data?.data?.id });
        // Forcer le rechargement des données
        queryClient.invalidateQueries(['drafts']);
        queryClient.invalidateQueries(['validated']);
        queryClient.invalidateQueries(['rejected']);
        queryClient.invalidateQueries('queue');
        queryClient.refetchQueries(['drafts']);
      },
      onError: (error) => {
        log.error('Posts', 'Rejet réseau', { message: error?.message });
      }
    }
  );

  const restoreNetworkMutation = useMutation(
    ({ postId, network }) => {
      log.debug('Posts', 'Restauration réseau', { postId, network });
      return postsService.restoreNetwork(postId, network);
    },
    {
      onSuccess: (data) => {
        log.debug('Posts', 'Réseau restauré', { postId: data?.data?.id });
        queryClient.invalidateQueries(['drafts']);
        queryClient.invalidateQueries(['validated']);
        queryClient.invalidateQueries(['rejected']);
        queryClient.invalidateQueries('queue');
        queryClient.refetchQueries(['drafts']);
      },
      onError: (error) => {
        log.error('Posts', 'Restauration réseau', { message: error?.message });
      }
    }
  );

  // Mutation pour le rejet global d'un post
  const rejectPostMutation = useMutation(
    ({ postId, rejectionReason }) => {
      log.debug('Posts', 'Rejet global post', { postId });
      return postsService.rejectPost(postId, rejectionReason);
    },
    {
      onSuccess: (data) => {
        log.debug('Posts', 'Post rejeté globalement', { postId: data?.data?.id });
        // Forcer le rechargement des données
        queryClient.invalidateQueries(['drafts']);
        queryClient.invalidateQueries(['validated']);
        queryClient.invalidateQueries(['rejected']);
        queryClient.invalidateQueries('queue');
        queryClient.refetchQueries(['drafts']);
        alert('Post rejeté globalement avec succès (tous les réseaux rejetés et retirés de la queue)');
      },
      onError: (error) => {
        log.error('Posts', 'Rejet global', { message: error?.message });
        alert('Erreur lors du rejet global: ' + (error.response?.data?.detail || error.message));
      }
    }
  );

  // Mutation pour la restauration globale d'un post
  const restorePostMutation = useMutation(
    (postId) => {
      log.debug('Posts', 'Restauration globale', { postId });
      return postsService.restorePost(postId);
    },
    {
      onSuccess: (data) => {
        log.debug('Posts', 'Post restauré globalement', { postId: data?.data?.id });
        // Forcer le rechargement des données
        queryClient.invalidateQueries(['drafts']);
        queryClient.invalidateQueries(['validated']);
        queryClient.invalidateQueries(['rejected']);
        queryClient.invalidateQueries('queue');
        queryClient.refetchQueries(['drafts']);
        queryClient.refetchQueries(['rejected']);
        alert('Post restauré globalement avec succès (tous les réseaux rejetés restaurés en brouillon)');
      },
      onError: (error) => {
        log.error('Posts', 'Restauration globale', { message: error?.message });
        alert('Erreur lors de la restauration globale: ' + (error.response?.data?.detail || error.message));
      }
    }
  );

  // Handlers
  const handleViewPost = (post, network = null) => {
    setSelectedPost(post);
    setSelectedNetwork(network);
    setGeneratedContent(post.generated_content || {});
    setIsModalOpen(true);
  };

  const handleEditPost = (post, network) => {
    setSelectedPost(post);
    setSelectedNetwork(network);
    setGeneratedContent(post.generated_content || {});
    setIsModalOpen(true);
  };

  const handleSaveNetworkContent = (postId, network, content) => {
    // Utiliser le contenu actuel du post pour éviter la perte des autres réseaux
    // Si le post sélectionné existe, utiliser son generated_content, sinon utiliser l'état local
    const currentPost = selectedPost || safeDrafts.find(p => p.id === postId) || 
                        safeValidated.find(p => p.id === postId) || 
                        safeRejected.find(p => p.id === postId);
    const currentContent = currentPost?.generated_content || generatedContent || {};
    const updatedContent = { ...currentContent, [network]: content };
    setGeneratedContent(updatedContent);
    saveMutation.mutate({ 
      id: postId, 
      data: { generated_content: updatedContent } 
    });
  };


  // Handlers pour la validation granulaire
  const handleValidateNetwork = (postId, network) => {
    validateNetworkMutation.mutate({ postId, network });
  };

  const handleRejectNetwork = (postId, network, rejectionReason) => {
    rejectNetworkMutation.mutate({ postId, network, rejectionReason });
  };

  const handleRestoreNetwork = (postId, network) => {
    // Créer une mutation spécifique pour la restauration
    restoreNetworkMutation.mutate({ postId, network });
  };

  const handleRejectPost = (postId) => {
    if (window.confirm('Êtes-vous sûr de vouloir rejeter globalement cet article ?\n\nTous les réseaux seront rejetés et retirés de la queue de publication.')) {
      // Pas besoin de motif - envoyer null ou un objet vide
      rejectPostMutation.mutate({ 
        postId, 
        rejectionReason: null 
      });
    }
  };

  const handleRestorePost = (postId) => {
    if (window.confirm('Êtes-vous sûr de vouloir restaurer globalement cet article ?\n\nTous les réseaux rejetés seront restaurés en brouillon.')) {
      restorePostMutation.mutate(postId);
    }
  };

  // Pas besoin de séparer par réseau, on garde les posts groupés par feed

  const getCurrentPosts = () => {
    if (activeTab === 'drafts') return safeDrafts;
    if (activeTab === 'validated') return safeValidated;
    return safeRejected;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gestion des Posts</h1>
          <p className="mt-2 text-gray-600">Gérez vos posts par réseau social</p>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'drafts', label: 'Brouillons', count: draftMeta.total ?? safeDrafts.length },
                { id: 'validated', label: 'Validés', count: validatedMeta.total ?? safeValidated.length },
                { id: 'rejected', label: 'Rejetés', count: rejectedMeta.total ?? safeRejected.length }
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

        {/* Filters */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recherche
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Rechercher dans les posts..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <input
              type="text"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              list="posts-source-hints-list"
              placeholder="Choisir ou saisir un nom de flux RSS"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <datalist id="posts-source-hints-list">
              {sourceSuggestions.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
            <p className="mt-1 text-xs text-gray-500">
              Liste des flux créés dans Flux ; le filtre porte sur l&apos;URL source ou le nom du flux.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date
            </label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm('');
                setSourceFilter('');
                setDateFilter('');
              }}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Effacer les filtres
            </button>
          </div>
        </div>

        {/* Posts List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-4 text-gray-600">Chargement des posts...</p>
          </div>
        ) : draftsError || validatedError || rejectedError ? (
          <div className="text-center py-12">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">
                Erreur lors du chargement des posts: {draftsError?.message || validatedError?.message || rejectedError?.message}
              </p>
            </div>
          </div>
        ) : getCurrentPosts().length === 0 ? (
          <div className="text-center py-12">
            <div className="bg-gray-50 rounded-lg p-8">
              <p className="text-gray-500 text-lg">Aucun post trouvé</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {getCurrentPosts().map((post) => (
              <PostFeedCard
                key={post.id}
                post={post}
                onView={handleViewPost}
                onValidate={handleValidateNetwork}
                onReject={handleRejectNetwork}
                onRejectGlobal={handleRejectPost}
                onRestoreGlobal={handleRestorePost}
                onEdit={handleEditPost}
                onSave={handleSaveNetworkContent}
                onCancel={() => setIsModalOpen(false)}
                onRestore={handleRestoreNetwork}
              />
            ))}
          </div>
        )}

        {!isLoading && !draftsError && !validatedError && !rejectedError && getCurrentPosts().length > 0 && (
          <Pagination meta={currentPaginationMeta} onPageChange={handlePageChange} />
        )}

        {/* Modal */}
        {isModalOpen && selectedPost && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-start mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedPost.title}
                    {selectedNetwork && (
                      <span className="ml-2 text-lg font-normal text-gray-600">
                        - {selectedNetwork === 'x' ? 'X (Twitter)' : selectedNetwork}
                      </span>
                    )}
                  </h2>
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <FaTimes className="text-xl" />
                  </button>
                </div>

                {/* Post Content avec images */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Contenu original:</h3>
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <div 
                      className="text-gray-800 prose max-w-none"
                      dangerouslySetInnerHTML={{ 
                        __html: selectedPost.content 
                      }}
                    />
                  </div>
                </div>

                {/* Source Info */}
                {selectedPost.source_url && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Source:</h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <a 
                        href={selectedPost.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        {selectedPost.source_url}
                      </a>
                    </div>
                  </div>
                )}

                {/* Contenu généré pour le réseau spécifique ou tous les réseaux */}
                {selectedPost.generated_content && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      {selectedNetwork ? `Contenu généré pour ${selectedNetwork === 'x' ? 'X (Twitter)' : selectedNetwork}:` : 'Contenu généré:'}
                    </h3>
                    <div className="space-y-4">
                      {selectedNetwork ? (
                        // Affichage pour un réseau spécifique
                        <div className="border rounded-lg p-4">
                          <p className="text-gray-800 whitespace-pre-wrap">
                            {selectedPost.generated_content[selectedNetwork] || 'Aucun contenu généré pour ce réseau'}
                          </p>
                        </div>
                      ) : (
                        // Affichage pour tous les réseaux
                        Object.entries(selectedPost.generated_content).map(([network, content]) => (
                          <div key={network} className="border rounded-lg p-4">
                            <h4 className="font-medium text-gray-900 mb-2 capitalize">
                              {network === 'x' ? 'X (Twitter)' : network}
                            </h4>
                            <p className="text-gray-800 whitespace-pre-wrap">{content}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {/* Statuts de validation */}
                {selectedPost.network_validations && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Statuts de validation:</h3>
                    <div className="space-y-2">
                      {selectedNetwork ? (
                        // Affichage pour un réseau spécifique
                        <div className="flex items-center space-x-2">
                          <span className="font-medium capitalize">{selectedNetwork}:</span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            selectedPost.network_validations[selectedNetwork]?.status === 'validated' ? 'bg-green-100 text-green-800' :
                            selectedPost.network_validations[selectedNetwork]?.status === 'rejected' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {selectedPost.network_validations[selectedNetwork]?.status || 'draft'}
                          </span>
                          {selectedPost.network_validations[selectedNetwork]?.rejection_reason && (
                            <span className="text-sm text-gray-600">
                              ({selectedPost.network_validations[selectedNetwork].rejection_reason})
                            </span>
                          )}
                        </div>
                      ) : (
                        // Affichage pour tous les réseaux
                        Object.entries(selectedPost.network_validations).map(([network, validation]) => (
                          <div key={network} className="flex items-center space-x-2">
                            <span className="font-medium capitalize">{network}:</span>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              validation.status === 'validated' ? 'bg-green-100 text-green-800' :
                              validation.status === 'rejected' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {validation.status}
                            </span>
                            {validation.rejection_reason && (
                              <span className="text-sm text-gray-600">
                                ({validation.rejection_reason})
                              </span>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  >
                    Fermer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Posts;