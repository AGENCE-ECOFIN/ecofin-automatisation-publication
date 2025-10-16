import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaClock, FaPlay, FaPause, FaCheck, FaTimes, FaPlus, FaGlobe, FaImage, FaSave, FaUpload, FaToggleOn, FaToggleOff, FaExternalLinkAlt } from 'react-icons/fa';
import { FaFacebook, FaLinkedin, FaTwitter } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { postsService, publicationQueueService, networksService, feedsService, api } from '../services/api';
import SocialNetworkIcon from '../components/SocialNetworkIcon';
import ScheduleConfigModal from '../components/ScheduleConfigModal';

const UnifiedPublication = () => {
  const [activeTab, setActiveTab] = useState('queue');
  const [showDirectPost, setShowDirectPost] = useState(false);
  const [showNetworkConfig, setShowNetworkConfig] = useState(false);
  const [showScheduleConfigModal, setShowScheduleConfigModal] = useState(false);
  const [selectedNetworkForSchedule, setSelectedNetworkForSchedule] = useState(null);
  const [editingPost, setEditingPost] = useState(null);
  const [feedFilter, setFeedFilter] = useState('');
  const [networkFilter, setNetworkFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [, forceUpdate] = useState();

  const queryClient = useQueryClient();
  
  // Rafraîchir chaque seconde pour mettre à jour le chrono
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate({});
    }, 1000);
    return () => clearInterval(interval);
  }, []);
  
  // Toast simple
  const showToast = (message, type = 'info') => {
    alert(message);
  };

  const [networkFormData, setNetworkFormData] = useState({});
  const [isSavingNetwork, setIsSavingNetwork] = useState(false);

  // Fonction pour sauvegarder la configuration d'un réseau
  const handleSaveNetwork = async (networkId) => {
    const data = networkFormData[networkId];
    if (!data) {
      showToast('⚠️ Aucune modification');
      return;
    }

    setIsSavingNetwork(true);
    try {
      const networkData = {
        is_active: data.is_active,
        default_publication_delay: parseInt(data.default_publication_delay),
        max_posts_per_day: parseInt(data.max_posts_per_day)
      };

      console.log('🔧 Saving network:', networkId, networkData);
      await networksService.updateNetwork(networkId, networkData);
      queryClient.invalidateQueries('networks');
      showToast('✅ Configuration mise à jour avec succès !', 'success');
      
      // Réinitialiser le formulaire
      setNetworkFormData(prev => {
        const newData = { ...prev };
        delete newData[networkId];
        return newData;
      });
    } catch (error) {
      console.error('❌ Network update error:', error);
      showToast(`❌ Erreur: ${error?.response?.data?.detail || error.message}`, 'error');
    } finally {
      setIsSavingNetwork(false);
    }
  };

  const handleNetworkFormChange = (networkId, field, value) => {
    setNetworkFormData(prev => ({
      ...prev,
      [networkId]: {
        ...(prev[networkId] || {}),
        [field]: value
      }
    }));
  };



  // Récupération de la file d'attente de publication
  const { data: queueData } = useQuery('publication-queue', () => 
    publicationQueueService.getQueue()
  );
  const queueItems = queueData?.data || [];
  
  // Debug pour voir les données
  console.log('🔍 Queue Items Debug:', queueItems);

  // Récupération des réseaux
  const { data: networksData, isLoading: networksLoading, error: networksError } = useQuery('networks', networksService.getNetworks);
  const networks = networksData?.data || [];
  
  // Debug logs
  console.log('🔍 Networks Debug:', { 
    networksData, 
    networks, 
    count: networks.length,
    isLoading: networksLoading,
    error: networksError,
    token: localStorage.getItem('token') ? 'Present' : 'Missing'
  });

  // Récupération des flux pour les filtres
  const { data: feedsData } = useQuery('feeds', feedsService.getFeeds);
  const feeds = feedsData?.data || [];


  // Mutations pour la file d'attente
  const pauseItemMutation = useMutation(publicationQueueService.pauseItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      queryClient.refetchQueries('publication-queue');
      // Forcer le refresh du dashboard
      queryClient.invalidateQueries('dashboard');
      queryClient.refetchQueries('dashboard');
    }
  });

  const resumeItemMutation = useMutation(publicationQueueService.resumeItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('publication-queue');
      queryClient.refetchQueries('publication-queue');
      // Forcer le refresh du dashboard
      queryClient.invalidateQueries('dashboard');
      queryClient.refetchQueries('dashboard');
    }
  });



  const handlePauseItem = (itemId) => {
    if (window.confirm('⏸️ Voulez-vous mettre cette publication en pause ?')) {
    pauseItemMutation.mutate(itemId);
    }
  };

  const handleResumeItem = (itemId) => {
    if (window.confirm('▶️ Voulez-vous reprendre cette publication ?')) {
    resumeItemMutation.mutate(itemId);
    }
  };

  // Calculer le temps restant avant publication avec secondes qui défilent
  const getTimeRemaining = (scheduledAt) => {
    if (!scheduledAt) return null;
    
    const now = new Date();
    const scheduled = new Date(scheduledAt);
    const diffMs = scheduled - now;
    const totalSeconds = Math.floor(diffMs / 1000);
    
    // Si le temps est dépassé
    if (totalSeconds < 0) {
      return { 
        text: 'Prêt à publier', 
        class: 'text-green-600 font-bold animate-pulse', 
        isPast: true,
        isScheduled: false 
      };
    }
    
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    // Programmé (≤ 10 minutes) - Afficher heures:minutes:secondes qui défilent
    if (totalSeconds <= 600) {
      let timeText;
      if (hours > 0) {
        timeText = `${hours}h ${String(minutes).padStart(2, '0')}m ${String(seconds).padStart(2, '0')}s`;
      } else if (minutes > 0) {
        timeText = `${minutes}m ${String(seconds).padStart(2, '0')}s`;
      } else {
        timeText = `${seconds}s`;
      }
      
      return { 
        text: timeText,
        class: 'text-blue-600 font-bold tabular-nums', 
        isPast: false,
        isScheduled: true 
      };
    }
    
    // En attente (> 10 minutes) - Pas besoin des secondes
    if (totalSeconds < 3600) {
      return { 
        text: `${minutes}min`, 
        class: 'text-yellow-600', 
        isPast: false,
        isScheduled: false 
      };
    } else if (totalSeconds < 86400) {
      const timeText = minutes > 0 ? `${hours}h ${minutes}min` : `${hours}h`;
      return { 
        text: timeText,
        class: 'text-yellow-600', 
        isPast: false,
        isScheduled: false 
      };
    } else {
      const days = Math.floor(totalSeconds / 86400);
      const remainingHours = Math.floor((totalSeconds % 86400) / 3600);
      return { 
        text: `${days}j ${remainingHours}h`, 
        class: 'text-yellow-600', 
        isPast: false,
        isScheduled: false 
      };
    }
  };



  const handlePauseAll = () => {
    // Pause uniquement les éléments filtrés
    const filteredItems = getFilteredQueueItems();
    const itemsToPause = filteredItems.filter(item => item.status === 'PENDING' && !item.is_paused);
    
    if (itemsToPause.length === 0) {
      alert('Aucun élément à mettre en pause dans le filtre actuel');
      return;
    }
    
    if (window.confirm(`⏸️ Mettre en pause ${itemsToPause.length} publication(s) ${feedFilter || networkFilter || statusFilter ? 'filtrée(s)' : ''} ?`)) {
      itemsToPause.forEach(item => {
        pauseItemMutation.mutate(item.id);
      });
    }
  };

  const handleResumeAll = () => {
    // Reprendre uniquement les éléments filtrés
    const filteredItems = getFilteredQueueItems();
    const itemsToResume = filteredItems.filter(item => item.status === 'PENDING' && item.is_paused);
    
    if (itemsToResume.length === 0) {
      alert('Aucun élément en pause dans le filtre actuel');
      return;
    }
    
    if (window.confirm(`▶️ Reprendre ${itemsToResume.length} publication(s) ${feedFilter || networkFilter || statusFilter ? 'filtrée(s)' : ''} ?`)) {
      itemsToResume.forEach(item => {
        resumeItemMutation.mutate(item.id);
      });
    }
  };

  // Fonction de filtrage des éléments de la file d'attente
  const getFilteredQueueItems = () => {
    return queueItems.filter(item => {
      // Filtre par flux
      if (feedFilter) {
        if (feedFilter === 'direct') {
          // Afficher uniquement les posts directs (feed_id NULL)
          if (item.feed_id !== null) return false;
        } else {
          // Afficher uniquement ce flux spécifique
          if (item.feed_id !== parseInt(feedFilter)) return false;
        }
      }
      
      // Filtre par réseau
      if (networkFilter && item.network !== networkFilter) {
        return false;
      }
      
      // Filtre par statut
      if (statusFilter) {
        if (statusFilter === 'PAUSED' && !item.is_paused) return false;
        if (statusFilter === 'SCHEDULED' && item.status !== 'SCHEDULED') return false;
        if (statusFilter === 'WAITING_HOURS' && item.status !== 'WAITING_HOURS') return false;
        if (statusFilter === 'PENDING' && item.status !== 'PENDING') return false;
        if (statusFilter === 'PUBLISHING' && item.status !== 'PUBLISHING') return false;
        if (statusFilter === 'PUBLISHED' && item.status !== 'PUBLISHED') return false;
        if (statusFilter === 'FAILED' && item.status !== 'FAILED') return false;
        if (statusFilter === 'CANCELLED' && item.status !== 'CANCELLED') return false;
      }
      
      return true;
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'SCHEDULED': return <FaClock className="text-blue-500" />;
      case 'WAITING_HOURS': return <FaClock className="text-purple-500" />;
      case 'PENDING': return <FaPlay className="text-yellow-500" />;
      case 'PUBLISHING': return <FaPlay className="text-indigo-500" />;
      case 'PUBLISHED': return <FaCheck className="text-green-500" />;
      case 'FAILED': return <FaTimes className="text-red-500" />;
      case 'CANCELLED': return <FaPause className="text-gray-500" />;
      default: return <FaClock className="text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'SCHEDULED': return 'bg-blue-100 text-blue-800';
      case 'WAITING_HOURS': return 'bg-purple-100 text-purple-800';
      case 'PENDING': return 'bg-yellow-100 text-yellow-800';
      case 'PUBLISHING': return 'bg-indigo-100 text-indigo-800';
      case 'PUBLISHED': return 'bg-green-100 text-green-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      case 'CANCELLED': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'SCHEDULED': return '📅 Programmés';
      case 'WAITING_HOURS': return '🕐 En attente d\'horaires';
      case 'PENDING': return '⏳ Prêts à publier';
      case 'PUBLISHING': return '⚡ En cours';
      case 'PUBLISHED': return '✅ Publiés';
      case 'FAILED': return '❌ Échecs';
      case 'CANCELLED': return '🚫 Annulés';
      default: return '❓ Inconnu';
    }
  };

  const getNetworkIcon = (network) => {
    return <SocialNetworkIcon network={network} size="w-5 h-5" />;
  };


  const renderQueueTab = () => (
    <div className="space-y-6">
      {/* Header avec actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">File d'attente de publication</h2>
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
            <button 
              onClick={() => setShowDirectPost(true)}
              className="px-3 sm:px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm sm:text-base"
            >
              <FaPlus className="inline mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Post direct</span>
              <span className="sm:hidden">Post</span>
            </button>
            <button 
              onClick={() => setShowNetworkConfig(true)}
              className="px-3 sm:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm sm:text-base"
            >
              <FaGlobe className="inline mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Configuration des réseaux</span>
              <span className="sm:hidden">Config</span>
            </button>
            
            {/* Boutons pour configurer les horaires par réseau */}
            {networks?.map(network => (
              <button
                key={network.network}
                onClick={() => {
                  setSelectedNetworkForSchedule(network.network);
                  setShowScheduleConfigModal(true);
                }}
                className="px-2 sm:px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-xs sm:text-sm"
                title={`Configurer les horaires pour ${network.network}`}
              >
                📅 {network.network.charAt(0).toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border-2 border-blue-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-blue-700 mb-1">
              {queueItems.filter(item => item.status === 'SCHEDULED' && !item.is_paused).length}
            </div>
            <div className="text-sm font-medium text-blue-600">📅 Programmés</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border-2 border-purple-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-purple-700 mb-1">
              {queueItems.filter(item => item.status === 'WAITING_HOURS' && !item.is_paused).length}
            </div>
            <div className="text-sm font-medium text-purple-600">🕐 En attente d'horaires</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl border-2 border-yellow-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-yellow-700 mb-1">
              {queueItems.filter(item => item.status === 'PENDING' && !item.is_paused).length}
          </div>
            <div className="text-sm font-medium text-yellow-600">⏳ Prêts à publier</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border-2 border-orange-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-orange-700 mb-1">{queueItems.filter(item => item.is_paused).length}</div>
            <div className="text-sm font-medium text-orange-600">⏸️ En pause</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl border-2 border-indigo-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-indigo-700 mb-1">{queueItems.filter(item => item.status === 'PUBLISHING').length}</div>
            <div className="text-sm font-medium text-indigo-600">⚡ En cours</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border-2 border-green-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-green-700 mb-1">{queueItems.filter(item => item.status === 'PUBLISHED').length}</div>
            <div className="text-sm font-medium text-green-600">✅ Publiés</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border-2 border-red-200 shadow-sm hover:shadow-md transition-all duration-200">
            <div className="text-3xl font-bold text-red-700 mb-1">{queueItems.filter(item => item.status === 'FAILED').length}</div>
            <div className="text-sm font-medium text-red-600">❌ Échecs</div>
          </div>
        </div>

        {/* Filtres */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Filtres</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="feedFilter" className="block text-sm font-medium text-gray-700 mb-1">
                🗂️ Flux / Type
              </label>
              <select
                id="feedFilter"
                value={feedFilter}
                onChange={(e) => setFeedFilter(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">📋 Tous les types</option>
                <optgroup label="Type de post">
                  <option value="direct">📤 Posts directs</option>
                </optgroup>
                <optgroup label="Flux RSS">
                {feeds.map(feed => (
                    <option key={feed.id} value={feed.id}>📰 {feed.name}</option>
                ))}
                </optgroup>
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
                <option value="SCHEDULED">📅 Programmés</option>
                <option value="WAITING_HOURS">🕐 En attente d'horaires</option>
                <option value="PENDING">⏳ Prêts à publier</option>
                <option value="PAUSED">⏸️ En pause</option>
                <option value="PUBLISHING">⚡ En cours</option>
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
                Effacer filtres
              </button>
            </div>
          </div>
        </div>

        {/* Actions globales */}
        <div className="mt-4 flex space-x-2">
          <button 
            onClick={handleResumeAll}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <FaPlay className="inline mr-2" />
            Reprendre tout
          </button>
          <button 
            onClick={handlePauseAll}
            className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
          >
            <FaPause className="inline mr-2" />
            Pause tout
          </button>
        </div>
      </div>

      {/* Liste des éléments */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
              <tr>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span className="hidden sm:inline">Contenu</span>
                  <span className="sm:hidden">Post</span>
                </th>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Réseau
                </th>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span className="hidden sm:inline">Countdown</span>
                  <span className="sm:hidden">Temps</span>
                </th>
                <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Planifié
                </th>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {getFilteredQueueItems().map((item) => {
                console.log('🔍 Item Debug:', { id: item.id, status: item.status, is_paused: item.is_paused });
                return (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors duration-150">
                  <td className="px-3 sm:px-6 py-4">
                    <div className="max-w-xs">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        <span className="hidden sm:inline">{item.content.substring(0, 100)}...</span>
                        <span className="sm:hidden">{item.content.substring(0, 50)}...</span>
                      </p>
                      <p className="text-xs text-gray-500">
                        {item.feed_id ? `Flux #${item.feed_id}` : '📤 Post direct'}
                      </p>
                    </div>
                  </td>
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="mr-2">{getNetworkIcon(item.network)}</span>
                      <span className="text-sm font-medium text-gray-900 capitalize hidden sm:inline">
                        {item.network}
                      </span>
                      <div className="ml-2">
                        {item.is_paused && <span className="text-orange-600 font-medium text-xs">⏸️ En pause</span>}
                      </div>
                    </div>
                  </td>
                  {/* Colonne Statut */}
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                      {getStatusIcon(item.status)}
                      <span className="ml-1 hidden sm:inline">{getStatusText(item.status)}</span>
                    </span>
                  </td>
                  
                  {/* Colonne Countdown */}
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                    {item.is_paused ? (
                      <div className="flex flex-col">
                        <span className="text-xs text-orange-600">
                          ⏸️ Chrono arrêté
                        </span>
                      </div>
                    ) : (item.status === 'PENDING' || item.status === 'SCHEDULED' || item.status === 'WAITING_HOURS') ? (
                      (() => {
                        const timeInfo = getTimeRemaining(item.scheduled_at);
                        
                        return (
                          <div className="flex flex-col">
                            {timeInfo && (
                              <span className={`text-xs ${timeInfo.class}`}>
                                {timeInfo.isPast ? '⚡ Prêt à publier' : `⏱️ ${timeInfo.text}`}
                              </span>
                            )}
                          </div>
                        );
                      })()
                    ) : (
                      <span className="text-xs text-gray-500">-</span>
                    )}
                  </td>
                  <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.scheduled_at ? format(new Date(item.scheduled_at), 'dd/MM/yyyy HH:mm', { locale: fr }) : '-'}
                  </td>
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {item.status === 'PUBLISHED' ? (
                        <div className="flex items-center space-x-2">
                          <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-green-100 text-green-700">
                            <FaCheck className="mr-1" />
                            Publié
                          </span>
                          {item.publication_url && (
                            <a
                              href={item.publication_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-all duration-200"
                              title="Voir la publication"
                            >
                              <FaExternalLinkAlt className="w-4 h-4" />
                            </a>
                          )}
                        </div>
                      ) : item.status === 'FAILED' ? (
                        <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-red-100 text-red-700">
                          <FaTimes className="mr-1" />
                          Échec
                        </span>
                      ) : item.is_paused ? (
                        <button
                          onClick={() => handleResumeItem(item.id)}
                          className="p-2 text-green-600 hover:text-green-800 hover:bg-green-50 rounded-lg transition-all duration-200"
                          title="Reprendre"
                        >
                          <FaPlay className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handlePauseItem(item.id)}
                          className="p-2 text-yellow-600 hover:text-yellow-800 hover:bg-yellow-50 rounded-lg transition-all duration-200"
                          title="Mettre en pause"
                        >
                          <FaPause className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
                );
              })}
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

  const renderNetworkConfigModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Configuration Globale des Réseaux</h2>
              <p className="text-indigo-100 mt-1">Délais, limites et horaires pour tous les flux RSS</p>
            </div>
            <button
              onClick={() => setShowNetworkConfig(false)}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-all"
            >
              <FaTimes className="w-6 h-6" />
            </button>
          </div>
          </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {networks.map(network => {
              const formData = networkFormData[network.id] || {
                is_active: network.is_active,
                default_publication_delay: network.default_publication_delay,
                max_posts_per_day: network.max_posts_per_day
              };
              
              const Icon = network.network === 'facebook' ? FaFacebook : network.network === 'linkedin' ? FaLinkedin : FaTwitter;
              const color = network.network === 'facebook' ? '#1877F2' : network.network === 'linkedin' ? '#0A66C2' : '#000000';

              return (
                <div key={network.id} className="border-2 border-gray-200 rounded-xl bg-white shadow-lg hover:shadow-xl transition-all">
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 flex items-center justify-center bg-gray-50 rounded-full">
                          <Icon style={{ color, fontSize: '24px' }} />
                        </div>
            <div>
                          <h3 className="text-lg font-bold text-gray-900">
                            {network.network === 'x' ? 'X (Twitter)' : network.network.charAt(0).toUpperCase() + network.network.slice(1)}
                          </h3>
                        </div>
                      </div>
            </div>

                    {/* Toggle */}
                    <div className="mb-6">
                      <label className="flex items-center justify-between cursor-pointer">
                        <span className="text-sm font-bold text-gray-700">Statut</span>
                        <button
                          type="button"
                          onClick={() => handleNetworkFormChange(network.id, 'is_active', !formData.is_active)}
                          className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                            formData.is_active ? 'bg-green-500' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform ${
                              formData.is_active ? 'translate-x-7' : 'translate-x-1'
                            }`}
                          />
                        </button>
                </label>
              </div>

                    {/* Form */}
                    <div className="space-y-4">
              <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                          ⏱️ Délai (min)
                </label>
                <input
                  type="number"
                          value={formData.default_publication_delay}
                          onChange={(e) => handleNetworkFormChange(network.id, 'default_publication_delay', e.target.value)}
                          min="1"
                          className="w-full p-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                          📊 Max/jour
                </label>
                <input
                          type="number"
                          value={formData.max_posts_per_day}
                          onChange={(e) => handleNetworkFormChange(network.id, 'max_posts_per_day', e.target.value)}
                          min="1"
                          className="w-full p-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
            </div>

              <button
                        onClick={() => handleSaveNetwork(network.id)}
                        disabled={isSavingNetwork}
                        className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-bold hover:shadow-lg disabled:opacity-50 transition-all"
                      >
                        {isSavingNetwork ? (
                          <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            Sauvegarde...
                          </div>
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
            })}
          </div>
        </div>
      </div>
    </div>
  );

  const [directPostData, setDirectPostData] = useState({
    sourceContent: '',
    customPrompt: '',
    network: 'facebook',
    targetPageId: '',
    useAI: false,
    generatedContent: '',
    isGenerating: false,
    imageFile: null,
    imageUrl: '',
    linkUrl: ''
  });

  const [blotatoAccounts, setBlotatoAccounts] = useState(null);

  useEffect(() => {
    if (showDirectPost) {
      fetchBlotatoAccounts();
    }
  }, [showDirectPost]);

  const fetchBlotatoAccounts = async () => {
    try {
      const response = await api.get('/blotato-accounts/');
      setBlotatoAccounts(response.data);
    } catch (error) {
      console.error('❌ Erreur:', error);
    }
  };

  const handleGenerateContent = async () => {
    if (!directPostData.sourceContent) {
      alert('⚠️ Veuillez saisir le contenu source');
      return;
    }

    setDirectPostData(prev => ({ ...prev, isGenerating: true }));

    try {
      // Construire le contenu avec le lien si fourni
      let contentToGenerate = directPostData.sourceContent;
      if (directPostData.linkUrl) {
        contentToGenerate += `\n\nLien: ${directPostData.linkUrl}`;
      }

      // Utiliser le prompt personnalisé si fourni
      const customPrompt = directPostData.customPrompt || null;

      // Générer le contenu via l'API
      const response = await api.post('/test-generation', {
        network: directPostData.network,
        content: contentToGenerate,
        custom_prompt: customPrompt
      });

      let generated = response.data?.generated_content || directPostData.sourceContent;
      
      // Ajouter le lien à la fin si fourni (pour être sûr qu'il apparaît)
      if (directPostData.linkUrl && !generated.includes(directPostData.linkUrl)) {
        generated += `\n\n🔗 ${directPostData.linkUrl}`;
      }
      
      setDirectPostData(prev => ({
        ...prev,
        generatedContent: generated || 'Erreur de génération',
        isGenerating: false
      }));
    } catch (error) {
      console.error('❌ Erreur génération:', error);
      alert('❌ Erreur lors de la génération du contenu');
      setDirectPostData(prev => ({ ...prev, isGenerating: false }));
    }
  };

  const handlePublishDirectPost = async () => {
    let content = directPostData.generatedContent || directPostData.sourceContent;
    
    if (!content) {
      alert('⚠️ Veuillez saisir ou générer du contenu');
      return;
    }

    if (!directPostData.network) {
      alert('⚠️ Veuillez sélectionner un réseau');
      return;
    }

    if (!directPostData.targetPageId) {
      alert('⚠️ Veuillez sélectionner une page de destination');
      return;
    }

    // Ajouter le lien à la fin du contenu si fourni et pas déjà présent
    if (directPostData.linkUrl && !content.includes(directPostData.linkUrl)) {
      content += `\n\n🔗 ${directPostData.linkUrl}`;
    }

    if (window.confirm('📤 Publier ce post IMMÉDIATEMENT (pas de file d\'attente) ?')) {
      try {
        let mediaUrls = [];
        
        // Si une image a été uploadée, l'uploader d'abord
        if (directPostData.imageFile) {
          const formData = new FormData();
          formData.append('file', directPostData.imageFile);
          
          try {
            // Upload de l'image (vous devrez créer cet endpoint)
            const uploadResponse = await api.post('/upload/image', formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            });
            
            if (uploadResponse.data?.url) {
              mediaUrls = [uploadResponse.data.url];
            }
          } catch (uploadError) {
            console.error('❌ Erreur upload image:', uploadError);
            // Continuer sans image si l'upload échoue
            alert('⚠️ Impossible d\'uploader l\'image, publication sans image');
          }
        }
        
        // Créer directement l'entrée dans PublicationQueue
        const response = await api.post('/direct-post/', {
          network: directPostData.network,
          content: content,
          target_page_id: directPostData.targetPageId,
          media_urls: mediaUrls
        });

        // Afficher l'URL de publication si disponible
        if (response.data?.publication_url) {
          alert(`✅ Post publié avec succès !\n\n🔗 Voir le post:\n${response.data.publication_url}`);
        } else {
          showToast('✅ Post publié avec succès !');
        }
        
        // Nettoyer l'URL de l'image si créée
        if (directPostData.imageUrl && directPostData.imageFile) {
          URL.revokeObjectURL(directPostData.imageUrl);
        }
        
        setShowDirectPost(false);
        setDirectPostData({
          sourceContent: '',
          customPrompt: '',
          network: 'facebook',
          targetPageId: '',
          useAI: false,
          generatedContent: '',
          isGenerating: false,
          imageFile: null,
          imageUrl: '',
          linkUrl: ''
        });
        
        // Rafraîchir l'historique (pas la queue)
        queryClient.invalidateQueries('history');
      } catch (error) {
        console.error('❌ Erreur:', error);
        alert(`❌ Erreur : ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const getNetworkPages = (networkType) => {
    if (!blotatoAccounts) return [];
    
    if (networkType === 'facebook' && blotatoAccounts.facebook) {
      return blotatoAccounts.facebook.flatMap(account => 
        account.pages.map(page => ({
          id: page.pageId,
          name: page.pageName
        }))
      );
    }
    
    if (networkType === 'linkedin' && blotatoAccounts.linkedin) {
      return blotatoAccounts.linkedin.map(account => ({
        id: account.accountId,
        name: account.accountName
      }));
    }
    
    if (networkType === 'x' && blotatoAccounts.x) {
      return blotatoAccounts.x.map(account => ({
        id: account.accountId,
        name: account.accountName
      }));
    }
    
    return [];
  };

  const renderDirectPostModal = () => {
    const Icon = directPostData.network === 'facebook' ? FaFacebook : directPostData.network === 'linkedin' ? FaLinkedin : FaTwitter;
    const color = directPostData.network === 'facebook' ? '#1877F2' : directPostData.network === 'linkedin' ? '#0A66C2' : '#000000';

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold">Créer un post direct</h2>
                <p className="text-indigo-100 mt-1">Publication immédiate sur un réseau social</p>
              </div>
            <button
                onClick={() => setShowDirectPost(false)}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-all"
            >
              <FaTimes className="w-6 h-6" />
            </button>
                  </div>
                </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Réseau et Page */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Réseau */}
                  <div>
                <label className="block text-sm font-bold text-gray-700 mb-3">
                  🌐 Réseau social *
                    </label>
                <div className="space-y-2">
                  {['facebook', 'linkedin', 'x'].map(network => {
                    const NetworkIcon = network === 'facebook' ? FaFacebook : network === 'linkedin' ? FaLinkedin : FaTwitter;
                    const networkColor = network === 'facebook' ? '#1877F2' : network === 'linkedin' ? '#0A66C2' : '#000000';
                    const isSelected = directPostData.network === network;

                    return (
                      <label
                        key={network}
                        className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-all ${
                          isSelected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                    <input
                          type="radio"
                          value={network}
                          checked={isSelected}
                          onChange={(e) => setDirectPostData(prev => ({ ...prev, network: e.target.value, targetPageId: '' }))}
                          className="sr-only"
                        />
                        <NetworkIcon style={{ color: networkColor, fontSize: '24px' }} className="mr-3" />
                        <span className="font-medium capitalize">{network === 'x' ? 'X (Twitter)' : network}</span>
                        {isSelected && <FaCheck className="ml-auto text-indigo-600" />}
                      </label>
                    );
                  })}
                  </div>
                  </div>

              {/* Page de destination */}
                  <div>
                <label className="block text-sm font-bold text-gray-700 mb-3">
                  📄 Page de destination *
                    </label>
                {!blotatoAccounts ? (
                  <div className="flex items-center justify-center py-10 bg-gray-50 rounded-lg">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600 mr-2"></div>
                    <span className="text-gray-600">Chargement...</span>
                  </div>
                ) : (
                  <>
                    <select
                      value={directPostData.targetPageId}
                      onChange={(e) => setDirectPostData(prev => ({ ...prev, targetPageId: e.target.value }))}
                      className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="">-- Sélectionnez --</option>
                      {getNetworkPages(directPostData.network).map(page => (
                        <option key={page.id} value={page.id}>
                          {page.name}
                        </option>
                      ))}
                    </select>
                    {directPostData.targetPageId && (
                      <div className="mt-2 bg-green-50 border-l-4 border-green-500 p-3 rounded-r">
                        <p className="text-sm text-green-700 font-medium">
                          ✅ {getNetworkPages(directPostData.network).find(p => p.id === directPostData.targetPageId)?.name}
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
                  </div>

            {/* Upload Image (optionnel) */}
            <div className="p-6 bg-white rounded-xl shadow-sm border-2 border-gray-200">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                🖼️ Image (optionnel)
              </h3>

              <div className="space-y-4">
                {/* Upload d'image */}
                  <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">
                    📸 Ajouter une image
                    </label>
                  
                  <div className="flex items-center justify-center w-full">
                    <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <FaImage className="w-10 h-10 text-gray-400 mb-3" />
                        <p className="mb-2 text-sm text-gray-500">
                          <span className="font-semibold">Cliquez pour uploader</span> ou glissez-déposez
                        </p>
                        <p className="text-xs text-gray-500">PNG, JPG ou JPEG (max 10MB)</p>
                      </div>
                    <input
                        type="file" 
                        className="hidden" 
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) {
                            // Vérifier la taille (10MB max)
                            if (file.size > 10 * 1024 * 1024) {
                              alert('❌ Fichier trop volumineux (max 10MB)');
                              return;
                            }
                            
                            // Créer une URL locale pour l'aperçu
                            const imageUrl = URL.createObjectURL(file);
                            setDirectPostData(prev => ({ 
                              ...prev, 
                              imageFile: file,
                              imageUrl: imageUrl 
                            }));
                          }
                        }}
                      />
                    </label>
                  </div>

                  {/* Aperçu de l'image uploadée */}
                  {directPostData.imageUrl && (
                    <div className="mt-3 relative">
                      <img 
                        src={directPostData.imageUrl} 
                        alt="Aperçu" 
                        className="w-full h-64 object-cover rounded-lg border-2 border-indigo-200"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (directPostData.imageUrl) {
                            URL.revokeObjectURL(directPostData.imageUrl);
                          }
                          setDirectPostData(prev => ({ 
                            ...prev, 
                            imageFile: null,
                            imageUrl: '' 
                          }));
                        }}
                        className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors shadow-lg"
                      >
                        <FaTimes />
                    </button>
                      {directPostData.imageFile && (
                        <div className="mt-2 text-sm text-gray-600">
                          📎 {directPostData.imageFile.name} ({(directPostData.imageFile.size / 1024).toFixed(0)} KB)
                  </div>
                      )}
                </div>
                  )}
              </div>
          </div>
        </div>

            {/* Mode de création */}
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-xl p-6">
              <label className="flex items-center cursor-pointer mb-4">
                    <input
                  type="checkbox"
                  checked={directPostData.useAI}
                  onChange={(e) => setDirectPostData(prev => ({ ...prev, useAI: e.target.checked, generatedContent: '', sourceContent: '' }))}
                  className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                />
                <span className="ml-3 text-lg font-bold text-gray-900">
                  🤖 Utiliser l'IA pour générer le contenu
                </span>
              </label>

              {directPostData.useAI ? (
                <div className="space-y-4">
                  {/* Prompt */}
                  <div>
                    <label className="block text-sm font-bold text-purple-900 mb-2">
                      💬 Prompt personnalisé (optionnel)
                    </label>
                    <textarea
                      value={directPostData.customPrompt}
                      onChange={(e) => setDirectPostData(prev => ({ ...prev, customPrompt: e.target.value }))}
                      className="w-full p-4 border-2 border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white"
                      rows={2}
                      placeholder="Ex: Crée un post engageant et professionnel avec des emojis..."
                    />
                    <p className="text-xs text-purple-600 mt-1">
                      Instructions pour l'IA sur comment transformer votre contenu
                    </p>
      </div>

                  {/* Contenu source */}
                  <div>
                    <label className="block text-sm font-bold text-purple-900 mb-2">
                      📝 Contenu source *
                    </label>
                    <textarea
                      value={directPostData.sourceContent}
                      onChange={(e) => setDirectPostData(prev => ({ ...prev, sourceContent: e.target.value }))}
                      className="w-full p-4 border-2 border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white"
                      rows={4}
                      placeholder="Texte de base que l'IA va transformer..."
                    />
    </div>

                  {/* Bouton générer */}
            <button
                    type="button"
                    onClick={handleGenerateContent}
                    disabled={directPostData.isGenerating || !directPostData.sourceContent}
                    className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold text-lg shadow-lg hover:shadow-xl"
                  >
                    {directPostData.isGenerating ? (
                      <>
                        <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Génération en cours...
                      </>
                    ) : (
                      <>
                        ✨ Générer le contenu avec l'IA
                      </>
                    )}
            </button>

                  {/* Résultat généré */}
                  {directPostData.generatedContent && (
                    <div className="mt-4 p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                      <label className="block text-sm font-bold text-green-900 mb-2">
                        ✅ Contenu généré (éditable)
                    </label>
                      <textarea
                        value={directPostData.generatedContent}
                        onChange={(e) => setDirectPostData(prev => ({ ...prev, generatedContent: e.target.value }))}
                        className="w-full p-4 border-2 border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
                        rows={6}
                    />
                  </div>
                  )}
                </div>
              ) : (
                  <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">
                    📝 Contenu du post *
                    </label>
                  <textarea
                    value={directPostData.sourceContent}
                    onChange={(e) => setDirectPostData(prev => ({ ...prev, sourceContent: e.target.value }))}
                    className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    rows={8}
                    placeholder="Saisissez directement le contenu final à publier..."
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Mode manuel : Le texte sera publié tel quel
                  </p>
                </div>
              )}
                  </div>
                </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowDirectPost(false)}
              className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors font-medium"
            >
              Annuler
                  </button>
            <button
              type="button"
              onClick={handlePublishDirectPost}
              disabled={
                !directPostData.targetPageId || 
                (!directPostData.sourceContent && !directPostData.generatedContent)
              }
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold"
            >
              <FaCheck className="inline mr-2" />
              {directPostData.useAI && directPostData.generatedContent 
                ? 'Publier le contenu généré' 
                : 'Publier maintenant'
              }
                  </button>
        </div>
      </div>
    </div>
  );
  };

  const renderEditPostModal = () => (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Modifier le post</h3>
            <button
              onClick={() => setEditingPost(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <FaTimes className="w-6 h-6" />
            </button>
          </div>

          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contenu
              </label>
              <textarea
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                rows={4}
                defaultValue={editingPost?.content || ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Images
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <FaImage className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-600">
                  Cliquez pour changer les images
                </p>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  className="hidden"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setEditingPost(null)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                <FaSave className="inline mr-2" />
                Sauvegarder
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );

  const tabs = [
    { id: 'queue', label: 'File d\'attente', icon: FaClock, count: queueItems.length }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gestion des publications</h1>
          <p className="text-gray-600 mt-2">
            Gérez votre file d'attente de publication et créez des posts directs
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
          {activeTab === 'queue' && renderQueueTab()}
        </div>

        {/* Modals */}
        {showDirectPost && renderDirectPostModal()}
        {showNetworkConfig && renderNetworkConfigModal()}
        {editingPost && renderEditPostModal()}

        {/* Modal de configuration des horaires */}
        <ScheduleConfigModal
          isOpen={showScheduleConfigModal}
          onClose={() => {
            setShowScheduleConfigModal(false);
            setSelectedNetworkForSchedule(null);
          }}
          network={selectedNetworkForSchedule}
          onSave={() => {
            console.log('Horaires sauvegardés pour', selectedNetworkForSchedule);
          }}
        />
      </div>
    </div>
  );
};

export default UnifiedPublication;
