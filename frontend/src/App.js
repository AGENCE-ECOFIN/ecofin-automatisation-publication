import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Feeds from './pages/Feeds';
import Posts from './pages/Posts';
import Queue from './pages/Queue';
import History from './pages/History';
import SystemStatus from './pages/SystemStatus';
import Prompts from './pages/Prompts';
import UnifiedPublication from './pages/UnifiedPublication';
import TestConnection from './pages/TestConnection';
import UserManagement from './pages/UserManagement';
import AuditLogs from './pages/AuditLogs';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Chargement...</div>;
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={user ? <Navigate to="/" replace /> : <Login />} 
      />
      <Route 
        path="/test" 
        element={<TestConnection />} 
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
              <Route index element={<Dashboard />} />
              <Route path="feeds" element={<Feeds />} />
              <Route path="posts" element={<Posts />} />
              <Route path="queue" element={<Queue />} />
              <Route path="history" element={<History />} />
               <Route path="system-status" element={<SystemStatus />} />
               <Route path="prompts" element={<Prompts />} />
               <Route path="publications" element={<UnifiedPublication />} />
               <Route path="users" element={<UserManagement />} />
               <Route path="audit-logs" element={<AuditLogs />} />
      </Route>
    </Routes>
  );
}

export default App;
