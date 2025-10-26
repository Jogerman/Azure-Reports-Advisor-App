import { useQuery } from '@tanstack/react-query';
import reportService from '../services/reportService';
import { HistoryFilterParams } from '../types/history';

/**
 * Custom hook to fetch history statistics
 * Includes stale time of 2 minutes for caching
 */
export const useHistoryStats = (filters?: HistoryFilterParams) => {
  return useQuery({
    queryKey: ['history', 'statistics', filters],
    queryFn: () => reportService.getHistoryStatistics(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
  });
};
