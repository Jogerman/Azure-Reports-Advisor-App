import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { motion } from 'framer-motion';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { CategoryData, CHART_COLORS } from '../../types/analytics';

export interface ReportsByTypeChartProps {
  data: CategoryData[];
  loading: boolean;
}

/**
 * Reports By Type Chart Component
 * Pie/Donut chart showing report distribution by type
 */
const ReportsByTypeChart: React.FC<ReportsByTypeChartProps> = ({ data, loading }) => {
  // Custom label for pie chart
  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percent < 0.05) return null; // Don't show label if less than 5%

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-semibold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

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
          <SkeletonLoader variant="text" width="300px" height="16px" className="mb-6" />
          <div className="flex justify-center">
            <SkeletonLoader variant="circular" width="300px" height="300px" />
          </div>
        </div>
      </Card>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <Card>
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Reports by Type</h3>
          <p className="text-sm text-gray-600 mt-1">
            Distribution of report types ({total} total)
          </p>
        </div>

        {data.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
          >
            {/* Pie Chart */}
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomLabel}
                  outerRadius={100}
                  innerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={800}
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || CHART_COLORS.primary} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="grid grid-cols-2 gap-3 mt-6">
              {data.map((entry, index) => (
                <motion.div
                  key={index}
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: entry.color || CHART_COLORS.primary }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {entry.name}
                    </p>
                    <p className="text-xs text-gray-600">
                      {entry.value} ({entry.percentage.toFixed(1)}%)
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-gray-500">
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

export default React.memo(ReportsByTypeChart);
