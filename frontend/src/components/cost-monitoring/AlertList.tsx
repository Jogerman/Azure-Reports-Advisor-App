import React from 'react';
import { Link } from 'react-router-dom';
import { Alert } from '../../types/costMonitoring';
import AlertBadge from './AlertBadge';

interface AlertListProps {
  alerts: Alert[];
  onAcknowledge?: (id: string) => void;
  onResolve?: (id: string) => void;
  showActions?: boolean;
}

const AlertList: React.FC<AlertListProps> = ({
  alerts,
  onAcknowledge,
  onResolve,
  showActions = true,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="text-gray-400 mb-2">
          <svg
            className="mx-auto h-12 w-12"
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
        <h3 className="text-lg font-medium text-gray-900 mb-1">No alerts</h3>
        <p className="text-gray-500">There are no alerts to display.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <ul className="divide-y divide-gray-200">
        {alerts.map((alert) => (
          <li key={alert.id} className="hover:bg-gray-50">
            <div className="px-6 py-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <AlertBadge type="severity" value={alert.severity} />
                    <AlertBadge type="type" value={alert.alert_type} />
                    <AlertBadge type="status" value={alert.status} />
                  </div>

                  {/* Title and Message */}
                  <Link
                    to={`/cost-monitoring/alerts/${alert.id}`}
                    className="block"
                  >
                    <h3 className="text-lg font-medium text-gray-900 hover:text-blue-600">
                      {alert.title}
                    </h3>
                    <p className="mt-1 text-sm text-gray-600">{alert.message}</p>
                  </Link>

                  {/* Metadata */}
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>{alert.subscription_name}</span>
                    {alert.triggered_value && (
                      <span>
                        Triggered: {alert.triggered_value}
                        {alert.threshold_value && ` (threshold: ${alert.threshold_value})`}
                      </span>
                    )}
                    <span>{formatDate(alert.created_at)}</span>
                  </div>

                  {/* Acknowledgment/Resolution Info */}
                  {alert.acknowledged_at && (
                    <div className="mt-2 text-xs text-gray-500">
                      Acknowledged by {alert.acknowledged_by_name} on{' '}
                      {new Date(alert.acknowledged_at).toLocaleString()}
                    </div>
                  )}
                  {alert.resolved_at && (
                    <div className="mt-2 text-xs text-gray-500">
                      Resolved by {alert.resolved_by_name} on{' '}
                      {new Date(alert.resolved_at).toLocaleString()}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {showActions && alert.status === 'active' && (
                  <div className="ml-4 flex flex-col gap-2">
                    {onAcknowledge && (
                      <button
                        onClick={() => onAcknowledge(alert.id)}
                        className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded hover:bg-yellow-200"
                      >
                        Acknowledge
                      </button>
                    )}
                    {onResolve && (
                      <button
                        onClick={() => onResolve(alert.id)}
                        className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded hover:bg-green-200"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                )}
                {showActions && alert.status === 'acknowledged' && onResolve && (
                  <div className="ml-4">
                    <button
                      onClick={() => onResolve(alert.id)}
                      className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded hover:bg-green-200"
                    >
                      Resolve
                    </button>
                  </div>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AlertList;
