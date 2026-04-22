import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { FaRss, FaFileAlt, FaClock, FaHistory, FaCheck, FaTimes, FaSync } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { feedsService, postsService, publicationQueueService, DEFAULT_PAGE_SIZE } from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: feedsData = [], isLoading: feedsLoading } = useQuery(
    ['feeds', 'dashboard'],
    () => feedsService.getFeeds({ page: 1, pageSize: DEFAULT_PAGE_SIZE }),
    {
      refetchInterval: 10000,
      refetchIntervalInBackground: true
    }
  );
  const { data: draftsData = [], isLoading: draftsLoading } = useQuery(
    ['drafts', 'dashboard'],
    () => postsService.getDrafts({ page: 1, pageSize: DEFAULT_PAGE_SIZE }),
    {
      refetchInterval: 10000,
      refetchIntervalInBackground: true
    }
  );
  const { data: validatedData = [], isLoading: validatedLoading } = useQuery(
    ['validated', 'dashboard'],
    () => postsService.getValidated({ page: 1, pageSize: DEFAULT_PAGE_SIZE }),
    {
      refetchInterval: 10000,
      refetchIntervalInBackground: true
    }
  );
  const { data: queueData = [], isLoading: queueLoading, refetch: refetchQueue } = useQuery(
    ['publication-queue', 'dashboard'],
    () => publicationQueueService.getQueue({}, { page: 1, pageSize: DEFAULT_PAGE_SIZE }),
    {
    refetchInterval: 3000, // Rafraîchir toutes les 3 secondes
    refetchIntervalInBackground: true,
    staleTime: 0, // Toujours considérer les données comme périmées
    cacheTime: 0, // Ne pas mettre en cache
    refetchOnWindowFocus: true, // Rafraîchir quand la fenêtre reprend le focus
    refetchOnMount: true, // Rafraîchir au montage
    onSuccess: () => {
      setLastRefresh(new Date());
      setIsRefreshing(false);
    },
    onFetching: () => {
      setIsRefreshing(true);
    }
  });
  const { data: publishedData = [], isLoading: historyLoading } = useQuery(
    'dashboard-history',
    () => publicationQueueService.getQueue({ status: 'PUBLISHED' }, { page: 1, pageSize: DEFAULT_PAGE_SIZE })
  );

  const feeds = Array.isArray(feedsData?.data) ? feedsData.data : Array.isArray(feedsData) ? feedsData : [];
  const drafts = Array.isArray(draftsData?.data) ? draftsData.data : Array.isArray(draftsData) ? draftsData : [];
  const validated = Array.isArray(validatedData?.data) ? validatedData.data : Array.isArray(validatedData) ? validatedData : [];
  const queue = Array.isArray(queueData?.data) ? queueData.data : Array.isArray(queueData) ? queueData : [];
  const history = Array.isArray(publishedData?.data) ? publishedData.data : Array.isArray(publishedData) ? publishedData : [];

  const feedsTotal = feedsData?.pagination?.total ?? feeds.length;
  const draftsTotal = draftsData?.pagination?.total ?? drafts.length;
  const validatedTotal = validatedData?.pagination?.total ?? validated.length;
  const queueTotal = queueData?.pagination?.total ?? queue.length;


  // Calculer le temps restant
  const getTimeRemaining = (scheduledAt) => {
    if (!scheduledAt) return null;
    const now = new Date();
    const scheduled = new Date(scheduledAt);
    const diffMs = scheduled - now;
    const diffMinutes = Math.floor(diffMs / 60000);
    return { diffMinutes, isScheduled: diffMinutes <= 10 };
  };

  // Statistiques détaillées de la file d'attente
  const queueStats = {
    total: queueTotal,
    scheduled: queue?.filter(item => {
      if (item.status !== 'PENDING' || item.is_paused) return false;
      const timeInfo = getTimeRemaining(item.scheduled_at);
      return timeInfo?.isScheduled;
    })?.length || 0,
    pending: queue?.filter(item => {
      if (item.status !== 'PENDING' || item.is_paused) return false;
      const timeInfo = getTimeRemaining(item.scheduled_at);
      return !timeInfo?.isScheduled;
    })?.length || 0,
    paused: queue?.filter(item => item.is_paused)?.length || 0,
    publishing: queue?.filter(item => item.status === 'PUBLISHING')?.length || 0,
    published: queue?.filter(item => item.status === 'PUBLISHED')?.length || 0,
    failed: queue?.filter(item => item.status === 'FAILED')?.length || 0
  };
  
  const stats = [
    {
      name: 'Flux RSS',
      value: feedsTotal,
      icon: FaRss,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      name: 'Posts Brouillons',
      value: draftsTotal,
      icon: FaFileAlt,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100'
    },
    {
      name: 'Posts Validés',
      value: validatedTotal,
      icon: FaCheck,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      name: 'File d\'attente',
      value: queueTotal,
      icon: FaClock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ];

  const isLoading = feedsLoading || draftsLoading || validatedLoading || queueLoading;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-2 text-gray-600">Vue d'ensemble de votre système de publication</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                {isRefreshing ? (
                  <>
                    <FaSync className="w-4 h-4 text-blue-500 animate-spin" />
                    <span>Mise à jour en cours...</span>
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span>Mise à jour en temps réel</span>
                  </>
                )}
                <span className="text-xs text-gray-400">
                  Dernière mise à jour: {format(lastRefresh, 'HH:mm:ss', { locale: fr })}
                </span>
              </div>
              <button
                onClick={() => {
                  setIsRefreshing(true);
                  refetchQueue();
                }}
                disabled={isRefreshing}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-1"
              >
                <FaSync className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>Actualiser</span>
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <div key={stat.name} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Statistiques détaillées de la file d'attente */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">État de la file d'attente</h2>
            <p className="text-sm text-gray-600">Statistiques détaillées des publications en cours</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
                <div className="text-3xl font-bold text-blue-700">{queueStats.scheduled}</div>
                <div className="text-sm font-medium text-blue-600">Programmés</div>
                <p className="text-xs text-blue-500 mt-1">≤ 10 min</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                <div className="text-3xl font-bold text-yellow-700">{queueStats.pending}</div>
                <div className="text-sm font-medium text-yellow-600">En attente</div>
                <p className="text-xs text-yellow-500 mt-1">+ de 10 min</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg border-2 border-orange-200">
                <div className="text-3xl font-bold text-orange-700">{queueStats.paused}</div>
                <div className="text-sm font-medium text-orange-600">En pause</div>
              </div>
              <div className="text-center p-4 bg-indigo-50 rounded-lg border-2 border-indigo-200">
                <div className="text-3xl font-bold text-indigo-700">{queueStats.publishing}</div>
                <div className="text-sm font-medium text-indigo-600">En cours</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg border-2 border-green-200">
                <div className="text-3xl font-bold text-green-700">{queueStats.published}</div>
                <div className="text-sm font-medium text-green-600">Publiés</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg border-2 border-red-200">
                <div className="text-3xl font-bold text-red-700">{queueStats.failed}</div>
                <div className="text-sm font-medium text-red-600">Échecs</div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Posts */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Posts Récents</h2>
            </div>
            <div className="p-6">
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  <p className="mt-2 text-gray-600">Chargement...</p>
                </div>
              ) : (drafts?.length || 0) === 0 ? (
                <div className="text-center py-8">
                  <FaFileAlt className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-gray-500">Aucun post récent</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {drafts.slice(0, 5).map((post) => (
                    <div key={post.id} className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                          <FaFileAlt className="w-4 h-4 text-yellow-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {post.title}
                        </p>
                        <p className="text-xs text-gray-500">
                          {format(new Date(post.created_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}
                        </p>
                      </div>
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Brouillon
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent History */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Historique Récent</h2>
            </div>
            <div className="p-6">
              {historyLoading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  <p className="mt-2 text-gray-600">Chargement...</p>
                </div>
              ) : (history?.length || 0) === 0 ? (
                <div className="text-center py-8">
                  <FaHistory className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-gray-500">Aucun historique</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.slice(0, 5).map((item) => (
                    <div key={item.id} className="flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg">
                      <div className="flex-shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          item.status === 'PUBLISHED' ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                          {item.status === 'PUBLISHED' ? (
                            <FaCheck className="w-4 h-4 text-green-600" />
                          ) : (
                            <FaTimes className="w-4 h-4 text-red-600" />
                          )}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 capitalize">
                          {item.network}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {item.content?.substring(0, 50)}...
                        </p>
                        <p className="text-xs text-gray-400">
                          {item.published_at ? 
                            format(new Date(item.published_at), 'dd/MM/yyyy à HH:mm', { locale: fr }) :
                            'Date inconnue'
                          }
                        </p>
                      </div>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        item.status === 'PUBLISHED'
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {item.status === 'PUBLISHED' ? 'Publié' : 'Échec'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions Rapides</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => navigate('/feeds')}
              className="flex items-center justify-center px-4 py-3 border-2 border-blue-300 bg-blue-50 rounded-lg hover:bg-blue-100 hover:border-blue-400 transition-all shadow-sm hover:shadow-md"
            >
              <FaRss className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm font-semibold text-blue-700">Gérer les flux RSS</span>
            </button>
            <button 
              onClick={() => navigate('/posts')}
              className="flex items-center justify-center px-4 py-3 border-2 border-yellow-300 bg-yellow-50 rounded-lg hover:bg-yellow-100 hover:border-yellow-400 transition-all shadow-sm hover:shadow-md"
            >
              <FaFileAlt className="w-5 h-5 text-yellow-600 mr-2" />
              <span className="text-sm font-semibold text-yellow-700">Voir les posts</span>
            </button>
            <button 
              onClick={() => navigate('/history')}
              className="flex items-center justify-center px-4 py-3 border-2 border-gray-300 bg-gray-50 rounded-lg hover:bg-gray-100 hover:border-gray-400 transition-all shadow-sm hover:shadow-md"
            >
              <FaHistory className="w-5 h-5 text-gray-600 mr-2" />
              <span className="text-sm font-semibold text-gray-700">Voir l'historique</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;