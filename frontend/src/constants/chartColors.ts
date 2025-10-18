/**
 * Chart Colors Configuration
 *
 * This file defines colorblind-friendly chart colors that align with the
 * application's theme. The colors are chosen based on:
 * 1. Accessibility (WCAG AA contrast requirements)
 * 2. Colorblind-safe palette (distinguishable for common color vision deficiencies)
 * 3. Semantic meaning aligned with Azure Advisor recommendation categories
 */

// Theme-aware chart colors using Tailwind color palette
// These colors are extracted from tailwind.config.js to maintain consistency
export const THEME_COLORS = {
  azure: '#0078D4',      // azure-600: Primary brand color
  warning: '#f59e0b',    // warning-500: Amber/orange for cost
  danger: '#ef4444',     // danger-500: Red for security
  info: '#3b82f6',       // info-500: Blue for reliability
  purple: '#8b5cf6',     // purple-500: Purple for operational excellence
  success: '#22c55e',    // success-500: Green for performance
  gray: '#94a3b8',       // slate-400: Fallback/neutral color
} as const;

/**
 * Category-specific colors for Azure Advisor recommendations
 * Mapped to semantic theme colors for consistency
 */
export const CATEGORY_COLORS = {
  Cost: THEME_COLORS.warning,                    // Amber: Financial concern
  Security: THEME_COLORS.danger,                 // Red: Critical attention needed
  Reliability: THEME_COLORS.info,                // Blue: Stability and trust
  'Operational Excellence': THEME_COLORS.purple, // Purple: Process optimization
  Performance: THEME_COLORS.success,             // Green: Positive performance
  OperationalExcellence: THEME_COLORS.purple,    // Alternative naming
} as const;

/**
 * Impact level colors for recommendation severity
 * Using semantic colors to convey urgency/importance
 */
export const IMPACT_COLORS = {
  High: THEME_COLORS.danger,      // Red: High severity
  Medium: THEME_COLORS.warning,   // Amber: Medium severity
  Low: THEME_COLORS.info,         // Blue: Low severity
  Unknown: THEME_COLORS.gray,     // Gray: Unknown/neutral
} as const;

/**
 * Status colors for various states
 */
export const STATUS_COLORS = {
  Active: THEME_COLORS.success,    // Green: Active/healthy
  Pending: THEME_COLORS.warning,   // Amber: Pending action
  Resolved: THEME_COLORS.info,     // Blue: Completed
  Dismissed: THEME_COLORS.gray,    // Gray: Inactive
  Error: THEME_COLORS.danger,      // Red: Error state
} as const;

/**
 * Colorblind-friendly palette for general charts
 * Based on Wong's palette and Paul Tol's qualitative schemes
 * These colors are distinguishable for people with various types of color vision deficiency
 */
export const COLORBLIND_SAFE_PALETTE = [
  '#0078D4', // Azure blue (primary)
  '#f59e0b', // Amber (warm)
  '#3b82f6', // Sky blue (cool)
  '#22c55e', // Green (positive)
  '#8b5cf6', // Purple (distinct)
  '#ef4444', // Red (alert)
  '#06b6d4', // Cyan (alternative blue)
  '#f97316', // Orange (warm alternative)
] as const;

/**
 * Get a color from the colorblind-safe palette by index
 * Wraps around if index exceeds palette length
 */
export const getColorByIndex = (index: number): string => {
  return COLORBLIND_SAFE_PALETTE[index % COLORBLIND_SAFE_PALETTE.length];
};

/**
 * Get category color with fallback
 */
export const getCategoryColor = (category: string): string => {
  return CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || THEME_COLORS.gray;
};

/**
 * Get impact color with fallback
 */
export const getImpactColor = (impact: string): string => {
  return IMPACT_COLORS[impact as keyof typeof IMPACT_COLORS] || THEME_COLORS.gray;
};

/**
 * Get status color with fallback
 */
export const getStatusColor = (status: string): string => {
  return STATUS_COLORS[status as keyof typeof STATUS_COLORS] || THEME_COLORS.gray;
};
