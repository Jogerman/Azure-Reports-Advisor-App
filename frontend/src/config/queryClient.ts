import { QueryClient } from '@tanstack/react-query';

/**
 * Optimized React Query Configuration
 *
 * Performance optimizations:
 * - staleTime: 5 minutes - data considered fresh for 5 minutes
 * - gcTime: 10 minutes - cached data kept in memory for 10 minutes
 * - refetchOnWindowFocus: false - prevent unnecessary refetches
 * - refetchOnReconnect: true - refetch when connection restored
 * - retry: 1 - only retry failed queries once
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // How long data is considered fresh (no refetch)
      staleTime: 5 * 60 * 1000, // 5 minutes

      // How long unused data stays in cache
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)

      // Don't refetch when tab regains focus
      refetchOnWindowFocus: false,

      // Refetch when internet connection is restored
      refetchOnReconnect: true,

      // Only retry failed queries once
      retry: 1,

      // Prevent excessive retries on slow connections
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,

      // Don't retry on 4xx errors (client errors)
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

// Query keys for consistent cache management
export const queryKeys = {
  // Dashboard
  dashboardAnalytics: ['dashboard', 'analytics'] as const,
  trendData: (days: number) => ['analytics', 'trends', days] as const,
  categories: ['analytics', 'categories'] as const,
  recentActivity: (limit: number) => ['analytics', 'recent-activity', limit] as const,

  // Clients
  clients: (params?: any) => ['clients', params] as const,
  client: (id: string) => ['clients', id] as const,
  clientReports: (id: string) => ['clients', id, 'reports'] as const,

  // Reports
  reports: (params?: any) => ['reports', params] as const,
  report: (id: string) => ['reports', id] as const,
  reportStatus: (id: string) => ['reports', id, 'status'] as const,

  // Auth
  currentUser: ['auth', 'user'] as const,
} as const;

export default queryClient;
