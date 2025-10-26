import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { HistoryFilterState, HistoryFilterParams } from '../types/history';
import { ReportType, ReportStatus } from '../services/reportService';

const STORAGE_KEY = 'history-filters';

/**
 * Default filter state
 */
const getDefaultFilters = (): HistoryFilterState => ({
  search: '',
  reportTypes: [],
  statuses: [],
  createdBy: [],
  dateFrom: null,
  dateTo: null,
  clientId: '',
});

/**
 * Parse filters from URL search params
 */
const parseFiltersFromURL = (searchParams: URLSearchParams): Partial<HistoryFilterState> => {
  const filters: Partial<HistoryFilterState> = {};

  const search = searchParams.get('search');
  if (search) filters.search = search;

  const reportTypes = searchParams.get('reportTypes');
  if (reportTypes) filters.reportTypes = reportTypes.split(',') as ReportType[];

  const statuses = searchParams.get('statuses');
  if (statuses) filters.statuses = statuses.split(',') as ReportStatus[];

  const createdBy = searchParams.get('createdBy');
  if (createdBy) filters.createdBy = createdBy.split(',');

  const dateFrom = searchParams.get('dateFrom');
  if (dateFrom) filters.dateFrom = new Date(dateFrom);

  const dateTo = searchParams.get('dateTo');
  if (dateTo) filters.dateTo = new Date(dateTo);

  const clientId = searchParams.get('clientId');
  if (clientId) filters.clientId = clientId;

  return filters;
};

/**
 * Convert filter state to URL search params
 */
const filtersToURLParams = (filters: HistoryFilterState): URLSearchParams => {
  const params = new URLSearchParams();

  if (filters.search) params.set('search', filters.search);
  if (filters.reportTypes.length > 0) params.set('reportTypes', filters.reportTypes.join(','));
  if (filters.statuses.length > 0) params.set('statuses', filters.statuses.join(','));
  if (filters.createdBy.length > 0) params.set('createdBy', filters.createdBy.join(','));
  if (filters.dateFrom) params.set('dateFrom', filters.dateFrom.toISOString().split('T')[0]);
  if (filters.dateTo) params.set('dateTo', filters.dateTo.toISOString().split('T')[0]);
  if (filters.clientId) params.set('clientId', filters.clientId);

  return params;
};

/**
 * Convert filter state to API params
 */
const filtersToAPIParams = (filters: HistoryFilterState): HistoryFilterParams => {
  const params: HistoryFilterParams = {};

  if (filters.search) params.search = filters.search;
  if (filters.reportTypes.length > 0) params.report_type = filters.reportTypes;
  if (filters.statuses.length > 0) params.status = filters.statuses;
  if (filters.createdBy.length > 0) params.created_by = filters.createdBy;
  if (filters.dateFrom) params.date_from = filters.dateFrom.toISOString().split('T')[0];
  if (filters.dateTo) params.date_to = filters.dateTo.toISOString().split('T')[0];
  if (filters.clientId) params.client_id = filters.clientId;

  return params;
};

/**
 * Load filters from localStorage
 */
const loadFromStorage = (): Partial<HistoryFilterState> => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Convert date strings back to Date objects
      if (parsed.dateFrom) parsed.dateFrom = new Date(parsed.dateFrom);
      if (parsed.dateTo) parsed.dateTo = new Date(parsed.dateTo);
      return parsed;
    }
  } catch (error) {
    console.error('Failed to load filters from storage:', error);
  }
  return {};
};

/**
 * Save filters to localStorage
 */
const saveToStorage = (filters: HistoryFilterState): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
  } catch (error) {
    console.error('Failed to save filters to storage:', error);
  }
};

/**
 * Custom hook for managing History filters with URL sync and localStorage persistence
 */
export const useHistoryFilters = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialize filters from URL, then localStorage, then defaults
  const [filters, setFilters] = useState<HistoryFilterState>(() => {
    const urlFilters = parseFiltersFromURL(searchParams);
    const storedFilters = loadFromStorage();
    return {
      ...getDefaultFilters(),
      ...storedFilters,
      ...urlFilters, // URL takes precedence
    };
  });

  // Sync filters to URL params
  useEffect(() => {
    const params = filtersToURLParams(filters);
    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // Update a single filter field
  const updateFilter = useCallback(<K extends keyof HistoryFilterState>(
    key: K,
    value: HistoryFilterState[K]
  ) => {
    setFilters((prev) => {
      const updated = { ...prev, [key]: value };
      saveToStorage(updated);
      return updated;
    });
  }, []);

  // Update multiple filter fields
  const updateFilters = useCallback((updates: Partial<HistoryFilterState>) => {
    setFilters((prev) => {
      const updated = { ...prev, ...updates };
      saveToStorage(updated);
      return updated;
    });
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    const defaultFilters = getDefaultFilters();
    setFilters(defaultFilters);
    saveToStorage(defaultFilters);
  }, []);

  // Check if any filters are active
  const hasActiveFilters = useCallback(() => {
    const defaults = getDefaultFilters();
    return (
      filters.search !== defaults.search ||
      filters.reportTypes.length > 0 ||
      filters.statuses.length > 0 ||
      filters.createdBy.length > 0 ||
      filters.dateFrom !== null ||
      filters.dateTo !== null ||
      filters.clientId !== defaults.clientId
    );
  }, [filters]);

  // Get count of active filters
  const getActiveFilterCount = useCallback(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.reportTypes.length > 0) count++;
    if (filters.statuses.length > 0) count++;
    if (filters.createdBy.length > 0) count++;
    if (filters.dateFrom || filters.dateTo) count++;
    if (filters.clientId) count++;
    return count;
  }, [filters]);

  // Convert to API params for queries
  const getAPIParams = useCallback(() => {
    return filtersToAPIParams(filters);
  }, [filters]);

  return {
    filters,
    updateFilter,
    updateFilters,
    clearFilters,
    hasActiveFilters: hasActiveFilters(),
    activeFilterCount: getActiveFilterCount(),
    apiParams: getAPIParams(),
  };
};
