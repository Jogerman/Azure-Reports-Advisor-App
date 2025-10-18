import apiClient from './apiClient';
import { CategoryData, TrendDataPoint, ActivityItem } from '../components/dashboard';
import { API_ENDPOINTS } from '../config/api';

// Analytics types
export interface DashboardMetrics {
  totalRecommendations: number;
  totalPotentialSavings: number;
  activeClients: number;
  reportsGeneratedThisMonth: number;
  trends: {
    recommendations: number; // percentage change
    savings: number;
    clients: number;
    reports: number;
  };
}

export interface AnalyticsData {
  metrics: DashboardMetrics;
  categoryDistribution: CategoryData[];
  trendData: TrendDataPoint[];
  recentActivity: ActivityItem[];
}

// Analytics Service
class AnalyticsService {
  /**
   * Get dashboard analytics data
   * Fetches comprehensive analytics for the dashboard from the backend API
   */
  async getDashboardAnalytics(): Promise<AnalyticsData> {
    try {
      const response = await apiClient.get(API_ENDPOINTS.ANALYTICS.DASHBOARD);
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard analytics:', error);
      // Fallback to mock data if backend is not available
      console.warn('Falling back to mock data - backend may not be available');
      return this.getMockAnalyticsData();
    }
  }

  /**
   * Get trend data for a specific time range
   * @param days - Number of days to retrieve (7, 30, or 90)
   */
  async getTrendData(days: 7 | 30 | 90 = 30): Promise<TrendDataPoint[]> {
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.ANALYTICS.TRENDS}?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching trend data:', error);
      console.warn('Falling back to mock data - backend may not be available');
      return this.getMockTrendData(days);
    }
  }

  /**
   * Get category distribution data
   */
  async getCategoryDistribution(): Promise<CategoryData[]> {
    try {
      const response = await apiClient.get(API_ENDPOINTS.ANALYTICS.CATEGORIES);
      return response.data;
    } catch (error) {
      console.error('Error fetching category distribution:', error);
      console.warn('Falling back to mock data - backend may not be available');
      return this.getMockCategoryData();
    }
  }

  /**
   * Get recent activity
   * @param limit - Maximum number of items to return
   */
  async getRecentActivity(limit: number = 10): Promise<ActivityItem[]> {
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.ANALYTICS.RECENT_ACTIVITY}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching recent activity:', error);
      console.warn('Falling back to mock data - backend may not be available');
      return this.getMockActivityData(limit);
    }
  }

  // ==================== MOCK DATA GENERATORS ====================
  // These will be removed when the backend analytics endpoints are implemented

  private getMockAnalyticsData(): AnalyticsData {
    return {
      metrics: {
        totalRecommendations: 1247,
        totalPotentialSavings: 45890,
        activeClients: 24,
        reportsGeneratedThisMonth: 18,
        trends: {
          recommendations: 12.5,
          savings: 8.3,
          clients: 4.2,
          reports: 15.7,
        },
      },
      categoryDistribution: this.getMockCategoryData(),
      trendData: this.getMockTrendData(30),
      recentActivity: this.getMockActivityData(10),
    };
  }

  private getMockCategoryData(): CategoryData[] {
    return [
      { name: 'Cost', value: 342, color: '#f59e0b' },
      { name: 'Security', value: 189, color: '#ef4444' },
      { name: 'Reliability', value: 456, color: '#3b82f6' },
      { name: 'Operational Excellence', value: 178, color: '#8b5cf6' },
      { name: 'Performance', value: 82, color: '#10b981' },
    ];
  }

  private getMockTrendData(days: number): TrendDataPoint[] {
    const data: TrendDataPoint[] = [];
    const today = new Date();

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);

      // Generate realistic-looking data with some variation
      const baseValue = 2;
      const variation = Math.floor(Math.random() * 5);
      const weekendFactor = date.getDay() === 0 || date.getDay() === 6 ? 0.3 : 1;

      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.floor((baseValue + variation) * weekendFactor),
        label: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      });
    }

    return data;
  }

  private getMockActivityData(limit: number): ActivityItem[] {
    const activities: ActivityItem[] = [
      {
        id: '1',
        type: 'report_generated',
        title: 'Cost Optimization Report Generated',
        description: 'Successfully generated cost optimization report for Contoso Ltd.',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        clientName: 'Contoso Ltd.',
        reportType: 'Cost Optimization',
        reportId: 'report-1',
        status: 'completed',
      },
      {
        id: '2',
        type: 'report_processing',
        title: 'Executive Summary Processing',
        description: 'Processing executive summary report for Fabrikam Inc.',
        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
        clientName: 'Fabrikam Inc.',
        reportType: 'Executive Summary',
        reportId: 'report-2',
        status: 'processing',
      },
      {
        id: '3',
        type: 'report_generated',
        title: 'Security Assessment Complete',
        description: 'Security assessment report ready for download.',
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000), // 8 hours ago
        clientName: 'Adventure Works',
        reportType: 'Security Assessment',
        reportId: 'report-3',
        status: 'completed',
      },
      {
        id: '4',
        type: 'client_added',
        title: 'New Client Added',
        description: 'Northwind Traders has been added to your client list.',
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
        clientName: 'Northwind Traders',
        status: 'completed',
      },
      {
        id: '5',
        type: 'report_generated',
        title: 'Detailed Report Generated',
        description: 'Comprehensive detailed report completed for Wide World Importers.',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        clientName: 'Wide World Importers',
        reportType: 'Detailed Report',
        reportId: 'report-5',
        status: 'completed',
      },
      {
        id: '6',
        type: 'report_failed',
        title: 'Report Generation Failed',
        description: 'Failed to process CSV file. Please check the file format.',
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
        clientName: 'Tailspin Toys',
        reportType: 'Cost Optimization',
        reportId: 'report-6',
        status: 'failed',
      },
      {
        id: '7',
        type: 'report_generated',
        title: 'Operational Excellence Report Ready',
        description: 'Successfully generated operational excellence analysis.',
        timestamp: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000), // 4 days ago
        clientName: 'Contoso Ltd.',
        reportType: 'Operational Excellence',
        reportId: 'report-7',
        status: 'completed',
      },
      {
        id: '8',
        type: 'client_added',
        title: 'New Client Onboarded',
        description: 'Alpine Ski House has been successfully onboarded.',
        timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
        clientName: 'Alpine Ski House',
        status: 'completed',
      },
      {
        id: '9',
        type: 'report_generated',
        title: 'Security Assessment Complete',
        description: 'Security recommendations identified and documented.',
        timestamp: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000), // 6 days ago
        clientName: 'Fourth Coffee',
        reportType: 'Security Assessment',
        reportId: 'report-9',
        status: 'completed',
      },
      {
        id: '10',
        type: 'report_generated',
        title: 'Cost Savings Analysis Ready',
        description: 'Identified $12,450 in potential monthly savings.',
        timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
        clientName: 'Wingtip Toys',
        reportType: 'Cost Optimization',
        reportId: 'report-10',
        status: 'completed',
      },
    ];

    return activities.slice(0, limit);
  }
}

// Export singleton instance
const analyticsService = new AnalyticsService();
export default analyticsService;
