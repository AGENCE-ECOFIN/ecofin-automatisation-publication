import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  FaHome,
  FaRss,
  FaFileAlt,
  FaClock,
  FaHistory,
  FaBars,
  FaChevronLeft,
  FaServer,
  FaCogs,
  FaUsers,
  FaClipboardList
} from 'react-icons/fa';

const Sidebar = ({ isOpen, onToggle }) => {
  const navItems = [
    { path: '/', icon: FaHome, label: 'Dashboard' },
    { path: '/feeds', icon: FaRss, label: 'Flux RSS' },
    { path: '/posts', icon: FaFileAlt, label: 'Posts' },
    { path: '/publications', icon: FaClock, label: 'Publications' },
    { path: '/history', icon: FaHistory, label: 'Historique' },
    { path: '/system-status', icon: FaServer, label: 'Statut Système' },
    { path: '/prompts', icon: FaCogs, label: 'Prompts' },
    { path: '/users', icon: FaUsers, label: 'Utilisateurs' },
    { path: '/audit-logs', icon: FaClipboardList, label: 'Logs d\'Audit' },
  ];

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-white shadow-lg z-50 transition-all duration-300 ease-in-out
        ${isOpen ? 'w-64' : 'w-16'}
        lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary rounded-lg">
              <FaRss className="w-6 h-6 text-white" />
            </div>
            {isOpen && (
              <span className="text-lg font-bold text-gray-900">EcoFin Pub</span>
            )}
          </div>
          <button
            onClick={onToggle}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
          >
            {isOpen ? <FaChevronLeft /> : <FaBars />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) => `
                    flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-primary text-white' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {isOpen && (
                    <span className="text-sm font-medium">{item.label}</span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </>
  );
};

export default Sidebar;