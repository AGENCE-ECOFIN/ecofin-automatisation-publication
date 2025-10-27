import React, { useState, useEffect } from 'react';
import { FaFacebook, FaLinkedinIn, FaTwitter, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

const NetworkCard = ({ 
  network, 
  content, 
  validation, 
  onValidate, 
  onReject, 
  onView,
  onEdit,
  onSave,
  onCancel,
  onRestore,
  isDirectPublished = false  // Nouvelle prop pour les posts directs publiés
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(content);
  const [currentStatus, setCurrentStatus] = useState(validation?.status || 'draft');
  const [currentRejectionReason, setCurrentRejectionReason] = useState(validation?.rejection_reason);

  // Mettre à jour le statut quand les props changent
  useEffect(() => {
    setCurrentStatus(validation?.status || 'draft');
    setCurrentRejectionReason(validation?.rejection_reason);
  }, [validation]);

  // Mettre à jour le contenu quand les props changent
  useEffect(() => {
    setEditedContent(content);
  }, [content]);

  const status = currentStatus;

  const getNetworkIcon = (network) => {
    switch (network) {
      case 'facebook': return <FaFacebook className="text-blue-600" />;
      case 'linkedin': return <FaLinkedinIn className="text-blue-800" />;
      case 'x': return <FaTwitter className="text-black" />;
      default: return null;
    }
  };

  const getNetworkColor = (network) => {
    switch (network) {
      case 'facebook': return 'bg-blue-50 border-blue-200';
      case 'linkedin': return 'bg-blue-50 border-blue-200';
      case 'x': return 'bg-gray-50 border-gray-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'validated': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const handleSave = () => {
    onSave(network, editedContent);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedContent(content);
    setIsEditing(false);
  };

  return (
    <div className={`rounded-lg border p-3 ${getNetworkColor(network)}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getNetworkIcon(network)}
          <h4 className="font-medium text-gray-900 capitalize text-sm">
            {network === 'x' ? 'X (Twitter)' : network}
          </h4>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
          {status === 'validated' && <FaCheckCircle className="inline mr-1" />}
          {status === 'rejected' && <FaTimesCircle className="inline mr-1" />}
          {status}
        </span>
      </div>

      {isEditing ? (
        <textarea
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          rows="4"
          className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary text-sm"
        />
      ) : (
        <div className="mb-2">
          <p className="text-gray-800 whitespace-pre-wrap text-xs line-clamp-2">
            {content || 'Aucun contenu généré pour ce réseau'}
          </p>
        </div>
      )}

      {currentRejectionReason && status === 'rejected' && (
        <p className="text-red-700 text-xs italic mb-2">
          Raison: {currentRejectionReason}
        </p>
      )}

      <div className="flex justify-end space-x-1 mt-2">
        {isEditing ? (
          <>
            <button
              onClick={handleCancel}
              className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSave}
              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Enregistrer
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => onView(network)}
              className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
            >
              Voir
            </button>
            
            {/* Boutons d'action - ne pas afficher pour les posts directs publiés */}
            {!isDirectPublished && status === 'draft' && (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                >
                  Modifier
                </button>
                <button
                  onClick={() => onReject(network, '')}
                  className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Rejeter
                </button>
                <button
                  onClick={() => onValidate(network)}
                  className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                >
                  Valider
                </button>
              </>
            )}
            
            {!isDirectPublished && status === 'rejected' && (
              <button
                onClick={() => onRestore(network)}
                className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Restaurer
              </button>
            )}
            
            {status === 'validated' && (
              <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                ✓ Validé
              </span>
            )}
            
            {status === 'published' && (
              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                ✓ Publié
              </span>
            )}
            
            {status === 'failed' && (
              <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                ✗ Échec
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default NetworkCard;