/**
 * Azure Integration Types
 * Type definitions for Azure Subscription management and Azure API integration
 */

/**
 * Azure Subscription Entity
 */
export interface AzureSubscription {
  id: string;
  client: string;
  client_name?: string;
  name: string;
  subscription_id: string;
  tenant_id: string;
  azure_client_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: {
    id: string;
    username: string;
    full_name: string;
  };
  last_sync_at: string | null;
  sync_status: 'never_synced' | 'success' | 'failed';
  sync_error_message: string;
}

/**
 * Azure Subscription Creation Payload
 */
export interface AzureSubscriptionCreate {
  client: string;
  name: string;
  subscription_id: string;
  tenant_id: string;
  azure_client_id: string;
  client_secret: string;
  is_active?: boolean;
}

/**
 * Azure Subscription Update Payload
 */
export interface AzureSubscriptionUpdate {
  name?: string;
  is_active?: boolean;
  client_secret?: string;
  tenant_id?: string;
  azure_client_id?: string;
}

/**
 * Connection Test Result
 */
export interface ConnectionTestResult {
  success: boolean;
  subscription_id: string;
  subscription_name?: string;
  error_message?: string;
}

/**
 * Azure Statistics
 */
export interface AzureStatistics {
  total_recommendations: number;
  by_category: {
    Cost: number;
    HighAvailability: number;
    Performance: number;
    Security: number;
    OperationalExcellence: number;
  };
  by_impact: {
    High: number;
    Medium: number;
    Low: number;
  };
  total_potential_savings?: number;
  currency?: string;
}

/**
 * Data Source Type
 */
export type DataSource = 'csv' | 'azure_api';

/**
 * Report Filters for Azure API
 */
export interface AzureReportFilters {
  category?: 'Cost' | 'HighAvailability' | 'Performance' | 'Security' | 'OperationalExcellence';
  impact?: 'High' | 'Medium' | 'Low';
  resource_group?: string;
}

/**
 * Create Report from Azure API Payload
 */
export interface CreateReportFromAzureAPI {
  client_id: string;
  report_type: string;
  azure_subscription: string;
  filters?: AzureReportFilters;
}

/**
 * Paginated Response
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Azure Subscription List Parameters
 */
export interface AzureSubscriptionListParams {
  client?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

/**
 * Sync Task Response
 */
export interface SyncTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

/**
 * Category Colors for Charts
 */
export const AZURE_CATEGORY_COLORS = {
  Cost: '#10B981',
  HighAvailability: '#3B82F6',
  Performance: '#F59E0B',
  Security: '#EF4444',
  OperationalExcellence: '#8B5CF6',
} as const;

/**
 * Impact Colors for Charts
 */
export const AZURE_IMPACT_COLORS = {
  High: '#EF4444',
  Medium: '#F59E0B',
  Low: '#10B981',
} as const;

/**
 * Sync Status Display
 */
export const SYNC_STATUS_DISPLAY = {
  never_synced: {
    label: 'Never Synced',
    color: 'gray',
    icon: '○',
  },
  success: {
    label: 'Success',
    color: 'green',
    icon: '✓',
  },
  failed: {
    label: 'Failed',
    color: 'red',
    icon: '✗',
  },
} as const;
