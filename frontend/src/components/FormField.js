import React from 'react';

const FormField = ({ 
  label, 
  type = 'text', 
  value, 
  onChange, 
  placeholder, 
  required = false,
  error,
  className = '',
  ...props 
}) => {
  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      {type === 'textarea' ? (
        <textarea
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className={`
            w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 
            focus:border-indigo-500 transition-colors duration-200 resize-none
            ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'}
          `}
          rows={4}
          {...props}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className={`
            w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 
            focus:border-indigo-500 transition-colors duration-200
            ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'}
          `}
          {...props}
        />
      )}
      
      {error && (
        <p className="text-sm text-red-600 flex items-center">
          <span className="mr-1">⚠️</span>
          {error}
        </p>
      )}
    </div>
  );
};

export default FormField;

