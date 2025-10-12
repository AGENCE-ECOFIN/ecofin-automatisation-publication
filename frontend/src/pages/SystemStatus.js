import React from 'react';
import { useQuery } from 'react-query';
import { FaCheck, FaTimes, FaExclamationTriangle, FaClock, FaSpinner, FaServer, FaTasks, FaPlay, FaPause } from 'react-icons/fa';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { feedsService, tasksService } from '../services/api';

const SystemStatus = () => {
  const { data: statusData = {}, isLoading, error } = useQuery('collection-status', feedsService.getCollectionStatus);
  const { data: tasksData = {}, isLoading: tasksLoading, error: tasksError } = useQuery('tasks-history', tasksService.getTasksHistory);
  
  const feeds = statusData?.feeds || [];
  
  // Données des tâches Celery
  const workers = tasksData?.workers || {};
  const workerCount = tasksData?.worker_count || 0;
  const activeTaskCount = tasksData?.active_task_count || 0;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'recent':
        return <FaCheck className="text-green-500" />;
      case 'overdue':
        return <FaExclamationTriangle className="text-yellow-500" />;
      case 'stale':
        return <FaTimes className="text-red-500" />;
      case 'never_collected':
        return <FaClock className="text-gray-500" />;
      default:
        return <FaSpinner className="text-blue-500 animate-spin" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'recent':
        return 'Collecté récemment';
      case 'overdue':
        return 'En retard';
      case 'stale':
        return 'Obsolète';
      case 'never_collected':
        return 'Jamais collecté';
      default:
        return 'Inconnu';
    }
  };


  const getWorkerStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <FaCheck className="text-green-500" />;
      case 'offline':
        return <FaTimes className="text-red-500" />;
      default:
        return <FaClock className="text-gray-500" />;
    }
  };

  const getTaskStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <FaPlay className="text-blue-500" />;
      case 'scheduled':
        return <FaClock className="text-yellow-500" />;
      case 'reserved':
        return <FaPause className="text-orange-500" />;
      default:
        return <FaTasks className="text-gray-500" />;
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Statut du Système</h1>
      <p className="text-gray-600 mb-8">
        Surveillez l'état des collectes RSS et des tâches Celery en temps réel.
      </p>

      {isLoading || tasksLoading ? (
        <div className="text-center p-10">
          <FaSpinner className="animate-spin text-indigo-600 text-4xl mx-auto mb-4" />
          <p className="text-gray-700">Chargement du statut du système...</p>
        </div>
      ) : error || tasksError ? (
        <div className="text-center p-10 text-red-600">
          <p>Erreur lors du chargement: {error?.message || tasksError?.message}</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Statistiques générales */}
          <div className="bg-white shadow-lg rounded-xl p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Statistiques Générales</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaServer className="text-blue-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Workers Actifs</p>
                    <p className="text-2xl font-bold text-blue-600">{workerCount}</p>
                  </div>
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaTasks className="text-green-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Tâches Actives</p>
                    <p className="text-2xl font-bold text-green-600">{activeTaskCount}</p>
                  </div>
                </div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaClock className="text-purple-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Flux RSS</p>
                    <p className="text-2xl font-bold text-purple-600">{feeds.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaPlay className="text-orange-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Dernière Mise à Jour</p>
                    <p className="text-sm font-medium text-orange-600">
                      {tasksData?.timestamp ? format(new Date(tasksData.timestamp), 'dd/MM/yyyy HH:mm', { locale: fr }) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Workers Celery */}
          <div className="bg-white shadow-lg rounded-xl p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Workers Celery</h2>
            {Object.keys(workers).length === 0 ? (
              <p className="text-gray-700">Aucun worker actif.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(workers).map(([workerName, workerInfo]) => (
                  <div key={workerName} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-medium text-gray-900">{workerName}</h3>
                      {getWorkerStatusIcon(workerInfo.status)}
                    </div>
                    <div className="space-y-2 text-sm text-gray-600">
                      <p><strong>Tâches totales:</strong> {workerInfo.total_tasks || 0}</p>
                      <p><strong>Pool size:</strong> {workerInfo.pool?.max_concurrency || 0}</p>
                      <p><strong>Current load:</strong> {workerInfo.pool?.current_load || 0}</p>
                      {workerInfo.rusage && (
                        <p><strong>CPU:</strong> {workerInfo.rusage.utime || 0}s</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tâches actives */}
          <div className="bg-white shadow-lg rounded-xl p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Tâches Actives</h2>
            {activeTaskCount === 0 ? (
              <p className="text-gray-700">Aucune tâche active.</p>
            ) : (
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-700 mb-3 flex items-center">
                    <FaServer className="text-blue-500 mr-2" />
                    Tâches en cours
                  </h3>
                  <p className="text-sm text-gray-600">
                    {activeTaskCount} tâche(s) active(s)
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Statut des flux RSS */}
          <div className="bg-white shadow-lg rounded-xl p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Statut des Flux RSS</h2>
            {feeds.length === 0 ? (
              <p className="text-gray-700">Aucun flux trouvé ou actif.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {feeds.map((feed) => (
                  <div key={feed.id} className="border border-gray-200 rounded-lg p-4 flex flex-col space-y-2">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(feed.collection_status)}
                      <h3 className="text-lg font-medium text-gray-900">{feed.name}</h3>
                    </div>
                    <p className="text-sm text-gray-600">URL: <a href={feed.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">{feed.url}</a></p>
                    <p className="text-sm text-gray-600">Fréquence: {feed.frequency_minutes} minutes</p>
                    <p className="text-sm text-gray-600">
                      Dernière collecte: {feed.last_fetch ? format(parseISO(feed.last_fetch), 'dd/MM/yyyy HH:mm', { locale: fr }) : 'Jamais'}
                      {feed.last_fetch && ` (${formatDistanceToNow(parseISO(feed.last_fetch), { addSuffix: true, locale: fr })})`}
                    </p>
                    <p className="text-sm font-semibold text-gray-700">Statut: {getStatusText(feed.collection_status)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemStatus;

