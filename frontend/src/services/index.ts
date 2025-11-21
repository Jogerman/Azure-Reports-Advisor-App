// Service exports for easy imports
export { default as apiClient } from './apiClient';
export { default as authService } from './authService';
export { default as clientService } from './clientService';
export { default as reportService } from './reportService';
export { default as analyticsService } from './analyticsService';

// Re-export types
export type { User, LoginRequest, LoginResponse } from './authService';
export type {
  Client,
  CreateClientData,
  UpdateClientData,
  ClientListParams,
  ClientListResponse,
} from './clientService';
export type {
  Report,
  ReportType,
  ReportStatus,
  UploadCSVData,
  GenerateReportData,
  ReportListParams,
  ReportListResponse,
  ReportStatusResponse,
  ManualRecommendation,
  RecommendationCategory,
  BusinessImpact,
} from './reportService';
// Analytics types are exported from types/analytics.ts