import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  DashboardMetrics,
  TrendsResponse,
  TrendsParams,
  CategoriesResponse,
  TopUsersResponse,
  UserActivityResponse,
  UserActivityParams,
  ActivitySummaryResponse,
  ActivitySummaryParams,
  SystemHealth,
  CostInsights,
  AnalyticsFilterParams,
} from '../types/analytics';

/**
 * Analytics Service
 * Handles all analytics-related API calls
 */
class AnalyticsService {
  /**
   * Get dashboard analytics (legacy method for Dashboard page)
   * @deprecated Use getDashboardMetrics instead
   */
  async getDashboardAnalytics(): Promise<any> {
    try {
      const response = await apiClient.get(API_ENDPOINTS.ANALYTICS.DASHBOARD);
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard analytics:', error);
      throw error;
    }
  }

  /**
   * Get dashboard metrics
   */
  async getDashboardMetrics(filters?: AnalyticsFilterParams): Promise<DashboardMetrics> {
    try {
      const response = await apiClient.get<DashboardMetrics>(
        API_ENDPOINTS.ANALYTICS.METRICS,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard metrics:', error);
      throw error;
    }
  }

  /**
   * Get reports over time trends
   */
  async getTrends(params?: TrendsParams): Promise<TrendsResponse> {
    try {
      const response = await apiClient.get<TrendsResponse>(
        API_ENDPOINTS.ANALYTICS.TRENDS,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching trends:', error);
      throw error;
    }
  }

  /**
   * Get reports by type distribution
   */
  async getReportsByType(filters?: AnalyticsFilterParams): Promise<CategoriesResponse> {
    try {
      const response = await apiClient.get<CategoriesResponse>(
        API_ENDPOINTS.ANALYTICS.CATEGORIES,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching reports by type:', error);
      throw error;
    }
  }

  /**
   * Get reports by status distribution
   */
  async getReportsByStatus(filters?: AnalyticsFilterParams): Promise<CategoriesResponse> {
    try {
      const response = await apiClient.get<CategoriesResponse>(
        API_ENDPOINTS.ANALYTICS.CATEGORIES,
        { params: { ...filters, group_by: 'status' } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching reports by status:', error);
      throw error;
    }
  }

  /**
   * Get top users by report count
   */
  async getTopUsers(filters?: AnalyticsFilterParams): Promise<TopUsersResponse> {
    try {
      const response = await apiClient.get<TopUsersResponse>(
        API_ENDPOINTS.ANALYTICS.RECENT_ACTIVITY,
        { params: { ...filters, type: 'top_users' } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching top users:', error);
      throw error;
    }
  }

  /**
   * Get user activity timeline
   */
  async getUserActivity(params?: UserActivityParams): Promise<UserActivityResponse> {
    try {
      const response = await apiClient.get<UserActivityResponse>(
        API_ENDPOINTS.ANALYTICS.USER_ACTIVITY,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching user activity:', error);
      throw error;
    }
  }

  /**
   * Get activity summary
   */
  async getActivitySummary(params?: ActivitySummaryParams): Promise<ActivitySummaryResponse> {
    try {
      const response = await apiClient.get<ActivitySummaryResponse>(
        API_ENDPOINTS.ANALYTICS.ACTIVITY_SUMMARY,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching activity summary:', error);
      throw error;
    }
  }

  /**
   * Get system health metrics
   */
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await apiClient.get<SystemHealth>(
        API_ENDPOINTS.ANALYTICS.SYSTEM_HEALTH
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching system health:', error);
      throw error;
    }
  }

  /**
   * Get cost insights
   */
  async getCostInsights(filters?: AnalyticsFilterParams): Promise<CostInsights> {
    try {
      const response = await apiClient.get<CostInsights>(
        API_ENDPOINTS.ANALYTICS.COST_INSIGHTS,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching cost insights:', error);
      throw error;
    }
  }

  /**
   * Export dashboard data as CSV
   */
  async exportDashboardCSV(filters?: AnalyticsFilterParams): Promise<Blob> {
    try {
      const response = await apiClient.get(
        `${API_ENDPOINTS.ANALYTICS.METRICS}/export/`,
        {
          params: filters,
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error exporting dashboard CSV:', error);
      throw error;
    }
  }

  /**
   * Helper: Download file from blob
   */
  downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

// Export singleton instance
const analyticsService = new AnalyticsService();
export default analyticsService;
