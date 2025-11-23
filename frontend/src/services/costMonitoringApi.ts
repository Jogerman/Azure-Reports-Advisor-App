/**
 * Cost Monitoring API Service
 *
 * Provides methods to interact with the Cost Monitoring backend API.
 */

import apiClient from './apiClient';
import {
  AzureSubscription,
  CreateAzureSubscription,
  UpdateAzureSubscription,
  CostData,
  CostSummary,
  Budget,
  CreateBudget,
  BudgetSummary,
  SpendingTrend,
  BudgetForecast,
  AlertRule,
  CreateAlertRule,
  Alert,
  AlertSummary,
  CostAnomaly,
  AnomalySummary,
  DetectAnomaliesRequest,
  CostForecast,
  GenerateForecastRequest,
  PaginatedResponse,
  TaskResponse,
} from '../types/costMonitoring';

const BASE_PATH = '/cost-monitoring';

// ============================================================================
// Azure Subscriptions API
// ============================================================================

export const subscriptionsApi = {
  /**
   * Get all Azure subscriptions
   */
  list: async (params?: {
    client?: number;
    is_active?: boolean;
    search?: string;
    page?: number;
  }): Promise<PaginatedResponse<AzureSubscription>> => {
    const response = await apiClient.get(`${BASE_PATH}/subscriptions/`, { params });
    return response.data;
  },

  /**
   * Get a single subscription by ID
   */
  get: async (id: string): Promise<AzureSubscription> => {
    const response = await apiClient.get(`${BASE_PATH}/subscriptions/${id}/`);
    return response.data;
  },

  /**
   * Create a new Azure subscription
   */
  create: async (data: CreateAzureSubscription): Promise<AzureSubscription> => {
    const response = await apiClient.post(`${BASE_PATH}/subscriptions/`, data);
    return response.data;
  },

  /**
   * Update an existing subscription
   */
  update: async (id: string, data: UpdateAzureSubscription): Promise<AzureSubscription> => {
    const response = await apiClient.patch(`${BASE_PATH}/subscriptions/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a subscription
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/subscriptions/${id}/`);
  },

  /**
   * Trigger cost data sync for a subscription
   */
  syncCosts: async (id: string): Promise<TaskResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/subscriptions/${id}/sync_costs/`);
    return response.data;
  },

  /**
   * Validate Azure credentials
   */
  validateCredentials: async (id: string): Promise<{ valid: boolean; message: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/subscriptions/${id}/validate_credentials/`);
    return response.data;
  },

  /**
   * Get cost summary for a subscription
   */
  costSummary: async (id: string, days: number = 30): Promise<any> => {
    const response = await apiClient.get(`${BASE_PATH}/subscriptions/${id}/cost_summary/`, {
      params: { days }
    });
    return response.data;
  },
};

// ============================================================================
// Cost Data API
// ============================================================================

export const costsApi = {
  /**
   * Get cost data with filters
   */
  list: async (params?: {
    subscription?: string;
    date?: string;
    service_name?: string;
    resource_group?: string;
    is_anomaly?: boolean;
    page?: number;
  }): Promise<PaginatedResponse<CostData>> => {
    const response = await apiClient.get(`${BASE_PATH}/costs/`, { params });
    return response.data;
  },

  /**
   * Get cost data summary
   */
  summary: async (subscriptionId: string, days: number = 30): Promise<CostSummary> => {
    const response = await apiClient.get(`${BASE_PATH}/costs/summary/`, {
      params: { subscription_id: subscriptionId, days }
    });
    return response.data;
  },
};

// ============================================================================
// Budgets API
// ============================================================================

