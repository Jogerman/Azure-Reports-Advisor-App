import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FiPlus,
  FiEdit,
  FiTrash2,
  FiRefreshCw,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiAlertCircle,
} from 'react-icons/fi';
import { format } from 'date-fns';
import { azureSubscriptionApi } from '../../services/azureIntegrationApi';
import { AzureSubscription, AzureSubscriptionCreate, AzureSubscriptionUpdate } from '../../types/azureIntegration';
import AzureSubscriptionForm from '../azure/AzureSubscriptionForm';
import { Button, Card, LoadingSpinner, Modal, ConfirmDialog, showToast } from '../common';

interface ClientAzureSubscriptionsProps {
  clientId: string;
  clientName: string;
}

const ClientAzureSubscriptions: React.FC<ClientAzureSubscriptionsProps> = ({ clientId, clientName }) => {
  const queryClient = useQueryClient();

  // State
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState<AzureSubscription | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [syncingIds, setSyncingIds] = useState<Set<string>>(new Set());

  // Fetch subscriptions for this client
  const { data: subscriptions = [], isLoading, refetch } = useQuery({
    queryKey: ['azure-subscriptions', clientId],
    queryFn: async () => {
      const response = await azureSubscriptionApi.list({ client: clientId });
      return response.results;
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: AzureSubscriptionCreate) => azureSubscriptionApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['azure-subscriptions', clientId] });
      queryClient.invalidateQueries({ queryKey: ['client', clientId] });
      showToast.success('Azure subscription added successfully');
      setShowAddModal(false);
    },
    onError: (error: any) => {
      showToast.error(error.response?.data?.detail || 'Failed to add subscription');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: AzureSubscriptionUpdate }) =>
      azureSubscriptionApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['azure-subscriptions', clientId] });
      showToast.success('Azure subscription updated successfully');
      setShowEditModal(false);
      setSelectedSubscription(null);
    },
    onError: (error: any) => {
      showToast.error(error.response?.data?.detail || 'Failed to update subscription');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => azureSubscriptionApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['azure-subscriptions', clientId] });
      queryClient.invalidateQueries({ queryKey: ['client', clientId] });
      showToast.success('Azure subscription deleted successfully');
      setShowDeleteDialog(false);
      setSelectedSubscription(null);
    },
    onError: (error: any) => {
      showToast.error(error.response?.data?.detail || 'Failed to delete subscription');
    },
  });

  // Sync mutation
  const handleSync = async (subscription: AzureSubscription) => {
    setSyncingIds((prev) => new Set(prev).add(subscription.id));
    try {
      await azureSubscriptionApi.syncNow(subscription.id);
      showToast.success('Sync initiated successfully');
      setTimeout(() => refetch(), 2000);
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || 'Failed to initiate sync');
    } finally {
      setSyncingIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(subscription.id);
        return newSet;
      });
    }
  };

  const handleAdd = async (data: AzureSubscriptionCreate | AzureSubscriptionUpdate) => {
    setIsSubmitting(true);
    try {
      await createMutation.mutateAsync({ ...data, client: clientId } as AzureSubscriptionCreate);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (data: AzureSubscriptionCreate | AzureSubscriptionUpdate) => {
    if (!selectedSubscription) return;
    setIsSubmitting(true);
    try {
      await updateMutation.mutateAsync({
        id: selectedSubscription.id,
        data: data as AzureSubscriptionUpdate,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSyncStatusBadge = (subscription: AzureSubscription) => {
    switch (subscription.sync_status) {
      case 'success':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <FiCheckCircle className="w-3 h-3" />
            Success
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <FiXCircle className="w-3 h-3" />
            Failed
          </span>
        );
      case 'never_synced':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <FiClock className="w-3 h-3" />
            Never Synced
          </span>
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center py-8">
          <LoadingSpinner text="Loading Azure subscriptions..." />
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Azure Subscriptions</h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage Azure API credentials for automated report generation
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          icon={<FiPlus />}
          onClick={() => setShowAddModal(true)}
        >
          Add Subscription
        </Button>
      </div>

      {subscriptions.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          <FiAlertCircle className="w-12 h-12 mx-auto text-gray-400 mb-3" />
          <p className="text-base font-medium mb-1">No Azure subscriptions configured</p>
          <p className="text-sm mb-4">
            Add Azure API credentials to enable automated report generation for {clientName}
          </p>
          <Button
            variant="primary"
            icon={<FiPlus />}
            onClick={() => setShowAddModal(true)}
          >
            Add Your First Subscription
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {subscriptions.map((subscription) => {
            const isSyncing = syncingIds.has(subscription.id);

            return (
              <div
                key={subscription.id}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-base font-semibold text-gray-900">
                        {subscription.name}
                      </h3>
                      {getSyncStatusBadge(subscription)}
                      {subscription.is_active ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <FiCheckCircle className="w-3 h-3" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          <FiXCircle className="w-3 h-3" />
                          Inactive
                        </span>
                      )}
                    </div>

                    <div className="space-y-1 text-sm text-gray-600">
                      <p>
                        <span className="font-medium">Subscription ID:</span>{' '}
                        <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                          {subscription.subscription_id}
                        </code>
                      </p>
                      {subscription.last_sync_at && (
                        <p>
                          <span className="font-medium">Last synced:</span>{' '}
                          {format(new Date(subscription.last_sync_at), 'MMM dd, yyyy HH:mm')}
                        </p>
                      )}
                      {subscription.sync_error_message && (
                        <p className="text-red-600">
                          <span className="font-medium">Error:</span> {subscription.sync_error_message}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleSync(subscription)}
                      disabled={isSyncing || !subscription.is_active}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Sync now"
                    >
                      <FiRefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                    </button>
                    <button
                      onClick={() => {
                        setSelectedSubscription(subscription);
                        setShowEditModal(true);
                      }}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                      title="Edit"
                    >
                      <FiEdit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        setSelectedSubscription(subscription);
                        setShowDeleteDialog(true);
                      }}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      title="Delete"
                    >
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title={`Add Azure Subscription for ${clientName}`}
        size="lg"
      >
        <AzureSubscriptionForm
          onSubmit={handleAdd}
          onCancel={() => setShowAddModal(false)}
          isSubmitting={isSubmitting}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedSubscription(null);
        }}
        title="Edit Azure Subscription"
        size="lg"
      >
        {selectedSubscription && (
          <AzureSubscriptionForm
            subscription={selectedSubscription}
            onSubmit={handleEdit}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedSubscription(null);
            }}
            isSubmitting={isSubmitting}
          />
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false);
          setSelectedSubscription(null);
        }}
        onConfirm={() => selectedSubscription && deleteMutation.mutate(selectedSubscription.id)}
        title="Delete Azure Subscription"
        message={`Are you sure you want to delete "${selectedSubscription?.name}"? This action cannot be undone and may affect report generation.`}
        confirmText="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </Card>
  );
};

export default ClientAzureSubscriptions;
