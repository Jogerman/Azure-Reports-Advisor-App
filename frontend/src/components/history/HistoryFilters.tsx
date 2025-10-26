import React, { useState, useCallback, useMemo } from 'react';
import { FiFilter, FiChevronDown, FiChevronUp, FiSearch, FiX } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import { useDebounce } from '../../hooks/useDebounce';
import Button from '../common/Button';
import MultiSelect, { MultiSelectOption } from '../common/MultiSelect';
import DateRangePicker from '../common/DateRangePicker';
import { HistoryFilterState } from '../../types/history';
import { ReportType, ReportStatus } from '../../services/reportService';
import { useReportUsers } from '../../hooks/useReportUsers';

interface HistoryFiltersProps {
  filters: HistoryFilterState;
  onApplyFilters: (filters: HistoryFilterState) => void;
  onClearFilters: () => void;
  isCollapsed: boolean;
  onToggle: () => void;
  totalCount: number;
  filteredCount: number;
}

// Report type options
const REPORT_TYPE_OPTIONS: MultiSelectOption[] = [
  { value: 'cost', label: 'Cost Optimization' },
  { value: 'security', label: 'Security' },
  { value: 'operations', label: 'Operational Excellence' },
  { value: 'detailed', label: 'Detailed Analysis' },
  { value: 'executive', label: 'Executive Summary' },
];

// Status options
const STATUS_OPTIONS: MultiSelectOption[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const HistoryFilters: React.FC<HistoryFiltersProps> = ({
  filters,
  onApplyFilters,
  onClearFilters,
  isCollapsed,
  onToggle,
  totalCount,
  filteredCount,
}) => {
  // Local state for filters (before applying)
  const [localFilters, setLocalFilters] = useState<HistoryFilterState>(filters);
  const [searchInput, setSearchInput] = useState(filters.search);

  // Debounce search input
  const debouncedSearch = useDebounce(searchInput, 500);

  // Fetch users for the dropdown
  const { data: usersData, isLoading: loadingUsers } = useReportUsers();

  // Convert users to MultiSelect options
  const userOptions: MultiSelectOption[] = useMemo(() => {
    if (!usersData?.users) return [];
    return usersData.users.map((user) => ({
      value: user.id,
      label: user.full_name || user.username,
      count: user.report_count,
    }));
  }, [usersData]);

  // Update local search when debounced value changes
  React.useEffect(() => {
    setLocalFilters((prev) => ({ ...prev, search: debouncedSearch }));
  }, [debouncedSearch]);

  // Handle filter changes
  const handleReportTypesChange = useCallback((types: string[]) => {
    setLocalFilters((prev) => ({ ...prev, reportTypes: types as ReportType[] }));
  }, []);

  const handleStatusesChange = useCallback((statuses: string[]) => {
    setLocalFilters((prev) => ({ ...prev, statuses: statuses as ReportStatus[] }));
  }, []);

  const handleUsersChange = useCallback((users: string[]) => {
    setLocalFilters((prev) => ({ ...prev, createdBy: users }));
  }, []);

  const handleDateRangeChange = useCallback((range: { from: Date | null; to: Date | null }) => {
    setLocalFilters((prev) => ({
      ...prev,
      dateFrom: range.from,
      dateTo: range.to,
    }));
  }, []);

  const handleClientIdChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalFilters((prev) => ({ ...prev, clientId: e.target.value }));
  }, []);

  // Apply filters
  const handleApply = useCallback(() => {
    onApplyFilters(localFilters);
  }, [localFilters, onApplyFilters]);

  // Clear all filters
  const handleClear = useCallback(() => {
    const cleared: HistoryFilterState = {
      search: '',
      reportTypes: [],
      statuses: [],
      createdBy: [],
      dateFrom: null,
      dateTo: null,
      clientId: '',
    };
    setLocalFilters(cleared);
    setSearchInput('');
    onClearFilters();
  }, [onClearFilters]);

  // Check if there are active filters
  const hasActiveFilters =
    localFilters.search ||
    localFilters.reportTypes.length > 0 ||
    localFilters.statuses.length > 0 ||
    localFilters.createdBy.length > 0 ||
    localFilters.dateFrom ||
    localFilters.dateTo ||
    localFilters.clientId;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        aria-expanded={!isCollapsed}
        aria-label="Toggle filters"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-azure-50 text-azure-600 flex items-center justify-center">
            <FiFilter className="w-5 h-5" />
          </div>
          <div className="text-left">
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
            <p className="text-sm text-gray-600">
              Showing {filteredCount.toLocaleString()} of {totalCount.toLocaleString()} reports
            </p>
          </div>
        </div>

        {isCollapsed ? (
          <FiChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <FiChevronUp className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {/* Filter Content */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 pt-2 space-y-4 border-t border-gray-100">
              {/* Search Input */}
              <div>
                <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <div className="relative">
                  <input
                    id="search"
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Search by client name, report type..."
                    className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500 focus:border-transparent"
                    aria-label="Search reports"
                  />
                  <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  {searchInput && (
                    <button
                      onClick={() => setSearchInput('')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      aria-label="Clear search"
                    >
                      <FiX className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Date Range */}
              <DateRangePicker
                label="Date Range"
                value={{ from: localFilters.dateFrom, to: localFilters.dateTo }}
                onChange={handleDateRangeChange}
                presets={true}
              />

              {/* Report Types */}
              <MultiSelect
                label="Report Types"
                options={REPORT_TYPE_OPTIONS}
                value={localFilters.reportTypes}
                onChange={handleReportTypesChange}
                placeholder="All report types"
                searchable={false}
              />

              {/* Statuses */}
              <MultiSelect
                label="Status"
                options={STATUS_OPTIONS}
                value={localFilters.statuses}
                onChange={handleStatusesChange}
                placeholder="All statuses"
                searchable={false}
              />

              {/* Users */}
              <MultiSelect
                label="Created By"
                options={userOptions}
                value={localFilters.createdBy}
                onChange={handleUsersChange}
                placeholder={loadingUsers ? 'Loading users...' : 'All users'}
                disabled={loadingUsers}
                searchable={true}
              />

              {/* Client ID */}
              <div>
                <label htmlFor="client-id" className="block text-sm font-medium text-gray-700 mb-1">
                  Client ID
                </label>
                <input
                  id="client-id"
                  type="text"
                  value={localFilters.clientId}
                  onChange={handleClientIdChange}
                  placeholder="Enter client ID..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500 focus:border-transparent"
                  aria-label="Filter by client ID"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <Button
                  variant="primary"
                  onClick={handleApply}
                  icon={<FiFilter />}
                  fullWidth
                >
                  Apply Filters
                </Button>
                <Button
                  variant="outline"
                  onClick={handleClear}
                  disabled={!hasActiveFilters}
                  fullWidth
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default React.memo(HistoryFilters);
