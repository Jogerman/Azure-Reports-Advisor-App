import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import Card from '../common/Card';
import Button from '../common/Button';
import SkeletonLoader from '../common/SkeletonLoader';
import { TrendData, REPORT_TYPE_CONFIGS } from '../../types/analytics';

export interface ReportsOverTimeChartProps {
  data: TrendData[];
  period: 'day' | 'week' | 'month';
  onPeriodChange: (period: 'day' | 'week' | 'month') => void;
  loading: boolean;
}

/**
 * Reports Over Time Chart Component
 * Line chart showing report generation trends by type
 */
const ReportsOverTimeChart: React.FC<ReportsOverTimeChartProps> = ({
  data,
  period,
  onPeriodChange,
  loading,
}) => {
  const [hiddenLines, setHiddenLines] = useState<Set<string>>(new Set());

  // Toggle line visibility
  const handleLegendClick = (dataKey: string) => {
    setHiddenLines((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(dataKey)) {
        newSet.delete(dataKey);
      } else {
        newSet.add(dataKey);
      }
      return newSet;
    });
  };

  // Format chart data for Recharts
  const chartData = useMemo(() => {
    return data.map((point) => ({
      date: formatDate(point.date, period),
      total: point.total,
      cost: point.by_type.cost,
      security: point.by_type.security,
      operations: point.by_type.operations,
      detailed: point.by_type.detailed,
      executive: point.by_type.executive,
    }));
  }, [data, period]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
        <p className="font-semibold text-gray-900 mb-2">{label}</p>
        <div className="space-y-1">
          {payload.map((entry: any) => {
            if (hiddenLines.has(entry.dataKey)) return null;
            const config = REPORT_TYPE_CONFIGS.find((c) => c.dataKey === entry.dataKey);
            return (
              <div key={entry.dataKey} className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm text-gray-600">
                    {config?.name || entry.name}:
                  </span>
                </div>
                <span className="text-sm font-semibold text-gray-900">
                  {entry.value}
                </span>
              </div>
            );
          })}
          <div className="border-t border-gray-200 pt-1 mt-1">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-gray-700">Total:</span>
              <span className="text-sm font-bold text-gray-900">
                {payload[0]?.payload?.total || 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <SkeletonLoader variant="text" width="200px" height="24px" />
            <SkeletonLoader variant="rectangular" width="200px" height="36px" />
          </div>
          <SkeletonLoader variant="rectangular" width="100%" height="400px" />
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Reports Over Time</h3>
            <p className="text-sm text-gray-600 mt-1">
              Report generation trends by type
            </p>
          </div>

          {/* Period Toggle */}
          <div className="inline-flex rounded-lg border border-gray-200 p-1">
            {(['day', 'week', 'month'] as const).map((p) => (
              <button
                key={p}
                onClick={() => onPeriodChange(p)}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  period === p
                    ? 'bg-azure-600 text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
                aria-pressed={period === p}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Chart */}
        {chartData.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="date"
                  stroke="#6B7280"
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickLine={{ stroke: '#E5E7EB' }}
                />
                <YAxis
                  stroke="#6B7280"
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickLine={{ stroke: '#E5E7EB' }}
                  allowDecimals={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  onClick={(e: any) => e.dataKey && handleLegendClick(e.dataKey)}
                  iconType="line"
                />

                {REPORT_TYPE_CONFIGS.map((config) => (
                  <Line
                    key={config.dataKey}
                    type="monotone"
                    dataKey={config.dataKey}
                    name={config.name}
                    stroke={config.color}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                    hide={hiddenLines.has(config.dataKey)}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        ) : (
          <div className="flex items-center justify-center h-[400px] text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">No data available</p>
              <p className="text-sm mt-1">Try adjusting your filters</p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

/**
 * Format date based on period granularity
 */
function formatDate(dateStr: string, period: 'day' | 'week' | 'month'): string {
  const date = new Date(dateStr);

  switch (period) {
    case 'day':
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    case 'week':
      return `Week ${getWeekNumber(date)}`;
    case 'month':
      return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    default:
      return dateStr;
  }
}

/**
 * Get week number of the year
 */
function getWeekNumber(date: Date): number {
  const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
  const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
  return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

export default React.memo(ReportsOverTimeChart);
