// Script pour forcer la reconnexion avec adminuser
export const forceLogin = async () => {
  try {
    // Supprimer l'ancien token
    localStorage.removeItem('token');
    
    // Se connecter avec adminuser
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'adminuser',
        password: 'adminpassword'
      })
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      console.log('✅ Connexion réussie avec adminuser');
      return { success: true, token: data.access_token };
    } else {
      const error = await response.text();
      console.error('❌ Erreur de connexion:', error);
      return { success: false, error };
    }
  } catch (error) {
    console.error('❌ Erreur réseau:', error);
    return { success: false, error: error.message };
  }
};

// Fonction pour tester la connexion
export const testConnection = async () => {
  try {
    const response = await fetch('http://localhost:8000/feeds', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (response.ok) {
      const feedsPayload = await response.json();
      const feeds = Array.isArray(feedsPayload?.items) ? feedsPayload.items : feedsPayload;
      console.log('✅ Connexion testée:', feeds.length, 'flux trouvés');
      return { success: true, feeds };
    } else {
      console.error('❌ Erreur test connexion:', response.status);
      return { success: false, status: response.status };
    }
  } catch (error) {
    console.error('❌ Erreur test:', error);
    return { success: false, error: error.message };
  }
};

