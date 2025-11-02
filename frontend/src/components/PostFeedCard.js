import React from 'react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import NetworkCard from './NetworkCard';

const PostFeedCard = ({ post, onView, onValidate, onReject, onEdit, onSave, onCancel, onRestore, onRejectGlobal, onRestoreGlobal }) => {
  // Pour les posts directs, utiliser les réseaux présents dans network_validations
  // Pour les posts de flux, utiliser les réseaux cibles du flux
  const targetNetworks = (post.is_direct || post.feed_id === null) 
    ? Object.keys(post.network_validations || {})
    : (post.feed?.target_networks || ['linkedin']);
  
  const generatedContent = post.generated_content || {};
  const networkValidations = post.network_validations || {};

  // Extraire l'image de l'article
  const getArticleImage = (content) => {
    if (!content) return null;
    const imgMatch = content.match(/<img[^>]+src="([^"]+)"/);
    return imgMatch ? imgMatch[1] : null;
  };

  // Priorité: source_image (stocké par le backend) > image dans le contenu HTML
  // source_image est disponible pour tous les posts (flux ou directs)
  const articleImage = post.source_image 
    ? post.source_image  // Image stockée par le backend (depuis RSS feed ou MinIO)
    : getArticleImage(post.content);  // Fallback: chercher dans le HTML du contenu

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden mb-6">
      {/* Image de l'article */}
      {articleImage && (
        <div className="h-48 bg-gray-200 overflow-hidden">
          <img 
            src={articleImage} 
            alt={post.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
                      onLoad={() => {
                        // Image chargée avec succès
                      }}
          />
        </div>
      )}
      
      {/* Contenu */}
      <div className="p-4">
        {/* Header du feed avec bouton de rejet global */}
        <div className="mb-4">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 flex-1">
              {post.title}
            </h3>
            {/* Boutons d'actions globales */}
            <div className="flex space-x-2 flex-shrink-0">
              {/* Bouton de rejet global */}
              {(post.status === 'draft' || post.status === 'validated') && onRejectGlobal && (
                <button
                  onClick={() => {
                    if (window.confirm(`Êtes-vous sûr de vouloir rejeter globalement cet article ?\n\nTous les réseaux seront rejetés et retirés de la queue de publication.`)) {
                      onRejectGlobal(post.id);
                    }
                  }}
                  className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  title="Rejeter globalement (tous les réseaux)"
                >
                  ❌ Rejeter tout
                </button>
              )}
              {/* Bouton de restauration globale */}
              {post.status === 'rejected' && onRestoreGlobal && (
                <button
                  onClick={() => {
                    if (window.confirm(`Êtes-vous sûr de vouloir restaurer globalement cet article ?\n\nTous les réseaux rejetés seront restaurés en brouillon.`)) {
                      onRestoreGlobal(post.id);
                    }
                  }}
                  className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  title="Restaurer globalement (tous les réseaux)"
                >
                  ✅ Restaurer tout
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-3 text-sm text-gray-600 mb-3">
            <span className="font-medium">{post.feed?.name || 'Inconnu'}</span>
            <span>•</span>
            <span>{format(new Date(post.created_at), 'dd MMM yyyy', { locale: fr })}</span>
            {post.source_url && (
              <>
                <span>•</span>
                <a 
                  href={post.source_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Voir l'article
                </a>
              </>
            )}
          </div>
        </div>

        {/* Réseaux sociaux */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Réseaux sociaux :</h4>
          {targetNetworks.map(network => {
            const content = generatedContent[network] || '';
            const validation = networkValidations[network] || { status: 'draft' };


            return (
              <NetworkCard
                key={network}
                network={network}
                content={content}
                validation={validation}
                onView={(network) => onView(post, network)}
                onValidate={(network) => onValidate(post.id, network)}
                onReject={(network, reason) => onReject(post.id, network, reason)}
                onEdit={(network) => onEdit(post, network)}
                onSave={(network, content) => onSave(post.id, network, content)}
                onCancel={() => onCancel()}
                onRestore={(network) => onRestore(post.id, network)}
                isDirectPublished={post.is_direct && (validation?.status === 'published' || validation?.status === 'failed')}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PostFeedCard;
