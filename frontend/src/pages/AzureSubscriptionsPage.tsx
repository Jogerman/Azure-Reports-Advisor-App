import React, { useState, useEffect } from 'react';
import { FiPlus, FiEdit, FiTrash2, FiRefreshCw, FiSearch, FiBarChart2, FiCheckCircle, FiXCircle, FiCircle } from 'react-icons/fi';
import { azureSubscriptionApi } from '../services/azureIntegrationApi';
import { AzureSubscription, AzureSubscriptionCreate, AzureSubscriptionUpdate, SYNC_STATUS_DISPLAY } from '../types/azureIntegration';
import AzureSubscriptionForm from '../components/azure/AzureSubscriptionForm';
import AzureStatisticsCard from '../components/azure/AzureStatisticsCard';
import Modal from '../components/common/Modal';
import ConfirmDialog from '../components/common/ConfirmDialog';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { showToast } from '../components/common/Toast';
import { format } from 'date-fns';

const AzureSubscriptionsPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<AzureSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [filterSyncStatus, setFilterSyncStatus] = useState<string>('');

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const [selectedSubscription, setSelectedSubscription] = useState<AzureSubscription | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [syncingIds, setSyncingIds] = useState<Set<string>>(new Set());

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (searchQuery) params.search = searchQuery;
      if (filterActive !== undefined) params.is_active = filterActive;

      const response = await azureSubscriptionApi.list(params);
      setSubscriptions(response.results);
    } catch (error) {
      showToast.error('Failed to load subscriptions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, [searchQuery, filterActive]);

  const handleAdd = async (data: AzureSubscriptionCreate | AzureSubscriptionUpdate) => {
    setIsSubmitting(true);
    try {
      await azureSubscriptionApi.create(data as AzureSubscriptionCreate);
      showToast.success('Azure subscription added successfully');
      setShowAddModal(false);
      fetchSubscriptions();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || 'Failed to add subscription');
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (data: AzureSubscriptionCreate | AzureSubscriptionUpdate) => {
    if (!selectedSubscription) return;

    setIsSubmitting(true);
    try {
      await azureSubscriptionApi.update(selectedSubscription.id, data as AzureSubscriptionUpdate);
      showToast.success('Azure subscription updated successfully');
      setShowEditModal(false);
      setSelectedSubscription(null);
      fetchSubscriptions();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || 'Failed to update subscription');
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedSubscription) return;

    try {
      await azureSubscriptionApi.delete(selectedSubscription.id);
      showToast.success('Azure subscription deleted successfully');
      setShowDeleteDialog(false);
      setSelectedSubscription(null);
      fetchSubscriptions();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || 'Failed to delete subscription');
    }
  };

  const handleSync = async (subscription: AzureSubscription) => {
    setSyncingIds(prev => new Set(prev).add(subscription.id));
    try {
      await azureSubscriptionApi.syncNow(subscription.id);
      showToast.success('Sync initiated successfully');
      // Refresh after a short delay to see updated status
      setTimeout(() => fetchSubscriptions(), 2000);
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || 'Failed to initiate sync');
    } finally {
      setSyncingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(subscription.id);
        return newSet;
      });
    }
  };

  const openEditModal = (subscription: AzureSubscription) => {
    setSelectedSubscription(subscription);
    setShowEditModal(true);
  };

  const openDeleteDialog = (subscription: AzureSubscription) => {
    setSelectedSubscription(subscription);
    setShowDeleteDialog(true);
  };

  const openStatsModal = (subscription: AzureSubscription) => {
    setSelectedSubscription(subscription);
    setShowStatsModal(true);
  };

  const filteredSubscriptions = subscriptions.filter(sub => {
    if (filterSyncStatus && sub.sync_status !== filterSyncStatus) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Azure Subscriptions</h1>
          <p className="mt-2 text-gray-600">
            Manage Azure subscriptions for automated report generation
          </p>
        </div>

        {/* Filters and Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Search */}
            <div className="flex-1 max-w-md">
              <div className="relative">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search by name or subscription ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-3">
              <select
                value={filterActive === undefined ? '' : filterActive.toString()}
                onChange={(e) => setFilterActive(e.target.value === '' ? undefined : e.target.value === 'true')}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
              >
                <option value="">All Status</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>

              <select
                value={filterSyncStatus}
                onChange={(e) => setFilterSyncStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
              >
                <option value="">All Sync Status</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="never_synced">Never Synced</option>
              </select>

              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-azure-600 text-white rounded-lg hover:bg-azure-700 focus:outline-none focus:ring-2 focus:ring-azure-500"
              >
                <FiPlus className="w-5 h-5" />
                <span>Add Subscription</span>
              </button>
            </div>
          </div>
        </div>

        {/* Subscriptions Table */}
        {loading ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
            <LoadingSpinner size="lg" text="Loading subscriptions..." />
          </div>
        ) : filteredSubscriptions.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <p className="text-gray-500">No Azure subscriptions found.</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-azure-600 text-white rounded-lg hover:bg-azure-700"
            >
              <FiPlus className="w-5 h-5" />
              <span>Add Your First Subscription</span>
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Subscription ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sync Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Sync
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredSubscriptions.map((subscription) => {
                    const syncStatus = SYNC_STATUS_DISPLAY[subscription.sync_status];
                    const isSyncing = syncingIds.has(subscription.id);

                    return (
                      <tr key={subscription.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{subscription.name}</div>
                          <div className="text-xs text-gray-500">
                            Created by {subscription.created_by.full_name}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 font-mono">{subscription.subscription_id}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
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
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`
                              inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium
                              ${syncStatus.color === 'green' ? 'bg-green-100 text-green-800' : ''}
                              ${syncStatus.color === 'red' ? 'bg-red-100 text-red-800' : ''}
                              ${syncStatus.color === 'gray' ? 'bg-gray-100 text-gray-800' : ''}
                            `}
                          >
                            <span>{syncStatus.icon}</span>
                            {syncStatus.label}
                          </span>
                          {subscription.sync_error_message && (
                            <div className="text-xs text-red-600 mt-1" title={subscription.sync_error_message}>
                              Error occurred
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {subscription.last_sync_at
                            ? format(new Date(subscription.last_sync_at), 'MMM dd, yyyy HH:mm')
                            : 'Never'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => openStatsModal(subscription)}
                              className="p-2 text-azure-600 hover:bg-azure-50 rounded-lg"
                              title="View statistics"
                            >
                              <FiBarChart2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleSync(subscription)}
                              disabled={isSyncing}
                              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                              title="Sync now"
                            >
                              <FiRefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                            </button>
                            <button
                              onClick={() => openEditModal(subscription)}
                              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                              title="Edit"
                            >
                              <FiEdit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => openDeleteDialog(subscription)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                              title="Delete"
                            >
                              <FiTrash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Add Modal */}
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add Azure Subscription"
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

        {/* Statistics Modal */}
        <Modal
          isOpen={showStatsModal}
          onClose={() => {
            setShowStatsModal(false);
            setSelectedSubscription(null);
          }}
          title="Subscription Statistics"
          size="xl"
        >
          {selectedSubscription && (
            <AzureStatisticsCard
              subscriptionId={selectedSubscription.id}
              subscriptionName={selectedSubscription.name}
              lastSyncAt={selectedSubscription.last_sync_at}
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
          onConfirm={handleDelete}
          title="Delete Azure Subscription"
          message={`Are you sure you want to delete "${selectedSubscription?.name}"? This action cannot be undone.`}
          confirmText="Delete"
          variant="danger"
        />
      </div>
    </div>
  );
};

export default AzureSubscriptionsPage;
