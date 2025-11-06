import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  FiDownload,
  FiTrash2,
  FiFilter,
  FiCalendar,
  FiUser,
  FiRefreshCw,
  FiBarChart2,
} from 'react-icons/fi';
import reportService, { Report, ReportListParams, ReportType, ReportStatus } from '../../services/reportService';
import apiClient from '../../services/apiClient';
import { Button, Card, LoadingSpinner, ConfirmDialog, showToast, Modal } from '../common';
import ReportStatusBadge from './ReportStatusBadge';
import ReportAnalytics from './ReportAnalytics';

interface ReportListProps {
  clientId?: string;
  showClientName?: boolean;
  pageSize?: number;
}

const ReportList: React.FC<ReportListProps> = ({
  clientId,
  showClientName = true,
  pageSize = 10,
}) => {
  const queryClient = useQueryClient();

  // State
  const [currentPage, setCurrentPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<ReportType | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<ReportStatus | 'all'>('all');
  const [deletingReport, setDeletingReport] = useState<Report | null>(null);
  const [viewingAnalytics, setViewingAnalytics] = useState<Report | null>(null);

  // Build query params
  const queryParams: ReportListParams = {
    page: currentPage,
    page_size: pageSize,
    client_id: clientId,
    report_type: typeFilter !== 'all' ? typeFilter : undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    ordering: '-created_at',
  };

  // Fetch reports
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['reports', queryParams],
    queryFn: () => reportService.getReports(queryParams),
    refetchInterval: (query) => {
      // Auto-refresh if there are processing reports
      const hasProcessing = query.state.data?.results.some(
        (r: Report) => r.status === 'processing' || r.status === 'pending' || r.status === 'uploaded' || r.status === 'generating'
      );
      return hasProcessing ? 5000 : false; // 5 seconds
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportService.deleteReport(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      showToast.success('Report deleted successfully');
      setDeletingReport(null);
    },
    onError: () => {
      showToast.error('Failed to delete report');
    },
  });

  // Generate HTML/PDF mutation
  const generateMutation = useMutation({
    mutationFn: async (reportId: string) => {
      // Use synchronous generation for now (async: false)
      const response = await apiClient.post(
        `/reports/${reportId}/generate/`,
        { format: 'both', async: false }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      showToast.success('Report files generated successfully!');
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.message || 'Failed to generate report files';
      showToast.error(errorMsg);
    },
  });

  // Download mutation
  const downloadMutation = useMutation({
    mutationFn: ({ id, format }: { id: string; format: 'html' | 'pdf' }) =>
      reportService.downloadReport(id, format),
    onSuccess: (blob, variables) => {
      const report = reports.find((r: Report) => r.id === variables.id);
      const filename = `${report?.client_name || 'report'}_${report?.report_type}_${variables.format === 'pdf' ? 'report.pdf' : 'report.html'}`;
      reportService.downloadFile(blob, filename);
      showToast.success(`Report downloaded successfully`);
    },
    onError: () => {
      showToast.error('Failed to download report');
    },
  });

  const handleDownload = (report: Report, format: 'html' | 'pdf') => {
    downloadMutation.mutate({ id: report.id, format });
  };

  const handleDelete = (report: Report) => {
    setDeletingReport(report);
  };

  const handleRefresh = () => {
    refetch();
    showToast.info('Refreshing reports...');
  };

  if (error) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">Failed to load reports. Please try again.</p>
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  const reports = data?.results || [];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  const getReportTypeLabel = (type: ReportType): string => {
    const labels: Record<ReportType, string> = {
      detailed: 'Detailed Report',
      executive: 'Executive Summary',
      cost: 'Cost Optimization',
      security: 'Security Assessment',
      operations: 'Operational Excellence',
    };
    return labels[type];
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="flex flex-wrap gap-3 flex-1">
            {/* Type Filter */}
            <div className="flex items-center space-x-2">
              <FiFilter className="text-gray-400" />
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value as any);
                  setCurrentPage(1);
                }}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
              >
                <option value="all">All Types</option>
                <option value="detailed">Detailed</option>
                <option value="executive">Executive</option>
                <option value="cost">Cost</option>
                <option value="security">Security</option>
                <option value="operations">Operations</option>
              </select>
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="uploaded">Uploaded</option>
              <option value="processing">Processing</option>
              <option value="generating">Generating</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            icon={<FiRefreshCw className={isFetching ? 'animate-spin' : ''} />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
        </div>

        <div className="mt-3 text-sm text-gray-600">
          Showing {reports.length} of {totalCount} reports
        </div>
      </Card>

      {/* Report List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Loading reports..." />
        </div>
      ) : reports.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-600">
            {typeFilter !== 'all' || statusFilter !== 'all'
              ? 'No reports found matching your filters'
              : 'No reports yet. Upload a CSV file to generate your first report!'}
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <Card key={report.id} hoverable>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="text-base font-semibold text-gray-900 mb-1">
                        {getReportTypeLabel(report.report_type)}
                      </h3>
                      {showClientName && report.client_name && (
                        <p className="text-sm text-gray-600 flex items-center">
                          <FiUser className="w-4 h-4 mr-1" />
                          {report.client_name}
                        </p>
                      )}
                    </div>
                    <ReportStatusBadge status={report.status} size="sm" />
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
                    <span className="flex items-center">
                      <FiCalendar className="w-4 h-4 mr-1" />
                      {format(new Date(report.created_at), 'MMM d, yyyy')}
                    </span>
                    {report.created_by_name && (
                      <span className="flex items-center">
                        <FiUser className="w-4 h-4 mr-1" />
                        Created by: {report.created_by_name}
                      </span>
                    )}
                    {report.processing_completed_at && (
                      <span className="text-xs">
                        Completed: {format(new Date(report.processing_completed_at), 'HH:mm')}
                      </span>
                    )}
                  </div>

                  {report.error_message && (
                    <p className="mt-2 text-sm text-red-600">{report.error_message}</p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {report.status === 'completed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      icon={<FiBarChart2 />}
                      onClick={() => setViewingAnalytics(report)}
                    >
                      View Analytics
                    </Button>
                  )}

                  {report.status === 'completed' && !report.html_file && !report.pdf_file && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => generateMutation.mutate(report.id)}
                      disabled={generateMutation.isPending}
                      loading={generateMutation.isPending}
                    >
                      Generate Files
                    </Button>
                  )}

                  {/* Download buttons - always show for completed reports, disable when files not ready */}
                  {report.status === 'completed' && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        icon={<FiDownload />}
                        onClick={() => handleDownload(report, 'pdf')}
                        disabled={downloadMutation.isPending || !report.pdf_file}
                      >
                        PDF
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        icon={<FiDownload />}
                        onClick={() => handleDownload(report, 'html')}
                        disabled={downloadMutation.isPending || !report.html_file}
                      >
                        HTML
                      </Button>
                    </>
                  )}

                  {(report.status === 'processing' || report.status === 'generating' || report.status === 'uploaded') && (
                    <span className="text-sm text-blue-600 flex items-center">
                      <FiRefreshCw className="w-4 h-4 mr-1 animate-spin" />
                      {report.status === 'uploaded' ? 'Processing...' :
                       report.status === 'generating' ? 'Generating...' : 'Processing...'}
                    </span>
                  )}

                  <button
                    onClick={() => handleDelete(report)}
                    className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    aria-label="Delete report"
                  >
                    <FiTrash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </Button>
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingReport}
        onClose={() => setDeletingReport(null)}
        onConfirm={() => deletingReport && deleteMutation.mutate(deletingReport.id)}
        title="Delete Report"
        message={`Are you sure you want to delete this ${deletingReport?.report_type} report? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />

      {/* Analytics Modal */}
      <Modal
        isOpen={!!viewingAnalytics}
        onClose={() => setViewingAnalytics(null)}
        title={viewingAnalytics ? `${getReportTypeLabel(viewingAnalytics.report_type)} - Analytics` : ''}
        size="xl"
      >
        {viewingAnalytics && <ReportAnalytics reportId={viewingAnalytics.id} />}
      </Modal>
    </div>
  );
};

export default ReportList;
