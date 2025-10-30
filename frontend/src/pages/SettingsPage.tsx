import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FiSettings, FiUser, FiBell, FiShield, FiGlobe, FiUsers } from 'react-icons/fi';
import Card from '../components/common/Card';
import { useAuth } from '../hooks/useAuth';
import UserProfile from '../components/auth/UserProfile';
import UserManagement from '../components/settings/UserManagement';

const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'users'>('overview');

  // For now, show user management to all authenticated users
  // The backend will enforce permissions based on actual roles
  const isAdmin = !!user; // TODO: Update once we fetch user details from backend

  const settingsSections = [
    {
      icon: <FiUser className="w-5 h-5" />,
      title: 'Profile Settings',
      description: 'Manage your personal information and preferences',
      badge: 'Coming Soon',
    },
    {
      icon: <FiBell className="w-5 h-5" />,
      title: 'Notifications',
      description: 'Configure email and in-app notification preferences',
      badge: 'Coming Soon',
    },
    {
      icon: <FiShield className="w-5 h-5" />,
      title: 'Security',
      description: 'Manage authentication and security settings',
      badge: 'Coming Soon',
    },
    {
      icon: <FiGlobe className="w-5 h-5" />,
      title: 'Regional Settings',
      description: 'Set your timezone, language, and date format preferences',
      badge: 'Coming Soon',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">
          Manage your account settings and preferences.
        </p>
      </div>

      {/* Tabs (only show if admin) */}
      {isAdmin && (
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`${
                  activeTab === 'overview'
                    ? 'border-azure-500 text-azure-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <FiSettings className="mr-2" />
                Overview
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={`${
                  activeTab === 'users'
                    ? 'border-azure-500 text-azure-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <FiUsers className="mr-2" />
                User Management
              </button>
            </nav>
          </div>
        </div>
      )}

      {/* User Management Tab */}
      {activeTab === 'users' && isAdmin && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <UserManagement />
        </motion.div>
      )}

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* User Profile Card */}
          {user && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mb-8"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Profile</h2>
              <UserProfile user={user} size="lg" />
            </motion.div>
          )}

      {/* Settings Sections */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Settings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {settingsSections.map((section, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * (index + 3) }}
              whileHover={{ y: -4 }}
            >
              <Card>
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-azure-50 text-azure-600 rounded-lg flex items-center justify-center">
                      {section.icon}
                    </div>
                    {section.badge && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        {section.badge}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {section.title}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {section.description}
                  </p>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </motion.div>

          {/* Additional Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-8"
          >
            <Card>
              <div className="p-6 bg-azure-50">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-azure-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FiSettings className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      Advanced Settings Coming Soon
                    </h3>
                    <p className="text-sm text-gray-600">
                      Additional settings and customization options will be available in future updates.
                      This includes API access, webhook configurations, and advanced reporting preferences.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        </>
      )}
    </motion.div>
  );
};

export default SettingsPage;
