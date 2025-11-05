"""
CSV Processing Service for Azure Advisor Reports.

This service handles parsing, validation, and processing of Azure Advisor CSV exports.
"""

import logging
import pandas as pd
import os
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CSVProcessingError(Exception):
    """Custom exception for CSV processing errors."""
    pass


class AzureAdvisorCSVProcessor:
    """
    Processes Azure Advisor CSV files and extracts recommendation data.
    """

    # Required columns in Azure Advisor CSV
    REQUIRED_COLUMNS = [
        'Category',
        'Recommendation',
    ]

    # Formula injection prefixes (CSV Injection prevention)
    # These characters at the start of a cell can cause Excel/Calc to execute formulas
    FORMULA_PREFIXES = ('=', '+', '-', '@', '|', '\t', '\r')

    # Optional columns (may vary between Azure Advisor exports)
    OPTIONAL_COLUMNS = [
        'Impact',
        'Business Impact',
        'Impacted Resource',
        'Resource Name',
        'Resource Type',
        'Resource Group',
        'Subscription ID',
        'Subscription Name',
        'Potential Benefits',
        'Potential Annual Cost Savings',
        'Currency',
        'Advisor Score Impact',
        'Retirement Date',
        'Retiring Feature',
        'Description',
    ]

    # Category mapping (Azure Advisor categories to internal categories)
    CATEGORY_MAPPING = {
        'Cost': 'cost',
        'cost': 'cost',
        'Security': 'security',
        'security': 'security',
        'Reliability': 'reliability',
        'reliability': 'reliability',
        'High Availability': 'reliability',
        'Operational Excellence': 'operational_excellence',
        'operational excellence': 'operational_excellence',
        'Performance': 'performance',
        'performance': 'performance',
    }

    # Impact mapping
    IMPACT_MAPPING = {
        'High': 'high',
        'high': 'high',
        'Medium': 'medium',
        'medium': 'medium',
        'Low': 'low',
        'low': 'low',
    }

    def __init__(self, file_path: str):
        """
        Initialize CSV processor with file path.

        Args:
            file_path: Path to the CSV file to process

        Raises:
            CSVProcessingError: If file path is invalid or outside MEDIA_ROOT
        """
        # SECURITY: Validate and sanitize file path to prevent path traversal attacks
        self.file_path = self._validate_file_path(file_path)
        self.df: Optional[pd.DataFrame] = None
        self.statistics: Dict = {}
        self.errors: List[str] = []

    def _validate_file_path(self, file_path: str) -> str:
        """
        Validate file path to prevent path traversal attacks.

        This method ensures that:
        1. The file path is absolute
        2. The file is located within MEDIA_ROOT (no path traversal)
        3. The path doesn't contain dangerous sequences like ../ or symbolic links

        Args:
            file_path: Path to validate

        Returns:
            str: Validated absolute file path

        Raises:
            CSVProcessingError: If path is invalid or outside allowed directory

        Security References:
        - CWE-22: Improper Limitation of a Pathname to a Restricted Directory
        - OWASP: Path Traversal
        """
        if not file_path:
            raise CSVProcessingError("File path cannot be empty")

        # Get absolute path and resolve any symbolic links
        try:
            abs_path = os.path.abspath(file_path)
            real_path = os.path.realpath(abs_path)
        except Exception as e:
            raise CSVProcessingError(f"Invalid file path: {str(e)}")

        # Get MEDIA_ROOT from settings (fallback to safer default)
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            raise CSVProcessingError("MEDIA_ROOT not configured - cannot validate file path")

        # Ensure MEDIA_ROOT is absolute
        media_root_abs = os.path.abspath(media_root)
        media_root_real = os.path.realpath(media_root_abs)

        # CRITICAL: Check that file is within MEDIA_ROOT (prevents path traversal)
        # Use os.path.commonpath to safely check if file is within allowed directory
        try:
            common = os.path.commonpath([media_root_real, real_path])
        except ValueError:
            # Paths are on different drives (Windows) or one is relative
            raise CSVProcessingError(
                f"File path validation failed: paths on different drives or invalid"
            )

        if common != media_root_real:
            logger.error(
                f"SECURITY: Path traversal attempt detected! "
                f"Attempted path: {file_path}, "
                f"Real path: {real_path}, "
                f"MEDIA_ROOT: {media_root_real}"
            )
            raise CSVProcessingError(
                f"Access denied: File must be within allowed directory. "
                f"Path traversal attempts are logged and monitored."
            )

        # Additional check: Ensure path doesn't contain suspicious patterns
        suspicious_patterns = ['..', '~', '//']
        for pattern in suspicious_patterns:
            if pattern in file_path:
                logger.warning(
                    f"SECURITY: Suspicious pattern '{pattern}' detected in path: {file_path}"
                )

        logger.debug(f"Path validation passed: {real_path} is within {media_root_real}")
        return real_path

    def validate_file(self) -> bool:
        """
        Validate that the file exists and is accessible.

        Returns:
            bool: True if file is valid, False otherwise

        Raises:
            CSVProcessingError: If file doesn't exist or isn't readable
        """
        if not os.path.exists(self.file_path):
            raise CSVProcessingError(f"File not found: {self.file_path}")

        if not os.path.isfile(self.file_path):
            raise CSVProcessingError(f"Path is not a file: {self.file_path}")

        # Check file size
        file_size = os.path.getsize(self.file_path)
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 52428800)

        if file_size > max_size:
            raise CSVProcessingError(
                f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
            )

        if file_size == 0:
            raise CSVProcessingError("File is empty")

        logger.info(f"File validation passed: {self.file_path} ({file_size} bytes)")
        return True

    def read_csv(self) -> pd.DataFrame:
        """
        Read CSV file with multiple encoding attempts.

        Returns:
            pd.DataFrame: Parsed CSV data

        Raises:
            CSVProcessingError: If CSV cannot be read
        """
        encodings = getattr(settings, 'CSV_ENCODING_OPTIONS', ['utf-8', 'utf-8-sig', 'latin-1'])

        for encoding in encodings:
            try:
                logger.info(f"Attempting to read CSV with encoding: {encoding}")
                self.df = pd.read_csv(
                    self.file_path,
                    encoding=encoding,
                    skipinitialspace=True,
                    na_values=['', 'N/A', 'NA', 'null', 'None'],
                    keep_default_na=True,
                    # FIX: Handle commas within quoted fields (Azure Advisor CSV format)
                    quotechar='"',
                    doublequote=True,
                    escapechar=None,
                    # Use Python engine for better error tolerance
                    engine='python',
                    # Warn on bad lines instead of crashing (Pandas 1.3.0+)
                    on_bad_lines='warn'
                )
                logger.info(f"Successfully read CSV with encoding: {encoding}")
                logger.info(f"CSV shape: {self.df.shape[0]} rows, {self.df.shape[1]} columns")
                return self.df
            except UnicodeDecodeError:
                logger.warning(f"Failed to read CSV with encoding: {encoding}")
                continue
            except pd.errors.EmptyDataError:
                raise CSVProcessingError("CSV file is empty or contains no data")
            except pd.errors.ParserError as e:
                # Log detailed error information for debugging
                logger.error(f"Parser error details: {str(e)}")
                # Try with more lenient settings
                try:
                    logger.info(f"Retrying with lenient parser settings for encoding: {encoding}")
                    self.df = pd.read_csv(
                        self.file_path,
                        encoding=encoding,
                        skipinitialspace=True,
                        na_values=['', 'N/A', 'NA', 'null', 'None'],
                        keep_default_na=True,
                        quotechar='"',
                        doublequote=True,
                        engine='python',
                        on_bad_lines='skip',  # Skip problematic lines
                    )
                    logger.warning(f"Successfully read CSV with lenient settings (some rows may have been skipped)")
                    logger.info(f"CSV shape: {self.df.shape[0]} rows, {self.df.shape[1]} columns")
                    return self.df
                except Exception as retry_error:
                    logger.error(f"Retry also failed: {str(retry_error)}")
                    raise CSVProcessingError(f"Failed to parse CSV: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error reading CSV: {str(e)}")
                continue

        raise CSVProcessingError(
            f"Failed to read CSV with any of the attempted encodings: {', '.join(encodings)}"
        )

    def validate_structure(self) -> bool:
        """
        Validate that the CSV has the required columns.

        Returns:
            bool: True if structure is valid

        Raises:
            CSVProcessingError: If required columns are missing
        """
        if self.df is None:
            raise CSVProcessingError("CSV not loaded. Call read_csv() first.")

        # Normalize column names (strip whitespace and handle case)
        self.df.columns = self.df.columns.str.strip()

        # Check for required columns (case-insensitive)
        df_columns_lower = [col.lower() for col in self.df.columns]
        missing_columns = []

        for required_col in self.REQUIRED_COLUMNS:
            if required_col.lower() not in df_columns_lower:
                missing_columns.append(required_col)

        if missing_columns:
            raise CSVProcessingError(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Available columns: {', '.join(self.df.columns)}"
            )

        # Check row count
        max_rows = getattr(settings, 'CSV_MAX_ROWS', 50000)
        if len(self.df) > max_rows:
            raise CSVProcessingError(
                f"CSV contains {len(self.df)} rows, which exceeds the maximum allowed ({max_rows})"
            )

        if len(self.df) == 0:
            raise CSVProcessingError("CSV contains no data rows")

        logger.info(f"CSV structure validation passed: {len(self.df)} rows")
        return True

    def normalize_column_names(self) -> None:
        """Normalize column names to match expected format."""
        if self.df is None:
            return

        # Create a mapping of lowercase column names to actual column names
        column_mapping = {}

        # Map common variations to standard names
        for col in self.df.columns:
            col_lower = col.lower().strip()

            # Map business impact variations
            if 'business' in col_lower and 'impact' in col_lower:
                column_mapping[col] = 'Business Impact'
            elif col_lower == 'impact':
                column_mapping[col] = 'Business Impact'
            # Map resource name variations
            elif 'impacted' in col_lower and 'resource' in col_lower:
                column_mapping[col] = 'Resource Name'
            elif col_lower == 'resource name':
                column_mapping[col] = 'Resource Name'
            # Map savings variations
            elif 'savings' in col_lower or 'cost' in col_lower:
                if 'annual' in col_lower:
                    column_mapping[col] = 'Potential Annual Cost Savings'

        if column_mapping:
            self.df.rename(columns=column_mapping, inplace=True)
            logger.info(f"Normalized columns: {column_mapping}")

    def sanitize_cell_value(self, value) -> str:
        """
        Sanitize cell value to prevent CSV injection attacks.

        Formula injection (CSV Injection) occurs when spreadsheet applications
        execute formulas in CSV cells starting with =, +, -, @, |, tab, or carriage return.

        This method prepends a single quote to values starting with dangerous characters,
        preventing formula execution while preserving the original data.

        References:
        - OWASP: https://owasp.org/www-community/attacks/CSV_Injection
        - CWE-1236: CSV Injection

        Args:
            value: Cell value to sanitize (any type)

        Returns:
            str: Sanitized value safe from formula injection

        Examples:
            >>> processor.sanitize_cell_value('=1+1')
            "'=1+1"
            >>> processor.sanitize_cell_value('Normal text')
            "Normal text"
            >>> processor.sanitize_cell_value('=cmd|"/c calc"!A1')
            "'=cmd|"/c calc"!A1"
        """
        # Return non-string values as-is
        if not isinstance(value, str):
            return value

        # Strip whitespace to check first character
        value = value.strip()

        # Empty strings are safe
        if not value:
            return value

        # Check if value starts with dangerous characters
        if value[0] in self.FORMULA_PREFIXES:
            # Prepend single quote to prevent formula execution
            sanitized = "'" + value
            logger.debug(f"CSV Injection prevented: Sanitized '{value[:50]}...' -> '{sanitized[:50]}...'")
            return sanitized

        return value

    def clean_data(self) -> None:
        """
        Clean and normalize data in the DataFrame with security controls.

        This method:
        1. Removes empty rows
        2. Fills NaN values
        3. Strips whitespace
        4. Sanitizes all string values to prevent CSV injection attacks
        """
        if self.df is None:
            return

        # Remove completely empty rows
        self.df.dropna(how='all', inplace=True)

        # Fill NaN values with empty strings for text columns
        text_columns = self.df.select_dtypes(include=['object']).columns
        self.df[text_columns] = self.df[text_columns].fillna('')

        # Strip whitespace and sanitize all string columns
        for col in text_columns:
            self.df[col] = self.df[col].str.strip()
            # CRITICAL: Sanitize for CSV injection (prevents formula execution in Excel/LibreOffice)
            self.df[col] = self.df[col].apply(self.sanitize_cell_value)

        logger.info(f"Data cleaning completed: {len(self.df)} rows, CSV injection protection applied")

    def parse_decimal(self, value, default=0) -> Decimal:
        """
        Parse a value to Decimal, handling various formats.

        Args:
            value: Value to parse
            default: Default value if parsing fails

        Returns:
            Decimal: Parsed decimal value
        """
        if pd.isna(value) or value == '':
            return Decimal(default)

        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                value = value.replace('$', '').replace('€', '').replace('£', '')
                value = value.replace(',', '').strip()

            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            logger.warning(f"Failed to parse decimal value: {value}, using default: {default}")
            return Decimal(default)

    def extract_recommendations(self) -> List[Dict]:
        """
        Extract and format recommendations from the DataFrame.

        Returns:
            List[Dict]: List of recommendation dictionaries
        """
        if self.df is None:
            raise CSVProcessingError("CSV not loaded")

        recommendations = []

        for idx, row in self.df.iterrows():
            try:
                # Map category
                raw_category = row.get('Category', '')
                category = self.CATEGORY_MAPPING.get(raw_category, 'operational_excellence')

                # Map impact
                raw_impact = row.get('Business Impact', row.get('Impact', 'medium'))
                business_impact = self.IMPACT_MAPPING.get(raw_impact, 'medium')

                # Parse potential savings
                raw_savings = row.get('Potential Annual Cost Savings', 0)
                potential_savings = self.parse_decimal(raw_savings, 0)

                # Parse advisor score impact
                raw_score = row.get('Advisor Score Impact', 0)
                advisor_score_impact = self.parse_decimal(raw_score, 0)

                # Parse retirement date
                retirement_date = None
                raw_date = row.get('Retirement Date', '')
                if raw_date and not pd.isna(raw_date):
                    try:
                        retirement_date = pd.to_datetime(raw_date).date()
                    except Exception:
                        logger.warning(f"Failed to parse retirement date: {raw_date}")

                recommendation_data = {
                    'category': category,
                    'business_impact': business_impact,
                    'recommendation': row.get('Recommendation', row.get('Description', '')),
                    'subscription_id': row.get('Subscription ID', ''),
                    'subscription_name': row.get('Subscription Name', ''),
                    'resource_group': row.get('Resource Group', ''),
                    'resource_name': row.get('Resource Name', row.get('Impacted Resource', '')),
                    'resource_type': row.get('Resource Type', ''),
                    'potential_savings': potential_savings,
                    'currency': row.get('Currency', 'USD'),
                    'potential_benefits': row.get('Potential Benefits', ''),
                    'retirement_date': retirement_date,
                    'retiring_feature': row.get('Retiring Feature', ''),
                    'advisor_score_impact': advisor_score_impact,
                    'csv_row_number': idx + 2,  # +2 because: 0-indexed + 1 for header row
                }

                recommendations.append(recommendation_data)

            except Exception as e:
                logger.error(f"Error processing row {idx}: {str(e)}")
                self.errors.append(f"Row {idx + 2}: {str(e)}")
                continue

        logger.info(f"Extracted {len(recommendations)} recommendations")
        return recommendations

    def calculate_statistics(self, recommendations: List[Dict]) -> Dict:
        """
        Calculate statistics from recommendations.

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            Dict: Statistics dictionary
        """
        if not recommendations:
            return {
                'total_recommendations': 0,
                'category_distribution': {},
                'business_impact_distribution': {},
                'total_potential_savings': 0,
                'average_potential_savings': 0,
                'estimated_monthly_savings': 0,
                'estimated_working_hours': 0,
                'advisor_score_impact': 0,
                'top_recommendations': [],
            }

        # Category distribution
        category_dist = {}
        for rec in recommendations:
            cat = rec['category']
            category_dist[cat] = category_dist.get(cat, 0) + 1

        # Business impact distribution
        impact_dist = {}
        for rec in recommendations:
            impact = rec['business_impact']
            impact_dist[impact] = impact_dist.get(impact, 0) + 1

        # Financial metrics
        total_savings = sum(float(rec['potential_savings']) for rec in recommendations)
        avg_savings = total_savings / len(recommendations) if recommendations else 0

        # Calculate Advisor Score Impact
        total_score_impact = sum(float(rec['advisor_score_impact']) for rec in recommendations)

        # Estimate working hours (rough estimate: 1 hour per recommendation)
        estimated_hours = len(recommendations)

        # Get top 10 recommendations by potential savings
        sorted_recs = sorted(
            recommendations,
            key=lambda x: float(x['potential_savings']),
            reverse=True
        )
        top_recs = sorted_recs[:10]

        top_recommendations = [
            {
                'category': rec['category'],
                'recommendation': rec['recommendation'][:100] + '...' if len(rec['recommendation']) > 100 else rec['recommendation'],
                'potential_savings': float(rec['potential_savings']),
                'business_impact': rec['business_impact'],
            }
            for rec in top_recs
        ]

        self.statistics = {
            'total_recommendations': len(recommendations),
            'category_distribution': category_dist,
            'business_impact_distribution': impact_dist,
            'total_potential_savings': round(total_savings, 2),
            'average_potential_savings': round(avg_savings, 2),
            'estimated_monthly_savings': round(total_savings / 12, 2),
            'estimated_working_hours': estimated_hours,
            'advisor_score_impact': round(total_score_impact, 2),
            'top_recommendations': top_recommendations,
            'processing_errors': len(self.errors),
        }

        logger.info(f"Statistics calculated: {self.statistics['total_recommendations']} recommendations, "
                   f"${self.statistics['total_potential_savings']:.2f} potential savings")

        return self.statistics

    def process(self) -> Tuple[List[Dict], Dict]:
        """
        Main processing method - orchestrates the entire CSV processing workflow.

        Returns:
            Tuple[List[Dict], Dict]: (recommendations list, statistics dict)

        Raises:
            CSVProcessingError: If any step of processing fails
        """
        try:
            logger.info(f"Starting CSV processing: {self.file_path}")

            # Step 1: Validate file
            self.validate_file()

            # Step 2: Read CSV
            self.read_csv()

            # Step 3: Validate structure
            self.validate_structure()

            # Step 4: Normalize columns
            self.normalize_column_names()

            # Step 5: Clean data
            self.clean_data()

            # Step 6: Extract recommendations
            recommendations = self.extract_recommendations()

            # Step 7: Calculate statistics
            statistics = self.calculate_statistics(recommendations)

            logger.info(f"CSV processing completed successfully: {len(recommendations)} recommendations")

            return recommendations, statistics

        except CSVProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during CSV processing: {str(e)}", exc_info=True)
            raise CSVProcessingError(f"Failed to process CSV: {str(e)}")


def process_csv_file(file_path: str) -> Tuple[List[Dict], Dict]:
    """
    Convenience function to process a CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        Tuple[List[Dict], Dict]: (recommendations list, statistics dict)

    Raises:
        CSVProcessingError: If processing fails
    """
    processor = AzureAdvisorCSVProcessor(file_path)
    return processor.process()
