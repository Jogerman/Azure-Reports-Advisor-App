/**
 * Analytics Types
 * Type definitions for the Analytics Dashboard module
 */

/**
 * Dashboard Metrics Response
 */
export interface DashboardMetrics {
  total_reports: number;
  total_reports_change: number; // % change
  active_users: number;
  active_users_change: number;
  total_cost_analyzed: number;
  total_cost_analyzed_change: number;
  avg_generation_time: number; // seconds
  avg_generation_time_change: number;
  storage_used: number; // bytes
  storage_used_formatted: string;
  success_rate: number; // percentage
}

/**
 * Trend Data Point (for reports over time)
 */
export interface TrendData {
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
  data: TrendData[];
}

/**
 * Category Data (for pie charts)
 */
export interface CategoryData {
  name: string;
  value: number;
  percentage: number;
  color?: string;
  [key: string]: any; // Allow additional properties for Recharts compatibility
}

/**
 * Categories Response
 */
export interface CategoriesResponse {
  data: CategoryData[];
}

/**
 * Top User
 */
export interface TopUser {
  id: string;
  username: string;
  full_name: string;
  reports_count: number;
  last_activity: string; // ISO datetime
  role: string;
}

/**
 * Top Users Response
 */
export interface TopUsersResponse {
  users: TopUser[];
}

/**
 * User Activity
 */
export interface UserActivity {
  id: string;
  user: {
    id: string;
    username: string;
    full_name: string;
  };
  activity_type: string;
  description: string;
  metadata: Record<string, any>;
  timestamp: string; // ISO datetime
}

/**
 * User Activity Response
 */
export interface UserActivityResponse {
  activities: UserActivity[];
  total_count: number;
}

/**
 * Activity Summary Item
 */
export interface ActivitySummary {
  activity_type: string;
  count: number;
  percentage: number;
}

/**
 * Activity Summary Response
 */
export interface ActivitySummaryResponse {
  summary: ActivitySummary[];
  total_activities: number;
  date_range: {
    from: string;
    to: string;
  };
}

/**
 * System Health
 */
export interface SystemHealth {
  database_size: number; // bytes
  database_size_formatted: string;
  total_reports: number;
  active_users_today: number;
  active_users_this_week: number;
  avg_report_generation_time: number; // seconds
  error_rate: number; // percentage
  storage_used: number; // bytes
  storage_used_formatted: string;
  uptime: string;
  last_calculated: string; // ISO datetime
}

/**
 * Cost Insights
 */
export interface CostInsights {
  total_cost_analyzed: number;
  potential_savings: number;
  savings_percentage: number;
  trends: Array<{
    month: string;
    cost: number;
  }>;
}

/**
 * Filter State for Analytics
 */
export interface AnalyticsFilterState {
  dateRange: {
    from: Date | null;
    to: Date | null;
    preset?: string;
  };
  reportTypes: string[];
  userRole?: string;
}

/**
 * API Filter Parameters
 */
export interface AnalyticsFilterParams {
  date_from?: string; // ISO date
  date_to?: string; // ISO date
  report_type?: string[];
  user_role?: string;
}

/**
 * Trends API Parameters
 */
export interface TrendsParams extends AnalyticsFilterParams {
  period?: 'day' | 'week' | 'month';
}

/**
 * User Activity API Parameters
 */
export interface UserActivityParams {
  user_id?: string;
  date_from?: string;
  date_to?: string;
  activity_type?: string;
  limit?: number;
  offset?: number;
}

/**
 * Activity Summary API Parameters
 */
export interface ActivitySummaryParams {
  date_from?: string;
  date_to?: string;
  group_by?: 'activity_type' | 'user' | 'day';
}

/**
 * Chart Colors Configuration
 */
export const CHART_COLORS = {
  cost: '#0078D4',
  security: '#D13438',
  operations: '#107C10',
  detailed: '#8B5CF6',
  executive: '#F59E0B',

  // Status colors
  completed: '#107C10',
  failed: '#D13438',
  processing: '#FFB900',
  pending: '#8B5CF6',

  // Additional chart colors
  primary: '#0078D4',
  secondary: '#50E6FF',
  success: '#107C10',
  warning: '#FFB900',
  danger: '#D13438',
  info: '#8B5CF6',
} as const;

/**
 * Chart Configuration for Report Types
 */
export interface ChartConfig {
  dataKey: keyof TrendData['by_type'];
  name: string;
  color: string;
}

export const REPORT_TYPE_CONFIGS: ChartConfig[] = [
  { dataKey: 'cost', name: 'Cost Optimization', color: CHART_COLORS.cost },
  { dataKey: 'security', name: 'Security Assessment', color: CHART_COLORS.security },
  { dataKey: 'operations', name: 'Operational Excellence', color: CHART_COLORS.operations },
  { dataKey: 'detailed', name: 'Detailed Report', color: CHART_COLORS.detailed },
  { dataKey: 'executive', name: 'Executive Summary', color: CHART_COLORS.executive },
];

/**
 * Activity Type Icons Mapping
 */
export const ACTIVITY_TYPE_ICONS: Record<string, string> = {
  report_generated: 'FiFileText',
  report_deleted: 'FiTrash2',
  report_downloaded: 'FiDownload',
  user_login: 'FiLogIn',
  user_logout: 'FiLogOut',
  client_created: 'FiUserPlus',
  client_updated: 'FiEdit',
  settings_changed: 'FiSettings',
};

/**
 * Date Range Presets
 */
export interface DateRangePreset {
  label: string;
  value: string;
  getDates: () => { from: Date; to: Date };
}

export const DATE_RANGE_PRESETS: DateRangePreset[] = [
  {
    label: 'Last 7 days',
    value: 'last_7_days',
    getDates: () => {
      const to = new Date();
      const from = new Date();
      from.setDate(from.getDate() - 7);
      return { from, to };
    },
  },
  {
    label: 'Last 30 days',
    value: 'last_30_days',
    getDates: () => {
      const to = new Date();
      const from = new Date();
      from.setDate(from.getDate() - 30);
      return { from, to };
    },
  },
  {
    label: 'Last 90 days',
    value: 'last_90_days',
    getDates: () => {
      const to = new Date();
      const from = new Date();
      from.setDate(from.getDate() - 90);
      return { from, to };
    },
  },
  {
    label: 'This month',
    value: 'this_month',
    getDates: () => {
      const to = new Date();
      const from = new Date(to.getFullYear(), to.getMonth(), 1);
      return { from, to };
    },
  },
  {
    label: 'Last month',
    value: 'last_month',
    getDates: () => {
      const to = new Date();
      to.setMonth(to.getMonth() - 1);
      const lastDay = new Date(to.getFullYear(), to.getMonth() + 1, 0);
      const from = new Date(to.getFullYear(), to.getMonth(), 1);
      return { from, to: lastDay };
    },
  },
  {
    label: 'This year',
    value: 'this_year',
    getDates: () => {
      const to = new Date();
      const from = new Date(to.getFullYear(), 0, 1);
      return { from, to };
    },
  },
];
