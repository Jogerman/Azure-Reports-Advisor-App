"""
Celery tasks for asynchronous Azure API data fetching and processing.

This module provides Celery tasks that handle:
- Fetching recommendations from Azure Advisor API
- Generating reports from Azure API data
- Testing Azure credentials and connectivity
- Syncing Azure statistics for dashboards

All tasks include comprehensive error handling, retry logic, and monitoring.
"""

import logging
import time
from typing import Dict, List
from datetime import datetime

from celery import shared_task, chain
from celery.exceptions import Ignore, SoftTimeLimitExceeded, Retry
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from apps.reports.models import Report, Recommendation
from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.services.azure_advisor_service import AzureAdvisorService
from apps.azure_integration.exceptions import (
    AzureAuthenticationError,
    AzureAPIError,
    AzureConnectionError,
)

logger = logging.getLogger(__name__)


def _save_recommendations_to_db(report: Report, recommendations: List[dict]) -> int:
    """
    Save Azure recommendations to database.

    Bulk create Recommendation objects from Azure API response.
    Uses transaction.atomic() to ensure all-or-nothing behavior.

    Args:
        report: Report instance to associate recommendations with
        recommendations: List of recommendation dictionaries from AzureAdvisorService

    Returns:
        int: Number of recommendations saved

    Raises:
        Exception: If database operation fails (transaction will rollback)

    Example:
        >>> report = Report.objects.get(id='...')
        >>> recommendations = [{'category': 'Cost', 'impact': 'High', ...}, ...]
        >>> count = _save_recommendations_to_db(report, recommendations)
        >>> print(f"Saved {count} recommendations")
    """
    logger.info(f"Preparing to save {len(recommendations)} recommendations for report {report.id}")

    # Map Azure category names to internal format
    category_mapping = {
        'Cost': 'cost',
        'HighAvailability': 'reliability',
        'Performance': 'performance',
        'Security': 'security',
        'OperationalExcellence': 'operational_excellence',
    }

    # Map Azure impact to business_impact
    impact_mapping = {
        'High': 'high',
        'Medium': 'medium',
        'Low': 'low',
    }

    recommendation_objects = []

    for rec_data in recommendations:
        # Map category
        azure_category = rec_data.get('category', 'Unknown')
        category = category_mapping.get(azure_category, 'cost')

        # Map impact
        azure_impact = rec_data.get('impact', 'Low')
        business_impact = impact_mapping.get(azure_impact, 'low')

        # Extract resource information
        resource_name = rec_data.get('impacted_resource', '')
        resource_type = rec_data.get('resource_type', '')
        resource_group = rec_data.get('resource_group', '')

        # Get recommendation text
        recommendation_text = rec_data.get('recommendation', '')
        if not recommendation_text:
            recommendation_text = rec_data.get('description', 'No description available')

        # Get description
        description = rec_data.get('description', '')

        # Get financial information
        potential_savings = rec_data.get('potential_savings', 0)
        if potential_savings is None:
            potential_savings = 0

        currency = rec_data.get('currency', 'USD')

        # Get metadata
        metadata = rec_data.get('metadata', {})

        # Extract subscription info from metadata if available
        extended_props = metadata.get('extended_properties', {})
        subscription_id = extended_props.get('subscriptionId', '')
        subscription_name = extended_props.get('subscriptionName', '')

        # Create Recommendation object
        recommendation_obj = Recommendation(
            report=report,
            category=category,
            business_impact=business_impact,
            recommendation=recommendation_text[:5000] if recommendation_text else '',
            subscription_id=str(subscription_id)[:255],
            subscription_name=str(subscription_name)[:255],
            resource_group=str(resource_group)[:255],
            resource_name=str(resource_name)[:255],
            resource_type=str(resource_type)[:255],
            potential_savings=potential_savings,
            currency=str(currency)[:3],
            potential_benefits=str(description)[:5000],
            advisor_score_impact=0,  # Azure API doesn't provide this directly
        )

        recommendation_objects.append(recommendation_obj)

    # Bulk create with transaction
    with transaction.atomic():
        Recommendation.objects.bulk_create(recommendation_objects, batch_size=1000)
        logger.info(
            f"Successfully saved {len(recommendation_objects)} recommendations "
            f"to database for report {report.id}"
        )

    return len(recommendation_objects)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=600,  # 10 minutes
    time_limit=660,
    queue='azure_api'
)
def fetch_azure_recommendations(self, report_id: str) -> dict:
    """
    Fetch recommendations from Azure Advisor API and save to database.

    This task:
    1. Retrieves the Report and AzureSubscription from database
    2. Updates report status to 'processing'
    3. Initializes AzureAdvisorService with encrypted credentials
    4. Fetches recommendations using filters from api_sync_metadata
    5. Saves recommendations to database (creates Recommendation objects)
    6. Updates report status and sync metadata
    7. Chains to generate_azure_report task for PDF/Excel generation

    Args:
        report_id: UUID string of the Report instance

    Returns:
        dict: Task result with keys:
            - status: 'success' or 'failed'
            - report_id: UUID string
            - recommendations_count: Number of recommendations fetched
            - error_message: Error details if failed (optional)

    Raises:
        Ignore: If report doesn't exist (likely deleted)
        Retry: If retriable error occurs (API error, connection error)

    Example:
        >>> result = fetch_azure_recommendations.delay('abc-123-def-456')
        >>> # Task executes asynchronously
        >>> # On completion, chains to generate_azure_report
    """
    logger.info(f"Starting Azure recommendations fetch for report {report_id}")

    start_time = time.time()
    report = None
    subscription = None

    try:
        # Get Report instance
        try:
            report = Report.objects.select_related('azure_subscription').get(id=report_id)
        except Report.DoesNotExist:
            error_msg = f"Report {report_id} not found - it may have been deleted"
            logger.error(error_msg)
            raise Ignore()

        # Validate data source
        if report.data_source != 'azure_api':
            error_msg = f"Report {report_id} is not configured for Azure API data source"
            logger.error(error_msg)
            report.status = 'failed'
            report.error_message = error_msg
            report.save(update_fields=['status', 'error_message'])
            raise Ignore()

        # Get Azure subscription
        subscription = report.azure_subscription
        if not subscription:
            error_msg = "Report has no Azure subscription configured"
            logger.error(f"{error_msg} for report {report_id}")
            report.status = 'failed'
            report.error_message = error_msg
            report.save(update_fields=['status', 'error_message'])
            raise Ignore()

        logger.info(
            f"Using Azure subscription: {subscription.name} "
            f"({subscription.subscription_id})"
        )

        # Update report status to processing
        report.status = 'processing'
        report.processing_started_at = timezone.now()
        report.save(update_fields=['status', 'processing_started_at'])

        # Extract filters from api_sync_metadata
        filters = {}
        if report.api_sync_metadata and isinstance(report.api_sync_metadata, dict):
            filters = report.api_sync_metadata.get('filters', {})

        logger.info(f"Applying filters: {filters}")

        # Initialize Azure Advisor Service
        logger.info("Initializing AzureAdvisorService")
        service = AzureAdvisorService(subscription)

        # Fetch recommendations from Azure API
        api_call_count = 0
        requested_at = timezone.now().isoformat()

        try:
            recommendations = service.fetch_recommendations(filters=filters)
            api_call_count = 1  # Simple count, could be enhanced to track pagination

            logger.info(
                f"Fetched {len(recommendations)} recommendations from Azure API "
                f"in {time.time() - start_time:.2f} seconds"
            )
        except Exception as e:
            # Log the error but let it propagate for error handling below
            logger.error(f"Error fetching recommendations from Azure API: {e}")
            raise

        # Save recommendations to database
        try:
            saved_count = _save_recommendations_to_db(report, recommendations)
            logger.info(f"Saved {saved_count} recommendations to database")
        except Exception as e:
            error_msg = f"Failed to save recommendations to database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.save(update_fields=[
                'status', 'error_message', 'processing_completed_at'
            ])
            subscription.update_sync_status('failed', error_msg)
            raise Ignore()

        # Calculate duration
        fetch_duration = time.time() - start_time
        fetched_at = timezone.now().isoformat()

        # Update api_sync_metadata
        sync_metadata = {
            'filters': filters,
            'requested_at': requested_at,
            'fetched_at': fetched_at,
            'recommendations_count': saved_count,
            'fetch_duration_seconds': round(fetch_duration, 2),
            'azure_api_calls': api_call_count,
        }

        # Update report with success status and metadata
        with transaction.atomic():
            report.api_sync_metadata = sync_metadata
            report.status = 'completed'
            report.processing_completed_at = timezone.now()
            report.error_message = ''
            report.save(update_fields=[
                'api_sync_metadata',
                'status',
                'processing_completed_at',
                'error_message'
            ])

        # Update subscription sync status
        subscription.update_sync_status('success')

        logger.info(
            f"Successfully completed Azure recommendations fetch for report {report_id}. "
            f"Saved {saved_count} recommendations in {fetch_duration:.2f}s"
        )

        # Chain to report generation task
        try:
            logger.info(f"Triggering automatic report generation for {report_id}")
            generate_azure_report.delay(str(report_id), format_type='both')
            logger.info(f"Report generation task dispatched for {report_id}")
        except Exception as e:
            logger.error(
                f"Failed to trigger report generation for {report_id}: {str(e)}",
                exc_info=True
            )
            # Don't fail the fetch task if report generation fails to dispatch

        return {
            'status': 'success',
            'report_id': str(report_id),
            'recommendations_count': saved_count,
            'fetch_duration_seconds': round(fetch_duration, 2),
        }

    except Ignore:
        # Re-raise Ignore exceptions
        raise

    except AzureAuthenticationError as e:
        error_msg = f"Azure authentication failed: {str(e)}"
        logger.error(error_msg)

        if report:
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.save(update_fields=[
                'status', 'error_message', 'processing_completed_at'
            ])

        if subscription:
            subscription.update_sync_status('failed', error_msg)

        # Don't retry authentication errors - they need manual intervention
        raise Ignore()

    except (AzureAPIError, AzureConnectionError) as e:
        error_msg = f"Azure API/Connection error: {str(e)}"
        logger.warning(f"{error_msg} - will retry")

        if report:
            report.status = 'failed'
            report.error_message = error_msg
            report.retry_count += 1
            report.save(update_fields=['status', 'error_message', 'retry_count'])

        # Retry on API and connection errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            # Max retries exceeded
            logger.error(f"Max retries exceeded for report {report_id}")
            if subscription:
                subscription.update_sync_status('failed', error_msg)
            raise Ignore()

    except SoftTimeLimitExceeded:
        error_msg = "Task timed out after 10 minutes"
        logger.error(f"Azure recommendations fetch timed out for report {report_id}")

        if report:
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.save(update_fields=[
                'status', 'error_message', 'processing_completed_at'
            ])

        if subscription:
            subscription.update_sync_status('failed', error_msg)

        raise Ignore()

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(f"Unexpected error fetching Azure recommendations: {error_msg}")

        if report:
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.save(update_fields=[
                'status', 'error_message', 'processing_completed_at'
            ])

        if subscription:
            subscription.update_sync_status('failed', error_msg)

        # Don't retry unexpected errors
        raise Ignore()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1200,  # 20 minutes (PDF generation can be slow)
    time_limit=1320,
    queue='reports'
)
def generate_azure_report(self, report_id: str, format_type: str = 'both') -> dict:
    """
    Generate PDF/Excel report from Azure recommendations.

    This task reuses the existing report generation logic but works with
    recommendations fetched from Azure API instead of CSV uploads.

    The task:
    1. Validates report status and recommendation count
    2. Updates status to 'generating'
    3. Uses existing report generators (PDF/Excel)
    4. Uploads files to Azure Blob Storage
    5. Updates report with file URLs
    6. Sets status back to 'completed'

    Args:
        report_id: UUID string of the Report instance
        format_type: 'html', 'pdf', or 'both' (default: 'both')

    Returns:
        dict: Generation result with keys:
            - status: 'success' or 'error'
            - report_id: UUID string
            - files_generated: List of file types generated
            - file_paths: Dict mapping file type to path
            - error: Error message if failed (optional)

    Raises:
        Ignore: If report doesn't exist
        Retry: If generation fails with retriable error

    Example:
        >>> result = generate_azure_report.delay('abc-123', format_type='pdf')
        >>> # Generates PDF report asynchronously
    """
    logger.info(f"Starting Azure report generation for report {report_id}")

    try:
        # Get report instance
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            error_msg = f"Report {report_id} not found - it may have been deleted"
            logger.error(error_msg)
            raise Ignore()

        # Validate report state
        if report.status not in ['completed', 'generating']:
            error_msg = (
                f"Report must be completed before generation. "
                f"Current status: {report.status}"
            )
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg, 'report_id': str(report_id)}

        # Check if we have recommendations
        recommendations_count = report.recommendations.count()
        if recommendations_count == 0:
            error_msg = 'Report has no recommendations to include'
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg, 'report_id': str(report_id)}

        # Validate format type
        if format_type not in ['html', 'pdf', 'both']:
            error_msg = f'Invalid format type: {format_type}'
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg, 'report_id': str(report_id)}

        logger.info(
            f"Generating {format_type} report for {report_id} "
            f"({recommendations_count} recommendations)"
        )

        # Update status to generating
        report.status = 'generating'
        report.save(update_fields=['status'])

        # Import generator module here to avoid circular imports
        from apps.reports.generators import get_generator_for_report

        # Get the appropriate generator
        generator = get_generator_for_report(report)

        files_generated = []
        file_paths = {}

        # Generate HTML
        if format_type in ['html', 'both']:
            logger.info(f"Generating HTML report for {report_id}")
            html_path = generator.generate_html()
            report.html_file = html_path
            files_generated.append('HTML')
            file_paths['html'] = str(html_path) if html_path else None
            logger.info(f"HTML report generated successfully: {html_path}")

        # Generate PDF
        if format_type in ['pdf', 'both']:
            logger.info(f"Generating PDF report for {report_id}")
            pdf_path = generator.generate_pdf()
            report.pdf_file = pdf_path
            files_generated.append('PDF')
            file_paths['pdf'] = str(pdf_path) if pdf_path else None
            logger.info(f"PDF report generated successfully: {pdf_path}")

        # Update report status back to completed
        report.status = 'completed'
        report.save(update_fields=['html_file', 'pdf_file', 'status', 'updated_at'])

        logger.info(
            f"Report generation completed for {report_id}: "
            f"{', '.join(files_generated)}"
        )

        return {
            'status': 'success',
            'report_id': str(report_id),
            'files_generated': files_generated,
            'file_paths': file_paths,
        }

    except Ignore:
        # Re-raise Ignore exceptions
        raise

    except Exception as e:
        error_msg = f"Report generation error: {str(e)}"
        logger.error(
            f"Report generation failed for {report_id}: {error_msg}",
            exc_info=True
        )

        # Update report status back to completed (generation is optional)
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'completed'
            report.save(update_fields=['status'])
        except Exception:
            pass

        # Retry on errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {
            'status': 'error',
            'error': error_msg,
            'report_id': str(report_id)
        }


