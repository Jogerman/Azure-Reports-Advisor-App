"""
Celery tasks for Reports app.
"""

import logging
from celery import shared_task
from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import Report
from .services.csv_processor import process_csv_file as process_csv_sync, CSVProcessingError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_csv_file(self, report_id, csv_file_path):
    """
    Process uploaded CSV file and extract recommendations.

    Args:
        self: Task instance
        report_id: UUID of the report
        csv_file_path: Path to the CSV file

    Returns:
        Dictionary with processing results
    """
    try:
        # Get report instance
        report = Report.objects.get(id=report_id)

        # Update status to processing
        report.status = 'processing'
        report.processing_started_at = timezone.now()
        report.celery_task_id = self.request.id
        report.save()

        logger.info(f"Processing CSV file for report {report_id}")

        # Process the CSV file
        result = process_csv_sync(csv_file_path, report)

        # Update report with results
        report.status = 'completed'
        report.processing_completed_at = timezone.now()
        report.total_recommendations = result.get('total_recommendations', 0)
        report.high_impact_count = result.get('high_impact_count', 0)
        report.medium_impact_count = result.get('medium_impact_count', 0)
        report.low_impact_count = result.get('low_impact_count', 0)
        report.estimated_savings = result.get('estimated_savings', 0)
        report.save()

        logger.info(f"Successfully processed CSV for report {report_id}")

        return {
            'status': 'success',
            'report_id': str(report_id),
            'total_recommendations': result.get('total_recommendations', 0),
            'estimated_savings': float(result.get('estimated_savings', 0))
        }

    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {
            'status': 'error',
            'message': f"Report {report_id} not found"
        }

    except CSVProcessingError as e:
        logger.error(f"CSV processing error for report {report_id}: {str(e)}")

        try:
            report = Report.objects.get(id=report_id)
            report.mark_as_failed(str(e))
        except Report.DoesNotExist:
            pass

        return {
            'status': 'error',
            'report_id': str(report_id),
            'message': str(e)
        }

    except Exception as e:
        logger.exception(f"Unexpected error processing CSV for report {report_id}")

        try:
            report = Report.objects.get(id=report_id)
            report.mark_as_failed(f"Unexpected error: {str(e)}")
        except Report.DoesNotExist:
            pass

        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'report_id': str(report_id),
                'message': f"Max retries exceeded: {str(e)}"
            }


@shared_task(bind=True, max_retries=3)
def generate_report(self, report_id, report_type='detailed'):
    """
    Generate PDF report from recommendations.

    Args:
        self: Task instance
        report_id: UUID of the report
        report_type: Type of report to generate

    Returns:
        Dictionary with generation results
    """
    try:
        # Get report instance
        report = Report.objects.get(id=report_id)

        # Update status to processing
        report.status = 'processing'
        report.processing_started_at = timezone.now()
        report.celery_task_id = self.request.id
        report.save()

        logger.info(f"Generating {report_type} report for {report_id}")

        # Get the appropriate generator
        from .generators import get_generator_for_report
        generator = get_generator_for_report(report_type)

        # Generate the report
        pdf_content = generator.generate(report)

        # Save the PDF file
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report.pdf_file.save(filename, ContentFile(pdf_content), save=False)

        # Update report status
        report.status = 'completed'
        report.processing_completed_at = timezone.now()
        report.file_size = len(pdf_content)
        report.save()

        logger.info(f"Successfully generated report {report_id}")

        return {
            'status': 'success',
            'report_id': str(report_id),
            'file_size': len(pdf_content),
            'file_url': report.pdf_file.url if report.pdf_file else None
        }

    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {
            'status': 'error',
            'message': f"Report {report_id} not found"
        }

    except Exception as e:
        logger.exception(f"Error generating report {report_id}")

        try:
            report = Report.objects.get(id=report_id)
            report.mark_as_failed(f"Report generation error: {str(e)}")
        except Report.DoesNotExist:
            pass

        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'report_id': str(report_id),
                'message': f"Max retries exceeded: {str(e)}"
            }


@shared_task
def cleanup_old_reports(days=90):
    """
    Cleanup old reports and their files.

    Args:
        days: Number of days to keep reports

    Returns:
        Dictionary with cleanup results
    """
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    logger.info(f"Cleaning up reports older than {cutoff_date}")

    old_reports = Report.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    )

    count = old_reports.count()

    # Delete files and reports
    for report in old_reports:
        try:
            if report.csv_file:
                report.csv_file.delete(save=False)
            if report.pdf_file:
                report.pdf_file.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting files for report {report.id}: {str(e)}")

    old_reports.delete()

    logger.info(f"Cleaned up {count} old reports")

    return {
        'status': 'success',
        'deleted_count': count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def update_report_statistics():
    """
    Update statistics for all completed reports.

    Returns:
        Dictionary with update results
    """
    logger.info("Updating report statistics")

    reports = Report.objects.filter(status='completed')
    updated_count = 0

    for report in reports:
        try:
            recommendations = report.recommendations.all()

            report.total_recommendations = recommendations.count()
            report.high_impact_count = recommendations.filter(impact='High').count()
            report.medium_impact_count = recommendations.filter(impact='Medium').count()
            report.low_impact_count = recommendations.filter(impact='Low').count()
            report.estimated_savings = recommendations.aggregate(
                total=models.Sum('potential_savings')
            )['total'] or 0

            report.save()
            updated_count += 1

        except Exception as e:
            logger.error(f"Error updating statistics for report {report.id}: {str(e)}")

    logger.info(f"Updated statistics for {updated_count} reports")

    return {
        'status': 'success',
        'updated_count': updated_count
    }
