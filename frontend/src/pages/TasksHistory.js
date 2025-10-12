import React from 'react';
import { useQuery } from 'react-query';
import { FaSpinner, FaCheck, FaExclamationTriangle, FaClock, FaServer, FaTasks, FaPlay, FaPause } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { tasksService } from '../services/api';

const TasksHistory = () => {
  const { data: historyData = {}, isLoading: historyLoading, error: historyError } = useQuery('tasks-history', tasksService.getTasksHistory);
  const { data: statsData = {}, isLoading: statsLoading, error: statsError } = useQuery('tasks-stats', tasksService.getTasksStats);

  const workers = historyData?.workers || {};
  const activeTasks = historyData?.active_tasks || {};
  const scheduledTasks = historyData?.scheduled_tasks || {};
  const reservedTasks = historyData?.reserved_tasks || {};
  
  const totalWorkers = statsData?.total_workers || 0;
  const totalActiveTasks = statsData?.total_active_tasks || 0;

  const getWorkerStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <FaCheck className="text-green-500" />;
      case 'offline':
        return <FaExclamationTriangle className="text-red-500" />;
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
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Historique des Tâches Celery</h1>
      <p className="text-gray-600 mb-8">
        Surveillez l'état des workers Celery et l'historique des tâches en temps réel.
      </p>

      {historyLoading || statsLoading ? (
        <div className="text-center p-10">
          <FaSpinner className="animate-spin text-indigo-600 text-4xl mx-auto mb-4" />
          <p className="text-gray-700">Chargement de l'historique des tâches...</p>
        </div>
      ) : historyError || statsError ? (
        <div className="text-center p-10 text-red-600">
          <p>Erreur lors du chargement de l'historique: {historyError?.message || statsError?.message}</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Statistiques générales */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Statistiques Générales</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaServer className="text-blue-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Workers Actifs</p>
                    <p className="text-2xl font-bold text-blue-600">{totalWorkers}</p>
                  </div>
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaTasks className="text-green-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Tâches Actives</p>
                    <p className="text-2xl font-bold text-green-600">{totalActiveTasks}</p>
                  </div>
                </div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FaClock className="text-purple-500 text-2xl mr-3" />
                  <div>
                    <p className="text-sm text-gray-600">Dernière Mise à Jour</p>
                    <p className="text-sm font-medium text-purple-600">
                      {historyData?.timestamp ? format(new Date(historyData.timestamp), 'dd/MM/yyyy HH:mm', { locale: fr }) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Workers */}
          <div className="bg-white shadow-md rounded-lg p-6">
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
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Tâches Actives</h2>
            {Object.keys(activeTasks).length === 0 ? (
              <p className="text-gray-700">Aucune tâche active.</p>
            ) : (
              <div className="space-y-4">
                {Object.entries(activeTasks).map(([worker, tasks]) => (
                  <div key={worker} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-700 mb-3 flex items-center">
                      <FaServer className="text-blue-500 mr-2" />
                      {worker}
                    </h3>
                    {tasks.length === 0 ? (
                      <p className="text-gray-600">Aucune tâche active sur ce worker.</p>
                    ) : (
                      <div className="space-y-2">
                        {tasks.map((task, index) => (
                          <div key={index} className="bg-blue-50 rounded-lg p-3 flex items-center justify-between">
                            <div className="flex items-center">
                              {getTaskStatusIcon('active')}
                              <div className="ml-3">
                                <p className="font-medium text-gray-900">{task.name}</p>
                                <p className="text-sm text-gray-600">ID: {task.id}</p>
                              </div>
                            </div>
                            <div className="text-sm text-gray-500">
                              {task.time_start ? format(new Date(task.time_start * 1000), 'HH:mm:ss', { locale: fr }) : 'N/A'}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tâches programmées */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Tâches Programmées</h2>
            {Object.keys(scheduledTasks).length === 0 ? (
              <p className="text-gray-700">Aucune tâche programmée.</p>
            ) : (
              <div className="space-y-4">
                {Object.entries(scheduledTasks).map(([worker, tasks]) => (
                  <div key={worker} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-700 mb-3 flex items-center">
                      <FaClock className="text-yellow-500 mr-2" />
                      {worker}
                    </h3>
                    {tasks.length === 0 ? (
                      <p className="text-gray-600">Aucune tâche programmée sur ce worker.</p>
                    ) : (
                      <div className="space-y-2">
                        {tasks.map((task, index) => (
                          <div key={index} className="bg-yellow-50 rounded-lg p-3 flex items-center justify-between">
                            <div className="flex items-center">
                              {getTaskStatusIcon('scheduled')}
                              <div className="ml-3">
                                <p className="font-medium text-gray-900">{task.request.name}</p>
                                <p className="text-sm text-gray-600">ID: {task.id}</p>
                              </div>
                            </div>
                            <div className="text-sm text-gray-500">
                              ETA: {task.eta ? format(new Date(task.eta), 'HH:mm:ss', { locale: fr }) : 'N/A'}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tâches réservées */}
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Tâches Réservées</h2>
            {Object.keys(reservedTasks).length === 0 ? (
              <p className="text-gray-700">Aucune tâche réservée.</p>
            ) : (
              <div className="space-y-4">
                {Object.entries(reservedTasks).map(([worker, tasks]) => (
                  <div key={worker} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-700 mb-3 flex items-center">
                      <FaPause className="text-orange-500 mr-2" />
                      {worker}
                    </h3>
                    {tasks.length === 0 ? (
                      <p className="text-gray-600">Aucune tâche réservée sur ce worker.</p>
                    ) : (
                      <div className="space-y-2">
                        {tasks.map((task, index) => (
                          <div key={index} className="bg-orange-50 rounded-lg p-3 flex items-center justify-between">
                            <div className="flex items-center">
                              {getTaskStatusIcon('reserved')}
                              <div className="ml-3">
                                <p className="font-medium text-gray-900">{task.name}</p>
                                <p className="text-sm text-gray-600">ID: {task.id}</p>
                              </div>
                            </div>
                            <div className="text-sm text-gray-500">
                              {task.time_start ? format(new Date(task.time_start * 1000), 'HH:mm:ss', { locale: fr }) : 'N/A'}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
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

export default TasksHistory;
