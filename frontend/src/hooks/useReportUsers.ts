import { useQuery } from '@tanstack/react-query';
import reportService from '../services/reportService';

/**
 * Custom hook to fetch list of users who created reports
 * Cached for 10 minutes as this data changes infrequently
 */
export const useReportUsers = () => {
  return useQuery({
    queryKey: ['report-users'],
    queryFn: () => reportService.getReportUsers(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
};
