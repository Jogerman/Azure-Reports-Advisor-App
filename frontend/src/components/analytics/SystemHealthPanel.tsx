import React from 'react';
import { motion } from 'framer-motion';
import {
  FiDatabase,
  FiUsers,
  FiClock,
  FiAlertCircle,
  FiHardDrive,
  FiActivity,
} from 'react-icons/fi';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { SystemHealth } from '../../types/analytics';

export interface SystemHealthPanelProps {
  health: SystemHealth | undefined;
  loading: boolean;
}

/**
 * System Health Panel Component
 * Displays system health metrics with gauges (Admin/Manager only)
 */
const SystemHealthPanel: React.FC<SystemHealthPanelProps> = ({ health, loading }) => {
  // Format time
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Get status color
  const getStatusColor = (value: number, type: 'error_rate' | 'generation_time'): string => {
    if (type === 'error_rate') {
      if (value <= 2) return 'text-success-600 bg-success-100';
      if (value <= 5) return 'text-warning-600 bg-warning-100';
      return 'text-danger-600 bg-danger-100';
    }
    // generation_time
    if (value <= 30) return 'text-success-600 bg-success-100';
    if (value <= 60) return 'text-warning-600 bg-warning-100';
    return 'text-danger-600 bg-danger-100';
  };

  // Circular progress component
  const CircularProgress: React.FC<{
    value: number;
    max: number;
    label: string;
    color: string;
  }> = ({ value, max, label, color }) => {
    const percentage = Math.min((value / max) * 100, 100);
    const circumference = 2 * Math.PI * 45; // radius = 45
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32">
          <svg className="transform -rotate-90 w-32 h-32">
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="#E5E7EB"
              strokeWidth="8"
              fill="none"
            />
            <motion.circle
              cx="64"
              cy="64"
              r="45"
              stroke={color}
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: 'easeInOut' }}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {percentage.toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
        <p className="text-sm font-medium text-gray-700 mt-2 text-center">{label}</p>
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
              <SkeletonLoader variant="text" width="200px" height="24px" className="mb-2" />
              <SkeletonLoader variant="text" width="150px" height="16px" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <SkeletonLoader key={i} variant="rectangular" width="100%" height="120px" />
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (!health) {
    return (
      <Card>
        <div className="p-6 text-center text-gray-500">
          <FiActivity className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p className="text-lg font-medium">System health unavailable</p>
        </div>
      </Card>
    );
  }

  const errorRateStatus = getStatusColor(health.error_rate, 'error_rate');
  const generationTimeStatus = getStatusColor(
    health.avg_report_generation_time,
    'generation_time'
  );

  return (
    <Card>
      <motion.div
        className="p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-azure-100 text-azure-600 flex items-center justify-center flex-shrink-0">
              <FiActivity className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
              <p className="text-sm text-gray-600 mt-1">
                Real-time system performance metrics
              </p>
            </div>
          </div>
          {health.last_calculated && (
            <span className="text-xs text-gray-500">
              Last updated: {new Date(health.last_calculated).toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Database Size */}
          <motion.div
            className="bg-gray-50 rounded-lg p-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-azure-100 text-azure-600 flex items-center justify-center">
                <FiDatabase className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600">Database Size</p>
                <p className="text-2xl font-bold text-gray-900">
                  {health.database_size_formatted}
                </p>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {health.total_reports} total reports
            </div>
          </motion.div>

          {/* Active Users Today */}
          <motion.div
            className="bg-gray-50 rounded-lg p-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-info-100 text-info-600 flex items-center justify-center">
                <FiUsers className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600">Active Users</p>
                <p className="text-2xl font-bold text-gray-900">
                  {health.active_users_today}
                </p>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {health.active_users_this_week} this week
            </div>
          </motion.div>

          {/* Avg Generation Time */}
          <motion.div
            className={`rounded-lg p-4 ${generationTimeStatus}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-white/50 flex items-center justify-center">
                <FiClock className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium">Avg Generation Time</p>
                <p className="text-2xl font-bold">
                  {formatTime(health.avg_report_generation_time)}
                </p>
              </div>
            </div>
            <div className="text-xs opacity-80">
              {health.avg_report_generation_time <= 30
                ? 'Excellent performance'
                : health.avg_report_generation_time <= 60
                ? 'Good performance'
                : 'Consider optimization'}
            </div>
          </motion.div>

          {/* Error Rate */}
          <motion.div
            className={`rounded-lg p-4 ${errorRateStatus}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-white/50 flex items-center justify-center">
                <FiAlertCircle className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium">Error Rate</p>
                <p className="text-2xl font-bold">{health.error_rate.toFixed(2)}%</p>
              </div>
            </div>
            <div className="text-xs opacity-80">
              {health.error_rate <= 2
                ? 'System healthy'
                : health.error_rate <= 5
                ? 'Monitor closely'
                : 'Action required'}
            </div>
          </motion.div>

          {/* Storage Used */}
          <motion.div
            className="bg-gray-50 rounded-lg p-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-warning-100 text-warning-600 flex items-center justify-center">
                <FiHardDrive className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600">Storage Used</p>
                <p className="text-2xl font-bold text-gray-900">
                  {health.storage_used_formatted}
                </p>
              </div>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-warning-600 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: '65%' }}
                transition={{ duration: 1, delay: 0.6 }}
              />
            </div>
          </motion.div>

          {/* Uptime */}
          <motion.div
            className="bg-success-50 rounded-lg p-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-success-100 text-success-600 flex items-center justify-center">
                <FiActivity className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-success-700">System Uptime</p>
                <p className="text-2xl font-bold text-success-900">{health.uptime}</p>
              </div>
            </div>
            <div className="text-xs text-success-600">All systems operational</div>
          </motion.div>
        </div>

        {/* Alert Banner (if error rate is high) */}
        {health.error_rate > 5 && (
          <motion.div
            className="mt-6 p-4 bg-danger-50 border border-danger-200 rounded-lg flex items-start gap-3"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <FiAlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-danger-900">
                High Error Rate Detected
              </p>
              <p className="text-xs text-danger-700 mt-1">
                The system error rate is above the recommended threshold. Please investigate
                recent failures and consider system maintenance.
              </p>
            </div>
          </motion.div>
        )}
      </motion.div>
    </Card>
  );
};

export default React.memo(SystemHealthPanel);
