import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaClock, FaPlay, FaPause, FaEye, FaCheck, FaTimes, FaPlus, FaGlobe, FaUsers } from 'react-icons/fa';
import { postsService, publicationQueueService } from '../services/api';

const UnifiedQueue = () => {
  const [activeTab, setActiveTab] = useState('posts');
  const [selectedPosts, setSelectedPosts] = useState([]);

  const queryClient = useQueryClient();

  // Récupération des posts en attente
  const { data: postsData, isLoading: postsLoading } = useQuery('posts-queue', () => 
    postsService.getPosts('queue')
  );
  const posts = postsData?.data || [];

  // Récupération de la file d'attente de publication
  const { data: queueData, isLoading: queueLoading } = useQuery('publication-queue', () => 
    publicationQueueService.getQueue()
  );
  const queueItems = queueData?.data || [];

  // Mutations pour les posts
  const validatePostMutation = useMutation(postsService.validatePost, {
    onSuccess: () => {
      queryClient.invalidateQueries('posts-queue');
      queryClient.invalidateQueries('posts-validated');
    }
  });

  const rejectPostMutation = useMutation(postsService.rejectPost, {
    onSuccess: () => {
      queryClient.invalidateQueries('posts-queue');
      queryClient.invalidateQueries('posts-rejected');
    }
  });

  // Mutations pour la file d'attente de publication
  const pauseItemMutation = useMutation(publicationQueueService.pauseItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      queryClient.refetchQueries('publication-queue');
    }
  });

  const resumeItemMutation = useMutation(publicationQueueService.resumeItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      queryClient.refetchQueries('publication-queue');
    }
  });

  // Mutation pour ajouter les posts validés à la file de publication
  const addValidatedPostsMutation = useMutation(publicationQueueService.addValidatedPosts, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      alert('Posts validés ajoutés à la file de publication avec succès !');
    },
    onError: (error) => {
      console.error('Erreur lors de l\'ajout des posts validés:', error);
      alert('Erreur lors de l\'ajout des posts validés: ' + error.message);
    }
  });

  const handleValidatePost = (postId) => {
    validatePostMutation.mutate(postId);
  };

  const handleRejectPost = (postId) => {
    rejectPostMutation.mutate(postId);
  };

  const handlePauseItem = (itemId) => {
    pauseItemMutation.mutate(itemId);
  };

  const handleResumeItem = (itemId) => {
    resumeItemMutation.mutate(itemId);
  };

  const handleAddValidatedPosts = () => {
    if (window.confirm('Ajouter tous les posts validés à la file de publication ?')) {
      addValidatedPostsMutation.mutate();
    }
  };

  const handleSelectPost = (postId) => {
    setSelectedPosts(prev => 
      prev.includes(postId) 
        ? prev.filter(id => id !== postId)
        : [...prev, postId]
    );
  };

  const handleValidateSelected = () => {
    selectedPosts.forEach(postId => {
      validatePostMutation.mutate(postId);
    });
    setSelectedPosts([]);
  };

  const handleRejectSelected = () => {
    selectedPosts.forEach(postId => {
      rejectPostMutation.mutate(postId);
    });
    setSelectedPosts([]);
  };

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

  const renderPostsTab = () => (
    <div className="space-y-6">
      {/* Header avec actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">Posts en attente de validation</h2>
          <div className="flex space-x-2">
            {selectedPosts.length > 0 && (
              <>
                <button 
                  onClick={handleValidateSelected}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <FaCheck className="inline mr-2" />
                  Valider sélectionnés ({selectedPosts.length})
                </button>
                <button 
                  onClick={handleRejectSelected}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  <FaTimes className="inline mr-2" />
                  Rejeter sélectionnés ({selectedPosts.length})
                </button>
              </>
            )}
            <button 
              onClick={handleAddValidatedPosts}
              disabled={addValidatedPostsMutation.isLoading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              <FaPlus className="inline mr-2" />
              {addValidatedPostsMutation.isLoading ? 'Ajout...' : 'Ajouter posts validés à la publication'}
            </button>
          </div>
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{posts.length}</div>
            <div className="text-sm text-gray-600">Total en attente</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{posts.filter(post => post.status === 'draft').length}</div>
            <div className="text-sm text-yellow-600">Brouillons</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{selectedPosts.length}</div>
            <div className="text-sm text-blue-600">Sélectionnés</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">0</div>
            <div className="text-sm text-green-600">Validés aujourd'hui</div>
          </div>
        </div>
      </div>

      {/* Liste des posts */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input 
                    type="checkbox" 
                    className="rounded border-gray-300"
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPosts(posts.map(p => p.id));
                      } else {
                        setSelectedPosts([]);
                      }
                    }}
                    checked={selectedPosts.length === posts.length && posts.length > 0}
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contenu
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Flux
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Créé
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {posts.map((post) => (
                <tr key={post.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input 
                      type="checkbox" 
                      className="rounded border-gray-300"
                      checked={selectedPosts.includes(post.id)}
                      onChange={() => handleSelectPost(post.id)}
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="max-w-xs">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {post.title || 'Sans titre'}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {post.content ? post.content.substring(0, 100) + '...' : 'Aucun contenu'}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-gray-900">
                      Flux #{post.feed_id}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      <FaClock className="mr-1" />
                      En attente
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {post.created_at ? new Date(post.created_at).toLocaleString('fr-FR') : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleValidatePost(post.id)}
                        className="text-green-600 hover:text-green-900"
                        title="Valider"
                      >
                        <FaCheck className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleRejectPost(post.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Rejeter"
                      >
                        <FaTimes className="w-4 h-4" />
                      </button>
                      <button
                        className="text-blue-600 hover:text-blue-900"
                        title="Voir détails"
                      >
                        <FaEye className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {posts.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FaClock className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun post en attente</h3>
          <p className="mt-1 text-sm text-gray-500">
            Les nouveaux posts collectés apparaîtront ici.
          </p>
        </div>
      )}
    </div>
  );

  const renderPublicationTab = () => (
    <div className="space-y-6">
      {/* Header avec statistiques */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">File d'attente de publication</h2>
          <div className="flex space-x-2">
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
            <div className="text-2xl font-bold text-gray-900">{queueItems.length}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{queueItems.filter(item => item.status === 'PENDING').length}</div>
            <div className="text-sm text-yellow-600">En attente</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{queueItems.filter(item => item.status === 'SCHEDULED').length}</div>
            <div className="text-sm text-blue-600">Programmés</div>
          </div>
          <div className="text-center p-3 bg-indigo-50 rounded-lg">
            <div className="text-2xl font-bold text-indigo-600">{queueItems.filter(item => item.status === 'PUBLISHING').length}</div>
            <div className="text-sm text-indigo-600">En cours</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{queueItems.filter(item => item.status === 'PUBLISHED').length}</div>
            <div className="text-sm text-green-600">Publiés</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{queueItems.filter(item => item.status === 'FAILED').length}</div>
            <div className="text-sm text-red-600">Échecs</div>
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
              {queueItems.map((item) => (
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
                      <span className="ml-1">{item.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.scheduled_at ? new Date(item.scheduled_at).toLocaleString('fr-FR') : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {item.status === 'PENDING' && !item.is_paused && (
                        <button
                          onClick={() => handlePauseItem(item.id)}
                          className="text-yellow-600 hover:text-yellow-900"
                          title="Mettre en pause"
                        >
                          <FaPause className="w-4 h-4" />
                        </button>
                      )}
                      {item.status === 'PENDING' && item.is_paused && (
                        <button
                          onClick={() => handleResumeItem(item.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Reprendre"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        className="text-blue-600 hover:text-blue-900"
                        title="Voir détails"
                      >
                        <FaEye className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {queueItems.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FaClock className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun élément dans la file de publication</h3>
          <p className="mt-1 text-sm text-gray-500">
            Les publications programmées apparaîtront ici.
          </p>
        </div>
      )}
    </div>
  );

  const tabs = [
    { id: 'posts', label: 'Posts en attente', icon: FaClock, count: posts.length },
    { id: 'publication', label: 'File de publication', icon: FaGlobe, count: queueItems.length }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">File d'attente unifiée</h1>
          <p className="text-gray-600 mt-2">
            Gérez les posts en attente de validation et la file de publication
          </p>
        </div>

        {/* Navigation par onglets */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{tab.label}</span>
                    <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                      activeTab === tab.id 
                        ? 'bg-indigo-100 text-indigo-600' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {tab.count}
                    </span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Contenu */}
        <div>
          {activeTab === 'posts' && renderPostsTab()}
          {activeTab === 'publication' && renderPublicationTab()}
        </div>
      </div>
    </div>
  );
};

export default UnifiedQueue;
