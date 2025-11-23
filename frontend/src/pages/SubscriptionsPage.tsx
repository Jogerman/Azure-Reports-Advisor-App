import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import costMonitoringApi from '../services/costMonitoringApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { showToast } from '../components/common/Toast';
import SubscriptionCard from '../components/cost-monitoring/SubscriptionCard';
import { CreateAzureSubscription } from '../types/costMonitoring';

const SubscriptionsPage: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => costMonitoringApi.subscriptions.list(),
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => costMonitoringApi.subscriptions.syncCosts(id),
    onSuccess: () => {
      showToast.success('Cost sync initiated successfully');
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
    onError: () => showToast.error('Failed to sync costs'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => costMonitoringApi.subscriptions.delete(id),
    onSuccess: () => {
      showToast.success('Subscription deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
    onError: () => showToast.error('Failed to delete subscription'),
  });

  const handleSync = (id: string) => {
    syncMutation.mutate(id);
  };

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this subscription?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Loading subscriptions..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Azure Subscriptions</h1>
          <p className="mt-2 text-gray-600">
            Manage Azure subscriptions for cost monitoring
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
        >
          + Add Subscription
        </button>
      </div>

      {/* Subscriptions Grid */}
      {data && data.results.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.results.map((subscription) => (
            <SubscriptionCard
              key={subscription.id}
              subscription={subscription}
              onSync={handleSync}
              onDelete={handleDelete}
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
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No subscriptions configured
          </h3>
          <p className="text-gray-500 mb-6">
            Get started by adding your first Azure subscription
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
          >
            Add Your First Subscription
          </button>
        </div>
      )}
    </div>
  );
};

export default SubscriptionsPage;
