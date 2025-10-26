import React, { useState } from 'react';
import { FiDownload, FiFileText } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '../common/Button';
import { showToast } from '../common/Toast';
import analyticsService from '../../services/analyticsService';
import { AnalyticsFilterParams } from '../../types/analytics';

interface ExportDashboardButtonProps {
  filters?: AnalyticsFilterParams;
  disabled?: boolean;
}

/**
 * Export Dashboard Button Component
 * Allows exporting dashboard data to CSV
 */
const ExportDashboardButton: React.FC<ExportDashboardButtonProps> = ({
  filters,
  disabled = false,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  // Handle CSV export
  const handleExportCSV = async () => {
    try {
      setIsExporting(true);
      setShowMenu(false);

      const blob = await analyticsService.exportDashboardCSV(filters);
      const filename = `analytics-dashboard-${new Date().toISOString().split('T')[0]}.csv`;

      analyticsService.downloadFile(blob, filename);

      showToast.success(`Downloaded: ${filename}`);
    } catch (error) {
      console.error('Export failed:', error);
      showToast.error('Failed to export dashboard data');
    } finally {
      setIsExporting(false);
    }
  };

  // Handle PDF export (future implementation)
  const handleExportPDF = () => {
    setShowMenu(false);
    showToast.info('PDF export coming soon!');
  };

  return (
    <div className="relative">
      {/* Export Button */}
      <Button
        variant="outline"
        icon={<FiDownload />}
        onClick={() => setShowMenu(!showMenu)}
        loading={isExporting}
        disabled={disabled}
      >
        Export
      </Button>

      {/* Export Menu */}
      <AnimatePresence>
        {showMenu && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowMenu(false)}
            />

            {/* Menu Dropdown */}
            <motion.div
              className="absolute right-0 top-full mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden"
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
            >
              {/* Export to CSV */}
              <button
                onClick={handleExportCSV}
                disabled={isExporting}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="w-10 h-10 rounded-lg bg-success-100 text-success-600 flex items-center justify-center">
                  <FiFileText className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">Export to CSV</p>
                  <p className="text-xs text-gray-600">Download raw data</p>
                </div>
              </button>

              {/* Export to PDF (Coming Soon) */}
              <button
                onClick={handleExportPDF}
                disabled={isExporting}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border-t border-gray-100"
              >
                <div className="w-10 h-10 rounded-lg bg-danger-100 text-danger-600 flex items-center justify-center">
                  <FiDownload className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">Export to PDF</p>
                  <p className="text-xs text-gray-600">Full dashboard snapshot</p>
                  <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium bg-azure-100 text-azure-700 rounded">
                    Coming Soon
                  </span>
                </div>
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default React.memo(ExportDashboardButton);
