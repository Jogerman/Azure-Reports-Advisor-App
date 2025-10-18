import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiFileText,
  FiCheckCircle,
  FiClock,
  FiXCircle,
  FiDownload,
  FiEye,
} from 'react-icons/fi';
import { formatDistanceToNow } from 'date-fns';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';

export interface ActivityItem {
  id: string;
  type: 'report_generated' | 'report_processing' | 'report_failed' | 'client_added';
  title: string;
  description: string;
  timestamp: Date;
  clientName?: string;
  reportType?: string;
  reportId?: string;
  status?: 'completed' | 'processing' | 'failed' | 'pending';
}

export interface RecentActivityProps {
  activities: ActivityItem[];
  title?: string;
  subtitle?: string;
  maxItems?: number;
  loading?: boolean;
  showActions?: boolean;
}

const RecentActivity: React.FC<RecentActivityProps> = ({
  activities,
  title = 'Recent Activity',
  subtitle,
  maxItems = 10,
  loading = false,
  showActions = true,
}) => {
  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <FiCheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <FiClock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <FiXCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FiFileText className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'processing':
        return 'bg-blue-50 border-blue-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const displayActivities = activities.slice(0, maxItems);

  if (loading) {
    return (
      <Card>
        <div className="p-6" role="status" aria-busy="true" aria-label="Loading recent activity">
          <div className="mb-4">
            <SkeletonLoader variant="text" width="30%" height="24px" className="mb-2" />
            {subtitle && <SkeletonLoader variant="text" width="50%" height="16px" />}
          </div>
          <div className="space-y-4">
            {[...Array(5)].map((_, index) => (
              <div key={index} className="flex items-start space-x-3">
                <SkeletonLoader variant="circular" width="40px" height="40px" />
                <div className="flex-1 space-y-2">
                  <SkeletonLoader variant="text" width="75%" height="16px" />
                  <SkeletonLoader variant="text" width="50%" height="12px" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600 mb-4">{subtitle}</p>}
          <div className="text-center py-12">
            <FiClock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No recent activity</p>
            <p className="text-sm text-gray-400 mt-1">
              Activity will appear here as you use the platform
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
        </div>

        <div className="space-y-4">
          {displayActivities.map((activity, index) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`flex items-start space-x-3 p-4 rounded-lg border transition-all hover:shadow-sm ${getStatusColor(
                activity.status
              )}`}
            >
              {/* Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {getStatusIcon(activity.status)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {activity.title}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {activity.description}
                    </p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-xs text-gray-500">
                        {formatDistanceToNow(new Date(activity.timestamp), {
                          addSuffix: true,
                        })}
                      </span>
                      {activity.clientName && (
                        <span className="text-xs text-gray-500">
                          Client: {activity.clientName}
                        </span>
                      )}
                      {activity.reportType && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-azure-100 text-azure-800">
                          {activity.reportType}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  {showActions && activity.reportId && activity.status === 'completed' && (
                    <div className="flex items-center space-x-2 ml-4">
                      <Link to={`/reports/${activity.reportId}`}>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="p-2 text-gray-400 hover:text-azure-600 transition-colors"
                          title="View report"
                        >
                          <FiEye className="w-4 h-4" />
                        </motion.button>
                      </Link>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                        title="Download report"
                      >
                        <FiDownload className="w-4 h-4" />
                      </motion.button>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* View All Link */}
        {activities.length > maxItems && (
          <div className="mt-6 text-center">
            <Link
              to="/history"
              className="text-sm font-medium text-azure-600 hover:text-azure-700 transition-colors"
            >
              View all activity ({activities.length} items)
            </Link>
          </div>
        )}
      </div>
    </Card>
  );
};

export default RecentActivity;
