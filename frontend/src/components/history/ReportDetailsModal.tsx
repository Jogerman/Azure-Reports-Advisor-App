import React from 'react';
import { FiDownload, FiEye, FiFileText, FiFile, FiAlertCircle } from 'react-icons/fi';
import { format, parseISO, differenceInSeconds } from 'date-fns';
import Modal from '../common/Modal';
import ReportStatusBadge from '../reports/ReportStatusBadge';
import { Report } from '../../services/reportService';

interface ReportDetailsModalProps {
  report: Report | null;
  isOpen: boolean;
  onClose: () => void;
  onDownload: (report: Report, format: 'html' | 'pdf') => void;
}

const ReportDetailsModal: React.FC<ReportDetailsModalProps> = ({
  report,
  isOpen,
  onClose,
  onDownload,
}) => {
  if (!report) return null;

  // Format date
  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return '-';
    try {
      const date = parseISO(dateStr);
      return format(date, 'PPpp');
    } catch {
      return dateStr;
    }
  };

  // Format file size
  const formatSize = (bytes?: number): string => {
    if (!bytes) return '-';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  // Calculate duration
  const calculateDuration = (): string => {
    if (!report.processing_started_at || !report.processing_completed_at) return '-';
    try {
      const start = parseISO(report.processing_started_at);
      const end = parseISO(report.processing_completed_at);
      const seconds = differenceInSeconds(end, start);

      if (seconds < 60) return `${seconds}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds}s`;
    } catch {
      return '-';
    }
  };

  // Get report type label
  const getReportTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      cost: 'Cost Optimization',
      security: 'Security',
      operations: 'Operational Excellence',
      detailed: 'Detailed Analysis',
      executive: 'Executive Summary',
    };
    return labels[type] || type;
  };

  const isCompleted = report.status === 'completed';
  const isFailed = report.status === 'failed';

  // Extract metrics from analysis_data if available
  const metrics = report.analysis_data?.summary;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Report Details"
      size="lg"
    >
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex items-start justify-between pb-4 border-b border-gray-200">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 capitalize mb-2">
              {getReportTypeLabel(report.report_type)}
            </h3>
            <div className="flex items-center gap-2">
              <ReportStatusBadge status={report.status} size="md" />
            </div>
          </div>
        </div>

        {/* General Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">General Information</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InfoItem label="Client" value={report.client_name || report.client_id} />
            <InfoItem label="Created By" value={report.created_by || 'System'} />
            <InfoItem label="Created At" value={formatDate(report.created_at)} />
            <InfoItem label="Completed At" value={formatDate(report.processing_completed_at)} />
            <InfoItem label="Duration" value={calculateDuration()} />
            <InfoItem label="Report ID" value={report.id} mono />
          </div>
        </div>

        {/* Files Section */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Generated Files</h4>
          <div className="space-y-2">
            {/* CSV File */}
            <FileItem
              icon={<FiFile className="w-4 h-4" />}
              label="CSV Input"
              filename={report.csv_file?.split('/').pop() || 'advisor-export.csv'}
              size={formatSize((report as any).csv_size)}
              available={!!report.csv_file}
              onDownload={() => {
                // CSV download would need a separate endpoint
                console.log('Download CSV:', report.csv_file);
              }}
              showDownload={false} // CSV download not implemented in this modal
            />

            {/* HTML File */}
            <FileItem
              icon={<FiFileText className="w-4 h-4" />}
              label="HTML Report"
              filename={report.html_file?.split('/').pop() || 'report.html'}
              size={formatSize((report as any).html_size)}
              available={!!report.html_file && isCompleted}
              onDownload={() => onDownload(report, 'html')}
              onView={() => onDownload(report, 'html')} // HTML opens in new tab
              showView
            />

            {/* PDF File */}
            <FileItem
              icon={<FiFileText className="w-4 h-4" />}
              label="PDF Report"
              filename={report.pdf_file?.split('/').pop() || 'report.pdf'}
              size={formatSize((report as any).pdf_size)}
              available={!!report.pdf_file && isCompleted}
              onDownload={() => onDownload(report, 'pdf')}
            />
          </div>
        </div>

        {/* Metrics Section (if completed) */}
        {isCompleted && metrics && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Report Metrics</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {metrics.total_recommendations !== undefined && (
                <MetricCard
                  label="Total Recommendations"
                  value={metrics.total_recommendations.toLocaleString()}
                  color="azure"
                />
              )}
              {metrics.potential_savings !== undefined && (
                <MetricCard
                  label="Potential Savings"
                  value={`$${metrics.potential_savings.toLocaleString()}`}
                  color="success"
                />
              )}
              {metrics.high_impact !== undefined && (
                <MetricCard
                  label="High Impact"
                  value={metrics.high_impact.toLocaleString()}
                  color="danger"
                />
              )}
              {metrics.medium_impact !== undefined && (
                <MetricCard
                  label="Medium Impact"
                  value={metrics.medium_impact.toLocaleString()}
                  color="warning"
                />
              )}
              {metrics.low_impact !== undefined && (
                <MetricCard
                  label="Low Impact"
                  value={metrics.low_impact.toLocaleString()}
                  color="info"
                />
              )}
            </div>
          </div>
        )}

        {/* Error Message (if failed) */}
        {isFailed && report.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <FiAlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-red-900 mb-1">Error Details</h4>
                <p className="text-sm text-red-700 whitespace-pre-wrap">{report.error_message}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

// Info Item Component
interface InfoItemProps {
  label: string;
  value: string;
  mono?: boolean;
}

const InfoItem: React.FC<InfoItemProps> = ({ label, value, mono = false }) => (
  <div>
    <dt className="text-xs font-medium text-gray-500 mb-1">{label}</dt>
    <dd className={`text-sm text-gray-900 ${mono ? 'font-mono text-xs' : ''}`}>{value}</dd>
  </div>
);

// File Item Component
interface FileItemProps {
  icon: React.ReactNode;
  label: string;
  filename: string;
  size: string;
  available: boolean;
  onDownload?: () => void;
  onView?: () => void;
  showDownload?: boolean;
  showView?: boolean;
}

const FileItem: React.FC<FileItemProps> = ({
  icon,
  label,
  filename,
  size,
  available,
  onDownload,
  onView,
  showDownload = true,
  showView = false,
}) => (
  <div
    className={`flex items-center justify-between p-3 rounded-lg border ${
      available
        ? 'bg-gray-50 border-gray-200'
        : 'bg-gray-100 border-gray-200 opacity-60'
    }`}
  >
    <div className="flex items-center gap-3 flex-1 min-w-0">
      <div className={`flex-shrink-0 ${available ? 'text-gray-700' : 'text-gray-400'}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{filename}</p>
        <p className="text-xs text-gray-500">{label} • {size}</p>
      </div>
    </div>

    {available && (
      <div className="flex items-center gap-2 ml-3">
        {showView && onView && (
          <button
            onClick={onView}
            className="p-2 text-azure-600 hover:bg-azure-50 rounded-md transition-colors"
            title="View in browser"
          >
            <FiEye className="w-4 h-4" />
          </button>
        )}
        {showDownload && onDownload && (
          <button
            onClick={onDownload}
            className="p-2 text-azure-600 hover:bg-azure-50 rounded-md transition-colors"
            title="Download file"
          >
            <FiDownload className="w-4 h-4" />
          </button>
        )}
      </div>
    )}

    {!available && (
      <span className="text-xs text-gray-400 ml-3">Not available</span>
    )}
  </div>
);

// Metric Card Component
interface MetricCardProps {
  label: string;
  value: string;
  color: 'azure' | 'success' | 'danger' | 'warning' | 'info';
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, color }) => {
  const colorClasses = {
    azure: 'bg-azure-50 text-azure-700 border-azure-200',
    success: 'bg-success-50 text-success-700 border-success-200',
    danger: 'bg-danger-50 text-danger-700 border-danger-200',
    warning: 'bg-warning-50 text-warning-700 border-warning-200',
    info: 'bg-info-50 text-info-700 border-info-200',
  };

  return (
    <div className={`p-3 rounded-lg border ${colorClasses[color]}`}>
      <p className="text-xs font-medium opacity-75 mb-1">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
};

export default ReportDetailsModal;
