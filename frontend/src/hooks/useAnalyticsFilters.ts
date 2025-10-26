import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AnalyticsFilterState, AnalyticsFilterParams } from '../types/analytics';

/**
 * Default filter state
 */
const DEFAULT_FILTERS: AnalyticsFilterState = {
  dateRange: {
    from: null,
    to: null,
    preset: 'last_30_days',
  },
  reportTypes: [],
  userRole: undefined,
};

/**
 * Custom hook for managing analytics filters
 * Handles filter state, URL synchronization, and localStorage persistence
 */
export const useAnalyticsFilters = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<AnalyticsFilterState>(() => {
    // Try to restore from URL first, then localStorage, then defaults
    const savedFilters = localStorage.getItem('analyticsFilters');

    if (searchParams.toString()) {
      return parseFiltersFromURL(searchParams);
    } else if (savedFilters) {
      try {
        return JSON.parse(savedFilters);
      } catch {
        return DEFAULT_FILTERS;
      }
    }

    return DEFAULT_FILTERS;
  });

  /**
   * Update filters and persist to URL and localStorage
   */
  const updateFilters = useCallback(
    (newFilters: Partial<AnalyticsFilterState>) => {
      setFilters((prev) => {
        const updated = { ...prev, ...newFilters };

        // Persist to localStorage
        localStorage.setItem('analyticsFilters', JSON.stringify(updated));

        // Update URL
        const params = serializeFiltersToURL(updated);
        setSearchParams(params, { replace: true });

        return updated;
      });
    },
    [setSearchParams]
  );

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    localStorage.removeItem('analyticsFilters');
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);

  /**
   * Convert filters to API parameters
   */
  const apiParams: AnalyticsFilterParams = {
    date_from: filters.dateRange.from?.toISOString().split('T')[0],
    date_to: filters.dateRange.to?.toISOString().split('T')[0],
    report_type: filters.reportTypes.length > 0 ? filters.reportTypes : undefined,
    user_role: filters.userRole,
  };

  return {
    filters,
    updateFilters,
    clearFilters,
    apiParams,
  };
};

/**
 * Parse filters from URL search params
 */
function parseFiltersFromURL(searchParams: URLSearchParams): AnalyticsFilterState {
  const dateFrom = searchParams.get('date_from');
  const dateTo = searchParams.get('date_to');
  const reportTypes = searchParams.get('report_types');
  const userRole = searchParams.get('user_role');
  const preset = searchParams.get('preset');

  return {
    dateRange: {
      from: dateFrom ? new Date(dateFrom) : null,
      to: dateTo ? new Date(dateTo) : null,
      preset: preset || undefined,
    },
    reportTypes: reportTypes ? reportTypes.split(',') : [],
    userRole: userRole || undefined,
  };
}

/**
 * Serialize filters to URL search params
 */
function serializeFiltersToURL(filters: AnalyticsFilterState): Record<string, string> {
  const params: Record<string, string> = {};

  if (filters.dateRange.from) {
    params.date_from = filters.dateRange.from.toISOString().split('T')[0];
  }
  if (filters.dateRange.to) {
    params.date_to = filters.dateRange.to.toISOString().split('T')[0];
  }
  if (filters.dateRange.preset) {
    params.preset = filters.dateRange.preset;
  }
  if (filters.reportTypes.length > 0) {
    params.report_types = filters.reportTypes.join(',');
  }
  if (filters.userRole) {
    params.user_role = filters.userRole;
  }

  return params;
}
