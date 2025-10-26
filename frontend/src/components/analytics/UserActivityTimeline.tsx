import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiFileText,
  FiTrash2,
  FiDownload,
  FiLogIn,
  FiLogOut,
  FiUserPlus,
  FiEdit,
  FiSettings,
  FiActivity,
} from 'react-icons/fi';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { UserActivity } from '../../types/analytics';
import { formatDistanceToNow } from 'date-fns';

export interface UserActivityTimelineProps {
  activities: UserActivity[];
  loading: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

/**
 * User Activity Timeline Component
 * Timeline/list of recent user activities
 */
const UserActivityTimeline: React.FC<UserActivityTimelineProps> = ({
  activities,
  loading,
  onLoadMore,
  hasMore = false,
}) => {
  const [filter, setFilter] = useState<string>('all');

  // Get icon for activity type
  const getActivityIcon = (activityType: string): React.ReactNode => {
    const iconClass = 'w-4 h-4';
    switch (activityType) {
      case 'report_generated':
        return <FiFileText className={iconClass} />;
      case 'report_deleted':
        return <FiTrash2 className={iconClass} />;
      case 'report_downloaded':
        return <FiDownload className={iconClass} />;
      case 'user_login':
        return <FiLogIn className={iconClass} />;
      case 'user_logout':
        return <FiLogOut className={iconClass} />;
      case 'client_created':
        return <FiUserPlus className={iconClass} />;
      case 'client_updated':
        return <FiEdit className={iconClass} />;
      case 'settings_changed':
        return <FiSettings className={iconClass} />;
      default:
        return <FiActivity className={iconClass} />;
    }
  };

  // Get color for activity type
  const getActivityColor = (activityType: string): string => {
    switch (activityType) {
      case 'report_generated':
        return 'bg-success-100 text-success-700 border-success-200';
      case 'report_deleted':
        return 'bg-danger-100 text-danger-700 border-danger-200';
      case 'report_downloaded':
        return 'bg-azure-100 text-azure-700 border-azure-200';
      case 'user_login':
      case 'user_logout':
        return 'bg-info-100 text-info-700 border-info-200';
      case 'client_created':
      case 'client_updated':
        return 'bg-warning-100 text-warning-700 border-warning-200';
      case 'settings_changed':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  // Filter activities
  const filteredActivities =
    filter === 'all'
      ? activities
      : activities.filter((a) => a.activity_type === filter);

  // Get unique activity types for filter
  const activityTypes = Array.from(
    new Set(activities.map((a) => a.activity_type))
  );

  if (loading) {
    return (
      <Card>
        <div className="p-6">
          <SkeletonLoader variant="text" width="200px" height="24px" className="mb-2" />
          <SkeletonLoader variant="text" width="300px" height="16px" className="mb-6" />
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex gap-4">
                <SkeletonLoader variant="circular" width="40px" height="40px" />
                <div className="flex-1">
                  <SkeletonLoader variant="text" width="80%" height="20px" className="mb-2" />
                  <SkeletonLoader variant="text" width="60%" height="16px" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          <p className="text-sm text-gray-600 mt-1">Latest user actions and events</p>
        </div>

        {/* Filter Tabs */}
        {activityTypes.length > 1 && (
          <div className="flex flex-wrap gap-2 mb-6">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                filter === 'all'
                  ? 'bg-azure-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            {activityTypes.slice(0, 4).map((type) => (
              <button
                key={type}
                onClick={() => setFilter(type)}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                  filter === type
                    ? 'bg-azure-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {formatActivityType(type)}
              </button>
            ))}
          </div>
        )}

        {/* Timeline */}
        {filteredActivities.length > 0 ? (
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />

            {/* Activity Items */}
            <div className="space-y-4">
              <AnimatePresence>
                {filteredActivities.map((activity, index) => (
                  <motion.div
                    key={activity.id}
                    className="relative flex gap-4"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    {/* Icon */}
                    <div
                      className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2 ${getActivityColor(
                        activity.activity_type
                      )}`}
                    >
                      {getActivityIcon(activity.activity_type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0 pb-4">
                      <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900 truncate">
                              {activity.description}
                            </p>
                            <p className="text-xs text-gray-600 mt-1">
                              by{' '}
                              <span className="font-medium">
                                {activity.user.full_name}
                              </span>
                            </p>
                          </div>
                          <span className="text-xs text-gray-500 whitespace-nowrap">
                            {formatDistanceToNow(new Date(activity.timestamp), {
                              addSuffix: true,
                            })}
                          </span>
                        </div>

                        {/* Metadata */}
                        {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-3">
                            {Object.entries(activity.metadata)
                              .slice(0, 3)
                              .map(([key, value]) => (
                                <span
                                  key={key}
                                  className="px-2 py-1 text-xs bg-white rounded border border-gray-200 text-gray-600"
                                >
                                  <span className="font-medium">{key}:</span>{' '}
                                  {String(value)}
                                </span>
                              ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* Load More Button */}
            {hasMore && onLoadMore && (
              <motion.div
                className="mt-6 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <button
                  onClick={onLoadMore}
                  className="px-4 py-2 text-sm font-medium text-azure-600 hover:text-azure-700 hover:bg-azure-50 rounded-lg transition-colors"
                >
                  Load more activities
                </button>
              </motion.div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            <div className="text-center">
              <FiActivity className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="text-lg font-medium">No activities found</p>
              <p className="text-sm mt-1">
                {filter === 'all'
                  ? 'No recent activity to display'
                  : 'No activities match the selected filter'}
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

/**
 * Format activity type for display
 */
function formatActivityType(type: string): string {
  return type
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default React.memo(UserActivityTimeline);
