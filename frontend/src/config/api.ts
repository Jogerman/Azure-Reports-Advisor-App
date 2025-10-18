const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login/',
    LOGOUT: '/auth/logout/',
    USER: '/auth/user/',
    REFRESH: '/auth/refresh/',
  },

  // Clients
  CLIENTS: {
    LIST: '/clients/',
    DETAIL: (id: string) => `/clients/${id}/`,
    CREATE: '/clients/',
    UPDATE: (id: string) => `/clients/${id}/`,
    DELETE: (id: string) => `/clients/${id}/`,
  },

  // Reports
  REPORTS: {
    LIST: '/reports/',
    UPLOAD: '/reports/upload/',
    GENERATE: (id: string) => `/reports/${id}/generate/`,
    DETAIL: (id: string) => `/reports/${id}/`,
    STATUS: (id: string) => `/reports/${id}/status/`,
    DOWNLOAD: (id: string, format: 'html' | 'pdf' = 'pdf') => `/reports/${id}/download/${format}/`,
    PROCESS: (id: string) => `/reports/${id}/process/`,
  },

  // Analytics
  ANALYTICS: {
    DASHBOARD: '/analytics/dashboard/',
    TRENDS: '/analytics/trends/',
    CATEGORIES: '/analytics/categories/',
    RECENT_ACTIVITY: '/analytics/recent-activity/',
    CLIENT_PERFORMANCE: '/analytics/client-performance/',
  },

  // Health
  HEALTH: '/health/',
} as const;

export { API_BASE_URL };