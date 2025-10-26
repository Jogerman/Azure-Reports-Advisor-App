import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { FiDollarSign, FiTrendingDown, FiTrendingUp } from 'react-icons/fi';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { CostInsights, CHART_COLORS } from '../../types/analytics';

export interface CostInsightsCardProps {
  data: CostInsights | undefined;
  loading: boolean;
}

/**
 * Cost Insights Card Component
 * Displays cost analysis insights with mini trend chart
 */
const CostInsightsCard: React.FC<CostInsightsCardProps> = ({ data, loading }) => {
  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Custom tooltip for mini chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-xs font-medium text-gray-900 mb-1">{payload[0].payload.month}</p>
        <p className="text-sm font-semibold text-azure-600">
          {formatCurrency(payload[0].value)}
        </p>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <SkeletonLoader variant="circular" width="48px" height="48px" />
            <div className="flex-1">
              <SkeletonLoader variant="text" width="150px" height="20px" className="mb-2" />
              <SkeletonLoader variant="text" width="100px" height="16px" />
            </div>
          </div>
          <SkeletonLoader variant="rectangular" width="100%" height="120px" className="mb-4" />
          <div className="grid grid-cols-2 gap-4">
            <SkeletonLoader variant="rectangular" width="100%" height="80px" />
            <SkeletonLoader variant="rectangular" width="100%" height="80px" />
          </div>
        </div>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <div className="p-6 text-center text-gray-500">
          <FiDollarSign className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p className="text-lg font-medium">No cost data available</p>
          <p className="text-sm mt-1">Cost insights will appear when reports are analyzed</p>
        </div>
      </Card>
    );
  }

  const savingsColor =
    data.savings_percentage >= 20
      ? 'text-success-600'
      : data.savings_percentage >= 10
      ? 'text-warning-600'
      : 'text-gray-600';

  return (
    <Card>
      <motion.div
        className="p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Header */}
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-lg bg-success-100 text-success-600 flex items-center justify-center flex-shrink-0">
            <FiDollarSign className="w-6 h-6" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900">Cost Insights</h3>
            <p className="text-sm text-gray-600 mt-1">Azure spending analysis</p>
          </div>
        </div>

        {/* Mini Trend Chart */}
        {data.trends && data.trends.length > 0 && (
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={100}>
              <AreaChart data={data.trends}>
                <defs>
                  <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.success} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.success} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 10, fill: '#6B7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis hide />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="cost"
                  stroke={CHART_COLORS.success}
                  strokeWidth={2}
                  fill="url(#costGradient)"
                  animationDuration={800}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Total Cost Analyzed */}
          <div className="bg-azure-50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <FiTrendingUp className="w-4 h-4 text-azure-600" />
              <p className="text-xs font-medium text-azure-700">Total Analyzed</p>
            </div>
            <p className="text-2xl font-bold text-azure-900">
              {formatCurrency(data.total_cost_analyzed)}
            </p>
          </div>

          {/* Potential Savings */}
          <div className="bg-success-50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <FiTrendingDown className="w-4 h-4 text-success-600" />
              <p className="text-xs font-medium text-success-700">Potential Savings</p>
            </div>
            <p className="text-2xl font-bold text-success-900">
              {formatCurrency(data.potential_savings)}
            </p>
          </div>
        </div>

        {/* Savings Percentage */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Savings Opportunity</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-success-600 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(data.savings_percentage, 100)}%` }}
                  transition={{ duration: 1, delay: 0.3 }}
                />
              </div>
              <span className={`text-lg font-bold ${savingsColor}`}>
                {data.savings_percentage.toFixed(1)}%
              </span>
            </div>
          </div>
          {data.savings_percentage >= 15 && (
            <motion.p
              className="text-xs text-success-600 mt-2 font-medium"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              Great opportunity for cost optimization!
            </motion.p>
          )}
        </div>
      </motion.div>
    </Card>
  );
};

export default React.memo(CostInsightsCard);
