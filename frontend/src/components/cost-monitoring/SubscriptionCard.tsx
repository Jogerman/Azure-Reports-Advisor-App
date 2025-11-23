import React from 'react';
import { Link } from 'react-router-dom';
import { AzureSubscription } from '../../types/costMonitoring';

interface SubscriptionCardProps {
  subscription: AzureSubscription;
  onSync?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  subscription,
  onSync,
  onEdit,
  onDelete,
}) => {
  const getStatusColor = (isActive: boolean) => {
    return isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  const getSyncFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      hourly: 'Every Hour',
      daily: 'Daily',
      weekly: 'Weekly',
    };
    return labels[frequency] || frequency;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Link
            to={`/cost-monitoring/subscriptions/${subscription.id}`}
            className="text-lg font-semibold text-gray-900 hover:text-blue-600"
          >
            {subscription.subscription_name}
          </Link>
          <p className="text-sm text-gray-500 mt-1">
            {subscription.subscription_id}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
            subscription.is_active
          )}`}
        >
          {subscription.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      {/* Details */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Client:</span>
          <span className="font-medium text-gray-900">{subscription.client_name}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Sync Frequency:</span>
          <span className="font-medium text-gray-900">
            {getSyncFrequencyLabel(subscription.sync_frequency)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Currency:</span>
          <span className="font-medium text-gray-900">{subscription.cost_currency}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Last Sync:</span>
          <span className="font-medium text-gray-900">
            {formatDate(subscription.last_sync)}
          </span>
        </div>
      </div>

      {/* Tags */}
      {subscription.tags && Object.keys(subscription.tags).length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {Object.entries(subscription.tags).slice(0, 3).map(([key, value]) => (
              <span
                key={key}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded"
              >
                {key}: {String(value)}
              </span>
            ))}
            {Object.keys(subscription.tags).length > 3 && (
              <span className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded">
                +{Object.keys(subscription.tags).length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t border-gray-200">
        {onSync && (
          <button
            onClick={() => onSync(subscription.id)}
            className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Sync Now
          </button>
        )}
        {onEdit && (
          <button
            onClick={() => onEdit(subscription.id)}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Edit
          </button>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(subscription.id)}
            className="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
};

export default SubscriptionCard;
