import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />
      
      <div className={`
        transition-all duration-300 ease-in-out
        ${sidebarOpen ? 'lg:ml-64' : 'lg:ml-16'}
      `}>
        <Header onToggleSidebar={toggleSidebar} />
        
        <main className="pt-16">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;