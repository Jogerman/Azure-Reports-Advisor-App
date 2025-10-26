import { useQuery } from '@tanstack/react-query';
import reportService from '../services/reportService';
import { TrendsParams } from '../types/history';

/**
 * Custom hook to fetch history trends data
 * Includes stale time of 5 minutes for caching
 */
export const useHistoryTrends = (params?: TrendsParams) => {
  return useQuery({
    queryKey: ['history', 'trends', params],
    queryFn: () => reportService.getHistoryTrends(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};
