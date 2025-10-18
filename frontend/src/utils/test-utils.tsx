import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';

// Re-export everything from testing library
export * from '@testing-library/react';

// Simple render without complex providers for component tests
export { render };

// Mock user data for testing
export const mockUser = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@example.com',
  name: 'Test User',
  role: 'analyst' as const,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

// Mock client data for testing
export const mockClient = {
  id: '123e4567-e89b-12d3-a456-426614174001',
  company_name: 'Test Company',
  industry: 'Technology',
  contact_email: 'contact@testcompany.com',
  contact_phone: '+1-555-0100',
  azure_subscription_ids: ['sub-1', 'sub-2'],
  status: 'active' as const,
  notes: 'Test client notes',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

// Mock report data for testing
export const mockReport = {
  id: '123e4567-e89b-12d3-a456-426614174002',
  client_id: mockClient.id,
  client: mockClient,
  report_type: 'detailed' as const,
  status: 'completed' as const,
  csv_file: '/media/csv_uploads/test.csv',
  html_file: '/media/reports/html/test.html',
  pdf_file: '/media/reports/pdf/test.pdf',
  created_by: mockUser.id,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  analysis_data: {
    total_recommendations: 50,
    category_distribution: {
      cost: 20,
      security: 15,
      reliability: 10,
      operational_excellence: 5,
    },
    estimated_monthly_savings: 5000,
  },
};

// Mock analytics data for testing
export const mockAnalytics = {
  metrics: {
    total_recommendations: { value: 500, change: 10 },
    total_savings: { value: 50000, change: 15 },
    active_clients: { value: 25, change: 5 },
    reports_this_month: { value: 12, change: 20 },
  },
  category_distribution: [
    { name: 'Cost', value: 200, color: '#10B981' },
    { name: 'Security', value: 150, color: '#EF4444' },
    { name: 'Reliability', value: 100, color: '#3B82F6' },
    { name: 'Operational Excellence', value: 50, color: '#8B5CF6' },
  ],
  trend_data: {
    labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
    data: [10, 15, 20, 25, 30, 35, 40],
  },
  recent_activity: [
    {
      id: '1',
      client_name: 'Test Company 1',
      report_type: 'detailed',
      status: 'completed',
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: '2',
      client_name: 'Test Company 2',
      report_type: 'executive',
      status: 'processing',
      created_at: '2025-01-01T01:00:00Z',
    },
  ],
};

// Helper to wait for async operations
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

// Helper to create mock file for file upload testing
export const createMockFile = (
  name = 'test.csv',
  size = 1024,
  type = 'text/csv'
): File => {
  const content = 'test,data\n1,2\n3,4';
  const blob = new Blob([content], { type });
  return new File([blob], name, { type });
};

// Helper to mock API responses
export const mockApiResponse = <T,>(data: T, delay = 0): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), delay));

// Helper to mock API errors
export const mockApiError = (
  message = 'API Error',
  status = 500,
  delay = 0
): Promise<never> =>
  new Promise((_, reject) =>
    setTimeout(
      () =>
        reject({
          response: {
            status,
            data: { message },
          },
        }),
      delay
    )
  );

// Helper to get element by test id
export const getByTestId = (testId: string) =>
  document.querySelector(`[data-testid="${testId}"]`);
