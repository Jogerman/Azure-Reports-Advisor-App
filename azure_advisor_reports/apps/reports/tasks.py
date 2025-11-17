"""
Celery tasks for asynchronous report processing.
"""

import logging
import tempfile
import os
from celery import shared_task
from celery.exceptions import Ignore, SoftTimeLimitExceeded
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage

from apps.reports.models import Report, Recommendation
from apps.reports.services.csv_processor import AzureAdvisorCSVProcessor, CSVProcessingError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, soft_time_limit=600, time_limit=660)
def process_csv_file(self, report_id):
    """
    Process uploaded CSV file asynchronously and create recommendations.

    Args:
        report_id: UUID of the Report instance

    Returns:
        dict: Processing result with status and details
    """
    logger.info(f"Starting CSV processing task for report {report_id}")

    try:
        # Get report instance
        report = Report.objects.get(id=report_id)

        # Update status to processing
        report.status = 'processing'
        report.processing_started_at = timezone.now()
        report.save(update_fields=['status', 'processing_started_at'])

        # Check if CSV file exists
        if not report.csv_file:
            raise ValueError("No CSV file attached to report")

        # Download file from Azure Blob Storage to a temporary location
        temp_file = None
        temp_file_path = None
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
            temp_file_path = temp_file.name

            logger.info(f"Downloading CSV file from storage to temporary file: {temp_file_path}")

            # Open the file from storage and copy it to the temp file
            with report.csv_file.open('rb') as storage_file:
                # Read and write in chunks (Azure Blob Storage doesn't have .chunks() method)
                chunk_size = 8192
                while True:
                    chunk = storage_file.read(chunk_size)
                    if not chunk:
                        break
                    temp_file.write(chunk)

            temp_file.close()
            logger.info(f"CSV file downloaded successfully to: {temp_file_path}")

            # Initialize CSV processor with temporary file path
            processor = AzureAdvisorCSVProcessor(temp_file_path)

            # Process CSV
            recommendations_data, statistics = processor.process()

        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Temporary file deleted: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")

        # Save recommendations to database
        with transaction.atomic():
            # Create recommendation instances
            recommendation_instances = []
            for rec_data in recommendations_data:
                recommendation = Recommendation(
                    report=report,
                    category=rec_data['category'],
                    business_impact=rec_data['business_impact'],
                    recommendation=rec_data['recommendation'][:5000] if rec_data['recommendation'] else '',
                    subscription_id=str(rec_data.get('subscription_id', ''))[:255],
                    subscription_name=str(rec_data.get('subscription_name', ''))[:255],
                    resource_group=str(rec_data.get('resource_group', ''))[:255],
                    resource_name=str(rec_data.get('resource_name', ''))[:255],
                    resource_type=str(rec_data.get('resource_type', ''))[:255],
                    potential_savings=rec_data.get('potential_savings', 0),
                    currency=str(rec_data.get('currency', 'USD'))[:3],
                    potential_benefits=str(rec_data.get('potential_benefits', ''))[:5000],
                    retirement_date=rec_data.get('retirement_date'),
                    retiring_feature=str(rec_data.get('retiring_feature', ''))[:255],
                    advisor_score_impact=rec_data.get('advisor_score_impact', 0),
                    csv_row_number=rec_data.get('csv_row_number'),
                )
                recommendation_instances.append(recommendation)

            # Bulk create recommendations
            if recommendation_instances:
                Recommendation.objects.bulk_create(recommendation_instances, batch_size=1000)
                logger.info(f"Created {len(recommendation_instances)} recommendations for report {report_id}")

            # Update report with statistics and mark as completed
            report.analysis_data = statistics
            report.status = 'completed'
            report.processing_completed_at = timezone.now()
            report.error_message = ''
            report.save(update_fields=[
                'analysis_data', 'status', 'processing_completed_at', 'error_message'
            ])

        logger.info(f"CSV processing completed successfully for report {report_id}")

        # Automatically trigger report generation after successful CSV processing
        try:
            logger.info(f"Triggering automatic report generation for {report_id}")
            generate_report.delay(str(report_id), format_type='both')
            logger.info(f"Report generation task dispatched for {report_id}")
        except Exception as e:
            logger.error(f"Failed to trigger report generation for {report_id}: {str(e)}", exc_info=True)
            # Don't fail the CSV processing task if report generation fails to dispatch

        return {
            'status': 'success',
            'report_id': str(report_id),
            'recommendations_count': len(recommendations_data),
            'statistics': statistics,
        }

    except Report.DoesNotExist:
        error_msg = f"Report with ID {report_id} not found - it may have been deleted"
        logger.error(error_msg)
        # Don't retry if the report doesn't exist - it was likely deleted
        # Raise Ignore to mark this task as complete without retries
        raise Ignore()

    except SoftTimeLimitExceeded:
        error_msg = "CSV processing timed out after 10 minutes. The file may be too large or complex."
        logger.error(f"CSV processing timed out for report {report_id}")

        # Update report status to failed
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.save(update_fields=['status', 'error_message', 'processing_completed_at'])
        except:
            pass

        return {'status': 'error', 'error': error_msg, 'report_id': str(report_id)}

    except CSVProcessingError as e:
        error_msg = f"CSV processing error: {str(e)}"
        logger.error(f"CSV processing failed for report {report_id}: {error_msg}")

        # Update report status to failed
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.retry_count += 1
            report.save(update_fields=['status', 'error_message', 'processing_completed_at', 'retry_count'])
        except:
            pass

        # Retry if not exceeded max retries
        if report.retry_count < 3:
            raise self.retry(exc=e, countdown=60 * (report.retry_count + 1))

        return {'status': 'error', 'error': error_msg, 'report_id': str(report_id)}

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error processing CSV for report {report_id}: {error_msg}", exc_info=True)

        # Update report status to failed
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = error_msg
            report.processing_completed_at = timezone.now()
            report.retry_count += 1
            report.save(update_fields=['status', 'error_message', 'processing_completed_at', 'retry_count'])
        except:
            pass

        # Retry on unexpected errors
        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_old_csv_files():
    """
    Periodic task to cleanup old CSV files and failed reports.

    This task should be scheduled to run daily via Celery Beat.
    """
    from datetime import timedelta
    from django.utils import timezone

    # Delete failed reports older than 7 days
    cutoff_date = timezone.now() - timedelta(days=7)
    old_failed_reports = Report.objects.filter(
        status='failed',
        created_at__lt=cutoff_date
    )

    count = old_failed_reports.count()
    if count > 0:
        old_failed_reports.delete()
        logger.info(f"Cleaned up {count} old failed reports")

    return {'deleted_reports': count}