@shared_task(
    bind=True,
    max_retries=1,  # Only retry once for connection tests
    soft_time_limit=30,  # Quick test
    time_limit=45,
    queue='azure_api'
)
def test_azure_connection(self, subscription_id: str) -> dict:
    """
    Test Azure subscription credentials and connectivity.

    Used when users add/update Azure subscriptions to verify credentials
    are valid and have proper permissions.

    This task:
    1. Loads AzureSubscription from database
    2. Initializes AzureAdvisorService
    3. Calls test_connection() to verify credentials
    4. Updates subscription's sync_status based on result
    5. Returns test results

    Args:
        subscription_id: UUID string of AzureSubscription

    Returns:
        dict: Test results with keys:
            - success: Boolean indicating if test passed
            - subscription_id: UUID string
            - subscription_name: Name of subscription
            - error_message: Error details if test failed

    Raises:
        Ignore: If subscription doesn't exist

    Example:
        >>> result = test_azure_connection.delay('abc-123-def')
        >>> # Returns test results
    """
    logger.info(f"Testing Azure connection for subscription {subscription_id}")

    try:
        # Get subscription
        try:
            subscription = AzureSubscription.objects.get(id=subscription_id)
        except AzureSubscription.DoesNotExist:
            error_msg = f"AzureSubscription {subscription_id} not found"
            logger.error(error_msg)
            raise Ignore()

        logger.info(
            f"Testing connection for: {subscription.name} "
            f"({subscription.subscription_id})"
        )

        # Initialize service and test connection
        try:
            service = AzureAdvisorService(subscription)
            result = service.test_connection()

            logger.info(f"Connection test result: {result}")

            # Update subscription sync status
            if result['success']:
                subscription.update_sync_status('success')
                logger.info(f"Connection test successful for {subscription.name}")
            else:
                subscription.update_sync_status('failed', result['error_message'])
                logger.warning(
                    f"Connection test failed for {subscription.name}: "
                    f"{result['error_message']}"
                )

            return result

        except AzureAuthenticationError as e:
            error_msg = str(e)
            logger.error(f"Authentication error: {error_msg}")
            subscription.update_sync_status('failed', error_msg)
            return {
                'success': False,
                'subscription_id': subscription.subscription_id,
                'subscription_name': subscription.name,
                'error_message': error_msg,
            }

        except (AzureAPIError, AzureConnectionError) as e:
            error_msg = str(e)
            logger.error(f"Connection/API error: {error_msg}")
            subscription.update_sync_status('failed', error_msg)

            # Retry once for connection errors
            if self.request.retries < self.max_retries:
                logger.info("Retrying connection test once")
                raise self.retry(exc=e, countdown=5)

            return {
                'success': False,
                'subscription_id': subscription.subscription_id,
                'subscription_name': subscription.name,
                'error_message': error_msg,
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            subscription.update_sync_status('failed', error_msg)
            return {
                'success': False,
                'subscription_id': subscription.subscription_id,
                'subscription_name': subscription.name,
                'error_message': error_msg,
            }

    except Ignore:
        raise


@shared_task(
    bind=True,
    soft_time_limit=120,  # 2 minutes
    time_limit=150,
    queue='azure_api'
)
def sync_azure_statistics(self, subscription_id: str) -> dict:
    """
    Fetch and cache Azure Advisor statistics for a subscription.

    Used for dashboard displays showing recommendation counts by
    category/impact without fetching full recommendation details.

    Statistics are cached for 1 hour to reduce API calls.

    This task:
    1. Loads AzureSubscription from database
    2. Initializes AzureAdvisorService
    3. Calls get_statistics() to fetch aggregated data
    4. Updates subscription's sync_status
    5. Returns statistics

    Args:
        subscription_id: UUID string of AzureSubscription

    Returns:
        dict: Statistics with keys:
            - total_recommendations: Total count
            - by_category: Dict of counts by category
            - by_impact: Dict of counts by impact level
            - total_potential_savings: Sum of cost savings (if any)
            - currency: Currency code for savings
            - success: Boolean indicating if fetch succeeded
            - error_message: Error details if failed

    Raises:
        Ignore: If subscription doesn't exist

    Example:
        >>> result = sync_azure_statistics.delay('abc-123-def')
        >>> # Returns statistics or error
    """
    logger.info(f"Syncing Azure statistics for subscription {subscription_id}")

    try:
        # Get subscription
        try:
            subscription = AzureSubscription.objects.get(id=subscription_id)
        except AzureSubscription.DoesNotExist:
            error_msg = f"AzureSubscription {subscription_id} not found"
            logger.error(error_msg)
            raise Ignore()

        logger.info(
            f"Fetching statistics for: {subscription.name} "
            f"({subscription.subscription_id})"
        )

        # Initialize service and get statistics
        try:
            service = AzureAdvisorService(subscription)
            stats = service.get_statistics()

            logger.info(
                f"Successfully fetched statistics: "
                f"{stats['total_recommendations']} recommendations"
            )

            # Update subscription sync status
            subscription.update_sync_status('success')

            # Add success flag to response
            stats['success'] = True
            stats['error_message'] = None

            return stats

        except AzureAuthenticationError as e:
            error_msg = str(e)
            logger.error(f"Authentication error: {error_msg}")
            subscription.update_sync_status('failed', error_msg)
            return {
                'success': False,
                'error_message': error_msg,
                'total_recommendations': 0,
                'by_category': {},
                'by_impact': {},
                'total_potential_savings': None,
                'currency': None,
            }

        except (AzureAPIError, AzureConnectionError) as e:
            error_msg = str(e)
            logger.error(f"Error fetching statistics: {error_msg}")
            subscription.update_sync_status('failed', error_msg)
            return {
                'success': False,
                'error_message': error_msg,
                'total_recommendations': 0,
                'by_category': {},
                'by_impact': {},
                'total_potential_savings': None,
                'currency': None,
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            subscription.update_sync_status('failed', error_msg)
            return {
                'success': False,
                'error_message': error_msg,
                'total_recommendations': 0,
                'by_category': {},
                'by_impact': {},
                'total_potential_savings': None,
                'currency': None,
            }

    except Ignore:
        raise
