import axios from 'axios';
import { 
  mockUser, 
  mockFeeds, 
  mockDrafts, 
  mockQueue, 
  mockHistory, 
  delay, 
  shouldSimulateError 
} from './mockData';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const USE_MOCK_DATA = false; // Désactivé pour utiliser l'API réelle


export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs de réponse
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Services API
export const authService = {
  login: async (credentials) => {
    if (USE_MOCK_DATA) {
      await delay(1000);
      if (shouldSimulateError()) {
        throw new Error('Erreur de connexion simulée');
      }
      return { data: { access_token: 'mock-token', user: mockUser } };
    }
    return api.post('/auth/login', credentials, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
  },
  register: async (userData) => {
    if (USE_MOCK_DATA) {
      await delay(800);
      if (shouldSimulateError()) {
        throw new Error('Erreur d\'inscription simulée');
      }
      return { data: { user: mockUser } };
    }
    return api.post('/auth/register', userData);
  },
  getMe: async () => {
    if (USE_MOCK_DATA) {
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur d\'authentification simulée');
      }
      return { data: mockUser };
    }
    return api.get('/auth/me');
  },
};

export const feedsService = {
         getFeeds: async () => {
           if (USE_MOCK_DATA) {
             await delay(600);
             if (shouldSimulateError()) {
               throw new Error('Erreur de récupération des flux simulée');
             }
             return { data: mockFeeds };
           }
           try {
             const response = await api.get('/feeds');
             return response;
           } catch (error) {
             console.error('❌ Erreur API getFeeds:', error);
             throw error;
           }
         },
         getCollectionStatus: async () => {
           if (USE_MOCK_DATA) {
             await delay(500);
             return { data: { feeds: [], active_tasks: {}, scheduled_tasks: {} } };
           }
           try {
             const response = await api.get('/feeds/status/collections');
             return response;
           } catch (error) {
             console.error('❌ Erreur API getCollectionStatus:', error);
             throw error;
           }
         },
  getFeed: async (id) => {
    if (USE_MOCK_DATA) {
      await delay(400);
      const feed = mockFeeds.find(f => f.id === parseInt(id));
      if (!feed) {
        throw new Error('Flux non trouvé');
      }
      return { data: feed };
    }
    return api.get(`/feeds/${id}`);
  },
  createFeed: async (feedData) => {
    if (USE_MOCK_DATA) {
      await delay(800);
      if (shouldSimulateError()) {
        throw new Error('Erreur de création du flux simulée');
      }
      const newFeed = {
        id: Math.max(...mockFeeds.map(f => f.id)) + 1,
        ...feedData,
        created_at: new Date().toISOString(),
        last_fetch: null
      };
      mockFeeds.push(newFeed);
      return { data: newFeed };
    }
    return api.post('/feeds', feedData);
  },
  updateFeed: async (id, feedData) => {
    if (USE_MOCK_DATA) {
      await delay(700);
      if (shouldSimulateError()) {
        throw new Error('Erreur de mise à jour du flux simulée');
      }
      const index = mockFeeds.findIndex(f => f.id === parseInt(id));
      if (index === -1) {
        throw new Error('Flux non trouvé');
      }
      mockFeeds[index] = { ...mockFeeds[index], ...feedData };
      return { data: mockFeeds[index] };
    }
    return api.put(`/feeds/${id}`, feedData);
  },
  deleteFeed: async (id) => {
    if (USE_MOCK_DATA) {
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de suppression du flux simulée');
      }
      const index = mockFeeds.findIndex(f => f.id === parseInt(id));
      if (index === -1) {
        throw new Error('Flux non trouvé');
      }
      mockFeeds.splice(index, 1);
      return { data: { message: 'Flux supprimé avec succès' } };
    }
    return api.delete(`/feeds/${id}`);
  },
  
  // Fonctions pour gérer les prompts
  updateFeedPrompts: async (feedId, networkPrompts) => {
    console.log('🔧 Updating feed prompts:', { feedId, networkPrompts });
    try {
      const response = await api.put(`/feeds/${feedId}/prompts`, {
        network_prompts: networkPrompts
      });
      console.log('✅ Feed prompts updated:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Update feed prompts error:', error);
      throw error;
    }
  },
  
  getFeedPrompts: async (feedId) => {
    console.log('🔧 Getting feed prompts:', feedId);
    try {
      const response = await api.get(`/feeds/${feedId}`);
      console.log('✅ Feed prompts retrieved:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Get feed prompts error:', error);
      throw error;
    }
  },
};

