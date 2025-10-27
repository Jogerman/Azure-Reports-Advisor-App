"""
File validation utilities for CSV uploads.
"""

import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import pandas as pd


def validate_file_size(file):
    """
    Validate that the uploaded file size is within the allowed limit.

    Args:
        file: UploadedFile instance

    Raises:
        ValidationError: If file size exceeds MAX_UPLOAD_SIZE
    """
    max_size = settings.MAX_UPLOAD_SIZE
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            _(f'File size ({file_size_mb:.2f}MB) exceeds the maximum allowed size ({max_size_mb:.0f}MB).')
        )


def validate_file_extension(file):
    """
    Validate that the uploaded file has an allowed extension.

    Args:
        file: UploadedFile instance

    Raises:
        ValidationError: If file extension is not in ALLOWED_CSV_EXTENSIONS
    """
    ext = os.path.splitext(file.name)[1].lower()
    allowed_extensions = settings.ALLOWED_CSV_EXTENSIONS

    if ext not in allowed_extensions:
        raise ValidationError(
            _(f'Invalid file extension "{ext}". Allowed extensions: {", ".join(allowed_extensions)}')
        )


def validate_csv_structure(file):
    """
    Validate that the CSV file has the required structure for Azure Advisor data.

    Args:
        file: UploadedFile instance

    Raises:
        ValidationError: If CSV structure is invalid or missing required columns
    """
    # Required columns from Azure Advisor CSV export
    # Note: Column names may vary slightly depending on Azure Advisor version
    required_columns_variants = [
        # Standard required columns (at least one variant must exist)
        ['Category', 'category', 'CATEGORY'],
        ['Impact', 'impact', 'IMPACT', 'Business Impact', 'business_impact'],
        ['Recommendation', 'recommendation', 'RECOMMENDATION', 'Description', 'description'],
        ['Affected Resource', 'affected_resource', 'Resource Name', 'resource_name', 'AFFECTED RESOURCE'],
        ['Type', 'type', 'TYPE', 'Resource Type', 'resource_type', 'RESOURCE TYPE'],
    ]

    try:
        # Try different encodings
        df = None
        last_error = None

        for encoding in settings.CSV_ENCODING_OPTIONS:
            try:
                # Reset file pointer
                file.seek(0)
                df = pd.read_csv(file, encoding=encoding, nrows=5)  # Read only first 5 rows for validation
                break
            except UnicodeDecodeError as e:
                last_error = e
                continue

        if df is None:
            raise ValidationError(
                _(f'Unable to read CSV file. Please ensure it is properly encoded (UTF-8 recommended). Error: {str(last_error)}')
            )

        # Check if file is empty
        if df.empty:
            raise ValidationError(_('CSV file is empty. Please upload a file with Azure Advisor recommendations.'))

        # Get actual column names from CSV
        csv_columns = [col.strip() for col in df.columns.tolist()]

        # Check for required columns (at least one variant of each required column)
        missing_columns = []
        for column_variants in required_columns_variants:
            found = any(variant in csv_columns for variant in column_variants)
            if not found:
                missing_columns.append(column_variants[0])  # Use first variant as primary name

        if missing_columns:
            raise ValidationError(
                _(f'CSV file is missing required columns: {", ".join(missing_columns)}. '
                  f'Please ensure this is a valid Azure Advisor export.')
            )

        # Check row count (optional - prevent processing extremely large files)
        file.seek(0)
        row_count = sum(1 for _ in file) - 1  # Subtract header row
        max_rows = settings.CSV_MAX_ROWS

        if row_count > max_rows:
            raise ValidationError(
                _(f'CSV file has {row_count:,} rows, exceeding the maximum allowed ({max_rows:,} rows). '
                  f'Please split the file into smaller chunks.')
            )

        if row_count == 0:
            raise ValidationError(_('CSV file has no data rows (only headers found).'))

    except pd.errors.ParserError as e:
        raise ValidationError(
            _(f'Invalid CSV format. Unable to parse file: {str(e)}')
        )
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(
            _(f'Error validating CSV structure: {str(e)}')
        )
    finally:
        # Reset file pointer for subsequent processing
        file.seek(0)


def validate_csv_content(file):
    """
    Validate CSV content for common issues.

    Args:
        file: UploadedFile instance

    Raises:
        ValidationError: If CSV content has issues
    """
    try:
        file.seek(0)

        # Try to read with different encodings
        df = None
        for encoding in settings.CSV_ENCODING_OPTIONS:
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise ValidationError(_('Unable to read CSV file with any supported encoding.'))

        # Check for completely empty columns
        empty_cols = df.columns[df.isna().all()].tolist()
        if len(empty_cols) > 5:  # Allow some empty columns
            raise ValidationError(
                _(f'CSV file has {len(empty_cols)} completely empty columns. '
                  f'Please clean up the file before uploading.')
            )

        # Check if all data columns are empty
        data_columns = [col for col in df.columns if col.lower() not in ['unnamed', 'index']]
        if df[data_columns].isna().all().all():
            raise ValidationError(_('CSV file appears to have no actual data (all cells are empty).'))

    except pd.errors.EmptyDataError:
        raise ValidationError(_('CSV file is empty or corrupted.'))
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        # Don't fail validation for minor content issues
        pass
    finally:
        file.seek(0)


def validate_csv_file(file):
    """
    Perform all CSV file validations.

    Args:
        file: UploadedFile instance

    Raises:
        ValidationError: If any validation fails
    """
    # Run all validators
    validate_file_size(file)
    validate_file_extension(file)
    validate_csv_structure(file)
    validate_csv_content(file)
