"""
Celery tasks for analytics operations.

These tasks run asynchronously to:
- Calculate and cache analytics metrics
- Clean up old activity records
- Generate periodic reports
"""

from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@shared_task(name='analytics.calculate_daily_metrics')
def calculate_daily_metrics():
    """
    Calculate and cache all analytics metrics.

    This task should run daily (e.g., at 2 AM) to pre-calculate
    expensive analytics queries and populate the cache.

    Returns:
        str: Status message
    """
    try:
        from apps.analytics.services import AnalyticsService

        logger.info("Starting daily metrics calculation...")

        # Invalidate all existing caches to force recalculation
        AnalyticsService.invalidate_cache()

        # Calculate and cache main metrics
        AnalyticsService.get_dashboard_metrics()
        logger.info("Calculated dashboard metrics")

        # Calculate category distribution
        AnalyticsService.get_category_distribution()
        logger.info("Calculated category distribution")

        # Calculate trend data for different periods
        for days in [7, 30, 90]:
            AnalyticsService.get_trend_data(days=days)
            logger.info(f"Calculated {days}-day trend data")

        # Calculate recent activity
        for limit in [5, 10, 15, 20]:
            AnalyticsService.get_recent_activity(limit=limit)
            logger.info(f"Calculated recent activity (limit={limit})")

        # Calculate business impact distribution
        AnalyticsService.get_business_impact_distribution()
        logger.info("Calculated business impact distribution")

        # Calculate activity summary
        for days in [7, 30]:
            AnalyticsService.get_activity_summary(days=days)
            logger.info(f"Calculated {days}-day activity summary")

        # Calculate system health
        AnalyticsService.get_system_health()
        logger.info("Calculated system health metrics")

        logger.info("Daily metrics calculation completed successfully")
        return "Daily metrics calculated and cached successfully"

    except Exception as e:
        logger.error(f"Failed to calculate daily metrics: {str(e)}", exc_info=True)
        raise


@shared_task(name='analytics.cleanup_old_activities')
def cleanup_old_activities(days=90):
    """
    Delete user activity records older than specified days.

    This helps keep the database size manageable while retaining
    recent activity history for analytics.

    Args:
        days (int): Delete activities older than this many days (default: 90)

    Returns:
        str: Status message with deletion count
    """
    try:
        from apps.analytics.models import UserActivity

        logger.info(f"Starting cleanup of activities older than {days} days...")

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        # Delete old activities
        deleted_count, _ = UserActivity.objects.filter(
            created_at__lt=cutoff_date
        ).delete()

        logger.info(f"Deleted {deleted_count} old activity records")

        return f"Deleted {deleted_count} activities older than {days} days"

    except Exception as e:
        logger.error(f"Failed to cleanup old activities: {str(e)}", exc_info=True)
        raise


@shared_task(name='analytics.calculate_dashboard_metrics_periodic')
def calculate_dashboard_metrics_periodic():
    """
    Calculate dashboard metrics for different time periods.

    This task runs periodically (e.g., every day) to calculate
    and store dashboard metrics for different periods.

    Returns:
        str: Status message
    """
    try:
        from apps.analytics.models import DashboardMetrics
        from django.utils import timezone

        logger.info("Starting periodic dashboard metrics calculation...")

        today = timezone.now().date()

        # Calculate metrics for different periods
        periods = ['daily', 'weekly', 'monthly']

        for period in periods:
            metrics = DashboardMetrics.calculate_for_date(
                target_date=today,
                period_type=period
            )
            logger.info(f"Calculated {period} metrics: {metrics}")

        logger.info("Periodic dashboard metrics calculation completed")
        return f"Dashboard metrics calculated for {', '.join(periods)}"

    except Exception as e:
        logger.error(f"Failed to calculate dashboard metrics: {str(e)}", exc_info=True)
        raise


