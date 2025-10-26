import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { FiUser, FiTrendingUp, FiClock } from 'react-icons/fi';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { TopUser } from '../../types/analytics';
import { formatDistanceToNow } from 'date-fns';

export interface TopUsersTableProps {
  users: TopUser[];
  loading: boolean;
}

/**
 * Top Users Table Component
 * Displays top users by report count
 */
const TopUsersTable: React.FC<TopUsersTableProps> = ({ users, loading }) => {
  const [sortBy, setSortBy] = useState<'reports' | 'activity'>('reports');

  // Sort users
  const sortedUsers = useMemo(() => {
    const sorted = [...users];
    if (sortBy === 'reports') {
      sorted.sort((a, b) => b.reports_count - a.reports_count);
    } else {
      sorted.sort((a, b) =>
        new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()
      );
    }
    return sorted.slice(0, 10); // Top 10
  }, [users, sortBy]);

  // Get initials from name
  const getInitials = (fullName: string): string => {
    const names = fullName.split(' ');
    if (names.length >= 2) {
      return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
    }
    return fullName.slice(0, 2).toUpperCase();
  };

  // Get role badge color
  const getRoleBadgeColor = (role: string): string => {
    const roleLower = role.toLowerCase();
    if (roleLower.includes('admin')) return 'bg-danger-100 text-danger-700';
    if (roleLower.includes('manager')) return 'bg-azure-100 text-azure-700';
    if (roleLower.includes('analyst')) return 'bg-info-100 text-info-700';
    return 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <Card>
        <div className="p-6">
          <SkeletonLoader variant="text" width="200px" height="24px" className="mb-2" />
          <SkeletonLoader variant="text" width="300px" height="16px" className="mb-6" />
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <SkeletonLoader key={i} variant="rectangular" width="100%" height="60px" />
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Top Users</h3>
            <p className="text-sm text-gray-600 mt-1">Most active report generators</p>
          </div>

          {/* Sort Toggle */}
          <div className="inline-flex rounded-lg border border-gray-200 p-1">
            <button
              onClick={() => setSortBy('reports')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${
                sortBy === 'reports'
                  ? 'bg-azure-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <FiTrendingUp className="w-4 h-4" />
              Most Reports
            </button>
            <button
              onClick={() => setSortBy('activity')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${
                sortBy === 'activity'
                  ? 'bg-azure-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <FiClock className="w-4 h-4" />
              Most Recent
            </button>
          </div>
        </div>

        {sortedUsers.length > 0 ? (
          <div className="space-y-3">
            {sortedUsers.map((user, index) => (
              <motion.div
                key={user.id}
                className="flex items-center gap-4 p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                {/* Rank */}
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                    index === 0
                      ? 'bg-warning-500 text-white'
                      : index === 1
                      ? 'bg-gray-400 text-white'
                      : index === 2
                      ? 'bg-warning-700 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {index + 1}
                </div>

                {/* Avatar */}
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-azure-600 text-white font-semibold text-sm">
                  {getInitials(user.full_name)}
                </div>

                {/* User Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-semibold text-gray-900 truncate">
                      {user.full_name}
                    </p>
                    <span
                      className={`px-2 py-0.5 text-xs font-medium rounded-full ${getRoleBadgeColor(
                        user.role
                      )}`}
                    >
                      {user.role}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 truncate">@{user.username}</p>
                </div>

                {/* Stats */}
                <div className="text-right">
                  <div className="flex items-center gap-1 text-azure-600 font-bold text-lg">
                    <FiTrendingUp className="w-4 h-4" />
                    <span>{user.reports_count}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {formatDistanceToNow(new Date(user.last_activity), { addSuffix: true })}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            <div className="text-center">
              <FiUser className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="text-lg font-medium">No users found</p>
              <p className="text-sm mt-1">No user activity for the selected period</p>
            </div>
          </div>
        )}

        {/* Desktop Table View (hidden on mobile) */}
        <div className="hidden lg:block mt-6">
          <div className="overflow-hidden border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reports
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Activity
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedUsers.map((user, index) => (
                  <motion.tr
                    key={user.id}
                    className="hover:bg-gray-50 transition-colors"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-bold text-xs ${
                          index === 0
                            ? 'bg-warning-500 text-white'
                            : index === 1
                            ? 'bg-gray-400 text-white'
                            : index === 2
                            ? 'bg-warning-700 text-white'
                            : 'bg-gray-200 text-gray-700'
                        }`}
                      >
                        {index + 1}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-azure-600 text-white font-semibold text-xs">
                          {getInitials(user.full_name)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
                          <p className="text-xs text-gray-500">@{user.username}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(
                          user.role
                        )}`}
                      >
                        {user.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <span className="text-sm font-semibold text-azure-600">
                        {user.reports_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-500">
                      {formatDistanceToNow(new Date(user.last_activity), { addSuffix: true })}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default React.memo(TopUsersTable);
