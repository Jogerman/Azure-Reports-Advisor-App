import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  color?: 'azure' | 'success' | 'warning' | 'danger' | 'info';
  loading?: boolean;
}

// Updated to use theme colors consistently
const colorClasses = {
  azure: 'bg-azure-50 text-azure-600',
  success: 'bg-success-50 text-success-600',
  warning: 'bg-warning-50 text-warning-600',
  danger: 'bg-danger-50 text-danger-600',
  info: 'bg-info-50 text-info-600',
} as const;

const getTrendColor = (value: number): string => {
  if (value > 0) return 'text-success-600';
  if (value < 0) return 'text-danger-600';
  return 'text-gray-600';
};

const getTrendIcon = (value: number): React.ReactNode => {
  if (value > 0) return <FiTrendingUp className="w-4 h-4" />;
  if (value < 0) return <FiTrendingDown className="w-4 h-4" />;
  return null;
};

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon,
  color = 'azure',
  loading = false,
}) => {
  // Memoize trend calculations to prevent unnecessary re-renders
  const trendData = useMemo(() => {
    if (change === undefined) return null;
    return {
      color: getTrendColor(change),
      icon: getTrendIcon(change),
      text: `${change > 0 ? '+' : ''}${change.toFixed(1)}%`,
    };
  }, [change]);

  if (loading) {
    return (
      <Card>
        <div className="p-6" role="status" aria-busy="true" aria-label={`Loading ${title} metric`}>
          <div className="flex items-center justify-between mb-4">
            <SkeletonLoader variant="rectangular" width="48px" height="48px" />
            <SkeletonLoader variant="text" width="64px" height="20px" />
          </div>
          <SkeletonLoader variant="text" width="96px" height="16px" className="mb-2" />
          <SkeletonLoader variant="text" width="128px" height="32px" />
        </div>
      </Card>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 10px 20px 0 rgba(0, 0, 0, 0.12)' }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <motion.div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color]}`}
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ type: 'spring', stiffness: 400, damping: 10 }}
            >
              {icon}
            </motion.div>
            {trendData && (
              <motion.div
                className={`flex items-center space-x-1 ${trendData.color}`}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                {trendData.icon}
                <span className="text-sm font-medium">
                  {trendData.text}
                </span>
              </motion.div>
            )}
          </div>

          <h3 className="text-sm font-medium text-gray-500 mb-1">{title}</h3>
          <motion.p
            className="text-3xl font-bold text-gray-900"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {value}
          </motion.p>

          {subtitle && (
            <p className="text-xs text-gray-500 mt-2">{subtitle}</p>
          )}

          {changeLabel && (
            <p className="text-xs text-gray-400 mt-1">{changeLabel}</p>
          )}
        </div>
      </Card>
    </motion.div>
  );
};

// Memoize component to prevent unnecessary re-renders
export default React.memo(MetricCard);
