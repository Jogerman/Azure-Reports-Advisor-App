/**
 * API Service for Azure Advisor Reports (v1.7.0)
 *
 * Centralized API client for all backend communication.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API Base URL from environment or default to localhost
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Type Definitions
// ============================================================================

export interface ManualRecommendation {
  category: 'cost' | 'security' | 'reliability' | 'operational_excellence' | 'performance';
  business_impact: 'high' | 'medium' | 'low';
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

export interface AddManualRecommendationsResponse {
  status: 'success' | 'error';
  message: string;
  data?: {
    recommendations_created: number;
    total_recommendations: number;
    total_potential_savings: number;
  };
  errors?: any;
}

export interface Report {
  id: string;
  title: string;
  status: string;
  created_at: string;
  // Add other report fields as needed
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Add manual recommendations to a report (v1.7.0)
 */
export const addManualRecommendations = async (
  reportId: string,
  recommendations: ManualRecommendation[]
): Promise<AddManualRecommendationsResponse> => {
  try {
    const response = await apiClient.post<AddManualRecommendationsResponse>(
      `/reports/${reportId}/add-manual-recommendations/`,
      { recommendations }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      return error.response.data;
    }
    throw error;
  }
};

/**
 * Get report details
 */
export const getReport = async (reportId: string): Promise<Report> => {
  const response = await apiClient.get<Report>(`/reports/${reportId}/`);
  return response.data;
};

/**
 * Get all reports
 */
export const getReports = async (params?: {
  client?: string;
  status?: string;
  page?: number;
}): Promise<{ results: Report[]; count: number }> => {
  const response = await apiClient.get('/reports/', { params });
  return response.data;
};

/**
 * Upload CSV and create report
 */
export const uploadCSV = async (
  file: File,
  clientId: string,
  reportType: string = 'detailed',
  title?: string
): Promise<any> => {
  const formData = new FormData();
  formData.append('csv_file', file);
  formData.append('client_id', clientId);
  formData.append('report_type', reportType);
  if (title) {
    formData.append('title', title);
  }

  const response = await apiClient.post('/reports/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Create report from Azure API
 */
export const createReportFromAzureAPI = async (data: {
  client_id: string;
  azure_subscription: string;
  report_type?: string;
  title?: string;
  filters?: {
    category?: string;
    impact?: string;
    resource_group?: string;
  };
}): Promise<any> => {
  const response = await apiClient.post('/reports/', {
    ...data,
    data_source: 'azure_api',
  });
  return response.data;
};

/**
 * Generate report (HTML/PDF)
 */
export const generateReport = async (
  reportId: string,
  format: 'html' | 'pdf' = 'html'
): Promise<any> => {
  const response = await apiClient.post(`/reports/${reportId}/generate/`, {
    format,
  });
  return response.data;
};

/**
 * Download report file
 */
export const downloadReport = async (
  reportId: string,
  format: 'html' | 'pdf' = 'pdf'
): Promise<Blob> => {
  const response = await apiClient.get(`/reports/${reportId}/download/`, {
    params: { format },
    responseType: 'blob',
  });
  return response.data;
};

export default apiClient;
