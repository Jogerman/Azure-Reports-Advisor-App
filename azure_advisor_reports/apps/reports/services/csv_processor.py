"""
CSV file processor for Azure Advisor recommendations.
"""

import csv
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.db import transaction
from ..models import Recommendation

logger = logging.getLogger(__name__)


class CSVProcessingError(Exception):
    """Custom exception for CSV processing errors."""
    pass


def process_csv_file(csv_file_path, report):
    """
    Process CSV file containing Azure Advisor recommendations.

    Expected CSV format:
    - Category: Cost, Security, Performance, Operational Excellence, Reliability
    - Impact: High, Medium, Low
    - Title: Recommendation title
    - Description: Detailed description
    - Resource Name: Name of the resource
    - Resource Type: Type of Azure resource
    - Resource Group: Resource group name
    - Subscription ID: Azure subscription ID
    - Potential Savings: Estimated cost savings (optional)
    - Additional columns are stored in metadata

    Args:
        csv_file_path: Path to the CSV file
        report: Report instance to associate recommendations with

    Returns:
        Dictionary with processing results

    Raises:
        CSVProcessingError: If CSV processing fails
    """
    try:
        recommendations_created = 0
        total_savings = Decimal('0')
        impact_counts = {'High': 0, 'Medium': 0, 'Low': 0}

        # Open and read CSV file
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
            # Detect dialect
            sample = csvfile.read(1024)
            csvfile.seek(0)
            dialect = csv.Sniffer().sniff(sample)

            # Read CSV
            reader = csv.DictReader(csvfile, dialect=dialect)

            # Validate headers
            required_headers = ['Category', 'Impact', 'Title', 'Description']
            headers = [h.strip() for h in reader.fieldnames]

            missing_headers = [h for h in required_headers if h not in headers]
            if missing_headers:
                raise CSVProcessingError(
                    f"Missing required columns: {', '.join(missing_headers)}"
                )

            # Process each row
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Clean and validate data
                        category = row.get('Category', '').strip()
                        impact = row.get('Impact', '').strip()
                        title = row.get('Title', '').strip()
                        description = row.get('Description', '').strip()

                        if not all([category, impact, title, description]):
                            logger.warning(
                                f"Row {row_num}: Skipping row with missing required fields"
                            )
                            continue

                        # Validate category
                        valid_categories = [
                            'Cost', 'Security', 'Performance',
                            'Operational Excellence', 'Reliability'
                        ]
                        if category not in valid_categories:
                            logger.warning(
                                f"Row {row_num}: Invalid category '{category}', "
                                f"using 'Operational Excellence'"
                            )
                            category = 'Operational Excellence'

                        # Validate impact
                        valid_impacts = ['High', 'Medium', 'Low']
                        if impact not in valid_impacts:
                            logger.warning(
                                f"Row {row_num}: Invalid impact '{impact}', using 'Medium'"
                            )
                            impact = 'Medium'

                        # Parse potential savings
                        potential_savings = None
                        savings_str = row.get('Potential Savings', '').strip()
                        if savings_str:
                            try:
                                # Remove currency symbols and commas
                                cleaned_savings = savings_str.replace('$', '').replace(',', '')
                                potential_savings = Decimal(cleaned_savings)
                                total_savings += potential_savings
                            except (InvalidOperation, ValueError):
                                logger.warning(
                                    f"Row {row_num}: Invalid savings value '{savings_str}'"
                                )

                        # Extract resource information
                        resource_name = row.get('Resource Name', '').strip() or None
                        resource_type = row.get('Resource Type', '').strip() or None
                        resource_group = row.get('Resource Group', '').strip() or None
                        subscription_id = row.get('Subscription ID', '').strip() or None

                        # Build metadata from additional columns
                        metadata = {}
                        metadata_fields = [
                            'Region', 'Tags', 'Severity', 'Risk', 'Action',
                            'Affected Resource', 'Last Detected', 'Recommendation ID'
                        ]
                        for field in metadata_fields:
                            if field in row and row[field]:
                                metadata[field.lower().replace(' ', '_')] = row[field].strip()

                        # Create recommendation
                        recommendation = Recommendation.objects.create(
                            report=report,
                            category=category,
                            impact=impact,
                            title=title[:500],  # Limit to field max length
                            description=description,
                            recommendation=row.get('Recommendation', description)[:1000],
                            resource_name=resource_name,
                            resource_type=resource_type,
                            resource_group=resource_group,
                            subscription_id=subscription_id,
                            potential_savings=potential_savings,
                            currency=row.get('Currency', 'USD').strip()[:3],
                            metadata=metadata
                        )

                        recommendations_created += 1
                        impact_counts[impact] += 1

                        logger.debug(
                            f"Row {row_num}: Created recommendation {recommendation.id}"
                        )

                    except Exception as e:
                        logger.error(f"Row {row_num}: Error processing row: {str(e)}")
                        # Continue processing other rows

        if recommendations_created == 0:
            raise CSVProcessingError(
                "No valid recommendations found in CSV file"
            )

        logger.info(
            f"Successfully processed {recommendations_created} recommendations "
            f"from CSV for report {report.id}"
        )

        return {
            'total_recommendations': recommendations_created,
            'high_impact_count': impact_counts['High'],
            'medium_impact_count': impact_counts['Medium'],
            'low_impact_count': impact_counts['Low'],
            'estimated_savings': total_savings,
        }

    except CSVProcessingError:
        raise

    except FileNotFoundError:
        raise CSVProcessingError(f"CSV file not found: {csv_file_path}")

    except csv.Error as e:
        raise CSVProcessingError(f"CSV format error: {str(e)}")

    except Exception as e:
        logger.exception("Unexpected error processing CSV file")
        raise CSVProcessingError(f"Unexpected error: {str(e)}")


