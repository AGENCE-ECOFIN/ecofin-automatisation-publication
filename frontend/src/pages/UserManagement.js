import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FaPlus, FaEdit, FaTrash, FaUser, FaUserShield, FaEye, FaEyeSlash } from 'react-icons/fa';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { usersService } from '../services/api';
import Modal from '../components/Modal';
import FormField from '../components/FormField';
import Button from '../components/Button';

const UserManagement = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const queryClient = useQueryClient();

  // États pour les formulaires
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    password: '',
    is_admin: false
  });

  const [editForm, setEditForm] = useState({
    username: '',
    email: '',
    password: '',
    is_admin: false
  });

  // Récupérer la liste des utilisateurs
  const { data: usersResponse, isLoading, error } = useQuery('users', usersService.getUsers);
  const users = usersResponse?.data || [];

  // Mutation pour créer un utilisateur
  const createUserMutation = useMutation(usersService.createUser, {
    onSuccess: () => {
      queryClient.invalidateQueries('users');
      setShowCreateModal(false);
      setCreateForm({ username: '', email: '', password: '', is_admin: false });
    }
  });

  // Mutation pour mettre à jour un utilisateur
  const updateUserMutation = useMutation(
    ({ id, data }) => usersService.updateUser(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('users');
        setShowEditModal(false);
        setSelectedUser(null);
      }
    }
  );

  // Mutation pour supprimer un utilisateur
  const deleteUserMutation = useMutation(usersService.deleteUser, {
    onSuccess: () => {
      queryClient.invalidateQueries('users');
    }
  });

  const handleCreateUser = (e) => {
    e.preventDefault();
    createUserMutation.mutate(createForm);
  };

  const handleEditUser = (e) => {
    e.preventDefault();
    updateUserMutation.mutate({
      id: selectedUser.id,
      data: editForm
    });
  };

  const handleDeleteUser = (userId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
      deleteUserMutation.mutate(userId);
    }
  };

  const openEditModal = (user) => {
    setSelectedUser(user);
    setEditForm({
      username: user.username,
      email: user.email,
      password: '',
      is_admin: user.is_admin
    });
    setShowEditModal(true);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-10 text-red-600">
        <p>Erreur lors du chargement des utilisateurs: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Gestion des Utilisateurs</h1>
          <p className="mt-2 text-gray-600">Gérez les utilisateurs et leurs permissions</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center justify-center space-x-2 w-full sm:w-auto"
        >
          <FaPlus className="w-4 h-4" />
          <span>Nouvel Utilisateur</span>
        </button>
      </div>

      {/* Liste des utilisateurs */}
      <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Utilisateurs ({users.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
              <tr>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Utilisateur
                </th>
                <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rôle
                </th>
                <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Créé le
                </th>
                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors duration-150">
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 sm:h-10 sm:w-10">
                        <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                          {user.is_admin ? (
                            <FaUserShield className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600" />
                          ) : (
                            <FaUser className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600" />
                          )}
                        </div>
                      </div>
                      <div className="ml-2 sm:ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.username}</div>
                        <div className="text-xs text-gray-500 sm:hidden">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.email}
                  </td>
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user.is_admin 
                        ? 'bg-purple-100 text-purple-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      <span className="hidden sm:inline">{user.is_admin ? 'Administrateur' : 'Utilisateur'}</span>
                      <span className="sm:hidden">{user.is_admin ? 'Admin' : 'User'}</span>
                    </span>
                  </td>
                  <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(user.created_at), 'dd/MM/yyyy', { locale: fr })}
                  </td>
                  <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => openEditModal(user)}
                        className="p-2 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-all duration-200"
                        title="Modifier"
                      >
                        <FaEdit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-all duration-200"
                        title="Supprimer"
                      >
                        <FaTrash className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de création */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Créer un Utilisateur"
        size="medium"
      >
        <form onSubmit={handleCreateUser} className="space-y-6">
          <FormField
            label="Nom d'utilisateur"
            type="text"
            value={createForm.username}
            onChange={(e) => setCreateForm({...createForm, username: e.target.value})}
            required
          />
          
          <FormField
            label="Email"
            type="email"
            value={createForm.email}
            onChange={(e) => setCreateForm({...createForm, email: e.target.value})}
            required
          />
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mot de passe</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={createForm.password}
                onChange={(e) => setCreateForm({...createForm, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors pr-12"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <FaEyeSlash className="h-4 w-4" /> : <FaEye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          
          <div className="flex items-center p-4 bg-gray-50 rounded-xl">
            <input
              type="checkbox"
              id="is_admin"
              checked={createForm.is_admin}
              onChange={(e) => setCreateForm({...createForm, is_admin: e.target.checked})}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="is_admin" className="ml-3 block text-sm font-medium text-gray-900">
              Administrateur
            </label>
          </div>
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Annuler
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={createUserMutation.isLoading}
              disabled={createUserMutation.isLoading}
            >
              {createUserMutation.isLoading ? 'Création...' : 'Créer'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal d'édition */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Modifier l'Utilisateur"
        size="medium"
      >
        {selectedUser && (
          <form onSubmit={handleEditUser} className="space-y-6">
            <FormField
              label="Nom d'utilisateur"
              type="text"
              value={editForm.username}
              onChange={(e) => setEditForm({...editForm, username: e.target.value})}
              required
            />
            
            <FormField
              label="Email"
              type="email"
              value={editForm.email}
              onChange={(e) => setEditForm({...editForm, email: e.target.value})}
              required
            />
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nouveau mot de passe (laisser vide pour ne pas changer)</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={editForm.password}
                  onChange={(e) => setEditForm({...editForm, password: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <FaEyeSlash className="h-4 w-4" /> : <FaEye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            
            <div className="flex items-center p-4 bg-gray-50 rounded-xl">
              <input
                type="checkbox"
                id="edit_is_admin"
                checked={editForm.is_admin}
                onChange={(e) => setEditForm({...editForm, is_admin: e.target.checked})}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="edit_is_admin" className="ml-3 block text-sm font-medium text-gray-900">
                Administrateur
              </label>
            </div>
            
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowEditModal(false)}
              >
                Annuler
              </Button>
              <Button
                type="submit"
                variant="primary"
                loading={updateUserMutation.isLoading}
                disabled={updateUserMutation.isLoading}
              >
                {updateUserMutation.isLoading ? 'Modification...' : 'Modifier'}
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default UserManagement;
