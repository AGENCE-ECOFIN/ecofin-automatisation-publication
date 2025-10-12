import React from 'react';
import { FaBars, FaUser, FaSignOutAlt } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';

const Header = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();

  return (
    <header className="fixed top-0 right-0 left-0 bg-white shadow-sm border-b border-gray-200 z-40">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onToggleSidebar}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
          >
            <FaBars className="w-5 h-5" />
          </button>
          
          <div className="hidden lg:block">
            <h1 className="text-xl font-semibold text-gray-900">EcoFin Publication</h1>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* User info */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium text-gray-900">{user?.username}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <FaUser className="w-4 h-4 text-white" />
              </div>
              
              <button
                onClick={logout}
                className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Déconnexion"
              >
                <FaSignOutAlt className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;