export const postsService = {
        getDrafts: async () => {
          if (USE_MOCK_DATA) {
            console.log('🔧 Using mock data for drafts');
            await delay(500);
            if (shouldSimulateError()) {
              throw new Error('Erreur de récupération des brouillons simulée');
            }
            return { data: mockDrafts };
          }
          try {
            const response = await api.get('/posts/drafts');
            return response;
          } catch (error) {
            console.error('❌ Drafts API error:', error);
            throw error;
          }
        },
  getValidated: async () => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for validated');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de récupération des posts validés simulée');
      }
      return { data: mockQueue };
    }
          try {
            const response = await api.get('/posts/validated');
            return response;
    } catch (error) {
      console.error('❌ Validated API error:', error);
      throw error;
    }
  },
  getQueue: async () => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for queue');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de récupération de la file d\'attente simulée');
      }
      return { data: mockQueue };
    }
    console.log('🔧 Fetching real queue from API...');
    try {
      const response = await api.get('/publication-queue/');
      console.log('✅ Queue API response:', response.data?.length || 0, 'items');
      return response;
    } catch (error) {
      console.error('❌ Queue API error:', error);
      throw error;
    }
  },
  getPost: async (id) => {
    if (USE_MOCK_DATA) {
      await delay(400);
      const post = [...mockDrafts, ...mockQueue].find(p => p.id === parseInt(id));
      if (!post) {
        throw new Error('Post non trouvé');
      }
      return { data: post };
    }
    return api.get(`/posts/${id}`);
  },
  createPost: async (postData) => {
    if (USE_MOCK_DATA) {
      await delay(800);
      if (shouldSimulateError()) {
        throw new Error('Erreur de création du post simulée');
      }
      const newPost = {
        id: Math.max(...mockDrafts.map(p => p.id), ...mockQueue.map(p => p.id)) + 1,
        ...postData,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      mockDrafts.push(newPost);
      return { data: newPost };
    }
    return api.post('/posts', postData);
  },
  updatePost: async (id, postData) => {
    if (USE_MOCK_DATA) {
      await delay(700);
      if (shouldSimulateError()) {
        throw new Error('Erreur de mise à jour du post simulée');
      }
      const allPosts = [...mockDrafts, ...mockQueue];
      const index = allPosts.findIndex(p => p.id === parseInt(id));
      if (index === -1) {
        throw new Error('Post non trouvé');
      }
      allPosts[index] = { ...allPosts[index], ...postData, updated_at: new Date().toISOString() };
      return { data: allPosts[index] };
    }
    return api.put(`/posts/${id}`, postData);
  },
  validatePost: async (id, data) => {
    if (USE_MOCK_DATA) {
      await delay(1000);
      if (shouldSimulateError()) {
        throw new Error('Erreur de validation du post simulée');
      }
      const draftIndex = mockDrafts.findIndex(p => p.id === parseInt(id));
      if (draftIndex !== -1) {
        const post = mockDrafts[draftIndex];
        mockDrafts.splice(draftIndex, 1);
        mockQueue.push({
          ...post,
          status: 'validated',
          scheduled_at: data.scheduled_at || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
        });
      }
      return { data: { message: 'Post validé avec succès' } };
    }
    return api.post(`/posts/${id}/validate`, data);
  },
  publishNow: async (id) => {
    if (USE_MOCK_DATA) {
      await delay(1200);
      if (shouldSimulateError()) {
        throw new Error('Erreur de publication immédiate simulée');
      }
      const queueIndex = mockQueue.findIndex(p => p.id === parseInt(id));
      if (queueIndex !== -1) {
        mockQueue.splice(queueIndex, 1);
        mockHistory.unshift({
          id: mockHistory.length + 1,
          post_id: parseInt(id),
          network: 'linkedin',
          is_success: true,
          published_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          error_message: null
        });
      }
      return { data: { message: 'Post publié avec succès' } };
    }
    return api.post(`/posts/${id}/publish-now`);
  },
         getHistory: async (limit = 100) => {
           if (USE_MOCK_DATA) {
             console.log('🔧 Using mock data for history');
             await delay(600);
             if (shouldSimulateError()) {
               throw new Error('Erreur de récupération de l\'historique simulée');
             }
             return { data: mockHistory.slice(0, limit) };
           }
           console.log('🔧 Fetching real history from API...');
           try {
             const response = await api.get(`/posts/history/publications?limit=${limit}`);
             console.log('✅ History API response:', response.data?.length || 0, 'publications');
             return response;
           } catch (error) {
             console.error('❌ History API error:', error);
             throw error;
           }
         },
         getRejected: async () => {
           if (USE_MOCK_DATA) {
             console.log('🔧 Using mock data for rejected');
             await delay(500);
             if (shouldSimulateError()) {
               throw new Error('Erreur de récupération des posts rejetés simulée');
             }
             return { data: [] };
           }
          try {
            const response = await api.get('/posts/rejected');
            return response;
           } catch (error) {
             console.error('❌ Rejected API error:', error);
             throw error;
           }
         },
         rejectPost: async (id, rejectionReason = null) => {
           if (USE_MOCK_DATA) {
             await delay(800);
             if (shouldSimulateError()) {
               throw new Error('Erreur de rejet du post simulée');
             }
             return { data: { message: 'Post rejeté avec succès' } };
           }
           // Envoyer un body vide si pas de raison, ou un objet avec rejection_reason si fourni
           // Envoyer un body vide {} si pas de raison (FastAPI accepte un body vide pour les schémas avec tous les champs optionnels)
           const body = rejectionReason ? { rejection_reason: rejectionReason } : {};
           return api.post(`/posts/${id}/reject`, body);
         },
         restorePost: async (id) => {
           if (USE_MOCK_DATA) {
             await delay(800);
             if (shouldSimulateError()) {
               throw new Error('Erreur de restauration du post simulée');
             }
             return { data: { message: 'Post restauré en brouillon avec succès' } };
           }
           return api.post(`/posts/${id}/restore`);
         },
         getDirect: async () => {
           if (USE_MOCK_DATA) {
             console.log('🔧 Using mock data for direct posts');
             await delay(500);
             if (shouldSimulateError()) {
               throw new Error('Erreur de récupération des posts directs simulée');
             }
             return { data: [] };
           }
          try {
            const response = await api.get('/posts/direct');
            return response;
           } catch (error) {
             console.error('❌ Direct posts API error:', error);
             throw error;
           }
         },
         getDirectPosts: async () => {
           if (USE_MOCK_DATA) {
             console.log('🔧 Using mock data for direct posts (immediate)');
             await delay(500);
             if (shouldSimulateError()) {
               throw new Error('Erreur de récupération des posts directs immédiats simulée');
             }
             return { data: [] };
           }
          try {
            const response = await api.get('/posts/direct');
            return response;
           } catch (error) {
             console.error('❌ Direct posts (immediate) API error:', error);
             throw error;
           }
         },

  // Nouvelles méthodes pour la validation granulaire
  validateNetwork: async (postId, network) => {
    console.log('🔧 Validating network:', { postId, network });
    try {
      const response = await api.post(`/posts/${postId}/networks/${network}/validate`);
      console.log('✅ Network validated:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Validate network error:', error);
      throw error;
    }
  },

  rejectNetwork: async (postId, network, rejectionReason) => {
    console.log('🔧 Rejecting network:', { postId, network, rejectionReason });
    try {
      const response = await api.post(`/posts/${postId}/networks/${network}/reject`, {
        network,
        action: 'reject',
        rejection_reason: rejectionReason
      });
      console.log('✅ Network rejected:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Reject network error:', error);
      throw error;
    }
  },

  restoreNetwork: async (postId, network) => {
    console.log('🔧 Restoring network:', { postId, network });
    try {
      // Utiliser l'endpoint spécifique de restauration
      const response = await api.post(`/posts/${postId}/networks/${network}/restore`);
      console.log('✅ Network restored:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Restore network error:', error);
      throw error;
    }
  },
};

