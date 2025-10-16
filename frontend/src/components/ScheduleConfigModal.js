import React, { useState, useEffect } from 'react';
import { FaTimes, FaPlus, FaTrash, FaSave, FaClock, FaCalendarAlt } from 'react-icons/fa';
import { api } from '../services/api';

const ScheduleConfigModal = ({ isOpen, onClose, network, onSave }) => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newConfig, setNewConfig] = useState({
    day_type: 'weekday',
    start_time: '09:00',
    end_time: '18:00',
    is_active: true,
    max_posts_per_day: 3
  });

  useEffect(() => {
    if (isOpen && network) {
      fetchScheduleConfigs();
    }
  }, [isOpen, network]);

  const fetchScheduleConfigs = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/schedule/?network=${network}`);
      setConfigs(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des horaires:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddConfig = () => {
    setConfigs([...configs, { ...newConfig, id: Date.now() }]);
    setNewConfig({
      day_type: 'weekday',
      start_time: '09:00',
      end_time: '18:00',
      is_active: true,
      max_posts_per_day: 3
    });
  };

  const handleUpdateConfig = (index, field, value) => {
    const updatedConfigs = [...configs];
    updatedConfigs[index][field] = value;
    setConfigs(updatedConfigs);
  };

  const handleRemoveConfig = (index) => {
    setConfigs(configs.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      
      // Préparer les données pour l'API
      const configsToSave = configs.map(config => ({
        network: network,
        day_type: config.day_type,
        start_time: config.start_time,
        end_time: config.end_time,
        is_active: config.is_active,
        max_posts_per_day: config.max_posts_per_day
      }));

      const response = await api.post('/schedule/bulk-update', {
        network: network,
        configs: configsToSave
      });

      onSave();
      onClose();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const getNetworkIcon = (network) => {
    switch (network) {
      case 'facebook': return '📘';
      case 'linkedin': return '💼';
      case 'x': return '🐦';
      default: return '📱';
    }
  };

  const getDayTypeLabel = (dayType) => {
    switch (dayType) {
      case 'weekday': return 'Semaine';
      case 'weekend': return 'Week-end';
      case 'holiday': return 'Vacances';
      default: return dayType;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {getNetworkIcon(network)} Configuration des Horaires - {network?.charAt(0).toUpperCase() + network?.slice(1)}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            <FaTimes />
          </button>
        </div>

        {/* Configuration existante */}
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Chargement...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {configs.map((config, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">
                    {getDayTypeLabel(config.day_type)}
                  </h3>
                  <button
                    onClick={() => handleRemoveConfig(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <FaTrash />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Type de jour */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Type de jour
                    </label>
                    <select
                      value={config.day_type}
                      onChange={(e) => handleUpdateConfig(index, 'day_type', e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="weekday">Semaine</option>
                      <option value="weekend">Week-end</option>
                      <option value="holiday">Vacances</option>
                    </select>
                  </div>

                  {/* Heure de début */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <FaClock className="inline mr-1" />
                      Début
                    </label>
                    <input
                      type="time"
                      value={config.start_time}
                      onChange={(e) => handleUpdateConfig(index, 'start_time', e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  {/* Heure de fin */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <FaClock className="inline mr-1" />
                      Fin
                    </label>
                    <input
                      type="time"
                      value={config.end_time}
                      onChange={(e) => handleUpdateConfig(index, 'end_time', e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  {/* Note: L'intervalle est géré par le délai global du réseau */}
                  <div className="col-span-2 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-700">
                      ℹ️ L'espacement entre publications est géré par le <strong>délai global</strong> dans "Configuration des réseaux"
                    </p>
                  </div>

                  {/* Max posts par jour */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max/jour
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={config.max_posts_per_day}
                      onChange={(e) => handleUpdateConfig(index, 'max_posts_per_day', parseInt(e.target.value))}
                      className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  {/* Actif */}
                  <div className="flex items-center">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={config.is_active}
                        onChange={(e) => handleUpdateConfig(index, 'is_active', e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm font-medium text-gray-700">Actif</span>
                    </label>
                  </div>
                </div>
              </div>
            ))}

            {/* Ajouter nouvelle configuration */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                <FaPlus className="inline mr-2" />
                Ajouter une configuration
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de jour
                  </label>
                  <select
                    value={newConfig.day_type}
                    onChange={(e) => setNewConfig({ ...newConfig, day_type: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="weekday">Semaine</option>
                    <option value="weekend">Week-end</option>
                    <option value="holiday">Vacances</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <FaClock className="inline mr-1" />
                    Début
                  </label>
                  <input
                    type="time"
                    value={newConfig.start_time}
                    onChange={(e) => setNewConfig({ ...newConfig, start_time: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <FaClock className="inline mr-1" />
                    Fin
                  </label>
                  <input
                    type="time"
                    value={newConfig.end_time}
                    onChange={(e) => setNewConfig({ ...newConfig, end_time: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-end">
                  <button
                    onClick={handleAddConfig}
                    className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center justify-center"
                  >
                    <FaPlus className="mr-2" />
                    Ajouter
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Annuler
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center"
          >
            <FaSave className="mr-2" />
            {loading ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScheduleConfigModal;