@shared_task(name='analytics.generate_weekly_report')
def generate_weekly_report():
    """
    Generate weekly analytics report.

    This task can be used to send weekly analytics summaries
    to administrators or stakeholders.

    Returns:
        str: Status message
    """
    try:
        from apps.analytics.services import AnalyticsService
        from django.utils import timezone

        logger.info("Starting weekly analytics report generation...")

        # Calculate metrics for the past 7 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        # Get activity summary
        activity_summary = AnalyticsService.get_activity_summary(days=7)

        # Get dashboard metrics
        dashboard_metrics = AnalyticsService.get_dashboard_metrics()

        # Get system health
        system_health = AnalyticsService.get_system_health()

        # Here you could send an email or save a report
        # For now, we'll just log the key metrics

        logger.info(f"Weekly Report Summary:")
        logger.info(f"  Total Activities: {activity_summary.get('total_activities', 0)}")
        logger.info(f"  Total Recommendations: {dashboard_metrics.get('totalRecommendations', 0)}")
        logger.info(f"  Active Clients: {dashboard_metrics.get('activeClients', 0)}")
        logger.info(f"  System Health - Error Rate: {system_health.get('error_rate', 0)}%")

        logger.info("Weekly analytics report generated successfully")
        return "Weekly analytics report generated successfully"

    except Exception as e:
        logger.error(f"Failed to generate weekly report: {str(e)}", exc_info=True)
        raise


@shared_task(name='analytics.cleanup_old_system_metrics')
def cleanup_old_system_metrics(days=30):
    """
    Delete old system health metrics.

    Keep only recent system health snapshots to avoid database bloat.

    Args:
        days (int): Delete metrics older than this many days (default: 30)

    Returns:
        str: Status message with deletion count
    """
    try:
        from apps.analytics.models import SystemHealthMetrics

        logger.info(f"Starting cleanup of system metrics older than {days} days...")

        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = SystemHealthMetrics.objects.filter(
            recorded_at__lt=cutoff_date
        ).delete()

        logger.info(f"Deleted {deleted_count} old system metric records")

        return f"Deleted {deleted_count} system metrics older than {days} days"

    except Exception as e:
        logger.error(f"Failed to cleanup old system metrics: {str(e)}", exc_info=True)
        raise


@shared_task(name='analytics.update_report_usage_stats')
def update_report_usage_stats():
    """
    Update report usage statistics for the current hour.

    This task can run hourly to track detailed usage patterns.

    Returns:
        str: Status message
    """
    try:
        from apps.analytics.models import ReportUsageStats
        from apps.reports.models import Report
        from django.utils import timezone
        from django.db.models import Count, Avg

        logger.info("Starting report usage stats update...")

        now = timezone.now()
        current_date = now.date()
        current_hour = now.hour

        # Get reports created in the last hour
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        reports_in_hour = Report.objects.filter(
            created_at__gte=hour_start,
            created_at__lt=hour_end
        )

        # Calculate statistics
        reports_generated = reports_in_hour.count()

        # Get report type breakdown
        report_type_breakdown = dict(
            reports_in_hour.values('report_type').annotate(
                count=Count('id')
            ).values_list('report_type', 'count')
        )

        # Calculate average processing time
        completed_reports = reports_in_hour.filter(
            status='completed',
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        )

        avg_processing_time = 0
        if completed_reports.exists():
            processing_times = [
                (r.processing_completed_at - r.processing_started_at).total_seconds() / 60
                for r in completed_reports
            ]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)

        # Count failed generations
        failed_generations = reports_in_hour.filter(status='failed').count()

        # Update or create stats record
        stats, created = ReportUsageStats.objects.update_or_create(
            date=current_date,
            hour=current_hour,
            defaults={
                'reports_generated': reports_generated,
                'report_type_breakdown': report_type_breakdown,
                'avg_processing_time_minutes': round(avg_processing_time, 2),
                'failed_generations': failed_generations,
            }
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} usage stats for {current_date} hour {current_hour}")

        return f"{action} usage stats: {reports_generated} reports generated"

    except Exception as e:
        logger.error(f"Failed to update report usage stats: {str(e)}", exc_info=True)
        raise
