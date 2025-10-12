import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { FaRss, FaEye, FaEyeSlash } from 'react-icons/fa';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const result = await login({
          username: formData.username,
          password: formData.password
        });
        if (!result.success) {
          setError(result.error);
        }
      } else {
        if (formData.password !== formData.confirmPassword) {
          setError('Les mots de passe ne correspondent pas');
          setLoading(false);
          return;
        }
        const result = await register({
          username: formData.username,
          email: formData.email,
          password: formData.password
        });
        if (!result.success) {
          setError(result.error);
        }
      }
    } catch (err) {
      setError('Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    });
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <FaRss className="text-4xl text-indigo-600 mr-3" />
          <h1 className="text-3xl font-bold text-indigo-600">EcoFin Pub</h1>
        </div>

        {/* Title */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-800">
            {isLogin ? 'Connexion' : 'Inscription'}
          </h2>
          <p className="text-gray-600 mt-2">
            {isLogin 
              ? 'Connectez-vous à votre compte' 
              : 'Créez votre compte pour commencer'
            }
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Nom d'utilisateur
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              placeholder="Votre nom d'utilisateur"
            />
          </div>

          {/* Email (only for registration) */}
          {!isLogin && (
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="votre@email.com"
              />
            </div>
          )}

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Mot de passe
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="Votre mot de passe"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-indigo-600 transition-colors"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>
          </div>

          {/* Confirm Password (only for registration) */}
          {!isLogin && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                Confirmer le mot de passe
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="Confirmez votre mot de passe"
              />
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'S\'inscrire')}
          </button>
        </form>

        {/* Switch Mode */}
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            {isLogin ? 'Pas encore de compte ?' : 'Déjà un compte ?'}
            <button
              onClick={toggleMode}
              className="ml-2 text-indigo-600 hover:text-indigo-700 font-medium underline"
            >
              {isLogin ? 'S\'inscrire' : 'Se connecter'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;