export const budgetsApi = {
  /**
   * Get all budgets
   */
  list: async (params?: {
    subscription?: string;
    status?: 'ok' | 'warning' | 'exceeded';
    is_active?: boolean;
    page?: number;
  }): Promise<PaginatedResponse<Budget>> => {
    const response = await apiClient.get(`${BASE_PATH}/budgets/`, { params });
    return response.data;
  },

  /**
   * Get a single budget by ID
   */
  get: async (id: string): Promise<Budget> => {
    const response = await apiClient.get(`${BASE_PATH}/budgets/${id}/`);
    return response.data;
  },

  /**
   * Create a new budget
   */
  create: async (data: CreateBudget): Promise<Budget> => {
    const response = await apiClient.post(`${BASE_PATH}/budgets/`, data);
    return response.data;
  },

  /**
   * Update an existing budget
   */
  update: async (id: string, data: Partial<CreateBudget>): Promise<Budget> => {
    const response = await apiClient.patch(`${BASE_PATH}/budgets/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a budget
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/budgets/${id}/`);
  },

  /**
   * Update current spend for a budget
   */
  updateSpend: async (id: string): Promise<any> => {
    const response = await apiClient.post(`${BASE_PATH}/budgets/${id}/update_spend/`);
    return response.data;
  },

  /**
   * Get spending trend for a budget
   */
  spendingTrend: async (id: string, days: number = 7): Promise<{ budget_name: string; trend: SpendingTrend[] }> => {
    const response = await apiClient.get(`${BASE_PATH}/budgets/${id}/spending_trend/`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Get forecast for end of budget period
   */
  forecast: async (id: string): Promise<{ budget_name: string; forecast: BudgetForecast }> => {
    const response = await apiClient.get(`${BASE_PATH}/budgets/${id}/forecast/`);
    return response.data;
  },

  /**
   * Get budget summary
   */
  summary: async (subscriptionId?: string): Promise<BudgetSummary> => {
    const response = await apiClient.get(`${BASE_PATH}/budgets/summary/`, {
      params: subscriptionId ? { subscription_id: subscriptionId } : undefined
    });
    return response.data;
  },
};

// ============================================================================
// Alert Rules API
// ============================================================================

export const alertRulesApi = {
  /**
   * Get all alert rules
   */
  list: async (params?: {
    subscription?: string;
    rule_type?: string;
    severity?: string;
    is_active?: boolean;
    page?: number;
  }): Promise<PaginatedResponse<AlertRule>> => {
    const response = await apiClient.get(`${BASE_PATH}/alert-rules/`, { params });
    return response.data;
  },

  /**
   * Get a single alert rule by ID
   */
  get: async (id: string): Promise<AlertRule> => {
    const response = await apiClient.get(`${BASE_PATH}/alert-rules/${id}/`);
    return response.data;
  },

  /**
   * Create a new alert rule
   */
  create: async (data: CreateAlertRule): Promise<AlertRule> => {
    const response = await apiClient.post(`${BASE_PATH}/alert-rules/`, data);
    return response.data;
  },

  /**
   * Update an existing alert rule
   */
  update: async (id: string, data: Partial<CreateAlertRule>): Promise<AlertRule> => {
    const response = await apiClient.patch(`${BASE_PATH}/alert-rules/${id}/`, data);
    return response.data;
  },

  /**
   * Delete an alert rule
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/alert-rules/${id}/`);
  },

  /**
   * Manually evaluate an alert rule
   */
  evaluate: async (id: string): Promise<TaskResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/alert-rules/${id}/evaluate/`);
    return response.data;
  },
};

// ============================================================================
// Alerts API
// ============================================================================

export const alertsApi = {
  /**
   * Get all alerts
   */
  list: async (params?: {
    subscription?: string;
    severity?: string;
    alert_type?: string;
    status?: string;
    page?: number;
  }): Promise<PaginatedResponse<Alert>> => {
    const response = await apiClient.get(`${BASE_PATH}/alerts/`, { params });
    return response.data;
  },

  /**
   * Get a single alert by ID
   */
  get: async (id: string): Promise<Alert> => {
    const response = await apiClient.get(`${BASE_PATH}/alerts/${id}/`);
    return response.data;
  },

  /**
   * Acknowledge an alert
   */
  acknowledge: async (id: string): Promise<{ message: string; alert: Alert }> => {
    const response = await apiClient.post(`${BASE_PATH}/alerts/${id}/acknowledge/`);
    return response.data;
  },

  /**
   * Resolve an alert
   */
  resolve: async (id: string): Promise<{ message: string; alert: Alert }> => {
    const response = await apiClient.post(`${BASE_PATH}/alerts/${id}/resolve/`);
    return response.data;
  },

  /**
   * Get alert summary
   */
  summary: async (subscriptionId?: string, days: number = 30): Promise<AlertSummary> => {
    const params: any = { days };
    if (subscriptionId) {
      params.subscription_id = subscriptionId;
    }
    const response = await apiClient.get(`${BASE_PATH}/alerts/summary/`, { params });
    return response.data;
  },
};

// ============================================================================
// Anomalies API
// ============================================================================

export const anomaliesApi = {
  /**
   * Get all cost anomalies
   */
  list: async (params?: {
    subscription?: string;
    date?: string;
    detection_method?: string;
    is_acknowledged?: boolean;
    service_name?: string;
    page?: number;
  }): Promise<PaginatedResponse<CostAnomaly>> => {
    const response = await apiClient.get(`${BASE_PATH}/anomalies/`, { params });
    return response.data;
  },

  /**
   * Get a single anomaly by ID
   */
  get: async (id: string): Promise<CostAnomaly> => {
    const response = await apiClient.get(`${BASE_PATH}/anomalies/${id}/`);
    return response.data;
  },

  /**
   * Acknowledge an anomaly
   */
  acknowledge: async (id: string, notes?: string): Promise<{ message: string; anomaly: CostAnomaly }> => {
    const response = await apiClient.post(`${BASE_PATH}/anomalies/${id}/acknowledge/`, { notes });
    return response.data;
  },

  /**
   * Trigger anomaly detection
   */
  detect: async (data: DetectAnomaliesRequest): Promise<TaskResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/anomalies/detect/`, data);
    return response.data;
  },

  /**
   * Get anomaly summary
   */
  summary: async (subscriptionId?: string, days: number = 30): Promise<AnomalySummary> => {
    const params: any = { days };
    if (subscriptionId) {
      params.subscription_id = subscriptionId;
    }
    const response = await apiClient.get(`${BASE_PATH}/anomalies/summary/`, { params });
    return response.data;
  },
};

