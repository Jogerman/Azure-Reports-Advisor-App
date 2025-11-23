import React, { useState, useEffect } from 'react';
import { FiRefreshCw, FiTrendingDown } from 'react-icons/fi';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { azureSubscriptionApi } from '../../services/azureIntegrationApi';
import { AzureStatistics, AZURE_CATEGORY_COLORS, AZURE_IMPACT_COLORS } from '../../types/azureIntegration';
import LoadingSpinner from '../common/LoadingSpinner';
import { format } from 'date-fns';

interface AzureStatisticsCardProps {
  subscriptionId: string;
  subscriptionName: string;
  lastSyncAt: string | null;
}

const AzureStatisticsCard: React.FC<AzureStatisticsCardProps> = ({
  subscriptionId,
  subscriptionName,
  lastSyncAt,
}) => {
  const [statistics, setStatistics] = useState<AzureStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStatistics = async () => {
    try {
      setError(null);
      const stats = await azureSubscriptionApi.getStatistics(subscriptionId);
      setStatistics(stats);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load statistics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, [subscriptionId]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchStatistics();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <LoadingSpinner size="md" text="Loading statistics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-red-600">
          <p className="font-medium">Error loading statistics</p>
          <p className="text-sm mt-1">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-azure-600 text-white rounded-lg hover:bg-azure-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!statistics) {
    return null;
  }

  // Prepare data for category chart
  const categoryData = Object.entries(statistics.by_category).map(([name, value]) => ({
    name,
    value,
    color: AZURE_CATEGORY_COLORS[name as keyof typeof AZURE_CATEGORY_COLORS] || '#999',
  }));

  // Prepare data for impact chart
  const impactData = Object.entries(statistics.by_impact).map(([name, value]) => ({
    name,
    value,
    color: AZURE_IMPACT_COLORS[name as keyof typeof AZURE_IMPACT_COLORS] || '#999',
  }));

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Azure Recommendations</h3>
            <p className="text-sm text-gray-600 mt-1">{subscriptionName}</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 text-gray-600 hover:text-azure-600 hover:bg-azure-50 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Refresh statistics"
          >
            <FiRefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Total Recommendations */}
        <div className="mb-6">
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold text-gray-900">
              {statistics.total_recommendations.toLocaleString()}
            </span>
            <span className="text-sm text-gray-600">Total Recommendations</span>
          </div>
          {statistics.total_potential_savings !== undefined && statistics.total_potential_savings > 0 && (
            <div className="flex items-center gap-2 mt-2 text-green-600">
              <FiTrendingDown className="w-4 h-4" />
              <span className="text-sm font-medium">
                Potential Savings: {statistics.currency || '$'}
                {statistics.total_potential_savings.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          )}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* By Category */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">By Category</h4>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, value }: any) => value > 0 ? `${name}: ${value}` : ''}
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => (
                    <span className="text-xs text-gray-700">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* By Impact */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">By Impact Level</h4>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={impactData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, value }: any) => value > 0 ? `${name}: ${value}` : ''}
                >
                  {impactData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => (
                    <span className="text-xs text-gray-700">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Last Sync */}
        {lastSyncAt && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Last synced: {format(new Date(lastSyncAt), 'MMM dd, yyyy HH:mm:ss')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AzureStatisticsCard;
