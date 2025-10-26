import { useMutation } from '@tanstack/react-query';
import reportService from '../services/reportService';
import { HistoryFilterParams } from '../types/history';

/**
 * Custom hook to handle CSV export with loading and error states
 * Returns the mutation directly for flexible usage
 */
export const useReportExport = () => {
  return useMutation({
    mutationFn: (filters?: HistoryFilterParams) => reportService.exportToCSV(filters),
  });
};
