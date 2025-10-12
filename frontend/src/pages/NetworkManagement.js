import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaGlobe, FaClock, FaUsers, FaPlay, FaPause, FaTrash, FaEdit, FaSave, FaPlus } from 'react-icons/fa';
import NetworkConfiguration from '../components/NetworkConfiguration';
import PublicationQueue from '../components/PublicationQueue';
import { networksService, publicationQueueService } from '../services/api';

const NetworkManagement = () => {
  const [activeTab, setActiveTab] = useState('networks');
  const [isCreatingNetwork, setIsCreatingNetwork] = useState(false);
  const [editingNetwork, setEditingNetwork] = useState(null);

  const queryClient = useQueryClient();

  // Récupération des réseaux
  const { data: networksData, isLoading: networksLoading } = useQuery('networks', networksService.getNetworks);
  const networks = networksData?.data || [];

  // Récupération de la file d'attente
  const { data: queueData, isLoading: queueLoading } = useQuery('publication-queue', () => 
    publicationQueueService.getQueue()
  );
  const queueItems = queueData?.data || [];

  // Mutations pour les réseaux
  const createNetworkMutation = useMutation(networksService.createNetwork, {
    onSuccess: () => {
      queryClient.invalidateQueries('networks');
    }
  });

  const updateNetworkMutation = useMutation(
    ({ networkId, networkData }) => networksService.updateNetwork(networkId, networkData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('networks');
      }
    }
  );

  // Mutations pour la file d'attente
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

  const cancelItemMutation = useMutation(publicationQueueService.cancelItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      queryClient.refetchQueries('publication-queue');
    }
  });

  const retryItemMutation = useMutation(publicationQueueService.retryItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      queryClient.refetchQueries('publication-queue');
    }
  });

  const handleSaveNetwork = (networkData) => {
    createNetworkMutation.mutate(networkData);
  };

  const handleUpdateNetwork = (networkId, networkData) => {
    updateNetworkMutation.mutate({ networkId, networkData });
  };

  const handlePauseItem = (itemId) => {
    pauseItemMutation.mutate(itemId);
  };

  const handleResumeItem = (itemId) => {
    resumeItemMutation.mutate(itemId);
  };

  const handleCancelItem = (itemId) => {
    cancelItemMutation.mutate(itemId);
  };

  const handleRetryItem = (itemId) => {
    retryItemMutation.mutate(itemId);
  };

  // Mutation pour ajouter les posts validés
  const addValidatedPostsMutation = useMutation(publicationQueueService.addValidatedPosts, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      alert('Posts validés ajoutés à la file d\'attente avec succès !');
    },
    onError: (error) => {
      console.error('Erreur lors de l\'ajout des posts validés:', error);
      alert('Erreur lors de l\'ajout des posts validés: ' + error.message);
    }
  });

  const handleAddValidatedPosts = () => {
    if (window.confirm('Ajouter tous les posts validés à la file d\'attente ?')) {
      addValidatedPostsMutation.mutate();
    }
  };

  const tabs = [
    { id: 'networks', label: 'Configuration des réseaux', icon: FaGlobe },
    { id: 'queue', label: 'File d\'attente', icon: FaClock },
    { id: 'destinations', label: 'Pages de destination', icon: FaUsers }
  ];

  const renderDestinationsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Pages de destination</h2>
          <p className="text-sm text-gray-600 mt-1">
            Gérez les pages et comptes de destination pour chaque réseau
          </p>
        </div>
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
          <FaPlus className="inline mr-2" />
          Nouvelle destination
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {networks.map(network => (
          <div key={network.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center space-x-3 mb-4">
              <span className="text-3xl">
                {network.network === 'facebook' ? '📘' : 
                 network.network === 'linkedin' ? '💼' : '🐦'}
              </span>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 capitalize">{network.network}</h3>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  network.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {network.is_active ? 'Actif' : 'Inactif'}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Page/Compte de destination
                </label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder={`ID de votre ${network.network === 'facebook' ? 'page Facebook' : 
                    network.network === 'linkedin' ? 'entreprise LinkedIn' : 'compte X'}`}
                  defaultValue={Object.values(network.page_configs)[0] || ''}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de la page
                </label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Nom affiché de la page"
                />
              </div>

              <div className="flex space-x-2">
                <button className="flex-1 px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors text-sm">
                  <FaSave className="inline mr-1" />
                  Sauvegarder
                </button>
                <button className="px-3 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors text-sm">
                  <FaEdit className="inline" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Attachement flux-destinations</h3>
        <p className="text-sm text-gray-600 mb-4">
          Configurez quels flux RSS sont publiés sur quelles pages de destination.
        </p>
        
        <div className="space-y-4">
          {/* Ici on pourrait ajouter une interface pour associer flux -> destinations */}
          <div className="text-center py-8 text-gray-500">
            <FaUsers className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <p>Interface d'attachement flux-destinations à implémenter</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gestion des réseaux</h1>
          <p className="text-gray-600 mt-2">
            Configurez vos réseaux sociaux et gérez la file d'attente de publication
          </p>
        </div>

        {/* Tabs */}
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
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div>
          {activeTab === 'networks' && (
            <NetworkConfiguration
              networks={networks}
              onSave={handleSaveNetwork}
              onUpdate={handleUpdateNetwork}
              isLoading={false}
            />
          )}
          
          {activeTab === 'queue' && (
            <PublicationQueue
              queueItems={queueItems}
              onPauseItem={handlePauseItem}
              onResumeItem={handleResumeItem}
              onCancelItem={handleCancelItem}
              onRetryItem={handleRetryItem}
              onAddValidatedPosts={handleAddValidatedPosts}
              isAddingValidatedPosts={addValidatedPostsMutation.isLoading}
            />
          )}
          
          {activeTab === 'destinations' && renderDestinationsTab()}
        </div>
      </div>
    </div>
  );
};

export default NetworkManagement;
