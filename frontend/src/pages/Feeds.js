import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaPlus, FaEdit, FaTrash, FaClock, FaCheck, FaTimes, FaExclamationTriangle } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { feedsService } from '../services/api';
import FeedCreationModal from '../components/FeedCreationModal';
import FeedEditModal from '../components/FeedEditModal';

const Feeds = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCreationModalOpen, setIsCreationModalOpen] = useState(false);
  const [editingFeed, setEditingFeed] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    frequency_minutes: 60,
    target_networks: [],
    is_active: true,
    network_prompts: {
      facebook: '',
      linkedin: '',
      x: ''
    },
    publication_timing: {
      facebook: 30,
      linkedin: 60,
      x: 15
    },
    social_pages: {
      facebook: '',
      linkedin: '',
      x: ''
    }
  });

  const queryClient = useQueryClient();

  const { data: feedsData = [], isLoading, error } = useQuery('feeds', feedsService.getFeeds);
  
  // S'assurer que feeds est un tableau
  const feeds = Array.isArray(feedsData?.data) ? feedsData.data : Array.isArray(feedsData) ? feedsData : [];
  
  console.log('🔍 Feeds Debug:', {
    feedsData,
    feeds,
    feedsLength: feeds?.length,
    isLoading,
    hasError: !!error
  });

  const createFeedMutation = useMutation(feedsService.createFeed, {
    onSuccess: () => {
      queryClient.invalidateQueries('feeds');
      setIsModalOpen(false);
      resetForm();
    },
  });

  const updateFeedMutation = useMutation(({ id, data }) => feedsService.updateFeed(id, data), {
    onSuccess: () => {
      queryClient.invalidateQueries('feeds');
      setIsModalOpen(false);
      setEditingFeed(null);
      resetForm();
    },
  });

  const deleteFeedMutation = useMutation(feedsService.deleteFeed, {
    onSuccess: () => {
      queryClient.invalidateQueries('feeds');
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      frequency_minutes: 60,
      target_networks: [],
      is_active: true,
      network_prompts: {
        facebook: '',
        linkedin: '',
        x: ''
      },
      publication_timing: {
        facebook: 30,
        linkedin: 60,
        x: 15
      },
      social_pages: {
        facebook: '',
        linkedin: '',
        x: ''
      }
    });
  };

  const handleOpenModal = (feed = null) => {
    if (feed) {
      setEditingFeed(feed);
    } else {
      setIsCreationModalOpen(true);
    }
  };

  const handleCreateFeed = (feedData) => {
    createFeedMutation.mutate(feedData);
    setIsCreationModalOpen(false);
  };

  const handleUpdateFeed = (feedId, feedData) => {
    updateFeedMutation.mutate({ id: feedId, data: feedData });
    setEditingFeed(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingFeed) {
      updateFeedMutation.mutate({ id: editingFeed.id, data: formData });
    } else {
      createFeedMutation.mutate(formData);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (name.startsWith('network_prompts.')) {
      const network = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        network_prompts: {
          ...prev.network_prompts,
          [network]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleNetworkChange = (e) => {
    const { value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      target_networks: checked 
        ? [...prev.target_networks, value]
        : prev.target_networks.filter(network => network !== value)
    }));
  };

  const handleDelete = (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce flux ?')) {
      deleteFeedMutation.mutate(id);
    }
  };

  // Fonction pour déterminer le statut de collecte
  const getCollectionStatus = (feed) => {
    if (!feed.last_fetch) {
      return { status: 'never', icon: FaTimes, color: 'text-red-500', label: 'Jamais collecté' };
    }
    
    const now = new Date();
    const lastFetch = new Date(feed.last_fetch);
    const diffMinutes = (now - lastFetch) / (1000 * 60);
    
    if (diffMinutes < feed.frequency_minutes) {
      return { status: 'recent', icon: FaCheck, color: 'text-green-500', label: 'Collecté récemment' };
    } else if (diffMinutes < feed.frequency_minutes * 2) {
      return { status: 'overdue', icon: FaExclamationTriangle, color: 'text-yellow-500', label: 'En retard' };
    } else {
      return { status: 'stale', icon: FaTimes, color: 'text-red-500', label: 'Collecte obsolète' };
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Flux RSS</h1>
          <p className="mt-2 text-gray-600">Gérez vos sources de contenu et leur fréquence de collecte</p>
        </div>

        {/* Add Button */}
        <div className="mb-6">
          <button
            onClick={() => handleOpenModal()}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors duration-200 flex items-center space-x-2"
          >
            <FaPlus />
            <span>Ajouter un flux</span>
          </button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="text-center p-10">
            <p className="text-gray-700">Chargement des flux...</p>
          </div>
        ) : error ? (
          <div className="text-center p-10 text-red-600">
            <p>Erreur lors du chargement des flux: {error.message}</p>
          </div>
        ) : feeds.length === 0 ? (
          <div className="text-center p-10">
            <p className="text-gray-700">Aucun flux trouvé. Ajoutez-en un pour commencer !</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Desktop Table */}
            <div className="hidden lg:block bg-white shadow-md rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full divide-y divide-gray-200" style={{minWidth: '1200px'}}>
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nom</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fréquence</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Réseaux cibles</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dernière collecte</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {feeds.map((feed) => {
                    const collectionStatus = getCollectionStatus(feed);
                    const StatusIcon = collectionStatus.icon;
                    
                    return (
                      <tr key={feed.id}>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900 max-w-xs">
                          <div className="truncate" title={feed.name}>
                            {feed.name}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-lg">
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <a 
                              href={feed.url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="text-indigo-600 hover:text-indigo-800 hover:underline break-all block font-mono text-xs leading-relaxed"
                              title={feed.url}
                            >
                              {feed.url}
                            </a>
                            <div className="mt-1 text-xs text-gray-400">
                              <span className="inline-flex items-center">
                                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 00-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                                </svg>
                                Lien externe
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex items-center">
                            <FaClock className="mr-2 text-gray-400" />
                            {feed.frequency_minutes} min
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex flex-wrap gap-1">
                            {feed.target_networks && feed.target_networks.length > 0 ? (
                              feed.target_networks.map(network => {
                                const networkInfo = {
                                  facebook: { icon: '📘', color: 'bg-blue-100 text-blue-800' },
                                  linkedin: { icon: '💼', color: 'bg-blue-100 text-blue-800' },
                                  x: { icon: '🐦', color: 'bg-gray-100 text-gray-800' }
                                };
                                const info = networkInfo[network] || { icon: '🌐', color: 'bg-gray-100 text-gray-800' };
                                return (
                                  <span key={network} className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${info.color}`}>
                                    <span className="mr-1">{info.icon}</span>
                                    {network}
                                  </span>
                                );
                              })
                            ) : (
                              <span className="text-gray-400 text-xs">Tous</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center">
                            <StatusIcon className={`mr-2 ${collectionStatus.color}`} />
                            <span className={collectionStatus.color}>{collectionStatus.label}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {feed.last_fetch ? format(new Date(feed.last_fetch), 'dd/MM/yyyy HH:mm', { locale: fr }) : 'Jamais'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleOpenModal(feed)}
                              className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <FaEdit className="mr-1" />
                              Éditer
                            </button>
                            <button
                              onClick={() => handleDelete(feed.id)}
                              className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                            >
                              <FaTrash className="mr-1" />
                              Supprimer
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                </table>
              </div>
            </div>

            {/* Mobile Cards */}
            <div className="lg:hidden space-y-4">
              {feeds.map((feed) => {
                const collectionStatus = getCollectionStatus(feed);
                const StatusIcon = collectionStatus.icon;
                
                return (
                  <div key={feed.id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">{feed.name}</h3>
                      <div className="flex items-center">
                        <StatusIcon className={`mr-2 ${collectionStatus.color}`} />
                        <span className={`text-sm ${collectionStatus.color}`}>{collectionStatus.label}</span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-2">URL</p>
                        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                          <a href={feed.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:text-indigo-800 hover:underline text-sm break-all block font-mono leading-relaxed">
                            {feed.url}
                          </a>
                          <div className="mt-1 text-xs text-gray-400 flex items-center">
                            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 00-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                            </svg>
                            Lien externe
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-gray-500">Fréquence</p>
                          <div className="flex items-center">
                            <FaClock className="mr-2 text-gray-400" />
                            <span className="text-sm text-gray-900">{feed.frequency_minutes} min</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Dernière collecte</p>
                          <p className="text-sm text-gray-900">
                            {feed.last_fetch ? format(new Date(feed.last_fetch), 'dd/MM/yyyy HH:mm', { locale: fr }) : 'Jamais'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex space-x-3 pt-3 border-t border-gray-200">
                        <button
                          onClick={() => handleOpenModal(feed)}
                          className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors duration-200 text-sm flex items-center justify-center"
                        >
                          <FaEdit className="mr-2" />
                          Éditer
                        </button>
                        <button
                          onClick={() => handleDelete(feed.id)}
                          className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors duration-200 text-sm flex items-center justify-center"
                        >
                          <FaTrash className="mr-2" />
                          Supprimer
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                {editingFeed ? 'Éditer le flux RSS' : 'Ajouter un nouveau flux RSS'}
              </h2>
              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Nom du flux</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">URL du flux</label>
                  <input
                    type="url"
                    id="url"
                    name="url"
                    value={formData.url}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="frequency_minutes" className="block text-sm font-medium text-gray-700 mb-1">Fréquence de collecte (minutes)</label>
                  <input
                    type="number"
                    id="frequency_minutes"
                    name="frequency_minutes"
                    value={formData.frequency_minutes}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                    min="1"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Réseaux sociaux cibles (optionnel)</label>
                  <div className="space-y-2">
                    {[
                      { value: 'facebook', label: 'Facebook', icon: '📘' },
                      { value: 'linkedin', label: 'LinkedIn', icon: '💼' },
                      { value: 'x', label: 'X (Twitter)', icon: '🐦' }
                    ].map(network => (
                      <label key={network.value} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          name="target_networks"
                          value={network.value}
                          checked={formData.target_networks.includes(network.value)}
                          onChange={handleNetworkChange}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                        <span className="text-lg">{network.icon}</span>
                        <span className="text-sm font-medium text-gray-700">{network.label}</span>
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Sélectionnez un ou plusieurs réseaux. Si aucun n'est sélectionné, tous les réseaux seront utilisés.</p>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Prompts spécifiques par réseau (optionnel)</label>
                  {['facebook', 'linkedin', 'x'].map(network => (
                    <div key={network} className="mb-3">
                      <label htmlFor={`prompt-${network}`} className="block text-xs font-medium text-gray-500 mb-1 capitalize">{network}</label>
                      <textarea
                        id={`prompt-${network}`}
                        name={`network_prompts.${network}`}
                        value={formData.network_prompts[network] || ''}
                        onChange={handleInputChange}
                        rows="2"
                        className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        placeholder={`Prompt pour ${network}...`}
                      ></textarea>
                    </div>
                  ))}
                </div>
                
                {/* Configuration des temps de publication */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Temps de publication par réseau (en minutes)</label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {['facebook', 'linkedin', 'x'].map(network => {
                      const networkInfo = {
                        facebook: { label: 'Facebook', icon: '📘', color: 'bg-blue-50 border-blue-200' },
                        linkedin: { label: 'LinkedIn', icon: '💼', color: 'bg-blue-50 border-blue-200' },
                        x: { label: 'X (Twitter)', icon: '🐦', color: 'bg-gray-50 border-gray-200' }
                      };
                      const info = networkInfo[network];
                      return (
                        <div key={network} className={`p-3 rounded-lg border ${info.color}`}>
                          <label htmlFor={`timing-${network}`} className="block text-xs font-medium text-gray-600 mb-1">
                            <span className="mr-1">{info.icon}</span>
                            {info.label}
                          </label>
                          <input
                            type="number"
                            id={`timing-${network}`}
                            name={`publication_timing.${network}`}
                            value={formData.publication_timing[network] || 0}
                            onChange={handleInputChange}
                            min="0"
                            max="1440"
                            className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                            placeholder="Minutes"
                          />
                          <p className="text-xs text-gray-500 mt-1">Délai après collecte</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Configuration des pages de destination */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Pages de destination par réseau</label>
                  <div className="space-y-3">
                    {['facebook', 'linkedin', 'x'].map(network => {
                      const networkInfo = {
                        facebook: { label: 'Facebook Page ID', icon: '📘', placeholder: 'ID de votre page Facebook' },
                        linkedin: { label: 'LinkedIn Company ID', icon: '💼', placeholder: 'ID de votre entreprise LinkedIn' },
                        x: { label: 'X (Twitter) User ID', icon: '🐦', placeholder: 'ID de votre compte X' }
                      };
                      const info = networkInfo[network];
                      return (
                        <div key={network} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
                          <span className="text-lg">{info.icon}</span>
                          <div className="flex-1">
                            <label htmlFor={`page-${network}`} className="block text-xs font-medium text-gray-600 mb-1">
                              {info.label}
                            </label>
                            <input
                              type="text"
                              id={`page-${network}`}
                              name={`social_pages.${network}`}
                              value={formData.social_pages[network] || ''}
                              onChange={handleInputChange}
                              className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                              placeholder={info.placeholder}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Configurez les identifiants de vos pages/entreprises sur chaque réseau social pour la publication automatique.
                  </p>
                </div>
                
                <div className="mb-6 flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">Actif</label>
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-5 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors duration-200"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={createFeedMutation.isLoading || updateFeedMutation.isLoading}
                  >
                    {editingFeed ? 'Mettre à jour' : 'Ajouter'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal de création multi-étapes */}
        <FeedCreationModal
          isOpen={isCreationModalOpen}
          onClose={() => setIsCreationModalOpen(false)}
          onSave={handleCreateFeed}
          isLoading={createFeedMutation.isLoading}
        />

        {/* Modal d'édition multi-étapes */}
        <FeedEditModal
          isOpen={!!editingFeed}
          onClose={() => setEditingFeed(null)}
          feed={editingFeed}
          onSave={handleUpdateFeed}
          isLoading={updateFeedMutation.isLoading}
        />
      </div>
    </div>
  );
};

export default Feeds;