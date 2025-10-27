import React from 'react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import NetworkCard from './NetworkCard';

const PostFeedCard = ({ post, onView, onValidate, onReject, onEdit, onSave, onCancel, onRestore }) => {
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

  // Pour les posts directs, utiliser source_image (depuis MinIO)
  // Pour les posts de flux, chercher dans le contenu de base
  const articleImage = post.is_direct 
    ? post.source_image  // Image depuis MinIO via le backend
    : getArticleImage(post.content);

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
        {/* Header du feed */}
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {post.title}
          </h3>
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
