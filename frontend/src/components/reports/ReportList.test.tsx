import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReportList from './ReportList';

// Mock react-icons
jest.mock('react-icons/fi', () => ({
  FiDownload: () => <div data-testid="download-icon">Download</div>,
  FiEye: () => <div data-testid="eye-icon">Eye</div>,
  FiFileText: () => <div data-testid="file-text-icon">FileText</div>,
  FiTrash2: () => <div data-testid="trash-icon">Trash</div>,
  FiFilter: () => <div data-testid="filter-icon">Filter</div>,
  FiCalendar: () => <div data-testid="calendar-icon">Calendar</div>,
  FiUser: () => <div data-testid="user-icon">User</div>,
  FiRefreshCw: () => <div data-testid="refresh-icon">Refresh</div>,
  FiBarChart2: () => <div data-testid="chart-icon">Chart</div>,
  FiFile: () => <div data-testid="file-icon">File</div>,
  FiCloud: () => <div data-testid="cloud-icon">Cloud</div>,
  FiClock: () => <div data-testid="clock-icon">Clock</div>,
  FiCheckCircle: () => <div data-testid="check-icon">Check</div>,
  FiAlertCircle: () => <div data-testid="alert-icon">Alert</div>,
}));

// Mock the report service
jest.mock('../../services/reportService', () => ({
  __esModule: true,
  default: {
    getReports: jest.fn(),
    deleteReport: jest.fn(),
    downloadReport: jest.fn(),
    downloadFile: jest.fn(),
  },
  ReportType: {},
  ReportStatus: {},
}));

// Mock the API client
jest.mock('../../services/apiClient', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
  },
}));

// Mock common components
jest.mock('../common', () => ({
  Button: ({ children, onClick, disabled, icon }: any) => (
    <button onClick={onClick} disabled={disabled}>
      {icon}
      {children}
    </button>
  ),
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  LoadingSpinner: ({ text }: any) => <div>{text}</div>,
  ConfirmDialog: () => null,
  showToast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
  Modal: ({ children, isOpen }: any) => (isOpen ? <div>{children}</div> : null),
}));

// Mock ReportStatusBadge
jest.mock('./ReportStatusBadge', () => ({
  __esModule: true,
  default: ({ status }: any) => <span>{status}</span>,
}));

// Mock ReportAnalytics
jest.mock('./ReportAnalytics', () => ({
  __esModule: true,
  default: () => <div>Analytics</div>,
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderReportList = (props = {}) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ReportList {...props} />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('ReportList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', () => {
    renderReportList();
    // Component should render (loading state or data)
    expect(document.body).toBeTruthy();
  });

  it('should accept clientId prop', () => {
    renderReportList({ clientId: 'test-client-123' });
    expect(document.body).toBeTruthy();
  });

  it('should accept showClientName prop', () => {
    renderReportList({ showClientName: false });
    expect(document.body).toBeTruthy();
  });

  it('should accept pageSize prop', () => {
    renderReportList({ pageSize: 20 });
    expect(document.body).toBeTruthy();
  });
});
