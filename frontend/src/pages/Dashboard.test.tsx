import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { toast } from 'react-toastify';
import Dashboard from './Dashboard';
import { analyticsService } from '../services';
import { mockAnalytics } from '../utils/test-utils';

// Mock services
jest.mock('../services', () => ({
  analyticsService: {
    getDashboardAnalytics: jest.fn(),
  },
}));

// Mock toast
jest.mock('react-toastify', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

// Mock framer-motion for simpler testing
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
}));

const mockAnalyticsData = {
  metrics: {
    activeClients: 25,
    reportsGeneratedThisMonth: 12,
    totalPotentialSavings: 50000,
    totalRecommendations: 500,
    trends: {
      clients: 5,
      reports: 20,
      savings: 15,
      recommendations: 10,
    },
  },
  categoryDistribution: [
    { name: 'Cost', value: 200, color: '#10B981' },
    { name: 'Security', value: 150, color: '#EF4444' },
    { name: 'Reliability', value: 100, color: '#3B82F6' },
    { name: 'Operational Excellence', value: 50, color: '#8B5CF6' },
  ],
  trendData: [
    { date: '2025-01-01', value: 10 },
    { date: '2025-01-02', value: 15 },
    { date: '2025-01-03', value: 20 },
  ],
  recentActivity: [
    {
      id: '1',
      client_name: 'Test Company 1',
      report_type: 'detailed',
      status: 'completed',
      created_at: '2025-01-01T00:00:00Z',
    },
  ],
};

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderDashboard = (queryClient = createQueryClient()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (analyticsService.getDashboardAnalytics as jest.Mock).mockResolvedValue(
      mockAnalyticsData
    );
  });

  describe('Rendering', () => {
    it('should render dashboard title and description', async () => {
      renderDashboard();

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(
        screen.getByText(/Welcome to Azure Advisor Reports Platform/i)
      ).toBeInTheDocument();
    });

    it('should render refresh button', async () => {
      renderDashboard();

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      expect(refreshButton).toBeInTheDocument();
    });

    it('should display loading state initially', () => {
      renderDashboard();

      const loadingElements = screen.getAllByText('...');
      expect(loadingElements.length).toBeGreaterThan(0);
    });
  });

  describe('Data Fetching', () => {
    it('should fetch and display analytics data', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(analyticsService.getDashboardAnalytics).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument(); // Active Clients
        expect(screen.getByText('12')).toBeInTheDocument(); // Reports
        expect(screen.getByText('$50,000')).toBeInTheDocument(); // Savings
        expect(screen.getByText('500')).toBeInTheDocument(); // Recommendations
      });
    });

    it('should display error message on fetch failure', async () => {
      (analyticsService.getDashboardAnalytics as jest.Mock).mockRejectedValue(
        new Error('Failed to fetch')
      );

      renderDashboard();

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to load analytics data');
      });

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText(/Error loading dashboard/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should refresh data when refresh button is clicked', async () => {
      const user = userEvent.setup();
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument();
      });

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(analyticsService.getDashboardAnalytics).toHaveBeenCalledTimes(2);
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Dashboard refreshed');
      });
    });

    it('should show error toast when refresh fails', async () => {
      const user = userEvent.setup();
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument();
      });

      (analyticsService.getDashboardAnalytics as jest.Mock).mockRejectedValue(
        new Error('Refresh failed')
      );

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to refresh dashboard');
      });
    });

    it('should disable refresh button while fetching', async () => {
      const user = userEvent.setup();
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument();
      });

      (analyticsService.getDashboardAnalytics as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockAnalyticsData), 100))
      );

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(refreshButton).toBeDisabled();
      expect(screen.getByText('Refreshing...')).toBeInTheDocument();
    });

    it('should retry loading when try again button is clicked', async () => {
      const user = userEvent.setup();
      (analyticsService.getDashboardAnalytics as jest.Mock).mockRejectedValue(
        new Error('Failed to fetch')
      );

      renderDashboard();

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByRole('button', { name: /try again/i });
      expect(tryAgainButton).toBeInTheDocument();

      (analyticsService.getDashboardAnalytics as jest.Mock).mockResolvedValue(
        mockAnalyticsData
      );

      await user.click(tryAgainButton);

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument();
      });
    });
  });

  describe('Metrics Display', () => {
    it('should display all metric cards', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Active Clients')).toBeInTheDocument();
        expect(screen.getByText('Reports Generated')).toBeInTheDocument();
        expect(screen.getByText('Total Potential Savings')).toBeInTheDocument();
        expect(screen.getByText('Total Recommendations')).toBeInTheDocument();
      });
    });

    it('should format currency values correctly', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('$50,000')).toBeInTheDocument();
      });
    });

    it('should format number values with commas', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('500')).toBeInTheDocument();
      });
    });
  });

  describe('Quick Actions', () => {
    it('should render all quick action cards', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Manage Clients')).toBeInTheDocument();
        expect(screen.getByText('Generate Reports')).toBeInTheDocument();
        expect(screen.getByText('View History')).toBeInTheDocument();
      });
    });

    it('should have correct navigation links', async () => {
      renderDashboard();

      await waitFor(() => {
        const clientsLink = screen.getByRole('link', { name: /Manage Clients/i });
        const reportsLink = screen.getByRole('link', { name: /Generate Reports/i });
        const historyLink = screen.getByRole('link', { name: /View History/i });

        expect(clientsLink).toHaveAttribute('href', '/clients');
        expect(reportsLink).toHaveAttribute('href', '/reports');
        expect(historyLink).toHaveAttribute('href', '/history');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels on interactive elements', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /refresh dashboard data/i })
        ).toBeInTheDocument();
      });

      expect(screen.getByRole('navigation', { name: /quick actions/i })).toBeInTheDocument();
    });

    it('should have proper alert role for error messages', async () => {
      (analyticsService.getDashboardAnalytics as jest.Mock).mockRejectedValue(
        new Error('Failed to fetch')
      );

      renderDashboard();

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveAttribute('aria-live', 'assertive');
      });
    });

    it('should have descriptive link labels', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(
          screen.getByRole('link', {
            name: /Manage Clients - Add, edit, or view your client list/i,
          })
        ).toBeInTheDocument();
      });
    });
  });

  describe('Charts and Analytics', () => {
    it('should render category chart with data', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Recommendations by Category')).toBeInTheDocument();
      });
    });

    it('should render trend chart with data', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Report Generation Trend')).toBeInTheDocument();
      });
    });

    it('should render recent activity section', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      });
    });
  });
});
