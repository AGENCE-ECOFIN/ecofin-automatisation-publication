import React, { useState, useEffect } from 'react';
import { FaTimes, FaSave, FaClock } from 'react-icons/fa';
import { api } from '../services/api';

const ScheduleConfigModal = ({ isOpen, onClose, network, onSave }) => {
  const [weekdayConfig, setWeekdayConfig] = useState({
    start_time: '09:00',
    end_time: '18:00',
    is_active: true
  });
  const [weekendConfig, setWeekendConfig] = useState({
    start_time: '10:00',
    end_time: '20:00',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [hasExistingConfigs, setHasExistingConfigs] = useState(false);

  useEffect(() => {
    if (isOpen && network) {
      fetchScheduleConfig();
    }
  }, [isOpen, network]);

  const fetchScheduleConfig = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/schedule/?network=${network}`);
      console.log('📊 Configurations chargées:', response.data);
      
      // Séparer les configurations semaine et week-end
      let weekdayFound = false;
      let weekendFound = false;
      
      if (response.data && response.data.length > 0) {
        response.data.forEach(config => {
          if (config.day_type === 'weekday') {
            setWeekdayConfig({
              start_time: config.start_time,
              end_time: config.end_time,
              is_active: config.is_active
            });
            weekdayFound = true;
          } else if (config.day_type === 'weekend') {
            setWeekendConfig({
              start_time: config.start_time,
              end_time: config.end_time,
              is_active: config.is_active
            });
            weekendFound = true;
          }
        });
      }
      
      // Si pas de configuration trouvée, utiliser les valeurs par défaut
      if (!weekdayFound) {
        setWeekdayConfig({
          start_time: '09:00',
          end_time: '18:00',
          is_active: true
        });
      }
      
      if (!weekendFound) {
        setWeekendConfig({
          start_time: '10:00',
          end_time: '20:00',
          is_active: true
        });
      }
      
      setHasExistingConfigs(weekdayFound || weekendFound);
    } catch (error) {
      console.error('Erreur lors du chargement des horaires:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      
      console.log('🔧 Configurations à sauvegarder:');
      console.log('  Semaine:', weekdayConfig);
      console.log('  Week-end:', weekendConfig);
      
      // Préparer les configurations à sauvegarder
      const configsToSave = [
        {
          network: network,
          day_type: 'weekday',
          day_of_week: null,  // Semaine (lundi-vendredi)
          start_time: weekdayConfig.start_time,
          end_time: weekdayConfig.end_time,
          is_active: weekdayConfig.is_active
        },
        {
          network: network,
          day_type: 'weekend',
          day_of_week: null,  // Week-end (samedi-dimanche)
          start_time: weekendConfig.start_time,
          end_time: weekendConfig.end_time,
          is_active: weekendConfig.is_active
        }
      ];

      // Sauvegarder les deux configurations
      await api.post('/schedule/bulk-update', {
        network: network,
        configs: configsToSave
      });

      // Recalculer les posts en attente avec les nouveaux horaires
      try {
        console.log('🔄 Recalcul des posts en attente...');
        await api.post(`/schedule/recalculate-queue/${network}`);
        console.log('✅ Posts recalculés avec succès');
      } catch (error) {
        console.warn('⚠️ Erreur lors du recalcul:', error);
      }
      
      onSave();
      onClose();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la sauvegarde: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getNetworkIcon = (network) => {
    switch (network) {
      case 'facebook': return '📘';
      case 'linkedin': return '💼';
      case 'x': return '🐦';
      case 'twitter': return '🐦';
      default: return '📱';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
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

        {/* Configuration */}
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Chargement...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Configuration Semaine */}
            <div className="border border-gray-200 rounded-lg p-6 bg-blue-50">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                📅 Semaine (Lundi - Vendredi)
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Heure de début */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FaClock className="inline mr-1" />
                    Heure de début
                  </label>
                  <input
                    type="time"
                    value={weekdayConfig.start_time}
                    onChange={(e) => setWeekdayConfig({ ...weekdayConfig, start_time: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {/* Heure de fin */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FaClock className="inline mr-1" />
                    Heure de fin
                  </label>
                  <input
                    type="time"
                    value={weekdayConfig.end_time}
                    onChange={(e) => setWeekdayConfig({ ...weekdayConfig, end_time: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {/* Actif */}
                <div className="flex items-center">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={weekdayConfig.is_active}
                      onChange={(e) => setWeekdayConfig({ ...weekdayConfig, is_active: e.target.checked })}
                      className="mr-3 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <span className="text-sm font-medium text-gray-700">Actif</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Configuration Week-end */}
            <div className="border border-gray-200 rounded-lg p-6 bg-green-50">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                🏖️ Week-end (Samedi - Dimanche)
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Heure de début */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FaClock className="inline mr-1" />
                    Heure de début
                  </label>
                  <input
                    type="time"
                    value={weekendConfig.start_time}
                    onChange={(e) => setWeekendConfig({ ...weekendConfig, start_time: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {/* Heure de fin */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FaClock className="inline mr-1" />
                    Heure de fin
                  </label>
                  <input
                    type="time"
                    value={weekendConfig.end_time}
                    onChange={(e) => setWeekendConfig({ ...weekendConfig, end_time: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {/* Actif */}
                <div className="flex items-center">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={weekendConfig.is_active}
                      onChange={(e) => setWeekendConfig({ ...weekendConfig, is_active: e.target.checked })}
                      className="mr-3 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <span className="text-sm font-medium text-gray-700">Actif</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Note explicative */}
            <div className="p-4 bg-blue-50 rounded-md">
              <p className="text-sm text-blue-700">
                <strong>ℹ️ Note :</strong> Vous pouvez configurer des horaires différents pour la semaine et le week-end. 
                L'espacement entre publications est géré par le délai global dans "Configuration des réseaux".
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Annuler
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center"
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
