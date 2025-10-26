import React, { useState, useCallback, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FiBarChart2, FiRefreshCw } from 'react-icons/fi';
import {
  KPICards,
  ReportsOverTimeChart,
  ReportsByTypeChart,
  ReportsByStatusChart,
  TopUsersTable,
  UserActivityTimeline,
  CostInsightsCard,
  SystemHealthPanel,
  AnalyticsFilters,
  ExportDashboardButton,
} from '../components/analytics';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import { showToast } from '../components/common/Toast';
import { useAnalyticsFilters } from '../hooks/useAnalyticsFilters';
import { useDashboardMetrics } from '../hooks/useDashboardMetrics';
import { useAnalyticsTrends } from '../hooks/useAnalyticsTrends';
import analyticsService from '../services/analyticsService';
import { useAuth } from '../hooks/useAuth';

/**
 * Analytics Page
 * Main analytics dashboard with comprehensive insights and metrics
 */
const AnalyticsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Check if user is admin or manager
  const isAdminOrManager =
    user?.email?.toLowerCase().includes('admin') ||
    user?.email?.toLowerCase().includes('manager') ||
    false;

  // Filters management
  const { filters, updateFilters, clearFilters, apiParams } = useAnalyticsFilters();

  // Period for trends chart
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day');

  // Fetch dashboard metrics
  const {
    data: metricsData,
    isLoading: metricsLoading,
    refetch: refetchMetrics,
  } = useDashboardMetrics(apiParams);

  // Fetch trends data
  const {
    data: trendsData,
    isLoading: trendsLoading,
    refetch: refetchTrends,
  } = useAnalyticsTrends({ ...apiParams, period });

  // Fetch reports by type
  const { data: reportsByTypeData, isLoading: reportsByTypeLoading } = useQuery({
    queryKey: ['analytics', 'by-type', apiParams],
    queryFn: () => analyticsService.getReportsByType(apiParams),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch reports by status
  const { data: reportsByStatusData, isLoading: reportsByStatusLoading } = useQuery({
    queryKey: ['analytics', 'by-status', apiParams],
    queryFn: () => analyticsService.getReportsByStatus(apiParams),
    staleTime: 5 * 60 * 1000,
  });

  // Fetch top users
  const { data: topUsersData, isLoading: topUsersLoading } = useQuery({
    queryKey: ['analytics', 'top-users', apiParams],
    queryFn: () => analyticsService.getTopUsers(apiParams),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Fetch user activity
  const { data: userActivityData, isLoading: userActivityLoading } = useQuery({
    queryKey: ['analytics', 'user-activity'],
    queryFn: () => analyticsService.getUserActivity({ limit: 20 }),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every 60 seconds
  });

  // Fetch cost insights
  const { data: costInsightsData, isLoading: costInsightsLoading } = useQuery({
    queryKey: ['analytics', 'cost-insights', apiParams],
    queryFn: () => analyticsService.getCostInsights(apiParams),
    staleTime: 5 * 60 * 1000,
  });

  // Fetch system health (admin/manager only)
  const { data: systemHealthData, isLoading: systemHealthLoading } = useQuery({
    queryKey: ['analytics', 'system-health'],
    queryFn: () => analyticsService.getSystemHealth(),
    enabled: isAdminOrManager,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });

  // Auto-refresh metrics every 2 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['analytics', 'metrics'] });
      queryClient.invalidateQueries({ queryKey: ['analytics', 'user-activity'] });
    }, 2 * 60 * 1000);

    return () => clearInterval(interval);
  }, [queryClient]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    refetchMetrics();
    refetchTrends();
    queryClient.invalidateQueries({ queryKey: ['analytics'] });
    showToast.success('Analytics data refreshed');
  }, [refetchMetrics, refetchTrends, queryClient]);

  // Handle filters change
  const handleFiltersChange = useCallback(
    (newFilters: typeof filters) => {
      updateFilters(newFilters);
    },
    [updateFilters]
  );

  // Handle filters reset
  const handleFiltersReset = useCallback(() => {
    clearFilters();
    showToast.info('Filters reset');
  }, [clearFilters]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 p-6 lg:p-8"
    >
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-azure-50 text-azure-600 flex items-center justify-center">
            <FiBarChart2 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Comprehensive insights and metrics for your reports
            </p>
          </div>
        </div>

        {/* Header Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <AnalyticsFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onReset={handleFiltersReset}
            showRoleFilter={isAdminOrManager}
          />
          <Button
            variant="outline"
            icon={<FiRefreshCw />}
            onClick={handleRefresh}
            size="md"
          >
            Refresh
          </Button>
          <ExportDashboardButton filters={apiParams} />
        </div>
      </div>

      {/* KPI Cards */}
      <KPICards metrics={metricsData} loading={metricsLoading} />

      {/* Charts Section 1: Trends & Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ReportsOverTimeChart
          data={trendsData?.data || []}
          period={period}
          onPeriodChange={setPeriod}
          loading={trendsLoading}
        />
        <ReportsByTypeChart
          data={reportsByTypeData?.data || []}
          loading={reportsByTypeLoading}
        />
      </div>

      {/* Charts Section 2: Top Users & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TopUsersTable
            users={topUsersData?.users || []}
            loading={topUsersLoading}
          />
        </div>
        <div>
          <ReportsByStatusChart
            data={reportsByStatusData?.data || []}
            loading={reportsByStatusLoading}
          />
        </div>
      </div>

      {/* Cost & Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CostInsightsCard data={costInsightsData} loading={costInsightsLoading} />
        <UserActivityTimeline
          activities={userActivityData?.activities || []}
          loading={userActivityLoading}
        />
      </div>

      {/* System Health Panel (Admin/Manager Only) */}
      {isAdminOrManager && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <SystemHealthPanel health={systemHealthData} loading={systemHealthLoading} />
        </motion.div>
      )}

      {/* Empty State (when no data) */}
      {!metricsLoading &&
        metricsData &&
        metricsData.total_reports === 0 && (
          <Card>
            <div className="p-12 text-center">
              <FiBarChart2 className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Analytics Data Yet
              </h3>
              <p className="text-gray-600 mb-6">
                Start generating reports to see insights and metrics appear here.
              </p>
              <Button
                variant="primary"
                onClick={() => (window.location.href = '/reports')}
              >
                Generate Your First Report
              </Button>
            </div>
          </Card>
        )}
    </motion.div>
  );
};

export default AnalyticsPage;