export const usersService = {
  getUsers: async () => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for users');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de récupération des utilisateurs simulée');
      }
      return { 
        data: [
          {
            id: 1,
            username: 'adminuser',
            email: 'admin@example.com',
            is_admin: true,
            created_at: '2024-01-01T00:00:00Z'
          },
          {
            id: 2,
            username: 'user1',
            email: 'user1@example.com',
            is_admin: false,
            created_at: '2024-01-02T00:00:00Z'
          }
        ]
      };
    }
    console.log('🔧 Fetching real users from API...');
    try {
      const response = await api.get('/users/');
      console.log('✅ Users API response:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Users API error:', error);
      throw error;
    }
  },
  createUser: async (userData) => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for create user');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de création d\'utilisateur simulée');
      }
      return { 
        data: {
          id: Date.now(),
          ...userData,
          created_at: new Date().toISOString()
        }
      };
    }
    console.log('🔧 Creating user via API...');
    try {
      const response = await api.post('/users/', userData);
      console.log('✅ Create user API response:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Create user API error:', error);
      throw error;
    }
  },
  updateUser: async (userId, userData) => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for update user');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de mise à jour d\'utilisateur simulée');
      }
      return { 
        data: {
          id: userId,
          ...userData,
          updated_at: new Date().toISOString()
        }
      };
    }
    console.log('🔧 Updating user via API...');
    try {
      const response = await api.put(`/users/${userId}`, userData);
      console.log('✅ Update user API response:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Update user API error:', error);
      throw error;
    }
  },
  deleteUser: async (userId) => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for delete user');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de suppression d\'utilisateur simulée');
      }
      return { 
        data: { message: 'Utilisateur supprimé avec succès' }
      };
    }
    console.log('🔧 Deleting user via API...');
    try {
      const response = await api.delete(`/users/${userId}`);
      console.log('✅ Delete user API response:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Delete user API error:', error);
      throw error;
    }
  }
};

