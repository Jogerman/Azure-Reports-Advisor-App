import React from 'react';
import { FiDownload } from 'react-icons/fi';
import Button from '../common/Button';
import { showToast } from '../common/Toast';
import { useReportExport } from '../../hooks/useReportExport';
import { HistoryFilterState } from '../../types/history';

interface ExportCSVButtonProps {
  filters: HistoryFilterState;
  totalCount: number;
  disabled?: boolean;
}

const ExportCSVButton: React.FC<ExportCSVButtonProps> = ({
  filters,
  totalCount,
  disabled = false,
}) => {
  const { mutate: exportCSV, isPending } = useReportExport();

  const handleExport = () => {
    if (totalCount === 0) {
      showToast.warning('No reports to export');
      return;
    }

    // Convert filters to API params
    const params: any = {};
    if (filters.search) params.search = filters.search;
    if (filters.reportTypes.length > 0) params.report_type = filters.reportTypes;
    if (filters.statuses.length > 0) params.status = filters.statuses;
    if (filters.createdBy.length > 0) params.created_by = filters.createdBy;
    if (filters.dateFrom) params.date_from = filters.dateFrom.toISOString().split('T')[0];
    if (filters.dateTo) params.date_to = filters.dateTo.toISOString().split('T')[0];
    if (filters.clientId) params.client_id = filters.clientId;

    exportCSV(params, {
      onSuccess: (blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;

        // Generate filename with timestamp
        const timestamp = new Date().toISOString().split('T')[0];
        link.download = `reports-export-${timestamp}.csv`;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        showToast.success(`Successfully exported ${totalCount} reports to CSV`);
      },
      onError: (error: any) => {
        console.error('Export failed:', error);
        showToast.error('Failed to export reports. Please try again.');
      },
    });
  };

  return (
    <Button
      variant="outline"
      size="md"
      icon={<FiDownload />}
      onClick={handleExport}
      loading={isPending}
      disabled={disabled || totalCount === 0 || isPending}
      title={totalCount === 0 ? 'No reports to export' : `Export ${totalCount} reports to CSV`}
    >
      Export CSV
    </Button>
  );
};

export default ExportCSVButton;
