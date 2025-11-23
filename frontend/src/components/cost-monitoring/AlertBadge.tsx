import React from 'react';
import { AlertSeverity, AlertStatus, AlertType } from '../../types/costMonitoring';

interface AlertBadgeProps {
  type: 'severity' | 'status' | 'type';
  value: AlertSeverity | AlertStatus | AlertType;
  className?: string;
}

const AlertBadge: React.FC<AlertBadgeProps> = ({ type, value, className = '' }) => {
  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: AlertStatus) => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'acknowledged':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'dismissed':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeColor = (alertType: AlertType) => {
    switch (alertType) {
      case 'threshold':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'anomaly':
        return 'bg-pink-100 text-pink-800 border-pink-200';
      case 'budget':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      case 'forecast':
        return 'bg-cyan-100 text-cyan-800 border-cyan-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getLabel = (val: string) => {
    return val.charAt(0).toUpperCase() + val.slice(1).replace('_', ' ');
  };

  let colorClass = '';
  if (type === 'severity') {
    colorClass = getSeverityColor(value as AlertSeverity);
  } else if (type === 'status') {
    colorClass = getStatusColor(value as AlertStatus);
  } else if (type === 'type') {
    colorClass = getTypeColor(value as AlertType);
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClass} ${className}`}
    >
      {getLabel(value)}
    </span>
  );
};

export default AlertBadge;
