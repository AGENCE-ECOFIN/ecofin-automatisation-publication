import React, { useState } from 'react';

const TestConnection = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setResult({
        success: response.ok,
        status: response.status,
        data: data
      });
    } catch (error) {
      setResult({
        success: false,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">Test de Connexion API</h1>
          <p className="text-gray-600 mb-8">
            Testez la connexion avec l'API backend pour vérifier que tout fonctionne correctement.
          </p>

          <div className="space-y-6">
            <button
              onClick={testConnection}
              disabled={loading}
              className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Test en cours...' : 'Tester la connexion'}
            </button>

            {result && (
              <div className={`p-6 rounded-lg border-2 ${
                result.success 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <h3 className={`text-lg font-semibold mb-4 ${
                  result.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {result.success ? '✅ Connexion réussie' : '❌ Connexion échouée'}
                </h3>
                
                {result.success ? (
                  <div className="space-y-2">
                    <p className="text-green-700">
                      <strong>Statut HTTP:</strong> {result.status}
                    </p>
                    <p className="text-green-700">
                      <strong>Réponse:</strong> {JSON.stringify(result.data, null, 2)}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-red-700">
                      <strong>Erreur:</strong> {result.error}
                    </p>
                    <p className="text-red-700">
                      <strong>Statut:</strong> {result.status || 'N/A'}
                    </p>
                  </div>
                )}
              </div>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-800 mb-3">Informations de test</h3>
              <div className="space-y-2 text-blue-700">
                <p><strong>URL de test:</strong> http://localhost:8000/health</p>
                <p><strong>Méthode:</strong> GET</p>
                <p><strong>Endpoint:</strong> /health</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestConnection;