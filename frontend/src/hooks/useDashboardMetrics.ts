import { useQuery, UseQueryResult } from '@tanstack/react-query';
import analyticsService from '../services/analyticsService';
import { DashboardMetrics, AnalyticsFilterParams } from '../types/analytics';

/**
 * Custom hook for fetching dashboard metrics
 */
export const useDashboardMetrics = (
  filters?: AnalyticsFilterParams
): UseQueryResult<DashboardMetrics, Error> => {
  return useQuery({
    queryKey: ['analytics', 'metrics', filters],
    queryFn: () => analyticsService.getDashboardMetrics(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    refetchOnWindowFocus: true,
    retry: 2,
  });
};
