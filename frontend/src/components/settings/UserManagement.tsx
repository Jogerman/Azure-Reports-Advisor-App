import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiUsers,
  FiEdit2,
  FiTrash2,
  FiCheck,
  FiX,
  FiShield,
  FiRefreshCw,
} from 'react-icons/fi';
import Card from '../common/Card';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import { showToast } from '../common/Toast';
import userService, { User } from '../../services/userService';
import { useAuth } from '../../hooks/useAuth';

const UserManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<{ [key: number]: boolean }>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [stats, setStats] = useState({
    total_users: 0,
    active_users: 0,
    inactive_users: 0,
  });

  const roles = [
    { value: 'admin', label: 'Administrator', color: 'bg-red-100 text-red-800' },
    { value: 'manager', label: 'Manager', color: 'bg-blue-100 text-blue-800' },
    { value: 'analyst', label: 'Analyst', color: 'bg-green-100 text-green-800' },
    { value: 'viewer', label: 'Viewer', color: 'bg-gray-100 text-gray-800' },
  ];

  useEffect(() => {
    fetchUsers();
    fetchStatistics();
  }, [roleFilter]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getUsers({
        role: roleFilter || undefined,
        search: searchTerm || undefined,
      });
      setUsers(response.results);
    } catch (error) {
      console.error('Error fetching users:', error);
      showToast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const stats = await userService.getUserStatistics();
      setStats(stats);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const handleSearch = () => {
    fetchUsers();
  };

  const handleChangeRole = async (userId: number, newRole: string) => {
    if (userId === Number(currentUser?.id)) {
      showToast.warning('You cannot change your own role');
      return;
    }

    try {
      setActionLoading((prev) => ({ ...prev, [userId]: true }));
      await userService.changeUserRole(userId, newRole);
      showToast.success('User role updated successfully');
      fetchUsers();
      fetchStatistics();
    } catch (error) {
      console.error('Error changing role:', error);
      showToast.error('Failed to update user role');
    } finally {
      setActionLoading((prev) => ({ ...prev, [userId]: false }));
    }
  };

  const handleToggleActive = async (user: User) => {
    if (user.id === Number(currentUser?.id)) {
      showToast.warning('You cannot deactivate your own account');
      return;
    }

    try {
      setActionLoading((prev) => ({ ...prev, [user.id]: true }));
      if (user.is_active) {
        await userService.deactivateUser(user.id);
        showToast.success('User deactivated successfully');
      } else {
        await userService.activateUser(user.id);
        showToast.success('User activated successfully');
      }
      fetchUsers();
      fetchStatistics();
    } catch (error) {
      console.error('Error toggling user status:', error);
      showToast.error('Failed to update user status');
    } finally {
      setActionLoading((prev) => ({ ...prev, [user.id]: false }));
    }
  };

  const getRoleColor = (role: string) => {
    const roleConfig = roles.find((r) => r.value === role);
    return roleConfig?.color || 'bg-gray-100 text-gray-800';
  };

  const getRoleLabel = (role: string) => {
    const roleConfig = roles.find((r) => r.value === role);
    return roleConfig?.label || role;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Users</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats.total_users}
                </p>
              </div>
              <div className="w-12 h-12 bg-azure-100 rounded-lg flex items-center justify-center">
                <FiUsers className="w-6 h-6 text-azure-600" />
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Users</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {stats.active_users}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <FiCheck className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Inactive Users</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {stats.inactive_users}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <FiX className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Users
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search by name or email..."
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-azure-500"
                />
                <Button onClick={handleSearch}>
                  Search
                </Button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Role
              </label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-azure-500"
              >
                <option value="">All Roles</option>
                {roles.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </Card>

      {/* Users Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <AnimatePresence>
                {users.map((user) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-azure-100 flex items-center justify-center">
                            <span className="text-azure-600 font-medium text-sm">
                              {user.first_name?.[0] || user.email[0].toUpperCase()}
                              {user.last_name?.[0] || ''}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.full_name}
                            {user.is_superuser && (
                              <FiShield className="inline ml-2 text-red-500" />
                            )}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={user.role}
                        onChange={(e) => handleChangeRole(user.id, e.target.value)}
                        disabled={actionLoading[user.id] || user.id === Number(currentUser?.id)}
                        className={`text-xs font-medium rounded-full px-3 py-1 ${getRoleColor(
                          user.role
                        )} border-0 focus:ring-2 focus:ring-azure-500 disabled:opacity-50`}
                      >
                        {roles.map((role) => (
                          <option key={role.value} value={role.value}>
                            {role.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleToggleActive(user)}
                        disabled={actionLoading[user.id] || user.id === Number(currentUser?.id)}
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                          user.is_active
                            ? 'bg-green-100 text-green-800 hover:bg-green-200'
                            : 'bg-red-100 text-red-800 hover:bg-red-200'
                        } disabled:opacity-50 transition-colors`}
                      >
                        {actionLoading[user.id] ? (
                          <FiRefreshCw className="w-3 h-3 animate-spin mr-1" />
                        ) : user.is_active ? (
                          <FiCheck className="w-3 h-3 mr-1" />
                        ) : (
                          <FiX className="w-3 h-3 mr-1" />
                        )}
                        {user.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.last_login
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          className="text-azure-600 hover:text-azure-900 disabled:opacity-50"
                          disabled={actionLoading[user.id]}
                        >
                          <FiEdit2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>

          {users.length === 0 && (
            <div className="text-center py-12">
              <FiUsers className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filter criteria.
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default UserManagement;
