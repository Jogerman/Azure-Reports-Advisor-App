/**
 * TypeScript types for Cost Monitoring module
 */

// ============================================================================
// Azure Subscription Types
// ============================================================================

export interface AzureSubscription {
  id: string;
  subscription_id: string;
  subscription_name: string;
  tenant_id: string;
  client: number;
  client_name: string;
  is_active: boolean;
  last_sync: string | null;
  sync_frequency: 'hourly' | 'daily' | 'weekly';
  cost_currency: string;
  tags: Record<string, any>;
  created_by: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateAzureSubscription {
  subscription_id: string;
  subscription_name: string;
  tenant_id: string;
  client_id: string;  // Azure credential
  client_secret: string;  // Azure credential
  client: number;  // Client FK
  is_active?: boolean;
  sync_frequency?: 'hourly' | 'daily' | 'weekly';
  cost_currency?: string;
  tags?: Record<string, any>;
}

export interface UpdateAzureSubscription {
  subscription_name?: string;
  tenant_id?: string;
  client_id?: string;
  client_secret?: string;
  is_active?: boolean;
  sync_frequency?: 'hourly' | 'daily' | 'weekly';
  cost_currency?: string;
  tags?: Record<string, any>;
}

// ============================================================================
// Cost Data Types
// ============================================================================

export interface CostData {
  id: string;
  subscription: string;
  subscription_name: string;
  date: string;
  cost: string;
  currency: string;
  service_name: string;
  service_tier: string;
  resource_group: string;
  resource_location: string;
  meter_category: string;
  meter_subcategory: string;
  meter_name: string;
  unit_of_measure: string;
  quantity: string | null;
  tags: Record<string, any>;
  is_anomaly: boolean;
  anomaly_score: number | null;
  created_at: string;
}

export interface CostSummary {
  period: string;
  total_cost: string;
  avg_daily_cost: string;
  cost_change_percentage: string;
  top_services: Array<{
    service_name: string;
    total_cost: string;
  }>;
}

// ============================================================================
// Budget Types
// ============================================================================

export interface Budget {
  id: string;
  subscription: string;
  subscription_name: string;
  name: string;
  description: string;
  amount: string;
  currency: string;
  period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date: string;
  end_date: string;
  current_spend: string;
  percentage_used: string;
  amount_remaining: string;
  status: 'ok' | 'warning' | 'exceeded';
  filters: {
    services?: string[];
    resource_groups?: string[];
    tags?: Record<string, any>;
  };
  is_active: boolean;
  thresholds: BudgetThreshold[];
  created_by: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
  last_updated: string;
}

export interface BudgetThreshold {
  id: string;
  budget: string;
  threshold_percentage: number;
  notification_channels: string[];
  is_active: boolean;
  last_triggered: string | null;
  created_at: string;
}

export interface CreateBudget {
  subscription: string;
  name: string;
  description?: string;
  amount: string;
  currency?: string;
  period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date: string;
  end_date: string;
  filters?: {
    services?: string[];
    resource_groups?: string[];
    tags?: Record<string, any>;
  };
  is_active?: boolean;
}

export interface BudgetSummary {
  total_budgets: number;
  active_budgets: number;
  budgets_exceeded: number;
  budgets_warning: number;
  total_allocated: string;
  total_spent: string;
}

export interface SpendingTrend {
  date: string;
  daily_cost: string;
  cumulative_cost: string;
  percentage_of_budget: string;
}

export interface BudgetForecast {
  forecast_total: string;
  forecast_exceeded: boolean;
  forecast_percentage: string;
  forecast_overage: string;
  daily_average: string;
  days_elapsed: number;
  days_remaining: number;
  total_days: number;
  current_spend: string;
  budget_amount: string;
}

// ============================================================================
// Alert Types
// ============================================================================

export type AlertType = 'threshold' | 'anomaly' | 'budget' | 'forecast';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';

export interface Alert {
  id: string;
  subscription: string;
  subscription_name: string;
  rule: string | null;
  rule_name: string | null;
  title: string;
  message: string;
  severity: AlertSeverity;
  alert_type: AlertType;
  triggered_value: string | null;
  threshold_value: string | null;
  context_data: Record<string, any>;
  status: AlertStatus;
  acknowledged_by: number | null;
  acknowledged_by_name: string | null;
  acknowledged_at: string | null;
  resolved_by: number | null;
  resolved_by_name: string | null;
  resolved_at: string | null;
  notification_sent: boolean;
  notification_channels: string[];
  created_at: string;
  updated_at: string;
}

export interface AlertRule {
  id: string;
  subscription: string;
  subscription_name: string;
  name: string;
  description: string;
  rule_type: AlertType | 'custom';
  severity: AlertSeverity;
  conditions: Record<string, any>;
  notification_channels: string[];
  cooldown_minutes: number;
  is_active: boolean;
  last_triggered: string | null;
  trigger_count: number;
  created_by: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateAlertRule {
  subscription: string;
  name: string;
  description?: string;
  rule_type: AlertType | 'custom';
  severity: AlertSeverity;
  conditions: Record<string, any>;
  notification_channels: string[];
  cooldown_minutes?: number;
  is_active?: boolean;
}

export interface AlertSummary {
  total_alerts: number;
  active_alerts: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  by_type: {
    threshold: number;
    anomaly: number;
    budget: number;
    forecast: number;
  };
}

// ============================================================================
// Anomaly Types
// ============================================================================

export type DetectionMethod = 'zscore' | 'iqr' | 'moving_avg' | 'isolation_forest';

export interface CostAnomaly {
  id: string;
  subscription: string;
  subscription_name: string;
  date: string;
  expected_cost: string;
  actual_cost: string;
  deviation_percentage: string;
  anomaly_score: number;
  confidence: number;
  detection_method: DetectionMethod;
  service_name: string;
  resource_group: string;
  context_data: Record<string, any>;
  is_acknowledged: boolean;
  acknowledged_by: number | null;
  acknowledged_by_name: string | null;
  acknowledged_at: string | null;
  notes: string;
  created_at: string;
}

export interface AnomalySummary {
  total_anomalies: number;
  unacknowledged: number;
  by_method: {
    zscore: number;
    iqr: number;
    moving_avg: number;
    isolation_forest: number;
  };
  avg_confidence: number;
}

export interface DetectAnomaliesRequest {
  subscription_id: string;
  days?: number;
  methods?: DetectionMethod[];
}

// ============================================================================
// Forecast Types
// ============================================================================

export type ModelType = 'linear' | 'arima' | 'prophet' | 'lstm';

export interface CostForecast {
  id: string;
  subscription: string;
  subscription_name: string;
  forecast_date: string;
  predicted_cost: string;
  lower_bound: string | null;
  upper_bound: string | null;
  confidence_interval: number;
  model_type: ModelType;
  model_accuracy: number | null;
  accuracy_percentage: number | null;
  service_name: string;
  context_data: Record<string, any>;
  actual_cost: string | null;
  prediction_error: string | null;
  created_at: string;
}

export interface GenerateForecastRequest {
  subscription_id: string;
  days?: number;
  model_type?: ModelType;
}

// ============================================================================
// Dashboard Types
// ============================================================================

export interface CostMonitoringDashboard {
  cost_summary: CostSummary;
  budget_summary: BudgetSummary;
  alert_summary: AlertSummary;
  anomaly_summary: AnomalySummary;
  recent_alerts: Alert[];
  recent_anomalies: CostAnomaly[];
  cost_trend: Array<{
    date: string;
    total_cost: string;
    service_breakdown: Record<string, number>;
  }>;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TaskResponse {
  message: string;
  task_id: string;
  subscription?: string;
}

export interface ApiError {
  detail?: string;
  error?: string;
  message?: string;
  [key: string]: any;
}
