import React, { useState } from 'react';
import { FaSave, FaEdit, FaEye, FaEyeSlash, FaGlobe, FaClock, FaUsers, FaKey } from 'react-icons/fa';

const NetworkConfiguration = ({ networks, onSave, onUpdate, isLoading }) => {
  // S'assurer que networks est toujours un tableau
  const networksList = Array.isArray(networks) ? networks : [];
  const [editingNetwork, setEditingNetwork] = useState(null);
  const [showCredentials, setShowCredentials] = useState({});

  const networkIcons = {
    facebook: '📘',
    linkedin: '💼',
    x: '🐦'
  };

  const networkColors = {
    facebook: 'bg-blue-50 border-blue-200',
    linkedin: 'bg-blue-50 border-blue-200',
    x: 'bg-gray-50 border-gray-200'
  };

  const toggleCredentials = (networkId) => {
    setShowCredentials(prev => ({
      ...prev,
      [networkId]: !prev[networkId]
    }));
  };

  const handleSave = (networkData) => {
    if (editingNetwork) {
      onUpdate(editingNetwork.id, networkData);
    } else {
      onSave(networkData);
    }
    setEditingNetwork(null);
  };

  const renderNetworkCard = (network) => (
    <div key={network.id} className={`p-6 rounded-lg border-2 ${networkColors[network.network]} transition-all duration-200 hover:shadow-lg`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-3xl">{networkIcons[network.network]}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 capitalize">{network.network}</h3>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                network.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {network.is_active ? 'Actif' : 'Inactif'}
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setEditingNetwork(network)}
          className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
        >
          <FaEdit className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Délai par défaut</span>
          <span className="text-sm font-medium text-gray-900">{network.default_publication_delay} min</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Max posts/jour</span>
          <span className="text-sm font-medium text-gray-900">{network.max_posts_per_day}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Pages configurées</span>
          <span className="text-sm font-medium text-gray-900">
            {network.page_configs ? Object.keys(network.page_configs).length : 0}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">API configurée</span>
          <span className={`text-sm font-medium ${
            network.api_credentials ? 'text-green-600' : 'text-red-600'
          }`}>
            {network.api_credentials ? 'Oui' : 'Non'}
          </span>
        </div>
      </div>

      {network.api_credentials && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={() => toggleCredentials(network.id)}
            className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800"
          >
            {showCredentials[network.id] ? <FaEyeSlash /> : <FaEye />}
            <span>{showCredentials[network.id] ? 'Masquer' : 'Voir'} les credentials</span>
          </button>
          
          {showCredentials[network.id] && (
            <div className="mt-2 p-3 bg-gray-50 rounded-lg">
              <pre className="text-xs text-gray-700 overflow-x-auto">
                {JSON.stringify(network.api_credentials, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderEditForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {editingNetwork ? 'Modifier la configuration' : 'Nouveau réseau'}
            </h2>
            <button
              onClick={() => setEditingNetwork(null)}
              className="text-gray-400 hover:text-gray-600 text-3xl p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ×
            </button>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
              network: formData.get('network'),
              is_active: formData.get('is_active') === 'on',
              default_publication_delay: parseInt(formData.get('default_publication_delay')),
              max_posts_per_day: parseInt(formData.get('max_posts_per_day')),
              api_credentials: JSON.parse(formData.get('api_credentials') || '{}'),
              page_configs: JSON.parse(formData.get('page_configs') || '{}'),
              optimal_posting_times: JSON.parse(formData.get('optimal_posting_times') || '[]')
            };
            handleSave(data);
          }}>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Réseau</label>
                <select
                  name="network"
                  defaultValue={editingNetwork?.network || ''}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="">Sélectionner un réseau</option>
                  <option value="facebook">Facebook</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="x">X (Twitter)</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  defaultChecked={editingNetwork?.is_active}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Activer ce réseau
                </label>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Délai par défaut (min)</label>
                  <input
                    type="number"
                    name="default_publication_delay"
                    defaultValue={editingNetwork?.default_publication_delay || 30}
                    min="0"
                    max="1440"
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Max posts/jour</label>
                  <input
                    type="number"
                    name="max_posts_per_day"
                    defaultValue={editingNetwork?.max_posts_per_day || 10}
                    min="1"
                    max="100"
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Credentials API (JSON)</label>
                <textarea
                  name="api_credentials"
                  rows="4"
                  defaultValue={editingNetwork?.api_credentials ? JSON.stringify(editingNetwork.api_credentials, null, 2) : '{}'}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                  placeholder='{"api_key": "your_key", "secret": "your_secret"}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Configuration des pages (JSON)</label>
                <textarea
                  name="page_configs"
                  rows="4"
                  defaultValue={editingNetwork?.page_configs ? JSON.stringify(editingNetwork.page_configs, null, 2) : '{}'}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                  placeholder='{"page_id": "123456", "access_token": "token"}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Heures optimales (JSON)</label>
                <textarea
                  name="optimal_posting_times"
                  rows="2"
                  defaultValue={editingNetwork?.optimal_posting_times ? JSON.stringify(editingNetwork.optimal_posting_times, null, 2) : '[]'}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                  placeholder='["09:00", "12:00", "18:00"]'
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-8 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => setEditingNetwork(null)}
                className="px-6 py-3 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-6 py-3 bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaSave className="inline mr-2" />
                {isLoading ? 'Sauvegarde...' : 'Sauvegarder'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Configuration des réseaux sociaux</h2>
          <p className="text-sm text-gray-600 mt-1">
            Gérez les paramètres globaux pour chaque réseau social
          </p>
        </div>
        <button
          onClick={() => setEditingNetwork({})}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <FaGlobe className="inline mr-2" />
          Nouveau réseau
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {networksList.map(renderNetworkCard)}
      </div>

      {networksList.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FaGlobe className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun réseau configuré</h3>
          <p className="mt-1 text-sm text-gray-500">
            Commencez par configurer vos réseaux sociaux.
          </p>
        </div>
      )}

      {editingNetwork && renderEditForm()}
    </div>
  );
};

export default NetworkConfiguration;
