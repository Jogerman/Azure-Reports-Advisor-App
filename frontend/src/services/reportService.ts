import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export type ReportType = 'detailed' | 'executive' | 'cost' | 'security' | 'operations';
export type ReportStatus = 'pending' | 'uploaded' | 'processing' | 'generating' | 'completed' | 'failed' | 'cancelled';

export interface Report {
  id: string;
  client_id: string;
  client_name?: string;
  report_type: ReportType;
  status: ReportStatus;
  csv_file?: string;
  html_file?: string;
  pdf_file?: string;
  analysis_data?: any;
  error_message?: string;
  created_by?: string;
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
  client_id?: string;
  report_type?: ReportType;
  status?: ReportStatus;
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
}

const reportService = new ReportService();
export default reportService;