/**
 * Number formatting utilities
 */

/**
 * Format a number with thousand separators (commas)
 * @param value - The number to format (can be number, string, null, or undefined)
 * @returns Formatted string with commas, or the original value if invalid
 *
 * @example
 * formatNumberWithCommas(26970) // "26,970"
 * formatNumberWithCommas(1234567.89) // "1,234,567.89"
 * formatNumberWithCommas("12345") // "12,345"
 */
export function formatNumberWithCommas(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '0';
  }

  try {
    // Convert to number if it's a string
    const numValue = typeof value === 'string' ? parseFloat(value) : value;

    // Check if it's a valid number
    if (isNaN(numValue)) {
      return String(value);
    }

    // Use toLocaleString for proper formatting
    return numValue.toLocaleString('en-US', {
      maximumFractionDigits: 20, // Preserve existing decimal places
    });
  } catch (error) {
    return String(value);
  }
}

/**
 * Format a currency value with dollar sign and commas
 * @param value - The number to format
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted currency string
 *
 * @example
 * formatCurrency(26970) // "$26,970"
 * formatCurrency(1234.56, 2) // "$1,234.56"
 */
export function formatCurrency(value: number | string | null | undefined, decimals: number = 0): string {
  if (value === null || value === undefined || value === '') {
    return '$0';
  }

  try {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(numValue)) {
      return '$0';
    }

    return numValue.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  } catch (error) {
    return '$0';
  }
}

/**
 * Format a number as a percentage
 * @param value - The number to format (0-100 scale)
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string
 *
 * @example
 * formatPercentage(45.6) // "45.6%"
 * formatPercentage(33.333, 2) // "33.33%"
 */
export function formatPercentage(value: number | string | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined || value === '') {
    return '0%';
  }

  try {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(numValue)) {
      return '0%';
    }

    return `${numValue.toFixed(decimals)}%`;
  } catch (error) {
    return '0%';
  }
}

/**
 * Compact number format for large values (e.g., 1.2K, 3.5M)
 * @param value - The number to format
 * @returns Compact formatted string
 *
 * @example
 * formatCompactNumber(1234) // "1.2K"
 * formatCompactNumber(1234567) // "1.2M"
 */
export function formatCompactNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '0';
  }

  if (isNaN(value)) {
    return '0';
  }

  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (absValue >= 1000000000) {
    return `${sign}${(absValue / 1000000000).toFixed(1)}B`;
  } else if (absValue >= 1000000) {
    return `${sign}${(absValue / 1000000).toFixed(1)}M`;
  } else if (absValue >= 1000) {
    return `${sign}${(absValue / 1000).toFixed(1)}K`;
  }

  return value.toLocaleString('en-US');
}
