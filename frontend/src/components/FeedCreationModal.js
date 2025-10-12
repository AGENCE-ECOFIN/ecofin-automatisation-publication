import React, { useState, useEffect } from 'react';
import { FaArrowRight, FaArrowLeft, FaRss, FaGlobe, FaClock, FaUsers, FaFacebook, FaLinkedin, FaTwitter, FaTimes, FaCheck } from 'react-icons/fa';
import { api } from '../services/api';

const FeedCreationModal = ({ isOpen, onClose, onSave, isLoading }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [blotatoAccounts, setBlotatoAccounts] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    frequency_minutes: 120,
    target_networks: [],
    social_pages: {},
    network_prompts: {},
    publication_timing: {},
    is_active: true
  });

  const steps = [
    { id: 1, title: 'Informations', icon: FaRss },
    { id: 2, title: 'Réseaux', icon: FaGlobe },
    { id: 3, title: 'Pages', icon: FaUsers },
    { id: 4, title: 'Prompts', icon: FaClock }
  ];

  useEffect(() => {
    if (isOpen) {
      fetchBlotatoAccounts();
    }
  }, [isOpen]);

  const fetchBlotatoAccounts = async () => {
    try {
      const response = await api.get('/blotato-accounts/');
      setBlotatoAccounts(response.data);
      console.log('📊 Comptes Blotato chargés:', response.data);
    } catch (error) {
      console.error('❌ Erreur:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (name.startsWith('network_prompts.') || name.startsWith('publication_timing.') || name.startsWith('social_pages.')) {
      const [parent, child] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: type === 'checkbox' ? checked : value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleNetworkChange = (e) => {
    const { value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      target_networks: checked 
        ? [...prev.target_networks, value]
        : prev.target_networks.filter(network => network !== value)
    }));
  };

  const handlePageChange = (network, pageId) => {
    setFormData(prev => ({
      ...prev,
      social_pages: {
        ...prev.social_pages,
        [network]: pageId
      }
    }));
  };

  const nextStep = () => {
    if (currentStep < steps.length) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.url || formData.target_networks.length === 0) {
      alert('Veuillez remplir tous les champs obligatoires');
      return;
    }
    await onSave(formData);
    handleClose();
  };

  const handleClose = () => {
    setFormData({
      name: '',
      url: '',
      frequency_minutes: 120,
      target_networks: [],
      social_pages: {},
      network_prompts: {},
      publication_timing: {},
      is_active: true
    });
    setCurrentStep(1);
    onClose();
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

  if (!isOpen) return null;

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-bold text-gray-700 mb-2">
          📝 Nom du flux *
        </label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleInputChange}
          placeholder="Ex: Blog Ecofin"
          className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-2">
          🔗 URL du flux RSS *
        </label>
        <input
          type="url"
          name="url"
          value={formData.url}
          onChange={handleInputChange}
          placeholder="https://example.com/feed"
          className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-gray-700 mb-2">
          ⏱️ Fréquence de collecte (minutes)
        </label>
        <input
          type="number"
          name="frequency_minutes"
          value={formData.frequency_minutes}
          onChange={handleInputChange}
          min="1"
          placeholder="120"
          className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
        />
        <p className="text-xs text-gray-500 mt-2">
          Ex: 60 = toutes les heures, 120 = toutes les 2 heures
        </p>
      </div>
    </div>
  );

  const renderStep2 = () => {
    const networks = [
      { id: 'facebook', label: 'Facebook', Icon: FaFacebook, color: '#1877F2' },
      { id: 'linkedin', label: 'LinkedIn', Icon: FaLinkedin, color: '#0A66C2' },
      { id: 'x', label: 'X (Twitter)', Icon: FaTwitter, color: '#000000' }
    ];

    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-600 mb-4">
          Sélectionnez les réseaux sociaux pour ce flux
        </p>

        {networks.map(({ id, label, Icon, color }) => {
          const isSelected = formData.target_networks.includes(id);
          return (
            <label
              key={id}
              className={`flex items-center p-6 border-2 rounded-xl cursor-pointer transition-all ${
                isSelected
                  ? 'border-indigo-500 bg-indigo-50 shadow-md'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="checkbox"
                value={id}
                checked={isSelected}
                onChange={handleNetworkChange}
                className="sr-only"
              />
              <div className="flex items-center flex-1">
                <div className="w-12 h-12 flex items-center justify-center bg-white rounded-full shadow-md">
                  <Icon style={{ color, fontSize: '24px' }} />
                </div>
                <div className="ml-4 flex-1">
                  <div className="font-bold text-gray-900">{label}</div>
                </div>
                {isSelected && (
                  <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center">
                    <FaCheck className="text-white" />
                  </div>
                )}
              </div>
            </label>
          );
        })}
      </div>
    );
  };

  const renderStep3 = () => (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 mb-4">
        Sélectionnez la page de destination pour chaque réseau
      </p>

      {formData.target_networks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>Aucun réseau sélectionné</p>
        </div>
      ) : !blotatoAccounts ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-gray-500 mt-4">Chargement...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {formData.target_networks.map(network => {
            const Icon = network === 'facebook' ? FaFacebook : network === 'linkedin' ? FaLinkedin : FaTwitter;
            const color = network === 'facebook' ? '#1877F2' : network === 'linkedin' ? '#0A66C2' : '#000000';
            const pages = getNetworkPages(network);
            const selectedPage = pages.find(p => p.id === formData.social_pages[network]);

            return (
              <div key={network} className="p-6 border-2 border-gray-200 rounded-xl bg-gray-50">
                <div className="flex items-center space-x-3 mb-4">
                  <Icon className="text-2xl" style={{ color }} />
                  <span className="font-bold text-gray-900 capitalize">
                    {network === 'x' ? 'X (Twitter)' : network}
                  </span>
                </div>

                <select
                  value={formData.social_pages[network] || ''}
                  onChange={(e) => handlePageChange(network, e.target.value)}
                  className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">-- Sélectionnez une page --</option>
                  {pages.map(page => (
                    <option key={page.id} value={page.id}>
                      {page.name}
                    </option>
                  ))}
                </select>

                {selectedPage && (
                  <div className="mt-3 bg-green-50 border-l-4 border-green-500 p-3 rounded-r">
                    <p className="text-sm text-green-700">
                      ✅ Page sélectionnée : <strong>{selectedPage.name}</strong>
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 mb-4">
        Personnalisez les prompts de génération pour chaque réseau (optionnel)
      </p>

      {formData.target_networks.map(network => {
        const Icon = network === 'facebook' ? FaFacebook : network === 'linkedin' ? FaLinkedin : FaTwitter;
        const color = network === 'facebook' ? '#1877F2' : network === 'linkedin' ? '#0A66C2' : '#000000';

        return (
          <div key={network} className="p-6 border-2 border-gray-200 rounded-xl bg-gray-50">
            <div className="flex items-center space-x-3 mb-4">
              <Icon className="text-2xl" style={{ color }} />
              <span className="font-bold text-gray-900 capitalize">
                {network === 'x' ? 'X (Twitter)' : network}
              </span>
            </div>

            <textarea
              name={`network_prompts.${network}`}
              value={formData.network_prompts[network] || ''}
              onChange={handleInputChange}
              placeholder={`Prompt personnalisé pour ${network}... (optionnel)`}
              rows="3"
              className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        );
      })}

      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r">
        <p className="text-sm text-blue-800">
          💡 Les délais de publication sont configurés globalement dans "Configuration des réseaux"
        </p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Créer un flux RSS</h2>
              <p className="text-indigo-100 mt-1">Étape {currentStep} sur {steps.length}</p>
            </div>
            <button
              onClick={handleClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-all"
            >
              <FaTimes className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Progress */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;

              return (
                <React.Fragment key={step.id}>
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                        isActive
                          ? 'bg-indigo-600 text-white shadow-lg scale-110'
                          : isCompleted
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-400'
                      }`}
                    >
                      {isCompleted ? <FaCheck /> : <Icon />}
                    </div>
                    <span className={`text-xs mt-2 font-medium text-center ${isActive ? 'text-indigo-600' : 'text-gray-500'}`}>
                      {step.title}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`h-1 flex-1 mx-2 rounded-full ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between items-center">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className="flex items-center space-x-2 px-6 py-3 text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
          >
            <FaArrowLeft />
            <span>Précédent</span>
          </button>

          {currentStep < steps.length ? (
            <button
              onClick={nextStep}
              disabled={
                (currentStep === 1 && (!formData.name || !formData.url)) ||
                (currentStep === 2 && formData.target_networks.length === 0)
              }
              className="flex items-center space-x-2 px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-bold hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <span>Suivant</span>
              <FaArrowRight />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="flex items-center space-x-2 px-8 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg font-bold hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Création...</span>
                </>
              ) : (
                <>
                  <FaCheck />
                  <span>Créer le flux</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeedCreationModal;
