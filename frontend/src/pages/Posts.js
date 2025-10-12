import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaEye, FaCheck, FaTimes, FaSave, FaUndo } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { postsService } from '../services/api';
import { cleanHtmlContent } from '../utils/htmlUtils';

const Posts = () => {
  const [activeTab, setActiveTab] = useState('drafts');
  const [selectedPost, setSelectedPost] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generatedContent, setGeneratedContent] = useState({});
  const [sourceFilter, setSourceFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const queryClient = useQueryClient();

  const { data: draftsData = [], isLoading: draftsLoading, error: draftsError } = useQuery('drafts', postsService.getDrafts);
  const { data: validatedData = [], isLoading: validatedLoading, error: validatedError } = useQuery('validated', postsService.getValidated);
  const { data: rejectedData = [], isLoading: rejectedLoading, error: rejectedError } = useQuery('rejected', postsService.getRejected);

  // S'assurer que les données sont toujours des tableaux
  const safeDrafts = Array.isArray(draftsData?.data) ? draftsData.data : Array.isArray(draftsData) ? draftsData : [];
  const safeValidated = Array.isArray(validatedData?.data) ? validatedData.data : Array.isArray(validatedData) ? validatedData : [];
  const safeRejected = Array.isArray(rejectedData?.data) ? rejectedData.data : Array.isArray(rejectedData) ? rejectedData : [];
  
  // Debug logs (réduits)
  console.log('🔍 Posts Debug:', {
    draftsCount: safeDrafts.length,
    validatedCount: safeValidated.length,
    rejectedCount: safeRejected.length,
    draftsLoading,
    validatedLoading,
    rejectedLoading
  });

  const validateMutation = useMutation(
    ({ id, data }) => postsService.validatePost(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('drafts');
        queryClient.invalidateQueries('validated');
        queryClient.invalidateQueries('queue');
        setIsModalOpen(false);
      }
    }
  );

  const rejectMutation = useMutation(
    (id) => postsService.rejectPost(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('drafts');
        queryClient.invalidateQueries('rejected');
        setIsModalOpen(false);
      }
    }
  );

  const saveMutation = useMutation(
    ({ id, data }) => postsService.updatePost(id, data),
    {
      onSuccess: (data) => {
        console.log('✅ Post sauvegardé avec succès:', data);
        queryClient.invalidateQueries('drafts');
        setIsModalOpen(false);
      },
      onError: (error) => {
        console.error('❌ Erreur lors de la sauvegarde:', error);
      }
    }
  );

  const restoreMutation = useMutation(
    (id) => postsService.restorePost(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('drafts');
        queryClient.invalidateQueries('rejected');
      }
    }
  );

  const handleViewPost = (post) => {
    setSelectedPost(post);
    setGeneratedContent(post.generated_content || {});
    setIsModalOpen(true);
  };

  const handleValidatePost = () => {
    if (selectedPost) {
      validateMutation.mutate({
        id: selectedPost.id,
        data: { generated_content: generatedContent }
      });
    }
  };

  const handleRejectPost = (postId) => {
    if (window.confirm('Êtes-vous sûr de vouloir rejeter ce post ?')) {
      rejectMutation.mutate(postId);
    }
  };

  const handleContentChange = (network, content) => {
    setGeneratedContent(prev => ({
      ...prev,
      [network]: content
    }));
  };

  const handleSavePost = () => {
    if (selectedPost) {
      const data = {
        generated_content: generatedContent
      };
      console.log('🔧 Sauvegarde du post:', { id: selectedPost.id, data });
      saveMutation.mutate({ id: selectedPost.id, data });
    }
  };

  const handleRestorePost = (postId) => {
    if (window.confirm('Êtes-vous sûr de vouloir remettre ce post en brouillon ?')) {
      restoreMutation.mutate(postId);
    }
  };

  // Fonction de filtrage
  const filterPosts = (posts) => {
    return posts.filter(post => {
      // Filtre par terme de recherche
      if (searchTerm && !post.title.toLowerCase().includes(searchTerm.toLowerCase()) && 
          !post.content.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // Filtre par source
      if (sourceFilter && post.source_url && !post.source_url.includes(sourceFilter)) {
        return false;
      }
      
      // Filtre par date
      if (dateFilter) {
        const postDate = new Date(post.created_at);
        const filterDate = new Date(dateFilter);
        if (postDate.toDateString() !== filterDate.toDateString()) {
          return false;
        }
      }
      
      return true;
    });
  };

  const getCurrentPosts = () => {
    const posts = activeTab === 'drafts' ? safeDrafts : 
                  activeTab === 'validated' ? safeValidated : 
                  activeTab === 'rejected' ? safeRejected : [];
    return filterPosts(posts);
  };

  // Obtenir les sources uniques pour le filtre
  const getUniqueSources = () => {
    const allPosts = [...safeDrafts, ...safeValidated, ...safeRejected];
    const sources = [...new Set(allPosts.map(post => {
      if (post.source_url) {
        try {
          return new URL(post.source_url).hostname;
        } catch {
          return post.source_url;
        }
      }
      return null;
    }).filter(Boolean))];
    return sources;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Posts</h1>
          <p className="mt-2 text-gray-600">Gérez vos posts générés automatiquement</p>
        </div>

        {/* Filtres */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Filtres</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Recherche */}
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Recherche</label>
              <input
                type="text"
                id="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Titre ou contenu..."
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Filtre par source */}
            <div>
              <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-1">Source</label>
              <select
                id="source"
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Toutes les sources</option>
                {getUniqueSources().map(source => (
                  <option key={source} value={source}>{source}</option>
                ))}
              </select>
            </div>

            {/* Filtre par date */}
            <div>
              <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input
                type="date"
                id="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Bouton reset */}
            <div className="flex items-end">
              <button
                onClick={() => {
                  setSearchTerm('');
                  setSourceFilter('');
                  setDateFilter('');
                }}
                className="w-full px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors duration-200"
              >
                Réinitialiser
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('drafts')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'drafts'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Brouillons ({filterPosts(safeDrafts).length}/{safeDrafts.length})
            </button>
            <button
              onClick={() => setActiveTab('validated')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'validated'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Validés ({filterPosts(safeValidated).length}/{safeValidated.length})
            </button>
            <button
              onClick={() => setActiveTab('rejected')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'rejected'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Rejetés ({filterPosts(safeRejected).length}/{safeRejected.length})
            </button>
          </nav>
        </div>

        {/* Content */}
        {draftsLoading || validatedLoading || rejectedLoading ? (
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {getCurrentPosts().map((post) => (
              <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                {/* Actions */}
                <div className="flex justify-end space-x-2 mb-4">
                  <button
                    onClick={() => handleViewPost(post)}
                    className="p-2 text-gray-400 hover:text-primary transition-colors"
                    title="Voir le post"
                  >
                    <FaEye />
                  </button>
                  {post.status === 'draft' && (
                    <>
                      <button
                        onClick={() => {
                          setSelectedPost(post);
                          setGeneratedContent(post.generated_content || {});
                          setIsModalOpen(true);
                        }}
                        className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                        title="Valider le post"
                      >
                        <FaCheck />
                      </button>
                      <button
                        onClick={() => handleRejectPost(post.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        title="Rejeter le post"
                      >
                        <FaTimes />
                      </button>
                    </>
                  )}
                  {post.status === 'rejected' && (
                    <button
                      onClick={() => handleRestorePost(post.id)}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Remettre en brouillon"
                    >
                      <FaUndo />
                    </button>
                  )}
                </div>

                {/* Content */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                      {post.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      post.status === 'draft' 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : post.status === 'validated'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {post.status === 'draft' ? 'Brouillon' : 
                       post.status === 'validated' ? 'Validé' : 'Rejeté'}
                    </span>
                  </div>

                  {/* Image si disponible */}
                  {post.source_image && (
                    <div className="mb-3">
                      <img 
                        src={post.source_image} 
                        alt="Article" 
                        className="w-full h-32 object-cover rounded-lg"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}

                  <p className="text-gray-600 text-sm line-clamp-3">
                    {cleanHtmlContent(post.content, 200)}
                  </p>

                  <div className="text-xs text-gray-500 space-y-1">
                    <p>Créé le: {format(new Date(post.created_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}</p>
                    {post.validated_at && (
                      <p>Validé le: {format(new Date(post.validated_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}</p>
                    )}
                    {post.source_url && (
                      <p>
                        Source: <a href={post.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Voir l'article</a>
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {isModalOpen && selectedPost && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                {/* Header */}
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">{selectedPost.title}</h2>
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>

                     {/* Image et contenu */}
                     {selectedPost.source_image && (
                       <div className="mb-6">
                         <h3 className="text-lg font-semibold text-gray-900 mb-3">Image collectée:</h3>
                         <div className="bg-gray-50 rounded-lg p-4">
                           <img 
                             src={selectedPost.source_image} 
                             alt="Article" 
                             className="max-w-full h-auto rounded-lg"
                             onError={(e) => {
                               e.target.style.display = 'none';
                               e.target.nextSibling.style.display = 'block';
                             }}
                           />
                           <p className="text-gray-500 text-sm mt-2" style={{display: 'none'}}>
                             Image non disponible
                           </p>
                         </div>
                       </div>
                     )}

                {selectedPost.status === 'draft' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Contenu généré pour les réseaux sociaux:</h3>

                    {(() => {
                      // Récupérer les réseaux cibles du flux
                      const targetNetworks = selectedPost.feed?.target_networks || ['linkedin'];
                      return targetNetworks.map((network) => (
                        <div key={network} className="space-y-2">
                          <label className="block text-sm font-medium text-gray-700 capitalize">
                            {network === 'x' ? 'X (Twitter)' : network}
                          </label>
                          <textarea
                            value={generatedContent[network] || ''}
                            onChange={(e) => handleContentChange(network, e.target.value)}
                            placeholder={`Contenu pour ${network === 'x' ? 'X (Twitter)' : network}...`}
                            rows="4"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                          />
                        </div>
                      ));
                    })()}

                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => setIsModalOpen(false)}
                        className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                      >
                        Annuler
                      </button>
                      <button
                        onClick={handleSavePost}
                        disabled={saveMutation.isLoading}
                        className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 flex items-center space-x-2"
                      >
                        <FaSave />
                        <span>{saveMutation.isLoading ? 'Enregistrement...' : 'Enregistrer'}</span>
                      </button>
                      <button
                        onClick={handleRejectPost}
                        disabled={rejectMutation.isLoading}
                        className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-md transition-colors disabled:opacity-50 flex items-center space-x-2"
                      >
                        <FaTimes />
                        <span>Rejeter</span>
                      </button>
                      <button
                        onClick={handleValidatePost}
                        disabled={validateMutation.isLoading}
                        className="px-4 py-2 bg-primary text-white hover:bg-primary/90 rounded-md transition-colors disabled:opacity-50 flex items-center space-x-2"
                      >
                        <FaCheck />
                        <span>Valider le post</span>
                      </button>
                    </div>
                  </div>
                )}

                {selectedPost.status === 'validated' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Contenu validé:</h3>
                    {selectedPost.generated_content && Object.entries(selectedPost.generated_content).map(([network, content]) => (
                      <div key={network} className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 capitalize mb-2">{network}</h4>
                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                          <p className="text-gray-700 whitespace-pre-wrap">{cleanHtmlContent(content)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Posts;