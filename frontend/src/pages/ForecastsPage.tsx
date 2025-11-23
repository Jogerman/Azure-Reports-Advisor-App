import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import costMonitoringApi from '../services/costMonitoringApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { CostForecast } from '../types/costMonitoring';

const ForecastsPage: React.FC = () => {
  const [selectedSubscription, setSelectedSubscription] = useState<string>('');

  const { data: subscriptions } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => costMonitoringApi.subscriptions.list({ is_active: true }),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['forecasts', selectedSubscription],
    queryFn: () =>
      costMonitoringApi.forecasts.list({
        subscription: selectedSubscription || undefined,
      }),
    enabled: !!selectedSubscription,
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Cost Forecasts</h1>
        <p className="mt-2 text-gray-600">
          View AI-powered cost predictions for your Azure subscriptions
        </p>
      </div>

      {/* Subscription Selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Subscription
        </label>
        <select
          value={selectedSubscription}
          onChange={(e) => setSelectedSubscription(e.target.value)}
          className="w-full md:w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Choose a subscription...</option>
          {subscriptions?.results.map((sub) => (
            <option key={sub.id} value={sub.id}>
              {sub.subscription_name}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {!selectedSubscription ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg
              className="mx-auto h-16 w-16"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Select a subscription
          </h3>
          <p className="text-gray-500">
            Choose a subscription from the dropdown to view cost forecasts
          </p>
        </div>
      ) : isLoading ? (
        <LoadingSpinner fullScreen text="Loading forecasts..." />
      ) : data && data.results.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Predicted Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Accuracy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actual
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.results.map((forecast: CostForecast) => (
                <tr key={forecast.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(forecast.forecast_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${parseFloat(forecast.predicted_cost).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {forecast.lower_bound && forecast.upper_bound ? (
                      <>
                        ${parseFloat(forecast.lower_bound).toLocaleString()} -{' '}
                        ${parseFloat(forecast.upper_bound).toLocaleString()}
                      </>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {forecast.model_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {forecast.accuracy_percentage ? (
                      <span
                        className={`font-medium ${
                          forecast.accuracy_percentage >= 80
                            ? 'text-green-600'
                            : forecast.accuracy_percentage >= 60
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {forecast.accuracy_percentage.toFixed(1)}%
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {forecast.actual_cost ? (
                      <div>
                        <div className="font-medium text-gray-900">
                          ${parseFloat(forecast.actual_cost).toLocaleString()}
                        </div>
                        {forecast.prediction_error && (
                          <div className="text-xs text-gray-500">
                            Error: $
                            {parseFloat(forecast.prediction_error).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No forecasts available
          </h3>
          <p className="text-gray-500">
            Generate forecasts for this subscription to see predictions
          </p>
        </div>
      )}
    </div>
  );
};

export default ForecastsPage;
