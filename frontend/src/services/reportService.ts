import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  HistoryStatistics,
  TrendsResponse,
  TrendsParams,
  UsersResponse,
  HistoryFilterParams,
} from '../types/history';

export type ReportType = 'detailed' | 'executive' | 'cost' | 'security' | 'operations';
export type ReportStatus = 'pending' | 'uploaded' | 'processing' | 'generating' | 'completed' | 'failed' | 'cancelled';

export type RecommendationCategory = 'cost' | 'security' | 'reliability' | 'operational_excellence' | 'performance';
export type BusinessImpact = 'high' | 'medium' | 'low';

export interface ManualRecommendation {
  category: RecommendationCategory;
  business_impact: BusinessImpact;
  recommendation: string;
  subscription_id?: string;
  subscription_name?: string;
  resource_group?: string;
  resource_name?: string;
  resource_type?: string;
  potential_savings?: number;
  currency?: string;
  potential_benefits?: string;
  retirement_date?: string;
  retiring_feature?: string;
  advisor_score_impact?: number;
}

export interface ManualRecommendationsRequest {
  recommendations: ManualRecommendation[];
}

export interface ManualRecommendationsResponse {
  status: 'success' | 'error';
  message: string;
  data?: {
    recommendations_created: number;
    total_recommendations: number;
    total_potential_savings?: number;
  };
  errors?: any;
}

export interface Report {
  id: string;
  client_id: string;
  client_name?: string;
  report_type: ReportType;
  status: ReportStatus;
  data_source?: 'csv' | 'azure_api';
  azure_subscription?: {
    id: string;
    name: string;
    subscription_id: string;
  };
  csv_file?: string;
  html_file?: string;
  pdf_file?: string;
  analysis_data?: any;
  error_message?: string;
  created_by?: string;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
  processing_started_at?: string;
  processing_completed_at?: string;
}

export interface UploadCSVData {
  client_id: string;
  csv_file: File;
  report_type?: ReportType;
}

export interface GenerateReportData {
  report_id: string;
  report_type: ReportType;
}

export interface ReportListParams {
  page?: number;
  page_size?: number;
  client?: string;  // Changed from client_id to match backend filter field
  report_type?: ReportType | ReportType[];
  status?: ReportStatus | ReportStatus[];
  created_by?: string | string[];
  date_from?: string;
  date_to?: string;
  ordering?: string;
  search?: string;
}

export interface ReportListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Report[];
}

export interface ReportStatusResponse {
  status: ReportStatus;
  progress?: number;
  message?: string;
  error_message?: string;
}

/**
 * Report management service
 */
class ReportService {
  /**
   * Upload CSV file for report generation
   */
  async uploadCSV(data: UploadCSVData): Promise<Report> {
    const formData = new FormData();
    formData.append('client_id', data.client_id);
    formData.append('csv_file', data.csv_file);

    if (data.report_type) {
      formData.append('report_type', data.report_type);
    }

    const response = await apiClient.post<Report>(
      API_ENDPOINTS.REPORTS.UPLOAD,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Generate HTML/PDF files for a completed report
   */
  async generateReport(reportId: string, format: 'html' | 'pdf' | 'both' = 'both'): Promise<any> {
    const response = await apiClient.post(
      API_ENDPOINTS.REPORTS.GENERATE(reportId),
      { format }
    );
    return response.data;
  }

  /**
   * Get list of reports with optional filters
   */
  async getReports(params?: ReportListParams): Promise<ReportListResponse> {
    const response = await apiClient.get<ReportListResponse>(
      API_ENDPOINTS.REPORTS.LIST,
      { params }
    );
    return response.data;
  }

  /**
   * Get single report by ID
   */
  async getReport(id: string): Promise<Report> {
    const response = await apiClient.get<Report>(
      API_ENDPOINTS.REPORTS.DETAIL(id)
    );
    return response.data;
  }

  /**
   * Get report generation status
   */
  async getReportStatus(id: string): Promise<ReportStatusResponse> {
    const response = await apiClient.get<ReportStatusResponse>(
      API_ENDPOINTS.REPORTS.STATUS(id)
    );
    return response.data;
  }

  /**
   * Download report file
   */
  async downloadReport(id: string, format: 'html' | 'pdf' = 'pdf'): Promise<Blob> {
    const response = await apiClient.get(
      API_ENDPOINTS.REPORTS.DOWNLOAD(id, format),
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  /**
   * Delete report
   */
  async deleteReport(id: string): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.REPORTS.DETAIL(id));
  }

  /**
   * Get report statistics/analytics
   */
  async getReportStatistics(id: string): Promise<any> {
    const response = await apiClient.get(
      `/reports/${id}/statistics/`
    );
    return response.data.data;
  }

  /**
   * Get report recommendations
   */
  async getReportRecommendations(id: string, params?: {
    category?: string;
    business_impact?: string;
    min_savings?: number;
  }): Promise<any[]> {
    const response = await apiClient.get(
      `/reports/${id}/recommendations/`,
      { params }
    );
    return response.data.data;
  }

  /**
   * Helper method to trigger file download or open in browser
   * HTML files open in new tab for inline viewing
   * PDF files download to disk
   */
  downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);

    // Check if this is an HTML file
    const isHtml = filename.toLowerCase().endsWith('.html');

    if (isHtml) {
      // HTML: Open in new tab for inline viewing
      window.open(url, '_blank');
      // Clean up after a delay to allow the new tab to load
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } else {
      // PDF: Download to disk
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }
  }

  /**
   * Get history statistics with filters
   */
  async getHistoryStatistics(filters?: HistoryFilterParams): Promise<HistoryStatistics> {
    const response = await apiClient.get<HistoryStatistics>(
      '/reports/history/statistics/',
      { params: filters }
    );
    return response.data;
  }

  /**
   * Get history trends data
   */
  async getHistoryTrends(params?: TrendsParams): Promise<TrendsResponse> {
    const response = await apiClient.get<TrendsResponse>(
      '/reports/history/trends/',
      { params }
    );
    return response.data;
  }

  /**
   * Get list of users who have created reports
   */
  async getReportUsers(): Promise<UsersResponse> {
    const response = await apiClient.get<UsersResponse>('/reports/users/');
    return response.data;
  }

  /**
   * Export reports to CSV with filters
   */
  async exportToCSV(filters?: HistoryFilterParams): Promise<Blob> {
    const response = await apiClient.post(
      '/reports/export-csv/',
      filters,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  /**
   * Helper method to download CSV file
   */
  downloadCSV(blob: Blob, filename: string = 'reports-export.csv'): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Add manual recommendations to a report (v1.7.0)
   */
  async addManualRecommendations(
    reportId: string,
    recommendations: ManualRecommendation[]
  ): Promise<ManualRecommendationsResponse> {
    const response = await apiClient.post<ManualRecommendationsResponse>(
      `/reports/${reportId}/add-manual-recommendations/`,
      { recommendations }
    );
    return response.data;
  }
}

const reportService = new ReportService();
export default reportService;