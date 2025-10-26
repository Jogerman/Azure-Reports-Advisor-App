import React, { useState, useCallback, useMemo } from 'react';
import { FiFilter, FiX, FiCalendar } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '../common/Button';
import MultiSelect, { MultiSelectOption } from '../common/MultiSelect';
import DateRangePicker from '../common/DateRangePicker';
import { AnalyticsFilterState, DATE_RANGE_PRESETS } from '../../types/analytics';

interface AnalyticsFiltersProps {
  filters: AnalyticsFilterState;
  onFiltersChange: (filters: AnalyticsFilterState) => void;
  onReset: () => void;
  showRoleFilter: boolean; // Only admins see this
}

// Report type options
const REPORT_TYPE_OPTIONS: MultiSelectOption[] = [
  { value: 'cost', label: 'Cost Optimization' },
  { value: 'security', label: 'Security Assessment' },
  { value: 'operations', label: 'Operational Excellence' },
  { value: 'detailed', label: 'Detailed Report' },
  { value: 'executive', label: 'Executive Summary' },
];

// User role options (admin only)
const USER_ROLE_OPTIONS = [
  { value: '', label: 'All Roles' },
  { value: 'admin', label: 'Admin' },
  { value: 'manager', label: 'Manager' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'viewer', label: 'Viewer' },
];

/**
 * Analytics Filters Component
 * Global filters for the analytics dashboard
 */
const AnalyticsFilters: React.FC<AnalyticsFiltersProps> = ({
  filters,
  onFiltersChange,
  onReset,
  showRoleFilter,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localFilters, setLocalFilters] = useState<AnalyticsFilterState>(filters);

  // Count active filters
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.dateRange.from || filters.dateRange.to) count++;
    if (filters.reportTypes.length > 0) count++;
    if (filters.userRole) count++;
    return count;
  }, [filters]);

  // Handle report types change
  const handleReportTypesChange = useCallback((types: string[]) => {
    setLocalFilters((prev) => ({ ...prev, reportTypes: types }));
  }, []);

  // Handle date range change
  const handleDateRangeChange = useCallback(
    (range: { from: Date | null; to: Date | null }) => {
      setLocalFilters((prev) => ({
        ...prev,
        dateRange: {
          from: range.from,
          to: range.to,
          preset: undefined, // Clear preset when custom range selected
        },
      }));
    },
    []
  );

  // Handle preset selection
  const handlePresetSelect = useCallback((presetValue: string) => {
    const preset = DATE_RANGE_PRESETS.find((p) => p.value === presetValue);
    if (preset) {
      const dates = preset.getDates();
      setLocalFilters((prev) => ({
        ...prev,
        dateRange: {
          from: dates.from,
          to: dates.to,
          preset: preset.value,
        },
      }));
    }
  }, []);

  // Handle role change
  const handleRoleChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setLocalFilters((prev) => ({
      ...prev,
      userRole: e.target.value || undefined,
    }));
  }, []);

  // Apply filters
  const handleApply = useCallback(() => {
    onFiltersChange(localFilters);
    setIsOpen(false);
  }, [localFilters, onFiltersChange]);

  // Reset filters
  const handleReset = useCallback(() => {
    onReset();
    setLocalFilters({
      dateRange: { from: null, to: null, preset: 'last_30_days' },
      reportTypes: [],
      userRole: undefined,
    });
    setIsOpen(false);
  }, [onReset]);

  // Close without applying
  const handleClose = useCallback(() => {
    setLocalFilters(filters); // Reset to current filters
    setIsOpen(false);
  }, [filters]);

  return (
    <div className="relative">
      {/* Filter Button */}
      <Button
        variant="outline"
        icon={<FiFilter />}
        onClick={() => setIsOpen(!isOpen)}
        className="relative"
      >
        Filters
        {activeFiltersCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-azure-600 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {activeFiltersCount}
          </span>
        )}
      </Button>

      {/* Filters Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleClose}
            />

            {/* Dropdown Panel */}
            <motion.div
              className="absolute right-0 top-full mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex items-center gap-2">
                  <FiFilter className="w-5 h-5 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                </div>
                <button
                  onClick={handleClose}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                  aria-label="Close filters"
                >
                  <FiX className="w-5 h-5 text-gray-600" />
                </button>
              </div>

              {/* Filter Content */}
              <div className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
                {/* Date Range Presets */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FiCalendar className="w-4 h-4 inline mr-1" />
                    Time Period
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {DATE_RANGE_PRESETS.map((preset) => (
                      <button
                        key={preset.value}
                        onClick={() => handlePresetSelect(preset.value)}
                        className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                          localFilters.dateRange.preset === preset.value
                            ? 'bg-azure-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Date Range
                  </label>
                  <DateRangePicker
                    value={{
                      from: localFilters.dateRange.from,
                      to: localFilters.dateRange.to,
                    }}
                    onChange={handleDateRangeChange}
                    presets={false}
                  />
                </div>

                {/* Report Types */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Report Types
                  </label>
                  <MultiSelect
                    options={REPORT_TYPE_OPTIONS}
                    value={localFilters.reportTypes}
                    onChange={handleReportTypesChange}
                    placeholder="All types"
                  />
                </div>

                {/* User Role (Admin only) */}
                {showRoleFilter && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      User Role
                    </label>
                    <select
                      value={localFilters.userRole || ''}
                      onChange={handleRoleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
                    >
                      {USER_ROLE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
                <Button variant="ghost" onClick={handleReset} size="sm">
                  Reset
                </Button>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleClose} size="sm">
                    Cancel
                  </Button>
                  <Button variant="primary" onClick={handleApply} size="sm">
                    Apply Filters
                  </Button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default React.memo(AnalyticsFilters);
