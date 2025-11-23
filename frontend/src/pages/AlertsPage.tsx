import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import costMonitoringApi from '../services/costMonitoringApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { showToast } from '../components/common/Toast';
import AlertList from '../components/cost-monitoring/AlertList';

const AlertsPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', statusFilter, severityFilter],
    queryFn: () =>
      costMonitoringApi.alerts.list({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      }),
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => costMonitoringApi.alerts.acknowledge(id),
    onSuccess: () => {
      showToast.success('Alert acknowledged successfully');
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
    onError: () => showToast.error('Failed to acknowledge alert'),
  });

  const resolveMutation = useMutation({
    mutationFn: (id: string) => costMonitoringApi.alerts.resolve(id),
    onSuccess: () => {
      showToast.success('Alert resolved successfully');
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
    onError: () => showToast.error('Failed to resolve alert'),
  });

  const handleAcknowledge = (id: string) => {
    acknowledgeMutation.mutate(id);
  };

  const handleResolve = (id: string) => {
    resolveMutation.mutate(id);
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Loading alerts..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Alerts</h1>
        <p className="mt-2 text-gray-600">
          View and manage cost monitoring alerts
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setStatusFilter('active')}
                className={`px-4 py-2 rounded-md font-medium ${
                  statusFilter === 'active'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setStatusFilter('acknowledged')}
                className={`px-4 py-2 rounded-md font-medium ${
                  statusFilter === 'acknowledged'
                    ? 'bg-yellow-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Acknowledged
              </button>
              <button
                onClick={() => setStatusFilter('resolved')}
                className={`px-4 py-2 rounded-md font-medium ${
                  statusFilter === 'resolved'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Resolved
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Severity
            </label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      {data && (
        <AlertList
          alerts={data.results}
          onAcknowledge={handleAcknowledge}
          onResolve={handleResolve}
        />
      )}
    </div>
  );
};

export default AlertsPage;
