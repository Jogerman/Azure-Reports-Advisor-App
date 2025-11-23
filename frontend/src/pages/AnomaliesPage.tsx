import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import costMonitoringApi from '../services/costMonitoringApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { showToast } from '../components/common/Toast';
import AnomalyCard from '../components/cost-monitoring/AnomalyCard';

const AnomaliesPage: React.FC = () => {
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['anomalies', showAcknowledged],
    queryFn: () =>
      costMonitoringApi.anomalies.list({
        is_acknowledged: showAcknowledged ? undefined : false,
      }),
  });

  const acknowledgeMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      costMonitoringApi.anomalies.acknowledge(id, notes),
    onSuccess: () => {
      showToast.success('Anomaly acknowledged successfully');
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
    },
    onError: () => showToast.error('Failed to acknowledge anomaly'),
  });

  const handleAcknowledge = (id: string, notes?: string) => {
    acknowledgeMutation.mutate({ id, notes });
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Loading anomalies..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Cost Anomalies</h1>
        <p className="mt-2 text-gray-600">
          Review detected anomalies in your Azure spending
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">
              Show acknowledged anomalies
            </span>
          </label>
        </div>
      </div>

      {/* Anomalies Grid */}
      {data && data.results.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {data.results.map((anomaly) => (
            <AnomalyCard
              key={anomaly.id}
              anomaly={anomaly}
              onAcknowledge={handleAcknowledge}
            />
          ))}
        </div>
      ) : (
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
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No anomalies detected
          </h3>
          <p className="text-gray-500">
            {showAcknowledged
              ? 'There are no acknowledged anomalies'
              : 'No unusual cost patterns have been detected'}
          </p>
        </div>
      )}
    </div>
  );
};

export default AnomaliesPage;
