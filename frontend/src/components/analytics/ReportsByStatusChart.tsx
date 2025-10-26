import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { motion } from 'framer-motion';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { CategoryData, CHART_COLORS } from '../../types/analytics';

export interface ReportsByStatusChartProps {
  data: CategoryData[];
  loading: boolean;
}

/**
 * Reports By Status Chart Component
 * Horizontal bar chart showing report distribution by status
 */
const ReportsByStatusChart: React.FC<ReportsByStatusChartProps> = ({ data, loading }) => {
  // Status color mapping
  const getStatusColor = (status: string): string => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('completed') || statusLower.includes('success')) {
      return CHART_COLORS.completed;
    }
    if (statusLower.includes('failed') || statusLower.includes('error')) {
      return CHART_COLORS.failed;
    }
    if (statusLower.includes('processing') || statusLower.includes('generating')) {
      return CHART_COLORS.processing;
    }
    if (statusLower.includes('pending') || statusLower.includes('queued')) {
      return CHART_COLORS.pending;
    }
    return CHART_COLORS.primary;
  };

  // Add colors to data
  const chartData = data.map((item) => ({
    ...item,
    color: getStatusColor(item.name),
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: data.color }}
          />
          <p className="font-semibold text-gray-900">{data.name}</p>
        </div>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">Count:</span>
            <span className="font-semibold text-gray-900">{data.value}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">Percentage:</span>
            <span className="font-semibold text-gray-900">
              {data.percentage.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <div className="p-6">
          <SkeletonLoader variant="text" width="200px" height="24px" className="mb-2" />
          <SkeletonLoader variant="text" width="250px" height="16px" className="mb-6" />
          <SkeletonLoader variant="rectangular" width="100%" height="300px" />
        </div>
      </Card>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <Card>
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Reports by Status</h3>
          <p className="text-sm text-gray-600 mt-1">
            Status distribution ({total} total)
          </p>
        </div>

        {chartData.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {/* Bar Chart */}
            <ResponsiveContainer width="100%" height={Math.max(chartData.length * 60, 200)}>
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
                <XAxis
                  type="number"
                  stroke="#6B7280"
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickLine={{ stroke: '#E5E7EB' }}
                  allowDecimals={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#6B7280"
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickLine={{ stroke: '#E5E7EB' }}
                  width={120}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }} />
                <Bar
                  dataKey="value"
                  radius={[0, 8, 8, 0]}
                  animationBegin={0}
                  animationDuration={800}
                  label={{ position: 'right', fill: '#6B7280', fontSize: 12 }}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 gap-2 mt-6">
              {chartData.map((entry, index) => (
                <motion.div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-sm font-medium text-gray-900">
                      {entry.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-gray-900">
                      {entry.value}
                    </span>
                    <span className="text-xs text-gray-600 min-w-[50px] text-right">
                      {entry.percentage.toFixed(1)}%
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">No data available</p>
              <p className="text-sm mt-1">No reports found for the selected filters</p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default React.memo(ReportsByStatusChart);
