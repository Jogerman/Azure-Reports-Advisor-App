import React from 'react';
import { Link } from 'react-router-dom';
import { CostAnomaly } from '../../types/costMonitoring';

interface AnomalyCardProps {
  anomaly: CostAnomaly;
  onAcknowledge?: (id: string, notes?: string) => void;
}

const AnomalyCard: React.FC<AnomalyCardProps> = ({ anomaly, onAcknowledge }) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-red-600';
    if (confidence >= 0.6) return 'text-orange-600';
    return 'text-yellow-600';
  };

  const getDetectionMethodLabel = (method: string) => {
    const labels: Record<string, string> = {
      zscore: 'Z-Score',
      iqr: 'IQR',
      moving_avg: 'Moving Average',
      isolation_forest: 'Isolation Forest',
    };
    return labels[method] || method;
  };

  const deviation = parseFloat(anomaly.deviation_percentage);
  const isIncrease = deviation > 0;

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${
        anomaly.is_acknowledged ? 'border-gray-300' : 'border-red-500'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Link
              to={`/cost-monitoring/anomalies/${anomaly.id}`}
              className="text-lg font-semibold text-gray-900 hover:text-blue-600"
            >
              {anomaly.service_name || 'Total Cost'}
            </Link>
            {anomaly.is_acknowledged && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                Acknowledged
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500">
            {new Date(anomaly.date).toLocaleDateString()} •{' '}
            {anomaly.subscription_name}
          </p>
          {anomaly.resource_group && (
            <p className="text-xs text-gray-400 mt-1">
              Resource Group: {anomaly.resource_group}
            </p>
          )}
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${isIncrease ? 'text-red-600' : 'text-green-600'}`}>
            {isIncrease ? '+' : ''}
            {deviation.toFixed(1)}%
          </div>
          <p className="text-xs text-gray-500">Deviation</p>
        </div>
      </div>

      {/* Cost Comparison */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 rounded p-3">
          <p className="text-xs text-gray-600 mb-1">Expected Cost</p>
          <p className="text-lg font-semibold text-gray-900">
            ${parseFloat(anomaly.expected_cost).toLocaleString()}
          </p>
        </div>
        <div className="bg-red-50 rounded p-3">
          <p className="text-xs text-gray-600 mb-1">Actual Cost</p>
          <p className="text-lg font-semibold text-red-900">
            ${parseFloat(anomaly.actual_cost).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Detection Info */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-gray-600">Method: </span>
            <span className="font-medium text-gray-900">
              {getDetectionMethodLabel(anomaly.detection_method)}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Confidence: </span>
            <span className={`font-bold ${getConfidenceColor(anomaly.confidence)}`}>
              {(anomaly.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">Score: </span>
            <span className="font-medium text-gray-900">
              {anomaly.anomaly_score.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Notes if acknowledged */}
      {anomaly.is_acknowledged && anomaly.notes && (
        <div className="bg-gray-50 rounded p-3 mb-4">
          <p className="text-xs text-gray-600 mb-1">Notes:</p>
          <p className="text-sm text-gray-900">{anomaly.notes}</p>
          {anomaly.acknowledged_at && (
            <p className="text-xs text-gray-500 mt-2">
              Acknowledged by {anomaly.acknowledged_by_name} on{' '}
              {new Date(anomaly.acknowledged_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* Action */}
      {!anomaly.is_acknowledged && onAcknowledge && (
        <button
          onClick={() => {
            const notes = prompt('Add notes (optional):');
            onAcknowledge(anomaly.id, notes || undefined);
          }}
          className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Acknowledge Anomaly
        </button>
      )}
    </div>
  );
};

export default AnomalyCard;