def validate_csv_file(csv_file):
    """
    Validate CSV file format before processing.

    Args:
        csv_file: File object or path to CSV file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Read first few lines to validate
        if hasattr(csv_file, 'read'):
            csv_file.seek(0)
            sample = csv_file.read(2048)
            csv_file.seek(0)
            content = csv_file.read().decode('utf-8-sig')
            csv_file.seek(0)
        else:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                sample = f.read(2048)
                f.seek(0)
                content = f.read()

        # Check if file is empty
        if not content.strip():
            return False, "CSV file is empty"

        # Try to parse CSV
        try:
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(content.splitlines(), dialect=dialect)
            headers = [h.strip() for h in reader.fieldnames]
        except csv.Error:
            return False, "Invalid CSV format"

        # Validate required headers
        required_headers = ['Category', 'Impact', 'Title', 'Description']
        missing_headers = [h for h in required_headers if h not in headers]

        if missing_headers:
            return False, f"Missing required columns: {', '.join(missing_headers)}"

        # Count rows
        row_count = sum(1 for _ in reader)
        if row_count == 0:
            return False, "CSV file contains no data rows"

        return True, None

    except Exception as e:
        return False, f"Error validating CSV: {str(e)}"


def export_recommendations_to_csv(recommendations_queryset, output_file):
    """
    Export recommendations to CSV file.

    Args:
        recommendations_queryset: QuerySet of Recommendation objects
        output_file: Path or file object to write CSV to

    Returns:
        Number of recommendations exported
    """
    fieldnames = [
        'Category', 'Impact', 'Title', 'Description', 'Recommendation',
        'Resource Name', 'Resource Type', 'Resource Group', 'Subscription ID',
        'Potential Savings', 'Currency', 'Created At'
    ]

    count = 0

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for rec in recommendations_queryset:
            writer.writerow({
                'Category': rec.category,
                'Impact': rec.impact,
                'Title': rec.title,
                'Description': rec.description,
                'Recommendation': rec.recommendation,
                'Resource Name': rec.resource_name or '',
                'Resource Type': rec.resource_type or '',
                'Resource Group': rec.resource_group or '',
                'Subscription ID': rec.subscription_id or '',
                'Potential Savings': str(rec.potential_savings) if rec.potential_savings else '',
                'Currency': rec.currency,
                'Created At': rec.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            count += 1

    return count
