import React from 'react';
import { FiClock, FiLoader, FiCheckCircle, FiXCircle } from 'react-icons/fi';
import { ReportStatus } from '../../services/reportService';

interface ReportStatusBadgeProps {
  status: ReportStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

const ReportStatusBadge: React.FC<ReportStatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const statusConfig: Record<ReportStatus, {
    label: string;
    icon: React.ReactNode;
    classes: string;
  }> = {
    pending: {
      label: 'Pending',
      icon: <FiClock className={iconSizes[size]} />,
      classes: 'bg-gray-100 text-gray-800 border border-gray-200',
    },
    uploaded: {
      label: 'Uploaded',
      icon: <FiCheckCircle className={iconSizes[size]} />,
      classes: 'bg-blue-100 text-blue-800 border border-blue-200',
    },
    processing: {
      label: 'Processing',
      icon: <FiLoader className={`${iconSizes[size]} animate-spin`} />,
      classes: 'bg-blue-100 text-blue-800 border border-blue-200',
    },
    generating: {
      label: 'Generating',
      icon: <FiLoader className={`${iconSizes[size]} animate-spin`} />,
      classes: 'bg-indigo-100 text-indigo-800 border border-indigo-200',
    },
    completed: {
      label: 'Completed',
      icon: <FiCheckCircle className={iconSizes[size]} />,
      classes: 'bg-green-100 text-green-800 border border-green-200',
    },
    failed: {
      label: 'Failed',
      icon: <FiXCircle className={iconSizes[size]} />,
      classes: 'bg-red-100 text-red-800 border border-red-200',
    },
    cancelled: {
      label: 'Cancelled',
      icon: <FiXCircle className={iconSizes[size]} />,
      classes: 'bg-gray-100 text-gray-800 border border-gray-300',
    },
  };

  const config = statusConfig[status] || {
    label: 'Unknown',
    icon: <FiClock className={iconSizes[size]} />,
    classes: 'bg-gray-100 text-gray-500 border border-gray-200',
  };

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-medium
        ${sizeClasses[size]}
        ${config.classes}
      `}
      aria-label={`Report status: ${config.label}`}
    >
      {showIcon && <span className="mr-1.5">{config.icon}</span>}
      {config.label}
    </span>
  );
};

export default ReportStatusBadge;
