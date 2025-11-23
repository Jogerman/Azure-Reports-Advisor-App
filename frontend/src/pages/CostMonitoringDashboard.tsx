import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import costMonitoringApi from '../services/costMonitoringApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { showToast } from '../components/common/Toast';
import BudgetWidget from '../components/cost-monitoring/BudgetWidget';
import AlertList from '../components/cost-monitoring/AlertList';
import AnomalyCard from '../components/cost-monitoring/AnomalyCard';
import CostTrendChart from '../components/cost-monitoring/CostTrendChart';

const CostMonitoringDashboard: React.FC = () => {
  const [selectedSubscription, setSelectedSubscription] = useState<string | undefined>(
    undefined
  );
  const [timeRange, setTimeRange] = useState(30);

  // Fetch subscriptions
  const { data: subscriptionsData } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => costMonitoringApi.subscriptions.list({ is_active: true }),
  });

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['cost-monitoring-dashboard', selectedSubscription, timeRange],
    queryFn: () =>
      costMonitoringApi.dashboard.getData(selectedSubscription, timeRange),
  });

  // Fetch cost trend
  const { data: costTrend } = useQuery({
    queryKey: ['cost-trend', selectedSubscription, timeRange],
    queryFn: async () => {
      if (!selectedSubscription) return [];
      const data = await costMonitoringApi.costs.list({
        subscription: selectedSubscription,
        page: 1,
      });
      return data.results;
    },
    enabled: !!selectedSubscription,
  });

  const handleAcknowledgeAlert = async (id: string) => {
    try {
      await costMonitoringApi.alerts.acknowledge(id);
      showToast.success('Alert acknowledged successfully');
    } catch (error) {
      showToast.error('Failed to acknowledge alert');
    }
  };

  const handleResolveAlert = async (id: string) => {
    try {
      await costMonitoringApi.alerts.resolve(id);
      showToast.success('Alert resolved successfully');
    } catch (error) {
      showToast.error('Failed to resolve alert');
    }
  };

  const handleAcknowledgeAnomaly = async (id: string, notes?: string) => {
    try {
      await costMonitoringApi.anomalies.acknowledge(id, notes);
      showToast.success('Anomaly acknowledged successfully');
    } catch (error) {
      showToast.error('Failed to acknowledge anomaly');
    }
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Loading dashboard..." />;
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Failed to load dashboard data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Cost Monitoring</h1>
        <p className="mt-2 text-gray-600">
          Monitor Azure costs, budgets, and anomalies in real-time
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subscription
            </label>
            <select
              value={selectedSubscription || ''}
              onChange={(e) =>
                setSelectedSubscription(e.target.value || undefined)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Subscriptions</option>
              {subscriptionsData?.results.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.subscription_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        {/* Total Cost */}
        {dashboardData?.cost_summary && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Total Cost
            </h3>
            <p className="text-3xl font-bold text-gray-900">
              ${parseFloat(dashboardData.cost_summary.total_cost).toLocaleString()}
            </p>
            {dashboardData.cost_summary.cost_change_percentage && (
              <p
                className={`text-sm mt-2 ${
                  parseFloat(dashboardData.cost_summary.cost_change_percentage) > 0
                    ? 'text-red-600'
                    : 'text-green-600'
                }`}
              >
                {parseFloat(dashboardData.cost_summary.cost_change_percentage) > 0
                  ? '+'
                  : ''}
                {dashboardData.cost_summary.cost_change_percentage}% vs previous
                period
              </p>
            )}
          </div>
        )}

        {/* Active Budgets */}
        {dashboardData?.budget_summary && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Active Budgets
            </h3>
            <p className="text-3xl font-bold text-gray-900">
              {dashboardData.budget_summary.active_budgets}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {dashboardData.budget_summary.budgets_exceeded} exceeded
            </p>
          </div>
        )}

        {/* Active Alerts */}
        {dashboardData?.alert_summary && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Active Alerts
            </h3>
            <p className="text-3xl font-bold text-red-600">
              {dashboardData.alert_summary.active_alerts}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {dashboardData.alert_summary.by_severity.critical} critical
            </p>
          </div>
        )}

        {/* Anomalies */}
        {dashboardData?.anomaly_summary && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Anomalies Detected
            </h3>
            <p className="text-3xl font-bold text-orange-600">
              {dashboardData.anomaly_summary.total_anomalies}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {dashboardData.anomaly_summary.unacknowledged} unacknowledged
            </p>
          </div>
        )}
      </div>

      {/* Cost Trend Chart */}
      {selectedSubscription && costTrend && costTrend.length > 0 && (
        <div className="mb-6">
          <CostTrendChart
            data={costTrend.map((item) => ({
              date: item.date,
              total_cost: item.cost,
            }))}
            title="Cost Trend"
            height={300}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Recent Alerts */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Recent Alerts
            </h2>
            <Link
              to="/cost-monitoring/alerts"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View all →
            </Link>
          </div>
          {dashboardData?.recent_alerts && (
            <AlertList
              alerts={dashboardData.recent_alerts}
              onAcknowledge={handleAcknowledgeAlert}
              onResolve={handleResolveAlert}
            />
          )}
        </div>

        {/* Recent Anomalies */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Recent Anomalies
            </h2>
            <Link
              to="/cost-monitoring/anomalies"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View all →
            </Link>
          </div>
          <div className="space-y-4">
            {dashboardData?.recent_anomalies &&
            dashboardData.recent_anomalies.length > 0 ? (
              dashboardData.recent_anomalies.map((anomaly) => (
                <AnomalyCard
                  key={anomaly.id}
                  anomaly={anomaly}
                  onAcknowledge={handleAcknowledgeAnomaly}
                />
              ))
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No anomalies detected</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Link
            to="/cost-monitoring/subscriptions"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg p-4 text-center transition-all"
          >
            <div className="text-2xl mb-2">📊</div>
            <div className="font-medium">Manage Subscriptions</div>
          </Link>
          <Link
            to="/cost-monitoring/budgets"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg p-4 text-center transition-all"
          >
            <div className="text-2xl mb-2">💰</div>
            <div className="font-medium">Manage Budgets</div>
          </Link>
          <Link
            to="/cost-monitoring/alert-rules"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg p-4 text-center transition-all"
          >
            <div className="text-2xl mb-2">🔔</div>
            <div className="font-medium">Configure Alerts</div>
          </Link>
          <Link
            to="/cost-monitoring/forecasts"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg p-4 text-center transition-all"
          >
            <div className="text-2xl mb-2">📈</div>
            <div className="font-medium">View Forecasts</div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default CostMonitoringDashboard;
