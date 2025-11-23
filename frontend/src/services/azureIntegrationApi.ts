import apiClient from './apiClient';
import {
  AzureSubscription,
  AzureSubscriptionCreate,
  AzureSubscriptionUpdate,
  AzureSubscriptionListParams,
  PaginatedResponse,
  ConnectionTestResult,
  AzureStatistics,
  SyncTaskResponse,
  CreateReportFromAzureAPI,
} from '../types/azureIntegration';
import { Report, ReportListResponse } from './reportService';

/**
 * Azure Subscription API Service
 */
export const azureSubscriptionApi = {
  /**
   * Get list of Azure subscriptions
   */
  async list(params?: AzureSubscriptionListParams): Promise<PaginatedResponse<AzureSubscription>> {
    const response = await apiClient.get<PaginatedResponse<AzureSubscription>>(
      '/azure/subscriptions/',
      { params }
    );
    return response.data;
  },

  /**
   * Get single Azure subscription by ID
   */
  async get(id: string): Promise<AzureSubscription> {
    const response = await apiClient.get<AzureSubscription>(
      `/azure/subscriptions/${id}/`
    );
    return response.data;
  },

  /**
   * Create new Azure subscription
   */
  async create(data: AzureSubscriptionCreate): Promise<AzureSubscription> {
    const response = await apiClient.post<AzureSubscription>(
      '/azure/subscriptions/',
      data
    );
    return response.data;
  },

  /**
   * Update existing Azure subscription
   */
  async update(id: string, data: AzureSubscriptionUpdate): Promise<AzureSubscription> {
    const response = await apiClient.patch<AzureSubscription>(
      `/azure/subscriptions/${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Delete Azure subscription
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/azure/subscriptions/${id}/`);
  },

  /**
   * Test Azure subscription connection
   */
  async testConnection(id: string): Promise<ConnectionTestResult> {
    const response = await apiClient.post<ConnectionTestResult>(
      `/azure/subscriptions/${id}/test-connection/`
    );
    return response.data;
  },

  /**
   * Get statistics for Azure subscription
   */
  async getStatistics(id: string): Promise<AzureStatistics> {
    const response = await apiClient.get<AzureStatistics>(
      `/azure/subscriptions/${id}/statistics/`
    );
    return response.data;
  },

  /**
   * Trigger manual sync for Azure subscription
   */
  async syncNow(id: string): Promise<SyncTaskResponse> {
    const response = await apiClient.post<SyncTaskResponse>(
      `/azure/subscriptions/${id}/sync-now/`
    );
    return response.data;
  },

  /**
   * Get reports associated with an Azure subscription
   */
  async listReports(id: string, params?: { page?: number; page_size?: number }): Promise<ReportListResponse> {
    const response = await apiClient.get<ReportListResponse>(
      `/azure/subscriptions/${id}/reports/`,
      { params }
    );
    return response.data;
  },
};

/**
 * Create report from Azure API
 */
export const createReportFromAzureAPI = async (data: CreateReportFromAzureAPI): Promise<Report> => {
  const response = await apiClient.post<Report>(
    '/reports/create-from-azure/',
    data
  );
  return response.data;
};

/**
 * Azure Integration Service (combined exports)
 */
const azureIntegrationService = {
  subscriptions: azureSubscriptionApi,
  createReportFromAzure: createReportFromAzureAPI,
};

export default azureIntegrationService;
