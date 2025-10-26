import React, { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FiRefreshCw, FiClock } from 'react-icons/fi';
import {
  HistoryStats,
  HistoryFilters,
  HistoryChart,
  HistoryTable,
  ReportDetailsModal,
  ExportCSVButton,
  Pagination,
} from '../components/history';
import Button from '../components/common/Button';
import ConfirmDialog from '../components/common/ConfirmDialog';
import { showToast } from '../components/common/Toast';
import { useHistoryFilters } from '../hooks/useHistoryFilters';
import { useHistoryStats } from '../hooks/useHistoryStats';
import { useHistoryTrends } from '../hooks/useHistoryTrends';
import reportService, { Report } from '../services/reportService';
import { SortingState, PaginationState, TrendsParams } from '../types/history';
import { useAuth } from '../hooks/useAuth';

const HistoryPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Filters management
  const {
    filters,
    updateFilters,
    clearFilters,
    apiParams,
  } = useHistoryFilters();

  // Local state
  const [isFiltersCollapsed, setIsFiltersCollapsed] = useState(false);
  const [granularity, setGranularity] = useState<'day' | 'week' | 'month'>('day');
  const [sorting, setSorting] = useState<SortingState>({
    field: 'created_at',
    direction: 'desc',
  });
  const [pagination, setPagination] = useState<PaginationState>({
    currentPage: 1,
    pageSize: 25,
    totalPages: 1,
    totalCount: 0,
  });

  // Modal state
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<Report | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  // Fetch statistics
  const { data: statsData, isLoading: statsLoading } = useHistoryStats(apiParams);

  // Fetch trends
  const trendsParams: TrendsParams = {
    granularity,
    ...apiParams,
  };
  const { data: trendsData, isLoading: trendsLoading } = useHistoryTrends(trendsParams);

  // Fetch reports list
  const {
    data: reportsData,
    isLoading: reportsLoading,
    refetch: refetchReports,
  } = useQuery({
    queryKey: [
      'reports',
      'history',
      apiParams,
      sorting,
      pagination.currentPage,
      pagination.pageSize,
    ],
    queryFn: async () => {
      const orderingField = sorting.direction === 'desc' ? `-${sorting.field}` : sorting.field;
      return reportService.getReports({
        ...apiParams,
        ordering: orderingField,
        page: pagination.currentPage,
        page_size: pagination.pageSize,
      });
    },
    staleTime: 30 * 1000, // 30 seconds
  });

  // Update pagination when data changes
  useEffect(() => {
    if (reportsData) {
      setPagination((prev) => ({
        ...prev,
        totalCount: reportsData.count,
        totalPages: Math.ceil(reportsData.count / prev.pageSize),
      }));
    }
  }, [reportsData]);

  // Auto-refresh if there are processing reports
  useEffect(() => {
    const hasProcessingReports = reportsData?.results.some(
      (r) => r.status === 'processing' || r.status === 'generating'
    );

    if (hasProcessingReports) {
      const interval = setInterval(() => {
        refetchReports();
        queryClient.invalidateQueries({ queryKey: ['history', 'statistics'] });
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [reportsData, refetchReports, queryClient]);

  // Delete report mutation
  const deleteMutation = useMutation({
    mutationFn: (reportId: string) => reportService.deleteReport(reportId),
    onSuccess: () => {
      showToast.success('Report deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['reports', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['history', 'statistics'] });
      queryClient.invalidateQueries({ queryKey: ['history', 'trends'] });
      setIsDeleteDialogOpen(false);
      setReportToDelete(null);
    },
    onError: () => {
      showToast.error('Failed to delete report');
    },
  });

  // Handlers
  const handleApplyFilters = useCallback(
    (newFilters: typeof filters) => {
      updateFilters(newFilters);
      setPagination((prev) => ({ ...prev, currentPage: 1 }));
    },
    [updateFilters]
  );

  const handleClearFilters = useCallback(() => {
    clearFilters();
    setPagination((prev) => ({ ...prev, currentPage: 1 }));
  }, [clearFilters]);

  const handleSortChange = useCallback((field: string) => {
    setSorting((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setPagination((prev) => ({ ...prev, currentPage: page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handlePageSizeChange = useCallback((pageSize: number) => {
    setPagination((prev) => ({
      ...prev,
      pageSize,
      currentPage: 1,
      totalPages: Math.ceil(prev.totalCount / pageSize),
    }));
  }, []);

  const handleRefresh = useCallback(() => {
    refetchReports();
    queryClient.invalidateQueries({ queryKey: ['history', 'statistics'] });
    queryClient.invalidateQueries({ queryKey: ['history', 'trends'] });
    showToast.success('Data refreshed');
  }, [refetchReports, queryClient]);

  const handleDownload = useCallback(
    async (report: Report, format: 'html' | 'pdf') => {
      try {
        const blob = await reportService.downloadReport(report.id, format);
        const filename = format === 'html'
          ? `${report.report_type}-report-${report.id}.html`
          : `${report.report_type}-report-${report.id}.pdf`;
        reportService.downloadFile(blob, filename);
        showToast.success(`Download started: ${filename}`);
      } catch (error) {
        console.error('Download failed:', error);
        showToast.error(`Failed to download ${format.toUpperCase()}`);
      }
    },
    []
  );

  const handleDelete = useCallback((report: Report) => {
    setReportToDelete(report);
    setIsDeleteDialogOpen(true);
  }, []);

  const handleConfirmDelete = useCallback(() => {
    if (reportToDelete) {
      deleteMutation.mutate(reportToDelete.id);
    }
  }, [reportToDelete, deleteMutation]);

  const handleViewDetails = useCallback((report: Report) => {
    setSelectedReport(report);
    setIsDetailsModalOpen(true);
  }, []);

  const reports = reportsData?.results || [];
  const totalCount = reportsData?.count || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 p-6 lg:p-8"
    >
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-azure-50 text-azure-600 flex items-center justify-center">
            <FiClock className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Report History</h1>
            <p className="text-gray-600 mt-1">View and manage all your generated reports</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            icon={<FiRefreshCw />}
            onClick={handleRefresh}
            size="md"
          >
            Refresh
          </Button>
          <ExportCSVButton
            filters={filters}
            totalCount={totalCount}
            disabled={reportsLoading}
          />
        </div>
      </div>

      {/* Statistics */}
      <HistoryStats stats={statsData} loading={statsLoading} />

      {/* Filters */}
      <HistoryFilters
        filters={filters}
        onApplyFilters={handleApplyFilters}
        onClearFilters={handleClearFilters}
        isCollapsed={isFiltersCollapsed}
        onToggle={() => setIsFiltersCollapsed(!isFiltersCollapsed)}
        totalCount={statsData?.total_reports || 0}
        filteredCount={totalCount}
      />

      {/* Chart */}
      <HistoryChart
        data={trendsData?.data || []}
        granularity={granularity}
        onGranularityChange={setGranularity}
        loading={trendsLoading}
      />

      {/* Table */}
      <HistoryTable
        reports={reports}
        loading={reportsLoading}
        sorting={sorting}
        onSortChange={handleSortChange}
        onDownload={handleDownload}
        onDelete={handleDelete}
        onViewDetails={handleViewDetails}
        currentUserRole={user?.email || ''}
      />

      {/* Pagination */}
      {!reportsLoading && reports.length > 0 && (
        <Pagination
          pagination={pagination}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      )}

      {/* Report Details Modal */}
      <ReportDetailsModal
        report={selectedReport}
        isOpen={isDetailsModalOpen}
        onClose={() => {
          setIsDetailsModalOpen(false);
          setSelectedReport(null);
        }}
        onDownload={handleDownload}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => {
          setIsDeleteDialogOpen(false);
          setReportToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete Report"
        message={`Are you sure you want to delete this ${reportToDelete?.report_type} report? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </motion.div>
  );
};

export default HistoryPage;
