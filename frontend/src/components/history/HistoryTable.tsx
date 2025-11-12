import React from 'react';
import {
  FiChevronUp,
  FiChevronDown,
  FiDownload,
  FiEye,
  FiTrash2,
  FiMoreVertical,
  FiFileText,
} from 'react-icons/fi';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { Menu } from '@headlessui/react';
import { AnimatePresence, motion } from 'framer-motion';
import Card from '../common/Card';
import ReportStatusBadge from '../reports/ReportStatusBadge';
import { Report } from '../../services/reportService';
import { SortingState } from '../../types/history';

interface HistoryTableProps {
  reports: Report[];
  loading: boolean;
  sorting: SortingState;
  onSortChange: (field: string) => void;
  onDownload: (report: Report, format: 'html' | 'pdf') => void;
  onDelete: (report: Report) => void;
  onViewDetails: (report: Report) => void;
  currentUserRole: string;
}

const HistoryTable: React.FC<HistoryTableProps> = ({
  reports,
  loading,
  sorting,
  onSortChange,
  onDownload,
  onDelete,
  onViewDetails,
  currentUserRole,
}) => {
  // Format date
  const formatDate = (dateStr: string): string => {
    try {
      const date = parseISO(dateStr);
      return format(date, 'MMM dd, yyyy HH:mm');
    } catch {
      return dateStr;
    }
  };

  // Format relative time
  const formatRelativeTime = (dateStr: string): string => {
    try {
      const date = parseISO(dateStr);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return '';
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

  // Get report type label
  const getReportTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      cost: 'Cost',
      security: 'Security',
      operations: 'Operations',
      detailed: 'Detailed',
      executive: 'Executive',
    };
    return labels[type] || type;
  };

  // Render sort icon
  const renderSortIcon = (field: string) => {
    if (sorting.field !== field) {
      return <FiChevronUp className="w-4 h-4 text-gray-300" />;
    }
    return sorting.direction === 'asc' ? (
      <FiChevronUp className="w-4 h-4 text-azure-600" />
    ) : (
      <FiChevronDown className="w-4 h-4 text-azure-600" />
    );
  };

  // Loading skeleton
  if (loading) {
    return (
      <Card>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      </Card>
    );
  }

  // Empty state
  if (reports.length === 0) {
    return (
      <Card>
        <div className="py-12 text-center">
          <FiFileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No reports found</h3>
          <p className="text-sm text-gray-500">Try adjusting your filters or create a new report.</p>
        </div>
      </Card>
    );
  }

  return (
    <>
      {/* Desktop Table */}
      <Card padding="none" className="hidden lg:block overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => onSortChange('report_type')}
                >
                  <div className="flex items-center gap-2">
                    <span>Type</span>
                    {renderSortIcon('report_type')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => onSortChange('client_name')}
                >
                  <div className="flex items-center gap-2">
                    <span>Client</span>
                    {renderSortIcon('client_name')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => onSortChange('created_by')}
                >
                  <div className="flex items-center gap-2">
                    <span>User</span>
                    {renderSortIcon('created_by')}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => onSortChange('created_at')}
                >
                  <div className="flex items-center gap-2">
                    <span>Date</span>
                    {renderSortIcon('created_at')}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <AnimatePresence mode="popLayout">
                {reports.map((report) => (
                  <motion.tr
                    key={report.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900 capitalize">
                        {getReportTypeLabel(report.report_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {report.client_name || report.client_id}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600">{report.created_by_name || 'Unknown'}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDate(report.created_at)}</div>
                      <div className="text-xs text-gray-500">{formatRelativeTime(report.created_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <ReportStatusBadge status={report.status} size="sm" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatSize((report as any).total_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <ActionMenu
                        report={report}
                        onDownload={onDownload}
                        onDelete={onDelete}
                        onViewDetails={onViewDetails}
                        canDelete={currentUserRole === 'admin' || report.created_by === currentUserRole}
                      />
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </Card>

      {/* Mobile Card List */}
      <div className="lg:hidden space-y-4">
        <AnimatePresence mode="popLayout">
          {reports.map((report) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <Card hoverable onClick={() => onViewDetails(report)}>
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900 capitalize">
                        {getReportTypeLabel(report.report_type)} Report
                      </h3>
                      <p className="text-xs text-gray-600 mt-0.5">
                        {report.client_name || report.client_id}
                      </p>
                    </div>
                    <ReportStatusBadge status={report.status} size="sm" />
                  </div>

                  {/* Details */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500">User:</span>
                      <span className="ml-1 text-gray-900">{report.created_by_name || 'Unknown'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Size:</span>
                      <span className="ml-1 text-gray-900">
                        {formatSize((report as any).total_size)}
                      </span>
                    </div>
                  </div>

                  {/* Date */}
                  <div className="text-xs text-gray-500">
                    {formatDate(report.created_at)} • {formatRelativeTime(report.created_at)}
                  </div>

                  {/* Actions */}
                  <div className="pt-2 border-t border-gray-200">
                    <ActionMenu
                      report={report}
                      onDownload={onDownload}
                      onDelete={onDelete}
                      onViewDetails={onViewDetails}
                      canDelete={currentUserRole === 'admin' || report.created_by === currentUserRole}
                      mobile
                    />
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
};

// Action Menu Component
interface ActionMenuProps {
  report: Report;
  onDownload: (report: Report, format: 'html' | 'pdf') => void;
  onDelete: (report: Report) => void;
  onViewDetails: (report: Report) => void;
  canDelete: boolean;
  mobile?: boolean;
}

const ActionMenu: React.FC<ActionMenuProps> = ({
  report,
  onDownload,
  onDelete,
  onViewDetails,
  canDelete,
  mobile = false,
}) => {
  const isCompleted = report.status === 'completed';

  if (mobile) {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onViewDetails(report);
          }}
          className="flex-1 px-3 py-1.5 text-xs bg-azure-50 text-azure-700 rounded-md hover:bg-azure-100 transition-colors"
        >
          View Details
        </button>
        {isCompleted && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDownload(report, 'pdf');
            }}
            className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            Download
          </button>
        )}
      </div>
    );
  }

  return (
    <Menu as="div" className="relative inline-block text-left">
      <Menu.Button
        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
      >
        <FiMoreVertical className="w-5 h-5" />
      </Menu.Button>

      <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right bg-white divide-y divide-gray-100 rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
        <div className="p-1">
          <Menu.Item>
            {({ active }: { active: boolean }) => (
              <button
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onViewDetails(report);
                }}
                className={`${
                  active ? 'bg-gray-100' : ''
                } group flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 rounded-md transition-colors`}
              >
                <FiEye className="w-4 h-4" />
                View Details
              </button>
            )}
          </Menu.Item>

          {isCompleted && (
            <>
              <Menu.Item>
                {({ active }: { active: boolean }) => (
                  <button
                    onClick={(e: React.MouseEvent) => {
                      e.stopPropagation();
                      onDownload(report, 'html');
                    }}
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } group flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 rounded-md transition-colors`}
                  >
                    <FiDownload className="w-4 h-4" />
                    Download HTML
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }: { active: boolean }) => (
                  <button
                    onClick={(e: React.MouseEvent) => {
                      e.stopPropagation();
                      onDownload(report, 'pdf');
                    }}
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } group flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 rounded-md transition-colors`}
                  >
                    <FiDownload className="w-4 h-4" />
                    Download PDF
                  </button>
                )}
              </Menu.Item>
            </>
          )}
        </div>

        {canDelete && (
          <div className="p-1">
            <Menu.Item>
              {({ active }: { active: boolean }) => (
                <button
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    onDelete(report);
                  }}
                  className={`${
                    active ? 'bg-red-50' : ''
                  } group flex items-center gap-3 w-full px-3 py-2 text-sm text-red-600 rounded-md transition-colors`}
                >
                  <FiTrash2 className="w-4 h-4" />
                  Delete Report
                </button>
              )}
            </Menu.Item>
          </div>
        )}
      </Menu.Items>
    </Menu>
  );
};

export default React.memo(HistoryTable);
