import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiUsers,
  FiFileText,
  FiDollarSign,
  FiTrendingUp,
  FiArrowRight,
  FiCheckCircle,
  FiAlertCircle,
  FiClock,
} from 'react-icons/fi';
import Card from '../components/common/Card';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down';
  icon: React.ReactNode;
  color: 'azure' | 'green' | 'orange' | 'red';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, trend, icon, color }) => {
  const colorClasses = {
    azure: 'bg-azure-50 text-azure-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color]}`}>
              {icon}
            </div>
            {change && (
              <span className={`text-sm font-medium ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                {change}
              </span>
            )}
          </div>
          <h3 className="text-sm font-medium text-gray-500 mb-1">{title}</h3>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
      </Card>
    </motion.div>
  );
};

const Dashboard: React.FC = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants} className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">
          Welcome to Azure Advisor Reports Platform. Here's an overview of your reports and clients.
        </p>
      </motion.div>

      {/* Metrics Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Clients"
          value="0"
          change="+0%"
          trend="up"
          icon={<FiUsers className="w-6 h-6" />}
          color="azure"
        />
        <MetricCard
          title="Reports Generated"
          value="0"
          change="+0%"
          trend="up"
          icon={<FiFileText className="w-6 h-6" />}
          color="green"
        />
        <MetricCard
          title="Total Potential Savings"
          value="$0"
          icon={<FiDollarSign className="w-6 h-6" />}
          color="orange"
        />
        <MetricCard
          title="Active Reports"
          value="0"
          icon={<FiTrendingUp className="w-6 h-6" />}
          color="red"
        />
      </motion.div>

      {/* Welcome Card */}
      <motion.div variants={itemVariants} className="mb-8">
        <Card>
          <div className="p-8">
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-azure-500 to-azure-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <FiCheckCircle className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Welcome to Azure Advisor Reports Platform!
                </h2>
                <p className="text-gray-600 mb-6">
                  The core UI components are ready and functional. You can now navigate through the platform using the sidebar.
                  Start by adding clients and generating professional Azure Advisor reports.
                </p>
                <div className="flex flex-wrap gap-4">
                  <Link to="/clients">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="inline-flex items-center px-6 py-3 bg-azure-600 text-white font-medium rounded-lg shadow-sm hover:bg-azure-700 transition-colors"
                    >
                      <FiUsers className="mr-2" />
                      Manage Clients
                      <FiArrowRight className="ml-2" />
                    </motion.button>
                  </Link>
                  <Link to="/reports">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="inline-flex items-center px-6 py-3 bg-white text-gray-700 font-medium rounded-lg shadow-sm border border-gray-300 hover:bg-gray-50 transition-colors"
                    >
                      <FiFileText className="mr-2" />
                      Generate Reports
                      <FiArrowRight className="ml-2" />
                    </motion.button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Quick Actions Grid */}
      <motion.div variants={itemVariants}>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <Card>
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <FiClock className="w-5 h-5 text-azure-600" />
                <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                View your recent reports and activity history.
              </p>
              <Link
                to="/history"
                className="inline-flex items-center text-sm font-medium text-azure-600 hover:text-azure-700"
              >
                View History
                <FiArrowRight className="ml-1 w-4 h-4" />
              </Link>
            </div>
          </Card>

          {/* Upload CSV */}
          <Card>
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <FiFileText className="w-5 h-5 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">Upload CSV</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Upload Azure Advisor CSV to generate a new report.
              </p>
              <Link
                to="/reports"
                className="inline-flex items-center text-sm font-medium text-green-600 hover:text-green-700"
              >
                Upload Now
                <FiArrowRight className="ml-1 w-4 h-4" />
              </Link>
            </div>
          </Card>

          {/* System Status */}
          <Card>
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <FiAlertCircle className="w-5 h-5 text-orange-600" />
                <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                All systems operational. Platform ready for use.
              </p>
              <div className="inline-flex items-center text-sm font-medium text-gray-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Operational
              </div>
            </div>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Dashboard;