@shared_task(bind=True, max_retries=3, default_retry_delay=60, soft_time_limit=900, time_limit=960)
def generate_report(self, report_id, report_type=None, format_type='both'):
    """
    Generate HTML and/or PDF report files asynchronously.

    Args:
        report_id: UUID of the Report instance
        report_type: Type of report to generate (optional, uses report.report_type if not provided)
        format_type: 'html', 'pdf', or 'both' (default: 'both')

    Returns:
        dict: Generation result with status and file paths
    """
    logger.info(f"Starting report generation task for report {report_id}")

    try:
        # Get report instance
        report = Report.objects.get(id=report_id)

        # Validate report state
        if report.status != 'completed':
            error_msg = f'Report must be completed before generation. Current status: {report.status}'
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}

        if report.recommendations.count() == 0:
            error_msg = 'Report has no recommendations to include'
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}

        # Validate format type
        if format_type not in ['html', 'pdf', 'both']:
            error_msg = f'Invalid format type: {format_type}'
            logger.error(error_msg)
            return {'status': 'error', 'error': error_msg}

        # Update status
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

        logger.info(f"Report generation completed for {report_id}: {', '.join(files_generated)}")

        return {
            'status': 'success',
            'report_id': str(report_id),
            'files_generated': files_generated,
            'file_paths': file_paths,
        }

    except Report.DoesNotExist:
        error_msg = f"Report with ID {report_id} not found - it may have been deleted"
        logger.error(error_msg)
        # Don't retry if the report doesn't exist - it was likely deleted
        raise Ignore()

    except Exception as e:
        error_msg = f"Report generation error: {str(e)}"
        logger.error(f"Report generation failed for {report_id}: {error_msg}", exc_info=True)

        # Update report status back to completed (generation is optional)
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'completed'
            report.save(update_fields=['status'])
        except:
            pass

        # Retry on errors
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {'status': 'error', 'error': error_msg, 'report_id': str(report_id)}


@shared_task
def retry_failed_report(report_id):
    """
    Retry processing a failed report.

    Args:
        report_id: UUID of the failed report

    Returns:
        dict: Result of retry attempt
    """
    try:
        report = Report.objects.get(id=report_id)

        if report.status != 'failed':
            return {'status': 'error', 'error': 'Report is not in failed status'}

        if not report.can_retry():
            return {'status': 'error', 'error': 'Maximum retry attempts exceeded'}

        # Reset status and trigger processing
        report.status = 'uploaded'
        report.error_message = ''
        report.save(update_fields=['status', 'error_message'])

        # Trigger processing task
        result = process_csv_file.delay(str(report_id))

        return {'status': 'success', 'task_id': result.id}

    except Report.DoesNotExist:
        return {'status': 'error', 'error': f'Report {report_id} not found'}
    except Exception as e:
        logger.error(f"Error retrying report {report_id}: {str(e)}", exc_info=True)
        return {'status': 'error', 'error': str(e)}
