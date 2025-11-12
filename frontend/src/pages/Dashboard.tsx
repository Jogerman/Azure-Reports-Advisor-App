import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  FiUsers,
  FiFileText,
  FiDollarSign,
  FiTrendingUp,
  FiArrowRight,
  FiAlertCircle,
  FiRefreshCw,
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import { MetricCard, CategoryChart, TrendChart, RecentActivity } from '../components/dashboard';
import { analyticsService } from '../services';

const Dashboard: React.FC = () => {
  // Use React Query for data fetching with auto-refresh every 30 seconds
  const {
    data: metricsData,
    isLoading: loading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => analyticsService.getDashboardMetrics(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    refetchIntervalInBackground: false, // Don't refresh when tab is not active
    staleTime: 20000, // Consider data stale after 20 seconds
    retry: 2, // Retry failed requests twice
  });

  // Handle errors with React effect
  React.useEffect(() => {
    if (error) {
      toast.error('Failed to load analytics data');
      console.error('Analytics error:', error);
    }
  }, [error]);

  const handleRefresh = async () => {
    try {
      await refetch();
      toast.success('Dashboard refreshed');
    } catch (err) {
      toast.error('Failed to refresh dashboard');
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  // Format currency
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format number with commas
  const formatNumber = (value: number): string => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants} className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
            <p className="text-gray-600">
              Welcome to Azure Advisor Reports Platform. Here's an overview of your reports and clients.
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRefresh}
            disabled={isFetching}
            className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            aria-label="Refresh dashboard data"
          >
            <FiRefreshCw className={`mr-2 w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            {isFetching ? 'Refreshing...' : 'Refresh'}
          </motion.button>
        </div>
      </motion.div>

      {/* Error State */}
      {error && (
        <motion.div
          variants={itemVariants}
          className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3"
          role="alert"
          aria-live="assertive"
        >
          <FiAlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
            <p className="text-sm text-red-700 mt-1">
              {error instanceof Error ? error.message : 'Failed to load analytics data'}
            </p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-sm font-medium text-red-600 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded"
              aria-label="Retry loading dashboard data"
            >
              Try again
            </button>
          </div>
        </motion.div>
      )}

      {/* Metrics Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Active Users"
          value={loading ? '...' : formatNumber(metricsData?.active_users || 0)}
          change={metricsData?.active_users_change}
          changeLabel="vs last month"
          icon={<FiUsers className="w-6 h-6" />}
          color="azure"
          loading={loading}
        />
        <MetricCard
          title="Total Reports"
          value={loading ? '...' : formatNumber(metricsData?.total_reports || 0)}
          change={metricsData?.total_reports_change}
          changeLabel="vs last month"
          icon={<FiFileText className="w-6 h-6" />}
          color="success"
          loading={loading}
        />
        <MetricCard
          title="Total Cost Analyzed"
          value={loading ? '...' : formatCurrency(metricsData?.total_cost_analyzed || 0)}
          change={metricsData?.total_cost_analyzed_change}
          changeLabel="vs last month"
          icon={<FiDollarSign className="w-6 h-6" />}
          color="warning"
          loading={loading}
        />
        <MetricCard
          title="Avg Generation Time"
          value={loading ? '...' : `${(metricsData?.avg_generation_time || 0).toFixed(1)}s`}
          subtitle={metricsData?.storage_used_formatted}
          change={metricsData?.avg_generation_time_change}
          changeLabel="vs last month"
          icon={<FiTrendingUp className="w-6 h-6" />}
          color="info"
          loading={loading}
        />
      </motion.div>

      {/* Additional Metrics */}
      <motion.div variants={itemVariants} className="mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">System Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">{loading ? '...' : `${(metricsData?.success_rate || 0).toFixed(1)}%`}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Storage Used</p>
              <p className="text-2xl font-bold text-azure-600">{loading ? '...' : metricsData?.storage_used_formatted || '0 B'}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants}>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" role="navigation" aria-label="Quick actions">
          {/* Manage Clients */}
          <Link
            to="/clients"
            className="focus:outline-none focus:ring-2 focus:ring-azure-500 focus:ring-offset-2 rounded-lg"
            aria-label="Manage Clients - Add, edit, or view your client list and their Azure subscriptions"
          >
            <motion.div
              whileHover={{ y: -4, boxShadow: '0 4px 12px 0 rgba(0, 0, 0, 0.1)' }}
              transition={{ duration: 0.2 }}
              className="p-6 bg-white rounded-lg shadow-sm border border-gray-200 hover:border-azure-300 transition-all h-full"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-azure-50 rounded-lg flex items-center justify-center" aria-hidden="true">
                  <FiUsers className="w-6 h-6 text-azure-600" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Manage Clients</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Add, edit, or view your client list and their Azure subscriptions.
              </p>
              <div className="inline-flex items-center text-sm font-medium text-azure-600">
                Go to Clients
                <FiArrowRight className="ml-1 w-4 h-4" aria-hidden="true" />
              </div>
            </motion.div>
          </Link>

          {/* Generate Reports */}
          <Link
            to="/reports"
            className="focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 rounded-lg"
            aria-label="Generate Reports - Upload Azure Advisor CSV and generate professional reports"
          >
            <motion.div
              whileHover={{ y: -4, boxShadow: '0 4px 12px 0 rgba(0, 0, 0, 0.1)' }}
              transition={{ duration: 0.2 }}
              className="p-6 bg-white rounded-lg shadow-sm border border-gray-200 hover:border-green-300 transition-all h-full"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center" aria-hidden="true">
                  <FiFileText className="w-6 h-6 text-green-600" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Generate Reports</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Upload Azure Advisor CSV and generate professional reports.
              </p>
              <div className="inline-flex items-center text-sm font-medium text-green-600">
                Upload CSV
                <FiArrowRight className="ml-1 w-4 h-4" aria-hidden="true" />
              </div>
            </motion.div>
          </Link>

          {/* View History */}
          <Link
            to="/history"
            className="focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 rounded-lg"
            aria-label="View History - Access all your previously generated reports and activity"
          >
            <motion.div
              whileHover={{ y: -4, boxShadow: '0 4px 12px 0 rgba(0, 0, 0, 0.1)' }}
              transition={{ duration: 0.2 }}
              className="p-6 bg-white rounded-lg shadow-sm border border-gray-200 hover:border-purple-300 transition-all h-full"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center" aria-hidden="true">
                  <FiTrendingUp className="w-6 h-6 text-purple-600" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">View History</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Access all your previously generated reports and activity.
              </p>
              <div className="inline-flex items-center text-sm font-medium text-purple-600">
                View History
                <FiArrowRight className="ml-1 w-4 h-4" aria-hidden="true" />
              </div>
            </motion.div>
          </Link>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Dashboard;