export const tasksService = {
  getTasksHistory: async () => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for tasks history');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de récupération de l\'historique des tâches simulée');
      }
      return { 
        data: {
          workers: {},
          active_tasks: {},
          scheduled_tasks: {},
          reserved_tasks: {},
          stats: {},
          timestamp: new Date().toISOString()
        }
      };
    }
    console.log('🔧 Fetching real Celery status from API...');
    try {
      const response = await api.get('/celery/status');
      console.log('✅ Celery status API response:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Celery status API error:', error);
      throw error;
    }
  },
  getTasksStats: async () => {
    if (USE_MOCK_DATA) {
      console.log('🔧 Using mock data for tasks stats');
      await delay(500);
      if (shouldSimulateError()) {
        throw new Error('Erreur de récupération des statistiques des tâches simulée');
      }
      return { 
        data: {
          total_workers: 1,
          total_active_tasks: 0,
          workers: [],
          timestamp: new Date().toISOString()
        }
      };
    }
    console.log('🔧 Fetching real tasks stats from API...');
    try {
      const response = await api.get('/tasks/stats');
      console.log('✅ Tasks stats API response:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Tasks stats API error:', error);
      throw error;
    }
  },
};

// Services pour les réseaux
export const networksService = {
  getNetworks: async () => {
    try {
      const response = await api.get('/networks/');
      return response;
    } catch (error) {
      console.error('❌ Get networks error:', error);
      throw error;
    }
  },

  createNetwork: async (networkData) => {
    console.log('🔧 Creating network:', networkData);
    try {
      const response = await api.post('/networks/', networkData);
      console.log('✅ Network created:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Create network error:', error);
      throw error;
    }
  },

  updateNetwork: async (networkId, networkData) => {
    console.log('🔧 Updating network:', { networkId, networkData });
    try {
      const response = await api.put(`/networks/${networkId}`, networkData);
      console.log('✅ Network updated:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Update network error:', error);
      throw error;
    }
  },

  deleteNetwork: async (networkId) => {
    console.log('🔧 Deleting network:', networkId);
    try {
      const response = await api.delete(`/networks/${networkId}`);
      console.log('✅ Network deleted:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Delete network error:', error);
      throw error;
    }
  },
};

// Services pour la file d'attente de publication
export const auditService = {
  getLogs: async (params = {}) => {
    try {
      const response = await api.get('/audit/', { params });
      return response;
    } catch (error) {
      console.error('❌ Audit logs API error:', error);
      throw error;
    }
  },
  getSummary: async () => {
    try {
      const response = await api.get('/audit/summary');
      return response;
    } catch (error) {
      console.error('❌ Audit summary API error:', error);
      throw error;
    }
  },
};

export const publicationQueueService = {
  getQueue: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.network) params.append('network', filters.network);
      if (filters.feed_id) params.append('feed_id', filters.feed_id);
      
      const response = await api.get(`/publication-queue/?${params.toString()}`);
      return response;
    } catch (error) {
      console.error('❌ Get publication queue error:', error);
      throw error;
    }
  },

  pauseItem: async (itemId) => {
    console.log('🔧 Pausing queue item:', itemId);
    try {
      const response = await api.put(`/publication-queue/${itemId}/pause`);
      console.log('✅ Queue item paused:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Pause queue item error:', error);
      throw error;
    }
  },

  resumeItem: async (itemId) => {
    console.log('🔧 Resuming queue item:', itemId);
    try {
      const response = await api.put(`/publication-queue/${itemId}/resume`);
      console.log('✅ Queue item resumed:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Resume queue item error:', error);
      throw error;
    }
  },

  cancelItem: async (itemId) => {
    console.log('🔧 Cancelling queue item:', itemId);
    try {
      const response = await api.put(`/publication-queue/${itemId}/cancel`);
      console.log('✅ Queue item cancelled:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Cancel queue item error:', error);
      throw error;
    }
  },

  retryItem: async (itemId) => {
    console.log('🔧 Retrying queue item:', itemId);
    try {
      const response = await api.put(`/publication-queue/${itemId}/retry`);
      console.log('✅ Queue item retried:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Retry queue item error:', error);
      throw error;
    }
  },

  getStats: async () => {
    console.log('🔧 Getting queue stats...');
    try {
      const response = await api.get('/publication-queue/stats/summary');
      console.log('✅ Queue stats retrieved:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Get queue stats error:', error);
      throw error;
    }
  },

  addValidatedPosts: async () => {
    console.log('🔧 Adding validated posts to queue...');
    try {
      const response = await api.post('/publication-queue/add-validated-posts');
      console.log('✅ Validated posts added to queue:', response.data);
      return response;
    } catch (error) {
      console.error('❌ Add validated posts error:', error);
      throw error;
    }
  },
};

