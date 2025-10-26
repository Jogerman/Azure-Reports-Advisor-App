import { useQuery, UseQueryResult } from '@tanstack/react-query';
import analyticsService from '../services/analyticsService';
import { TrendsResponse, TrendsParams } from '../types/analytics';

/**
 * Custom hook for fetching analytics trends
 */
export const useAnalyticsTrends = (
  params?: TrendsParams
): UseQueryResult<TrendsResponse, Error> => {
  return useQuery({
    queryKey: ['analytics', 'trends', params],
    queryFn: () => analyticsService.getTrends(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes (formerly cacheTime)
    refetchOnWindowFocus: false,
    retry: 2,
  });
};
