import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaGlobe, FaClock, FaUsers, FaPlay, FaPause, FaTrash, FaEdit, FaSave, FaPlus, FaCog, FaFacebook, FaLinkedin, FaTwitter, FaTimes, FaCheck } from 'react-icons/fa';
import { networksService, publicationQueueService } from '../services/api';
import { useToast } from '../hooks/useToast';

const PublicationManagement = () => {
  const [activeSection, setActiveSection] = useState('queue');
  const [editingNetwork, setEditingNetwork] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState({});
  const { showToast } = useToast();

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
      showToast('Réseau créé avec succès !', 'success');
      setShowEditModal(false);
    },
    onError: (error) => {
      showToast(`Erreur: ${error.message}`, 'error');
    }
  });

  const updateNetworkMutation = useMutation(
    ({ networkId, networkData }) => networksService.updateNetwork(networkId, networkData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('networks');
        showToast('Configuration mise à jour avec succès !', 'success');
        setShowEditModal(false);
      },
      onError: (error) => {
        showToast(`Erreur de mise à jour: ${error.message}`, 'error');
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

  const handleAddValidatedPosts = () => {
    if (window.confirm('Ajouter tous les posts validés à la file d\'attente ?')) {
      addValidatedPostsMutation.mutate();
    }
  };

  const sections = [
    { id: 'queue', label: 'File d\'attente', icon: FaClock },
    { id: 'networks', label: 'Configuration réseaux', icon: FaGlobe },
    { id: 'destinations', label: 'Pages de destination', icon: FaUsers }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'PENDING': return <FaClock className="text-yellow-500" />;
      case 'SCHEDULED': return <FaClock className="text-blue-500" />;
      case 'PUBLISHING': return <FaPlay className="text-indigo-500" />;
      case 'PUBLISHED': return <FaSave className="text-green-500" />;
      case 'FAILED': return <FaTrash className="text-red-500" />;
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
    const iconProps = { className: "w-6 h-6" };
    switch (network) {
      case 'facebook': return <FaFacebook {...iconProps} style={{ color: '#1877F2' }} />;
      case 'linkedin': return <FaLinkedin {...iconProps} style={{ color: '#0A66C2' }} />;
      case 'x': return <FaTwitter {...iconProps} style={{ color: '#000000' }} />;
      default: return <FaGlobe {...iconProps} className="text-gray-500" />;
    }
  };

  const openEditModal = (network) => {
    setEditingNetwork(network);
    setFormData({
      network: network?.network || '',
      is_active: network?.is_active !== undefined ? network.is_active : true,
      default_publication_delay: network?.default_publication_delay || 30,
      max_posts_per_day: network?.max_posts_per_day || 10
    });
    setShowEditModal(true);
  };

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSaveNetwork = () => {
    if (editingNetwork && editingNetwork.id) {
      // Mise à jour
      updateNetworkMutation.mutate({ 
        networkId: editingNetwork.id, 
        networkData: formData 
      });
    } else {
      // Création
      createNetworkMutation.mutate(formData);
    }
  };

  const renderQueueSection = () => (
    <div className="space-y-6">
      {/* Header avec statistiques */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">File d'attente de publication</h2>
          <div className="flex space-x-2">
            <button 
              onClick={handleAddValidatedPosts}
              disabled={addValidatedPostsMutation.isLoading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              <FaPlus className="inline mr-2" />
              {addValidatedPostsMutation.isLoading ? 'Ajout...' : 'Ajouter posts validés'}
            </button>
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
                      {item.status === 'PENDING' && (
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
                      {item.status === 'FAILED' && (
                        <button
                          onClick={() => handleRetryItem(item.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Réessayer"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleCancelItem(item.id)}
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

      {queueItems.length === 0 && (
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

  const renderNetworksSection = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Configuration des réseaux sociaux</h2>
          <p className="text-sm text-gray-600 mt-1">
            Gérez les paramètres globaux pour chaque réseau social
          </p>
        </div>
        <button
          onClick={() => setEditingNetwork({})}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <FaGlobe className="inline mr-2" />
          Nouveau réseau
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {networks.map(network => (
          <div key={network.id} className="bg-white rounded-lg shadow-md border-2 border-gray-100 p-6 hover:shadow-xl hover:border-indigo-200 transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="p-3 rounded-full bg-gray-50">
                  {getNetworkIcon(network.network)}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 capitalize">{network.network}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                      network.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {network.is_active ? '✓ Actif' : '✗ Inactif'}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => openEditModal(network)}
                className="p-3 text-gray-400 hover:text-white hover:bg-indigo-600 rounded-lg transition-all duration-200"
                title="Modifier la configuration"
              >
                <FaEdit className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center">
                  <FaClock className="w-4 h-4 mr-2 text-gray-400" />
                  Délai par défaut
                </span>
                <span className="text-sm font-bold text-indigo-600">{network.default_publication_delay} min</span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Max posts/jour</span>
                <span className="text-sm font-bold text-gray-900">{network.max_posts_per_day}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Pages configurées</span>
                <span className="text-sm font-bold text-gray-900">
                  {network.page_configs ? Object.keys(network.page_configs).length : 0}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Blotato</span>
                <span className={`text-sm font-bold ${
                  network.api_credentials ? 'text-green-600' : 'text-orange-600'
                }`}>
                  {network.api_credentials ? '✓ Configurée' : '⚠ À configurer'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {networks.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FaGlobe className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun réseau configuré</h3>
          <p className="mt-1 text-sm text-gray-500">
            Commencez par configurer vos réseaux sociaux.
          </p>
        </div>
      )}
    </div>
  );

  const renderDestinationsSection = () => (
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
                  defaultValue={Object.values(network.page_configs || {})[0] || ''}
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
    </div>
  );

  const renderEditModal = () => {
    if (!showEditModal) return null;

    const networkColors = {
      facebook: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
      linkedin: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-800' },
      x: { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-900' }
    };

    const colors = networkColors[formData.network] || { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-900' };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className={`${colors.bg} ${colors.border} border-b-4 p-6`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-white rounded-full shadow">
                  {getNetworkIcon(formData.network || editingNetwork?.network)}
                </div>
                <div>
                  <h2 className={`text-2xl font-bold ${colors.text}`}>
                    {editingNetwork && editingNetwork.id ? 'Modifier' : 'Nouveau'} Réseau
                  </h2>
                  <p className="text-sm text-gray-600 capitalize">
                    {formData.network || 'Configuration globale'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <FaTimes className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 space-y-6">
            {/* Réseau */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Réseau social
              </label>
              <select
                name="network"
                value={formData.network || ''}
                onChange={handleFormChange}
                disabled={editingNetwork && editingNetwork.id}
                className="w-full p-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
              >
                <option value="">-- Sélectionnez --</option>
                <option value="facebook">Facebook</option>
                <option value="linkedin">LinkedIn</option>
                <option value="x">X (Twitter)</option>
              </select>
            </div>

            {/* Actif */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="text-sm font-semibold text-gray-700">Réseau actif</label>
                <p className="text-xs text-gray-500 mt-1">Activer ou désactiver ce réseau</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active || false}
                  onChange={handleFormChange}
                  className="sr-only peer"
                />
                <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-green-600"></div>
              </label>
            </div>

            {/* Délai par défaut */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Délai de publication par défaut (minutes)
              </label>
              <input
                type="number"
                name="default_publication_delay"
                value={formData.default_publication_delay || 30}
                onChange={handleFormChange}
                min="1"
                className="w-full p-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Délai entre la collecte et la publication (utilisé si non spécifié par flux)
              </p>
            </div>

            {/* Max posts par jour */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Maximum de posts par jour
              </label>
              <input
                type="number"
                name="max_posts_per_day"
                value={formData.max_posts_per_day || 10}
                onChange={handleFormChange}
                min="1"
                className="w-full p-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Limite quotidienne de publications sur ce réseau
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3 rounded-b-xl">
            <button
              onClick={() => setShowEditModal(false)}
              className="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              <FaTimes className="inline mr-2" />
              Annuler
            </button>
            <button
              onClick={handleSaveNetwork}
              disabled={updateNetworkMutation.isLoading || createNetworkMutation.isLoading}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {(updateNetworkMutation.isLoading || createNetworkMutation.isLoading) ? (
                <>
                  <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Sauvegarde...
                </>
              ) : (
                <>
                  <FaCheck className="inline mr-2" />
                  Sauvegarder
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gestion des publications</h1>
          <p className="text-gray-600 mt-2">
            Gérez votre file d'attente de publication et configurez vos réseaux sociaux
          </p>
        </div>

        {/* Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {sections.map(section => {
                const Icon = section.icon;
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                      activeSection === section.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{section.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div>
          {activeSection === 'queue' && renderQueueSection()}
          {activeSection === 'networks' && renderNetworksSection()}
          {activeSection === 'destinations' && renderDestinationsSection()}
        </div>
      </div>

      {/* Modal d'édition */}
      {renderEditModal()}
    </div>
  );
};

export default PublicationManagement;

