import React from 'react';
import { useQuery } from 'react-query';
import { FaCheck, FaTimes, FaExclamationTriangle, FaClock, FaSpinner, FaServer, FaTasks, FaPlay, FaPause } from 'react-icons/fa';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { feedsService, tasksService } from '../services/api';

const CollectionStatus = () => {
  const { data: statusData = {}, isLoading, error } = useQuery('collection-status', feedsService.getCollectionStatus);
  const { data: tasksData = {}, isLoading: tasksLoading, error: tasksError } = useQuery('tasks-history', tasksService.getTasksHistory);
  
  const feeds = statusData?.feeds || [];
  const activeTasks = statusData?.active_tasks || {};
  const scheduledTasks = statusData?.scheduled_tasks || {};
  
  // Données des tâches Celery
  const workers = tasksData?.workers || {};
  const tasksActiveTasks = tasksData?.active_tasks || {};
  const tasksScheduledTasks = tasksData?.scheduled_tasks || {};
  const tasksReservedTasks = tasksData?.reserved_tasks || {};

  const getStatusIcon = (status) => {
    switch (status) {
      case 'recent':
        return <FaCheck className="text-green-500" />;
      case 'overdue':
        return <FaExclamationTriangle className="text-yellow-500" />;
      case 'stale':
        return <FaTimes className="text-red-500" />;
      case 'never_collected':
        return <FaTimes className="text-gray-500" />;
      default:
        return <FaClock className="text-gray-500" />;
    }
  };

  const getStatusLabel = (status) => {
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'recent':
        return 'text-green-600 bg-green-100';
      case 'overdue':
        return 'text-yellow-600 bg-yellow-100';
      case 'stale':
        return 'text-red-600 bg-red-100';
      case 'never_collected':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Statut des Collectes</h1>
          <p className="mt-2 text-gray-600">Surveillez l'état des collectes de vos flux RSS en temps réel</p>
        </div>

        {/* Tâches actives */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Tâches en cours</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            {Object.keys(activeTasks).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(activeTasks).map(([worker, tasks]) => (
                  <div key={worker} className="border-b border-gray-200 pb-4 last:border-b-0">
                    <h3 className="font-medium text-gray-700 mb-2">Worker: {worker}</h3>
                    <div className="space-y-2">
                      {tasks.map((task, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 bg-blue-50 rounded-md">
                          <FaSpinner className="text-blue-500 animate-spin" />
                          <div>
                            <p className="font-medium text-blue-800">{task.name}</p>
                            <p className="text-sm text-blue-600">ID: {task.id}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">Aucune tâche en cours</p>
            )}
          </div>
        </div>

        {/* Statut des flux */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Statut des flux</h2>
          {isLoading ? (
            <div className="text-center p-10">
              <FaSpinner className="animate-spin text-2xl text-gray-500 mx-auto mb-4" />
              <p className="text-gray-700">Chargement du statut des collectes...</p>
            </div>
          ) : error ? (
            <div className="text-center p-10 text-red-600">
              <p>Erreur lors du chargement du statut: {error.message}</p>
            </div>
          ) : feeds.length === 0 ? (
            <div className="text-center p-10">
              <p className="text-gray-700">Aucun flux trouvé</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {feeds.map((feed) => (
                <div key={feed.id} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">{feed.name}</h3>
                    <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(feed.collection_status)}`}>
                      {getStatusIcon(feed.collection_status)}
                      <span>{getStatusLabel(feed.collection_status)}</span>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-gray-500">URL</p>
                      <a href={feed.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline text-sm break-all">
                        {feed.url}
                      </a>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-500">Fréquence</p>
                        <p className="text-sm text-gray-900">{feed.frequency_minutes} minutes</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Statut</p>
                        <p className="text-sm text-gray-900">{feed.is_active ? 'Actif' : 'Inactif'}</p>
                      </div>
                    </div>
                    
                    {feed.last_fetch && (
                      <div>
                        <p className="text-sm font-medium text-gray-500">Dernière collecte</p>
                        <p className="text-sm text-gray-900">
                          {format(new Date(feed.last_fetch), 'dd/MM/yyyy HH:mm', { locale: fr })}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tâches programmées */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Tâches programmées</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            {Object.keys(scheduledTasks).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(scheduledTasks).map(([worker, tasks]) => (
                  <div key={worker} className="border-b border-gray-200 pb-4 last:border-b-0">
                    <h3 className="font-medium text-gray-700 mb-2">Worker: {worker}</h3>
                    <div className="space-y-2">
                      {tasks.map((task, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-md">
                          <FaClock className="text-yellow-500" />
                          <div>
                            <p className="font-medium text-yellow-800">{task.name}</p>
                            <p className="text-sm text-yellow-600">ID: {task.id}</p>
                            <p className="text-sm text-yellow-600">Programmé pour: {new Date(task.eta).toLocaleString()}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">Aucune tâche programmée</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionStatus;
