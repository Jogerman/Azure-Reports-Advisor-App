import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { FiDollarSign, FiAlertCircle, FiTrendingUp, FiPieChart } from 'react-icons/fi';
import reportService from '../../services/reportService';
import { Card, LoadingSpinner } from '../common';

interface ReportAnalyticsProps {
  reportId: string;
}

interface AnalyticsData {
  total_recommendations: number;
  recommendations_by_category: {
    [key: string]: number;
  };
  recommendations_by_impact: {
    [key: string]: number;
  };
  total_potential_savings: number;
  average_savings_per_recommendation: number;
  top_recommendation?: {
    category: string;
    impact: string;
    savings: number;
  };
}

interface Recommendation {
  id: string;
  category: string;
  business_impact: string;
  recommendation: string;
  resource_name: string;
  potential_savings: number;
  subscription_name: string;
}

const ReportAnalytics: React.FC<ReportAnalyticsProps> = ({ reportId }) => {
  // Fetch analytics data
  const { data: analyticsData, isLoading: loadingAnalytics } = useQuery<AnalyticsData>({
    queryKey: ['report-analytics', reportId],
    queryFn: async () => {
      const response = await reportService.getReportStatistics(reportId);
      return response;
    },
  });

  // Fetch recommendations
  const { data: recommendationsData, isLoading: loadingRecommendations } = useQuery<Recommendation[]>({
    queryKey: ['report-recommendations', reportId],
    queryFn: async () => {
      const response = await reportService.getReportRecommendations(reportId);
      return response;
    },
  });

  if (loadingAnalytics || loadingRecommendations) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" text="Loading analytics..." />
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-gray-600">No analytics data available</p>
        </div>
      </Card>
    );
  }

  const recommendations = recommendationsData || [];

  // Calculate category colors
  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      cost: 'text-green-600 bg-green-100',
      security: 'text-red-600 bg-red-100',
      reliability: 'text-blue-600 bg-blue-100',
      operational_excellence: 'text-purple-600 bg-purple-100',
      performance: 'text-orange-600 bg-orange-100',
    };
    return colors[category] || 'text-gray-600 bg-gray-100';
  };

  const getImpactBadge = (impact: string) => {
    const badges: { [key: string]: string } = {
      high: 'bg-red-100 text-red-800 border-red-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return badges[impact] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-azure-100 rounded-lg">
              <FiAlertCircle className="w-6 h-6 text-azure-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Recommendations</p>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.total_recommendations}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <FiDollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Potential Savings</p>
              <p className="text-2xl font-bold text-gray-900">
                ${(analyticsData.total_potential_savings || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <FiTrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Avg Savings</p>
              <p className="text-2xl font-bold text-gray-900">
                ${(analyticsData.average_savings_per_recommendation || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FiPieChart className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Categories</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(analyticsData.recommendations_by_category || {}).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Category Breakdown - Only show if data exists */}
      {Object.keys(analyticsData.recommendations_by_category || {}).length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Recommendations by Category
          </h3>
          <div className="space-y-3">
            {Object.entries(analyticsData.recommendations_by_category || {}).map(([category, count]) => {
              const percentage = (count / analyticsData.total_recommendations) * 100;
              return (
                <div key={category} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {category.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-600">
                      {count} ({percentage.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        category === 'cost' ? 'bg-green-500' :
                        category === 'security' ? 'bg-red-500' :
                        category === 'reliability' ? 'bg-blue-500' :
                        category === 'operational_excellence' ? 'bg-purple-500' :
                        'bg-orange-500'
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Impact Breakdown - Only show if data exists */}
      {Object.keys(analyticsData.recommendations_by_impact || {}).length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Recommendations by Impact Level
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(analyticsData.recommendations_by_impact || {}).map(([impact, count]) => {
              const percentage = (count / analyticsData.total_recommendations) * 100;
              return (
                <div key={impact} className="text-center p-4 border-2 border-gray-200 rounded-lg">
                  <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium capitalize mb-2 ${getImpactBadge(impact)}`}>
                    {impact} Impact
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-600">{percentage.toFixed(0)}% of total</p>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Top Recommendations */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Top Recommendations by Savings
        </h3>
        <div className="space-y-3">
          {recommendations
            .sort((a, b) => b.potential_savings - a.potential_savings)
            .slice(0, 5)
            .map((rec) => (
              <div key={rec.id} className="p-4 border border-gray-200 rounded-lg hover:border-azure-300 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`inline-flex px-2 py-1 rounded text-xs font-medium capitalize ${getCategoryColor(rec.category)}`}>
                        {rec.category.replace('_', ' ')}
                      </span>
                      <span className={`inline-flex px-2 py-1 rounded text-xs font-medium capitalize ${getImpactBadge(rec.business_impact)}`}>
                        {rec.business_impact}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-900 mb-1">{rec.resource_name}</p>
                    <p className="text-sm text-gray-600 line-clamp-2">{rec.recommendation}</p>
                    {rec.subscription_name && (
                      <p className="text-xs text-gray-500 mt-1">
                        Subscription: {rec.subscription_name}
                      </p>
                    )}
                  </div>
                  <div className="ml-4 text-right">
                    <p className="text-lg font-bold text-green-600">
                      ${(rec.potential_savings || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-xs text-gray-500">annual savings</p>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </Card>
    </div>
  );
};

export default ReportAnalytics;