// ============================================================================
// Forecasts API
// ============================================================================

export const forecastsApi = {
  /**
   * Get all cost forecasts
   */
  list: async (params?: {
    subscription?: string;
    forecast_date?: string;
    model_type?: string;
    page?: number;
  }): Promise<PaginatedResponse<CostForecast>> => {
    const response = await apiClient.get(`${BASE_PATH}/forecasts/`, { params });
    return response.data;
  },

  /**
   * Get a single forecast by ID
   */
  get: async (id: string): Promise<CostForecast> => {
    const response = await apiClient.get(`${BASE_PATH}/forecasts/${id}/`);
    return response.data;
  },

  /**
   * Generate new forecast
   */
  generate: async (data: GenerateForecastRequest): Promise<TaskResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/forecasts/generate/`, data);
    return response.data;
  },
};

// ============================================================================
// Combined Dashboard API
// ============================================================================

export const dashboardApi = {
  /**
   * Get comprehensive dashboard data
   */
  getData: async (subscriptionId?: string, days: number = 30) => {
    const promises = [
      subscriptionId ? costsApi.summary(subscriptionId, days) : Promise.resolve(null),
      budgetsApi.summary(subscriptionId),
      alertsApi.summary(subscriptionId, days),
      anomaliesApi.summary(subscriptionId, days),
      alertsApi.list({ subscription: subscriptionId, page: 1 }),
      anomaliesApi.list({ subscription: subscriptionId, is_acknowledged: false, page: 1 }),
    ];

    const results = await Promise.all(promises);
    const costSummary = results[0] as CostSummary | null;
    const budgetSummary = results[1] as BudgetSummary;
    const alertSummary = results[2] as AlertSummary;
    const anomalySummary = results[3] as AnomalySummary;
    const alertsResponse = results[4] as PaginatedResponse<Alert>;
    const anomaliesResponse = results[5] as PaginatedResponse<CostAnomaly>;

    return {
      cost_summary: costSummary,
      budget_summary: budgetSummary,
      alert_summary: alertSummary,
      anomaly_summary: anomalySummary,
      recent_alerts: alertsResponse.results.slice(0, 5),
      recent_anomalies: anomaliesResponse.results.slice(0, 5),
    };
  },
};

// Export all APIs as a single object
export default {
  subscriptions: subscriptionsApi,
  costs: costsApi,
  budgets: budgetsApi,
  alertRules: alertRulesApi,
  alerts: alertsApi,
  anomalies: anomaliesApi,
  forecasts: forecastsApi,
  dashboard: dashboardApi,
};
