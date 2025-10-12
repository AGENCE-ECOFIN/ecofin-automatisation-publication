// Données génériques pour le développement sans backend

export const mockUser = {
  id: 1,
  email: "admin@ecofin.com",
  username: "admin",
  is_active: true,
  created_at: "2024-01-01T00:00:00Z"
};

export const mockFeeds = [
  {
    id: 1,
    name: "TechCrunch",
    url: "https://techcrunch.com/feed/",
    frequency_minutes: 60,
    custom_prompt: "Créez un post engageant sur les dernières innovations technologiques",
    target_network: "linkedin",
    is_active: true,
    created_at: "2024-01-15T10:30:00Z",
    last_fetch: "2024-01-20T14:45:00Z"
  },
  {
    id: 2,
    name: "Les Échos",
    url: "https://www.lesechos.fr/rss.xml",
    frequency_minutes: 120,
    custom_prompt: "Analysez les tendances économiques et financières",
    target_network: "facebook",
    is_active: true,
    created_at: "2024-01-10T09:15:00Z",
    last_fetch: "2024-01-20T12:30:00Z"
  },
  {
    id: 3,
    name: "Medium Tech",
    url: "https://medium.com/feed/topic/technology",
    frequency_minutes: 180,
    custom_prompt: "",
    target_network: "",
    is_active: false,
    created_at: "2024-01-05T16:20:00Z",
    last_fetch: "2024-01-18T08:15:00Z"
  }
];

export const mockDrafts = [
  {
    id: 1,
    title: "L'IA révolutionne la finance",
    content: "L'intelligence artificielle transforme radicalement le secteur financier avec de nouvelles applications...",
    source_url: "https://example.com/article1",
    feed_id: 1,
    status: "draft",
    created_at: "2024-01-20T10:00:00Z",
    updated_at: "2024-01-20T10:00:00Z"
  },
  {
    id: 2,
    title: "Blockchain et décentralisation",
    content: "La technologie blockchain ouvre de nouvelles perspectives pour la décentralisation...",
    source_url: "https://example.com/article2",
    feed_id: 2,
    status: "draft",
    created_at: "2024-01-20T11:30:00Z",
    updated_at: "2024-01-20T11:30:00Z"
  }
];

export const mockQueue = [
  {
    id: 3,
    title: "Cryptomonnaies et régulation",
    content: "Les régulateurs s'adaptent à l'évolution rapide des cryptomonnaies...",
    source_url: "https://example.com/article3",
    feed_id: 1,
    status: "validated",
    scheduled_at: "2024-01-21T09:00:00Z",
    created_at: "2024-01-20T15:00:00Z"
  },
  {
    id: 4,
    title: "Fintech et inclusion financière",
    content: "Les fintechs démocratisent l'accès aux services financiers...",
    source_url: "https://example.com/article4",
    feed_id: 2,
    status: "validated",
    scheduled_at: "2024-01-21T14:00:00Z",
    created_at: "2024-01-20T16:30:00Z"
  }
];

export const mockHistory = [
  {
    id: 1,
    post_id: 5,
    network: "linkedin",
    is_success: true,
    published_at: "2024-01-20T08:00:00Z",
    created_at: "2024-01-20T08:00:00Z",
    error_message: null
  },
  {
    id: 2,
    post_id: 6,
    network: "facebook",
    is_success: true,
    published_at: "2024-01-20T10:30:00Z",
    created_at: "2024-01-20T10:30:00Z",
    error_message: null
  },
  {
    id: 3,
    post_id: 7,
    network: "x",
    is_success: false,
    published_at: null,
    created_at: "2024-01-20T12:00:00Z",
    error_message: "Erreur d'authentification API"
  },
  {
    id: 4,
    post_id: 8,
    network: "linkedin",
    is_success: true,
    published_at: "2024-01-19T16:45:00Z",
    created_at: "2024-01-19T16:45:00Z",
    error_message: null
  }
];

// Fonctions utilitaires pour simuler les délais d'API
export const delay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Simulateur d'erreurs aléatoires (10% de chance)
export const shouldSimulateError = () => Math.random() < 0.1;



