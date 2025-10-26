import { ReportType, ReportStatus, Report } from '../services/reportService';

/**
 * History Statistics Response
 */
export interface HistoryStatistics {
  total_reports: number;
  total_reports_change: number; // % change
  reports_this_month: number;
  reports_this_month_change: number;
  total_size: number; // bytes
  total_size_formatted: string; // "2.4 GB"
  total_size_change: number;
  breakdown: {
    cost: number;
    security: number;
    operations: number;
    detailed: number;
    executive: number;
  };
}

/**
 * Single trend data point
 */
export interface TrendDataPoint {
  date: string; // ISO date
  total: number;
  by_type: {
    cost: number;
    security: number;
    operations: number;
    detailed: number;
    executive: number;
  };
}

/**
 * Trends Response
 */
export interface TrendsResponse {
  data: TrendDataPoint[];
}

/**
 * User with report count
 */
export interface ReportUser {
  id: string;
  username: string;
  full_name: string;
  report_count: number;
}

/**
 * Users Response
 */
export interface UsersResponse {
  users: ReportUser[];
}

/**
 * Filter state for History page
 */
export interface HistoryFilterState {
  search: string;
  reportTypes: ReportType[];
  statuses: ReportStatus[];
  createdBy: string[];
  dateFrom: Date | null;
  dateTo: Date | null;
  clientId: string;
}

/**
 * API filter parameters
 */
export interface HistoryFilterParams {
  search?: string;
  report_type?: ReportType[];
  status?: ReportStatus[];
  created_by?: string[];
  date_from?: string; // ISO date
  date_to?: string; // ISO date
  client_id?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

/**
 * Trends API parameters
 */
export interface TrendsParams {
  granularity?: 'day' | 'week' | 'month';
  date_from?: string;
  date_to?: string;
  report_type?: ReportType[];
  status?: ReportStatus[];
  created_by?: string[];
  client_id?: string;
}

/**
 * Chart configuration for report types
 */
export interface ChartConfig {
  dataKey: string;
  name: string;
  color: string;
}

/**
 * Table sorting state
 */
export interface SortingState {
  field: string;
  direction: 'asc' | 'desc';
}

/**
 * Pagination state
 */
export interface PaginationState {
  currentPage: number;
  pageSize: number;
  totalPages: number;
  totalCount: number;
}

/**
 * Date range preset
 */
export interface DateRangePreset {
  label: string;
  getValue: () => { from: Date; to: Date };
}

/**
 * Multi-select option
 */
export interface SelectOption {
  value: string;
  label: string;
  count?: number;
}

/**
 * Export CSV parameters
 */
export interface ExportCSVParams {
  filters: HistoryFilterParams;
  columns?: string[];
}

/**
 * Report with extended details for History
 */
export interface HistoryReport extends Report {
  user_full_name?: string;
  csv_size?: number;
  html_size?: number;
  pdf_size?: number;
  total_size?: number;
  duration?: number; // seconds
}
