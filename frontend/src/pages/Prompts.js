import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaEdit, FaSave, FaTimes, FaPlus, FaTrash, FaCopy, FaRss, FaGlobe } from 'react-icons/fa';
import { feedsService } from '../services/api';

const Prompts = () => {
  const queryClient = useQueryClient();
  
  // Récupérer les flux RSS
  const { data: feedsData = [], isLoading: feedsLoading, error: feedsError } = useQuery('feeds', feedsService.getFeeds);
  
  // S'assurer que feeds est un tableau
  const feeds = Array.isArray(feedsData?.data) ? feedsData.data : Array.isArray(feedsData) ? feedsData : [];
  
  const [selectedFeed, setSelectedFeed] = useState(null);
  
  // Debug
  console.log('🔍 Prompts Debug:', {
    feedsData,
    feeds,
    feedsLength: feeds?.length,
    isLoading: feedsLoading,
    hasError: !!feedsError,
    selectedFeed: selectedFeed?.name,
    selectedFeedPrompts: selectedFeed?.network_prompts
  });
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    network: '',
    content: ''
  });

  // Prompts par défaut pour chaque réseau (utilisés si aucun prompt personnalisé)
  const defaultPrompts = {
    facebook: "Créez un post Facebook engageant basé sur l'article suivant. Le post doit être informatif, captivant et encourager l'interaction. Utilisez des emojis appropriés et une structure claire.",
    linkedin: "Rédigez un post LinkedIn professionnel basé sur l'article fourni. Le contenu doit être pertinent pour un public professionnel, avec des insights et des questions pour encourager la discussion.",
    x: "Créez un tweet concis et percutant basé sur l'article. Respectez la limite de caractères, utilisez des hashtags pertinents et créez de l'engagement."
  };

  const networks = [
    { key: 'facebook', name: 'Facebook', icon: '📘', color: 'bg-blue-100 text-blue-800' },
    { key: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'bg-blue-100 text-blue-800' },
    { key: 'x', name: 'X (Twitter)', icon: '🐦', color: 'bg-gray-100 text-gray-800' }
  ];

  // Sélectionner le premier flux par défaut
  useEffect(() => {
    if (feeds.length > 0 && !selectedFeed) {
      setSelectedFeed(feeds[0]);
    }
  }, [feeds, selectedFeed]);

  const handleEditPrompt = (network) => {
    setEditingPrompt(network);
    // Utiliser les prompts de l'API ou les valeurs par défaut
    const currentPrompt = selectedFeed?.network_prompts?.[network] || defaultPrompts[network];
    setFormData({
      network,
      content: currentPrompt
    });
    setIsModalOpen(true);
  };

  // Mutation pour sauvegarder les prompts
  const updatePromptsMutation = useMutation(
    ({ feedId, networkPrompts }) => feedsService.updateFeedPrompts(feedId, networkPrompts),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('feeds');
        // Mettre à jour l'état local immédiatement
        if (selectedFeed && selectedFeed.id === data.data.id) {
          setSelectedFeed(data.data);
        }
        console.log('✅ Prompts sauvegardés avec succès');
        // Fermer le modal après sauvegarde
        setIsModalOpen(false);
        setEditingPrompt(null);
        setFormData({ network: '', content: '' });
      },
      onError: (error) => {
        console.error('❌ Erreur lors de la sauvegarde:', error);
        alert('Erreur lors de la sauvegarde des prompts: ' + error.message);
      }
    }
  );

  const handleSavePrompt = () => {
    if (selectedFeed && editingPrompt) {
      // Mettre à jour les prompts du flux sélectionné
      const updatedPrompts = {
        ...selectedFeed.network_prompts,
        [editingPrompt]: formData.content
      };
      
      console.log('💾 Sauvegarde des prompts:', {
        feedId: selectedFeed.id,
        network: editingPrompt,
        prompts: updatedPrompts
      });
      
      // Sauvegarder via l'API
      updatePromptsMutation.mutate({
        feedId: selectedFeed.id,
        networkPrompts: updatedPrompts
      });
    }
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setEditingPrompt(null);
    setFormData({ network: '', content: '' });
  };

  const copyPrompt = (network) => {
    // Utiliser les prompts de l'API ou les valeurs par défaut
    const prompt = selectedFeed?.network_prompts?.[network] || defaultPrompts[network];
    navigator.clipboard.writeText(prompt);
    console.log('📋 Prompt copié:', { network, prompt: prompt.substring(0, 50) + '...' });
  };

  const resetToDefault = (network) => {
    if (selectedFeed) {
      const updatedPrompts = {
        ...selectedFeed.network_prompts,
        [network]: defaultPrompts[network]
      };
      
      // Sauvegarder via l'API
      updatePromptsMutation.mutate({
        feedId: selectedFeed.id,
        networkPrompts: updatedPrompts
      });
    }
  };

  if (feedsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-700">Chargement des flux RSS...</p>
        </div>
      </div>
    );
  }

  if (feedsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center text-red-600">
          <p>Erreur lors du chargement des flux: {feedsError.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Prompts par Flux RSS</h1>
          <p className="mt-2 text-gray-600">Gérez les prompts spécifiques pour chaque flux RSS et chaque réseau social</p>
        </div>

        {feeds.length === 0 ? (
          <div className="text-center py-12">
            <FaRss className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun flux RSS</h3>
            <p className="mt-1 text-sm text-gray-500">Ajoutez des flux RSS pour configurer leurs prompts.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Sélection du flux */}
            <div className="xl:col-span-1">
              <div className="bg-white shadow-lg rounded-xl p-6 border border-gray-100">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <FaRss className="mr-2 text-indigo-600" />
                  Flux RSS
                </h2>
                <div className="space-y-3">
                  {feeds.map((feed) => (
                    <button
                      key={feed.id}
                      onClick={() => setSelectedFeed(feed)}
                      className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 ${
                        selectedFeed?.id === feed.id
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-md'
                          : 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-1">
                          <div className={`w-3 h-3 rounded-full ${
                            selectedFeed?.id === feed.id ? 'bg-indigo-500' : 'bg-gray-300'
                          }`}></div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-gray-900 truncate">{feed.name}</p>
                          <p className="text-xs text-gray-500 break-all mt-1 leading-relaxed">{feed.url}</p>
                          {feed.network_prompts && Object.keys(feed.network_prompts).length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {Object.keys(feed.network_prompts).map((network) => (
                                <span key={network} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  {network}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Prompts du flux sélectionné */}
            <div className="xl:col-span-3">
              {selectedFeed ? (
                <div className="space-y-6">
                  <div className="bg-white shadow-lg rounded-xl p-8 border border-gray-100">
                    <div className="flex items-center justify-between mb-8">
                      <div className="flex-1">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Prompts pour {selectedFeed.name}</h2>
                        <p className="text-sm text-gray-600 mb-4">Configurez les prompts spécifiques pour chaque réseau social</p>
                        <div className="flex flex-wrap items-center gap-3">
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            🔗 Connecté à l'API
                          </span>
                          {selectedFeed.network_prompts && Object.keys(selectedFeed.network_prompts).length > 0 && (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              📝 Prompts personnalisés
                            </span>
                          )}
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            📊 {Object.keys(selectedFeed.network_prompts || {}).length}/3 réseaux configurés
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                      {networks.map((network) => {
                        const currentPrompt = selectedFeed.network_prompts?.[network.key] || defaultPrompts[network.key];
                        const isDefault = !selectedFeed.network_prompts?.[network.key];
                        
                        return (
                          <div key={network.key} className="bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all duration-200">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center space-x-3">
                                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${network.color}`}>
                                  <span className="text-2xl">{network.icon}</span>
                                </div>
                                <div>
                                  <h3 className="font-semibold text-gray-900">{network.name}</h3>
                                  {isDefault ? (
                                    <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full">Par défaut</span>
                                  ) : (
                                    <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">Personnalisé</span>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <div className="bg-white rounded-lg p-4 border border-gray-200 mb-4">
                              <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                                {currentPrompt}
                              </p>
                            </div>
                            
                            <div className="flex justify-between items-center">
                              <div className="flex space-x-2">
                                <button
                                  onClick={() => copyPrompt(network.key)}
                                  className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                  title="Copier le prompt"
                                >
                                  <FaCopy className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleEditPrompt(network.key)}
                                  className="p-2 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors"
                                  title="Modifier le prompt"
                                >
                                  <FaEdit className="w-4 h-4" />
                                </button>
                                {!isDefault && (
                                  <button
                                    onClick={() => resetToDefault(network.key)}
                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Réinitialiser au défaut"
                                  >
                                    <FaTimes className="w-4 h-4" />
                                  </button>
                                )}
                              </div>
                              <div className="text-xs text-gray-500">
                                {currentPrompt.length} caractères
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <FaGlobe className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Sélectionnez un flux RSS</h3>
                  <p className="mt-1 text-sm text-gray-500">Choisissez un flux pour configurer ses prompts.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Modal d'édition */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="p-8">
                <div className="flex justify-between items-center mb-8">
                  <div className="flex items-center space-x-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      networks.find(n => n.key === editingPrompt)?.color || 'bg-gray-100'
                    }`}>
                      <span className="text-2xl">{networks.find(n => n.key === editingPrompt)?.icon}</span>
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">
                        Modifier le prompt {networks.find(n => n.key === editingPrompt)?.name}
                      </h2>
                      <p className="text-sm text-gray-600">Personnalisez le contenu pour ce réseau social</p>
                    </div>
                  </div>
                  <button
                    onClick={handleCancel}
                    className="text-gray-400 hover:text-gray-600 text-3xl p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Contenu du prompt
                    </label>
                    <textarea
                      value={formData.content}
                      onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
                      rows="10"
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none"
                      placeholder="Entrez le contenu du prompt..."
                    />
                    <div className="mt-2 text-right text-sm text-gray-500">
                      {formData.content.length} caractères
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                    <h4 className="text-sm font-semibold text-blue-900 mb-4 flex items-center">
                      <span className="mr-2">💡</span>
                      Variables disponibles
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="flex items-center space-x-2">
                        <code className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-mono">{'{titre}'}</code>
                        <span className="text-sm text-blue-700">Titre de l'article</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <code className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-mono">{'{contenu}'}</code>
                        <span className="text-sm text-blue-700">Contenu de l'article</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <code className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-mono">{'{url}'}</code>
                        <span className="text-sm text-blue-700">URL de l'article</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <code className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-mono">{'{image}'}</code>
                        <span className="text-sm text-blue-700">Image de l'article</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
                  <button
                    onClick={handleCancel}
                    className="px-6 py-3 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors font-medium"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleSavePrompt}
                    disabled={updatePromptsMutation.isLoading}
                    className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:from-indigo-700 hover:to-indigo-800 rounded-xl transition-all duration-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-lg hover:shadow-xl"
                  >
                    <FaSave className="w-4 h-4" />
                    <span>{updatePromptsMutation.isLoading ? 'Sauvegarde...' : 'Sauvegarder'}</span>
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

export default Prompts;