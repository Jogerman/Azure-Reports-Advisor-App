import React from 'react';
import { FiFileText, FiUsers, FiDollarSign, FiClock, FiDatabase, FiCheckCircle } from 'react-icons/fi';
import MetricCard from '../dashboard/MetricCard';
import { DashboardMetrics } from '../../types/analytics';

export interface KPICardsProps {
  metrics: DashboardMetrics | undefined;
  loading: boolean;
}

/**
 * KPI Cards Component
 * Displays 6 key performance indicator cards for the analytics dashboard
 */
const KPICards: React.FC<KPICardsProps> = ({ metrics, loading }) => {
  // Format large numbers with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-US');
  };

  // Format currency
  const formatCurrency = (num: number): string => {
    return `$${num.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  // Format time (seconds to readable format)
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Total Reports */}
      <MetricCard
        title="Total Reports"
        value={metrics ? formatNumber(metrics.total_reports) : '-'}
        subtitle="All generated reports"
        change={metrics?.total_reports_change}
        changeLabel="vs. previous period"
        icon={<FiFileText className="w-6 h-6" />}
        color="azure"
        loading={loading}
      />

      {/* Active Users */}
      <MetricCard
        title="Active Users"
        value={metrics ? formatNumber(metrics.active_users) : '-'}
        subtitle="Users who generated reports"
        change={metrics?.active_users_change}
        changeLabel="vs. previous period"
        icon={<FiUsers className="w-6 h-6" />}
        color="info"
        loading={loading}
      />

      {/* Total Cost Analyzed */}
      <MetricCard
        title="Total Cost Analyzed"
        value={metrics ? formatCurrency(metrics.total_cost_analyzed) : '-'}
        subtitle="Cumulative Azure spending"
        change={metrics?.total_cost_analyzed_change}
        changeLabel="vs. previous period"
        icon={<FiDollarSign className="w-6 h-6" />}
        color="success"
        loading={loading}
      />

      {/* Avg Generation Time */}
      <MetricCard
        title="Avg Generation Time"
        value={metrics ? formatTime(metrics.avg_generation_time) : '-'}
        subtitle="Average report processing time"
        change={metrics?.avg_generation_time_change}
        changeLabel={
          metrics && metrics.avg_generation_time_change < 0
            ? 'Faster than previous period'
            : 'vs. previous period'
        }
        icon={<FiClock className="w-6 h-6" />}
        color="warning"
        loading={loading}
      />

      {/* Storage Used */}
      <MetricCard
        title="Storage Used"
        value={metrics ? metrics.storage_used_formatted : '-'}
        subtitle="Total file storage consumed"
        icon={<FiDatabase className="w-6 h-6" />}
        color="azure"
        loading={loading}
      />

      {/* Success Rate */}
      <MetricCard
        title="Success Rate"
        value={metrics ? `${metrics.success_rate.toFixed(1)}%` : '-'}
        subtitle="Reports completed successfully"
        icon={<FiCheckCircle className="w-6 h-6" />}
        color={metrics && metrics.success_rate >= 95 ? 'success' : metrics && metrics.success_rate >= 80 ? 'warning' : 'danger'}
        loading={loading}
      />
    </div>
  );
};

export default React.memo(KPICards);
