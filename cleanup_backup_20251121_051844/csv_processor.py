"""
Azure Advisor CSV Processing Pipeline
=====================================

This module provides comprehensive CSV parsing, validation, and data processing
capabilities for Azure Advisor recommendation exports.

Features:
- Handles UTF-8 with BOM encoding issues
- Validates CSV structure and required columns
- Processes large files efficiently with memory management
- Categorizes recommendations and calculates metrics
- Provides detailed error reporting and data validation

Author: Data Analytics Team
Date: September 29, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import io
import chardet


class RecommendationCategory(Enum):
    """Azure Advisor recommendation categories"""
    COST = "Cost"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    HIGH_AVAILABILITY = "HighAvailability"
    OPERATIONAL_EXCELLENCE = "OperationalExcellence"


class BusinessImpact(Enum):
    """Business impact levels"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskLevel(Enum):
    """Risk levels"""
    ERROR = "Error"
    WARNING = "Warning"
    NONE = "None"


@dataclass
class ValidationResult:
    """Result of CSV validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    row_count: int
    column_count: int
    missing_columns: List[str]
    extra_columns: List[str]


@dataclass
class ProcessingMetrics:
    """Metrics calculated during CSV processing"""
    total_recommendations: int
    category_distribution: Dict[str, int]
    business_impact_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]
    estimated_annual_savings: Decimal
    average_savings_per_recommendation: Decimal
    top_categories_by_savings: List[Tuple[str, Decimal]]
    recommendations_by_subscription: Dict[str, int]
    recommendations_by_resource_type: Dict[str, int]
    advisor_score: float


class AzureAdvisorCSVProcessor:
    """
    Processes Azure Advisor CSV exports with comprehensive validation and analysis
    """

    # Required columns in Azure Advisor CSV export
    REQUIRED_COLUMNS = [
        'Category',
        'Business Impact',
        'Recommendation',
        'Subscription ID',
        'Resource Name',
        'Resource Type'
    ]

    # Optional columns that may be present
    OPTIONAL_COLUMNS = [
        'Subscription Name',
        'Resource Group',
        'Potential Benefits',
        'Potential Annual Cost Savings (USD)',
        'Currency',
        'Retirement Date',
        'Retiring Feature',
        'Last Updated',
        'Assessment Key',
        'Resource ID',
        'Risk Level',
        'Impacted Field',
        'Impacted Value',
        'Recommendation Type ID',
        'Action'
    ]

    # All possible columns
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    def __init__(self, max_file_size_mb: int = 50, chunk_size: int = 1000):
        """
        Initialize the CSV processor

        Args:
            max_file_size_mb: Maximum allowed file size in MB
            chunk_size: Number of rows to process in each chunk for memory efficiency
        """
        self.max_file_size_mb = max_file_size_mb
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

        # Setup logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding to handle UTF-8 with BOM issues

        Args:
            file_path: Path to the CSV file

        Returns:
            Detected encoding string
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding']

                # Handle UTF-8 with BOM
                if encoding.lower() in ['utf-8', 'utf-8-sig']:
                    # Check for BOM
                    if raw_data.startswith(b'\xef\xbb\xbf'):
                        return 'utf-8-sig'
                    else:
                        return 'utf-8'

                return encoding
        except Exception as e:
            self.logger.warning(f"Could not detect encoding: {e}. Defaulting to utf-8-sig")
            return 'utf-8-sig'

    def validate_file_size(self, file_path: str) -> bool:
        """
        Validate file size is within limits

        Args:
            file_path: Path to the CSV file

        Returns:
            True if file size is acceptable
        """
        try:
            import os
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            if file_size_mb > self.max_file_size_mb:
                self.logger.error(
                    f"File size {file_size_mb:.1f}MB exceeds maximum allowed size of {self.max_file_size_mb}MB"
                )
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error checking file size: {e}")
            return False

    def validate_csv_structure(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate CSV structure and content

        Args:
            df: DataFrame to validate

        Returns:
            ValidationResult object with validation details
        """
        errors = []
        warnings = []

        # Check if DataFrame is empty
        if df.empty:
            errors.append("CSV file is empty")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                row_count=0,
                column_count=0,
                missing_columns=self.REQUIRED_COLUMNS,
                extra_columns=[]
            )

        # Get actual columns (case-insensitive comparison)
        actual_columns = df.columns.tolist()
        actual_columns_lower = [col.lower().strip() for col in actual_columns]
        required_columns_lower = [col.lower() for col in self.REQUIRED_COLUMNS]

        # Check for missing required columns
        missing_columns = []
        for req_col in self.REQUIRED_COLUMNS:
            if req_col.lower() not in actual_columns_lower:
                missing_columns.append(req_col)

        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        # Check for extra columns (informational)
        all_expected_lower = [col.lower() for col in self.ALL_COLUMNS]
        extra_columns = []
        for col in actual_columns:
            if col.lower().strip() not in all_expected_lower:
                extra_columns.append(col)

        if extra_columns:
            warnings.append(f"Unexpected columns found: {', '.join(extra_columns)}")

        # Validate data types and content
        if not missing_columns:  # Only if we have required columns
            try:
                # Check Category values
                if 'Category' in df.columns:
                    valid_categories = [cat.value for cat in RecommendationCategory]
                    invalid_categories = df['Category'].dropna().unique()
                    invalid_categories = [cat for cat in invalid_categories if cat not in valid_categories]

                    if invalid_categories:
                        warnings.append(f"Invalid category values found: {', '.join(invalid_categories)}")

                # Check Business Impact values
                if 'Business Impact' in df.columns:
                    valid_impacts = [impact.value for impact in BusinessImpact]
                    invalid_impacts = df['Business Impact'].dropna().unique()
                    invalid_impacts = [impact for impact in invalid_impacts if impact not in valid_impacts]

                    if invalid_impacts:
                        warnings.append(f"Invalid business impact values found: {', '.join(invalid_impacts)}")

                # Check for empty recommendations
                if 'Recommendation' in df.columns:
                    empty_recommendations = df['Recommendation'].isna().sum()
                    if empty_recommendations > 0:
                        warnings.append(f"{empty_recommendations} rows have empty recommendations")

            except Exception as e:
                warnings.append(f"Error during content validation: {str(e)}")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            row_count=len(df),
            column_count=len(df.columns),
            missing_columns=missing_columns,
            extra_columns=extra_columns
        )

    def parse_cost_savings(self, cost_str: str) -> Decimal:
        """
        Parse cost savings string and convert to decimal

        Args:
            cost_str: Cost string (e.g., "$2,400.00", "2400", "N/A")

        Returns:
            Decimal value of cost savings
        """
        if pd.isna(cost_str) or cost_str in ['N/A', '', 'Not Available']:
            return Decimal('0')

        try:
            # Remove currency symbols, commas, and whitespace
            clean_str = re.sub(r'[$,\s]', '', str(cost_str))

            # Handle negative values
            if clean_str.startswith('-'):
                clean_str = clean_str[1:]
                multiplier = -1
            else:
                multiplier = 1

            # Convert to decimal
            value = Decimal(clean_str) * multiplier
            return value

        except (InvalidOperation, ValueError) as e:
            self.logger.warning(f"Could not parse cost savings '{cost_str}': {e}")
            return Decimal('0')

    def parse_datetime(self, date_str: str) -> Optional[datetime]:
        """
        Parse datetime string from various formats

        Args:
            date_str: Date string in various formats

        Returns:
            Parsed datetime object or None
        """
        if pd.isna(date_str) or date_str == '':
            return None

        # Common date formats
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',      # ISO format with Z
            '%Y-%m-%dT%H:%M:%S',       # ISO format without Z
            '%Y-%m-%d %H:%M:%S',       # Standard format
            '%Y-%m-%d',                # Date only
            '%m/%d/%Y',                # US format
            '%d/%m/%Y',                # European format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue

        self.logger.warning(f"Could not parse date: {date_str}")
        return None

    def clean_and_standardize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the CSV data

        Args:
            df: Raw DataFrame

        Returns:
            Cleaned and standardized DataFrame
        """
        df_clean = df.copy()

        # Standardize column names (handle case variations)
        column_mapping = {}
        for col in df_clean.columns:
            col_lower = col.lower().strip()
            for expected_col in self.ALL_COLUMNS:
                if col_lower == expected_col.lower():
                    column_mapping[col] = expected_col
                    break

        df_clean = df_clean.rename(columns=column_mapping)

        # Clean text fields
        text_columns = ['Recommendation', 'Potential Benefits', 'Action', 'Resource Name']
        for col in text_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                df_clean[col] = df_clean[col].replace('nan', '')

        # Standardize category values
        if 'Category' in df_clean.columns:
            category_mapping = {
                'cost': 'Cost',
                'security': 'Security',
                'performance': 'Performance',
                'highavailability': 'HighAvailability',
                'operationalexcellence': 'OperationalExcellence',
                'high availability': 'HighAvailability',
                'operational excellence': 'OperationalExcellence'
            }

            df_clean['Category'] = df_clean['Category'].str.lower().map(
                lambda x: category_mapping.get(x, x.title() if isinstance(x, str) else x)
            )

        # Standardize business impact
        if 'Business Impact' in df_clean.columns:
            impact_mapping = {
                'high': 'High',
                'medium': 'Medium',
                'low': 'Low'
            }

            df_clean['Business Impact'] = df_clean['Business Impact'].str.lower().map(
                lambda x: impact_mapping.get(x, x.title() if isinstance(x, str) else x)
            )

        # Parse cost savings
        if 'Potential Annual Cost Savings (USD)' in df_clean.columns:
            df_clean['Parsed_Cost_Savings'] = df_clean['Potential Annual Cost Savings (USD)'].apply(
                self.parse_cost_savings
            )
        else:
            df_clean['Parsed_Cost_Savings'] = Decimal('0')

        # Parse dates
        if 'Last Updated' in df_clean.columns:
            df_clean['Parsed_Last_Updated'] = df_clean['Last Updated'].apply(
                self.parse_datetime
            )

        # Add computed fields
        df_clean['Processing_Date'] = datetime.now()

        # Create unique identifier if not present
        if 'Assessment Key' not in df_clean.columns:
            df_clean['Assessment Key'] = df_clean.apply(
                lambda row: f"{row.get('Resource Name', 'unknown')}-{row.get('Category', 'unknown')}-assessment",
                axis=1
            )

        return df_clean

    def calculate_metrics(self, df: pd.DataFrame) -> ProcessingMetrics:
        """
        Calculate comprehensive metrics from the processed data

        Args:
            df: Cleaned DataFrame

        Returns:
            ProcessingMetrics object with calculated metrics
        """
        total_recommendations = len(df)

        # Category distribution
        category_distribution = df['Category'].value_counts().to_dict() if 'Category' in df.columns else {}

        # Business impact distribution
        business_impact_distribution = df['Business Impact'].value_counts().to_dict() if 'Business Impact' in df.columns else {}

        # Risk distribution
        risk_distribution = df['Risk Level'].value_counts().to_dict() if 'Risk Level' in df.columns else {}

        # Cost savings calculations
        total_savings = df['Parsed_Cost_Savings'].sum() if 'Parsed_Cost_Savings' in df.columns else Decimal('0')
        avg_savings = total_savings / total_recommendations if total_recommendations > 0 else Decimal('0')

        # Top categories by savings
        if 'Category' in df.columns and 'Parsed_Cost_Savings' in df.columns:
            category_savings = df.groupby('Category')['Parsed_Cost_Savings'].sum().sort_values(ascending=False)
            top_categories_by_savings = [(cat, savings) for cat, savings in category_savings.head(5).items()]
        else:
            top_categories_by_savings = []

        # Subscriptions distribution
        subscriptions_dist = df['Subscription ID'].value_counts().to_dict() if 'Subscription ID' in df.columns else {}

        # Resource types distribution
        resource_types_dist = df['Resource Type'].value_counts().to_dict() if 'Resource Type' in df.columns else {}

        # Calculate Advisor Score (0-100 based on recommendation distribution and impact)
        advisor_score = self._calculate_advisor_score(df)

        return ProcessingMetrics(
            total_recommendations=total_recommendations,
            category_distribution=category_distribution,
            business_impact_distribution=business_impact_distribution,
            risk_distribution=risk_distribution,
            estimated_annual_savings=total_savings,
            average_savings_per_recommendation=avg_savings,
            top_categories_by_savings=top_categories_by_savings,
            recommendations_by_subscription=subscriptions_dist,
            recommendations_by_resource_type=resource_types_dist,
            advisor_score=advisor_score
        )

    def _calculate_advisor_score(self, df: pd.DataFrame) -> float:
        """
        Calculate Azure Advisor Score (0-100) based on recommendations

        Args:
            df: Processed DataFrame

        Returns:
            Advisor score between 0 and 100
        """
        if df.empty:
            return 100.0  # Perfect score if no recommendations

        # Weight factors for different impacts
        impact_weights = {
            'High': 3.0,
            'Medium': 2.0,
            'Low': 1.0
        }

        # Calculate weighted score based on business impact
        total_weight = 0
        if 'Business Impact' in df.columns:
            for impact, count in df['Business Impact'].value_counts().items():
                weight = impact_weights.get(impact, 1.0)
                total_weight += count * weight

        # Base score calculation (inverse relationship - more recommendations = lower score)
        base_score = max(0, 100 - (total_weight / len(df)) * 20)

        # Adjust based on category distribution (balance is better)
        if 'Category' in df.columns:
            category_counts = df['Category'].value_counts()
            category_balance = 1.0 - (category_counts.std() / category_counts.mean()) if len(category_counts) > 1 else 1.0
            base_score *= (0.8 + 0.2 * category_balance)

        return round(min(100.0, max(0.0, base_score)), 1)

    def process_csv_file(self, file_path: str) -> Tuple[pd.DataFrame, ValidationResult, ProcessingMetrics]:
        """
        Main method to process an Azure Advisor CSV file

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (processed_dataframe, validation_result, processing_metrics)
        """
        self.logger.info(f"Starting processing of CSV file: {file_path}")

        # Validate file size
        if not self.validate_file_size(file_path):
            raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size_mb}MB")

        # Detect encoding
        encoding = self.detect_encoding(file_path)
        self.logger.info(f"Detected encoding: {encoding}")

        try:
            # Read CSV file
            self.logger.info("Reading CSV file...")
            df = pd.read_csv(file_path, encoding=encoding, dtype=str)

            self.logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")

            # Validate structure
            self.logger.info("Validating CSV structure...")
            validation_result = self.validate_csv_structure(df)

            if not validation_result.is_valid:
                self.logger.error("CSV validation failed:")
                for error in validation_result.errors:
                    self.logger.error(f"  - {error}")
                raise ValueError(f"CSV validation failed: {'; '.join(validation_result.errors)}")

            # Log warnings
            for warning in validation_result.warnings:
                self.logger.warning(f"  - {warning}")

            # Clean and standardize data
            self.logger.info("Cleaning and standardizing data...")
            df_processed = self.clean_and_standardize_data(df)

            # Calculate metrics
            self.logger.info("Calculating metrics...")
            metrics = self.calculate_metrics(df_processed)

            self.logger.info("CSV processing completed successfully")
            self.logger.info(f"Total recommendations: {metrics.total_recommendations}")
            self.logger.info(f"Estimated annual savings: ${metrics.estimated_annual_savings:,.2f}")
            self.logger.info(f"Advisor Score: {metrics.advisor_score}")

            return df_processed, validation_result, metrics

        except Exception as e:
            self.logger.error(f"Error processing CSV file: {e}")
            raise


def process_azure_advisor_csv(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to process Azure Advisor CSV file

    Args:
        file_path: Path to the CSV file
        **kwargs: Additional arguments for AzureAdvisorCSVProcessor

    Returns:
        Dictionary containing processed data and metrics
    """
    processor = AzureAdvisorCSVProcessor(**kwargs)
    df, validation, metrics = processor.process_csv_file(file_path)

    return {
        'dataframe': df,
        'validation_result': validation,
        'metrics': metrics,
        'success': True
    }


# Example usage and testing
if __name__ == "__main__":
    # Test with the sample CSV file
    sample_file = "D:\\Code\\Azure Reports\\sample_azure_advisor_export.csv"

    try:
        result = process_azure_advisor_csv(sample_file)

        print("=== Processing Results ===")
        print(f"Success: {result['success']}")
        print(f"Rows processed: {len(result['dataframe'])}")
        print(f"Validation errors: {len(result['validation_result'].errors)}")
        print(f"Validation warnings: {len(result['validation_result'].warnings)}")

        metrics = result['metrics']
        print(f"\n=== Metrics ===")
        print(f"Total recommendations: {metrics.total_recommendations}")
        print(f"Estimated annual savings: ${metrics.estimated_annual_savings:,.2f}")
        print(f"Advisor Score: {metrics.advisor_score}")
        print(f"Category distribution: {metrics.category_distribution}")
        print(f"Business impact distribution: {metrics.business_impact_distribution}")

    except Exception as e:
        print(f"Error: {e}")