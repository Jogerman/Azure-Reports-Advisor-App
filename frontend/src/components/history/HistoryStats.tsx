import React from 'react';
import { FiFileText, FiCalendar, FiHardDrive, FiPieChart } from 'react-icons/fi';
import MetricCard from '../dashboard/MetricCard';
import Card from '../common/Card';
import { HistoryStatistics } from '../../types/history';

interface HistoryStatsProps {
  stats: HistoryStatistics | undefined;
  loading: boolean;
}

const HistoryStats: React.FC<HistoryStatsProps> = ({ stats, loading }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {/* Total Reports */}
      <MetricCard
        title="Total Reports"
        value={stats?.total_reports.toLocaleString() || '0'}
        change={stats?.total_reports_change}
        changeLabel="vs. last period"
        icon={<FiFileText className="w-6 h-6" />}
        color="azure"
        loading={loading}
      />

      {/* This Month */}
      <MetricCard
        title="This Month"
        value={stats?.reports_this_month.toLocaleString() || '0'}
        subtitle="Reports generated"
        change={stats?.reports_this_month_change}
        changeLabel="vs. last month"
        icon={<FiCalendar className="w-6 h-6" />}
        color="success"
        loading={loading}
      />

      {/* Total Size */}
      <MetricCard
        title="Total Size"
        value={stats?.total_size_formatted || '0 B'}
        subtitle="All report files"
        change={stats?.total_size_change}
        changeLabel="vs. last period"
        icon={<FiHardDrive className="w-6 h-6" />}
        color="info"
        loading={loading}
      />

      {/* Breakdown by Type */}
      <Card padding="md" className="h-full">
        <div className="h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-lg bg-warning-50 text-warning-600 flex items-center justify-center">
              <FiPieChart className="w-6 h-6" />
            </div>
          </div>

          <h3 className="text-sm font-medium text-gray-500 mb-3">By Report Type</h3>

          {loading ? (
            <div className="space-y-2 flex-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-6 bg-gray-200 rounded animate-pulse" />
              ))}
            </div>
          ) : stats?.breakdown ? (
            <div className="space-y-2 flex-1">
              {Object.entries(stats.breakdown).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${getTypeColor(type)}`}
                      aria-hidden="true"
                    />
                    <span className="text-sm text-gray-700 capitalize">
                      {type}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
              No data available
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

/**
 * Get color class for report type
 */
const getTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    cost: 'bg-azure-600',
    security: 'bg-danger-600',
    operations: 'bg-success-600',
    detailed: 'bg-info-600',
    executive: 'bg-warning-600',
  };
  return colors[type] || 'bg-gray-600';
};

export default React.memo(HistoryStats);
