import React from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaPlay, FaClock } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { postsService } from '../services/api';
import { cleanHtmlContent } from '../utils/htmlUtils';

const Queue = () => {
  const queryClient = useQueryClient();

  // Afficher les posts validés (qui sont dans la queue de publication)
  const { data: queueData = [], isLoading, error } = useQuery('queue', postsService.getQueue);
  
  // S'assurer que queue est un tableau
  const queue = Array.isArray(queueData?.data) ? queueData.data : Array.isArray(queueData) ? queueData : [];
  
  const publishNowMutation = useMutation(
    (id) => postsService.publishNow(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('queue');
        queryClient.invalidateQueries('history');
      }
    }
  );

  const handlePublishNow = (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir publier ce post maintenant ?')) {
      publishNowMutation.mutate(id);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">File d'attente</h1>
          <p className="mt-2 text-gray-600">Posts validés en attente de publication</p>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-4 text-gray-600">Chargement de la file d'attente...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">
                Erreur lors du chargement: {error.message}
              </p>
            </div>
          </div>
        ) : queue.length === 0 ? (
          <div className="text-center py-12">
            <FaClock className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">File d'attente vide</h3>
            <p className="mt-1 text-sm text-gray-500">
              Aucun post validé. Allez dans "Brouillons" pour valider des posts.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {queue.map((post) => (
              <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                      {post.title}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Créé le: {format(new Date(post.created_at), 'dd/MM/yyyy à HH:mm', { locale: fr })}
                    </p>
                  </div>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    ✅ Validé
                  </span>
                </div>

                <p className="text-gray-600 text-sm line-clamp-3 mb-4">
                  {cleanHtmlContent(post.content, 200)}
                </p>

                {post.generated_content && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Réseaux cibles:</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.keys(post.generated_content).map((network) => (
                        <span key={network} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700 capitalize">
                          {network === 'x' ? '𝕏' : network}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="text-xs text-gray-500">
                    {post.validated_at && (
                      <p>Validé le: {format(new Date(post.validated_at), 'dd/MM à HH:mm', { locale: fr })}</p>
                    )}
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handlePublishNow(post.id)}
                      disabled={publishNowMutation.isLoading}
                      className="inline-flex items-center px-3 py-1 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      <FaPlay className="w-3 h-3 mr-1" />
                      Publier
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Queue;