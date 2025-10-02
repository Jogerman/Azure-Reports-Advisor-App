// Service exports for easy imports
export { default as apiClient } from './apiClient';
export { default as authService } from './authService';
export { default as clientService } from './clientService';
export { default as reportService } from './reportService';

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
} from './reportService';