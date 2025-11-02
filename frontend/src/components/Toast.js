import React, { useEffect } from 'react';
import { FaCheck, FaExclamationTriangle, FaInfo, FaTimes } from 'react-icons/fa';

const Toast = ({ 
  message, 
  type = 'info', 
  isVisible, 
  onClose, 
  duration = 5000 
}) => {
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  if (!isVisible) return null;

  const typeConfig = {
    success: {
      icon: FaCheck,
      bgColor: 'bg-green-500',
      textColor: 'text-white',
      iconColor: 'text-green-100'
    },
    error: {
      icon: FaExclamationTriangle,
      bgColor: 'bg-red-500',
      textColor: 'text-white',
      iconColor: 'text-red-100'
    },
    warning: {
      icon: FaExclamationTriangle,
      bgColor: 'bg-yellow-500',
      textColor: 'text-white',
      iconColor: 'text-yellow-100'
    },
    info: {
      icon: FaInfo,
      bgColor: 'bg-blue-500',
      textColor: 'text-white',
      iconColor: 'text-blue-100'
    }
  };

  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div className="fixed top-4 right-4 z-50 transform transition-all duration-300 ease-in-out">
      <div className={`
        ${config.bgColor} ${config.textColor} 
        px-6 py-4 rounded-xl shadow-lg border border-white/20
        flex items-center space-x-3 min-w-80 max-w-md
        animate-in slide-in-from-right-full
      `}>
        <Icon className={`w-5 h-5 ${config.iconColor}`} />
        <span className="flex-1 text-sm font-medium">{message}</span>
        <button
          onClick={onClose}
          className="ml-2 p-1 hover:bg-white/20 rounded-lg transition-colors"
        >
          <FaTimes className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default Toast;








