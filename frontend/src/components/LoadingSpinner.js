import React from 'react';

const LoadingSpinner = ({ size = 'medium', color = 'indigo', text = 'Chargement...' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  const colorClasses = {
    indigo: 'text-indigo-600',
    blue: 'text-blue-600',
    green: 'text-green-600',
    red: 'text-red-600',
    gray: 'text-gray-600'
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-${color === 'indigo' ? 'indigo' : color}-600 ${sizeClasses[size]}`}></div>
      {text && (
        <p className={`mt-2 text-sm ${colorClasses[color]}`}>{text}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;


