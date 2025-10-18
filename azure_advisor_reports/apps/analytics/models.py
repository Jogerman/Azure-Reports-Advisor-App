"""
Analytics models for tracking metrics and performance data.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from apps.clients.models import Client
from apps.reports.models import Report


class DashboardMetrics(models.Model):
    """
    Pre-calculated dashboard metrics for performance optimization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Date range for metrics
    date = models.DateField(help_text="Date for these metrics")
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='daily'
    )

    # Core metrics
    total_clients = models.IntegerField(default=0)
    active_clients = models.IntegerField(default=0)
    total_reports = models.IntegerField(default=0)
    reports_generated_today = models.IntegerField(default=0)
    total_recommendations = models.IntegerField(default=0)
    total_potential_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Category distribution (stored as JSON)
    category_distribution = models.JSONField(
        default=dict,
        help_text="Distribution of recommendations by category"
    )
    impact_distribution = models.JSONField(
        default=dict,
        help_text="Distribution of recommendations by business impact"
    )
    industry_distribution = models.JSONField(
        default=dict,
        help_text="Distribution of clients by industry"
    )

    # Performance metrics
    avg_processing_time_seconds = models.IntegerField(default=0)
    success_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_dashboard_metrics'
        unique_together = ['date', 'period_type']
        indexes = [
            models.Index(fields=['date', 'period_type']),
            models.Index(fields=['calculated_at']),
        ]

    def __str__(self):
        return f"Dashboard Metrics - {self.date} ({self.period_type})"

    @classmethod
    def calculate_for_date(cls, target_date=None, period_type='daily'):
        """
        Calculate and store dashboard metrics for a specific date.
        """
        if target_date is None:
            target_date = timezone.now().date()

        # Define date range based on period type
        if period_type == 'daily':
            start_date = target_date
            end_date = target_date + timedelta(days=1)
        elif period_type == 'weekly':
            start_date = target_date - timedelta(days=target_date.weekday())
            end_date = start_date + timedelta(days=7)
        elif period_type == 'monthly':
            start_date = target_date.replace(day=1)
            if target_date.month == 12:
                end_date = target_date.replace(year=target_date.year + 1, month=1, day=1)
            else:
                end_date = target_date.replace(month=target_date.month + 1, day=1)
        else:  # yearly
            start_date = target_date.replace(month=1, day=1)
            end_date = target_date.replace(year=target_date.year + 1, month=1, day=1)

        # Calculate metrics
        from apps.reports.models import Recommendation

        total_clients = Client.objects.filter(
            created_at__date__lt=end_date
        ).count()

        active_clients = Client.objects.filter(
            status='active',
            created_at__date__lt=end_date
        ).count()

        reports_in_period = Report.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lt=end_date
        )

        total_reports = Report.objects.filter(
            created_at__date__lt=end_date
        ).count()

        recommendations_in_period = Recommendation.objects.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lt=end_date
        )

        total_recommendations = Recommendation.objects.filter(
            report__created_at__date__lt=end_date
        ).count()

        total_potential_savings = Recommendation.objects.filter(
            report__created_at__date__lt=end_date
        ).aggregate(
            total=models.Sum('potential_savings')
        )['total'] or 0

        # Category distribution
        category_dist = dict(
            recommendations_in_period.values('category').annotate(
                count=models.Count('id')
            ).values_list('category', 'count')
        )

        # Impact distribution
        impact_dist = dict(
            recommendations_in_period.values('business_impact').annotate(
                count=models.Count('id')
            ).values_list('business_impact', 'count')
        )

        # Industry distribution
        industry_dist = dict(
            Client.objects.filter(
                created_at__date__lt=end_date
            ).values('industry').annotate(
                count=models.Count('id')
            ).values_list('industry', 'count')
        )

        # Performance metrics
        completed_reports = Report.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lt=end_date,
            status='completed',
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        )

        avg_processing_time = 0
        if completed_reports.exists():
            processing_times = [
                (r.processing_completed_at - r.processing_started_at).total_seconds()
                for r in completed_reports
            ]
            avg_processing_time = sum(processing_times) / len(processing_times)

        success_rate = 0
        if reports_in_period.exists():
            successful_reports = reports_in_period.filter(status='completed').count()
            success_rate = (successful_reports / reports_in_period.count()) * 100

        # Create or update metrics record
        metrics, created = cls.objects.update_or_create(
            date=target_date,
            period_type=period_type,
            defaults={
                'total_clients': total_clients,
                'active_clients': active_clients,
                'total_reports': total_reports,
                'reports_generated_today': reports_in_period.count(),
                'total_recommendations': total_recommendations,
                'total_potential_savings': total_potential_savings,
                'category_distribution': category_dist,
                'impact_distribution': impact_dist,
                'industry_distribution': industry_dist,
                'avg_processing_time_seconds': int(avg_processing_time),
                'success_rate_percentage': round(success_rate, 2),
            }
        )

        return metrics


class UserActivity(models.Model):
    """
    Track user activities for analytics and audit purposes.
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create_client', 'Create Client'),
        ('update_client', 'Update Client'),
        ('delete_client', 'Delete Client'),
        ('upload_csv', 'Upload CSV'),
        ('generate_report', 'Generate Report'),
        ('download_report', 'Download Report'),
        ('share_report', 'Share Report'),
        ('view_dashboard', 'View Dashboard'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255, help_text="Brief description of the action")

    # Optional relationships
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)

    # Request metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # Additional context data
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_user_activity'
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} ({self.created_at})"

    @classmethod
    def log_activity(cls, user, action, description, **kwargs):
        """
        Convenience method to log user activity.
        """
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            **kwargs
        )


class ReportUsageStats(models.Model):
    """
    Track detailed usage statistics for reports and features.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Time period
    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True, help_text="Hour of day (0-23)")

    # Usage metrics
    reports_generated = models.IntegerField(default=0)
    csvs_uploaded = models.IntegerField(default=0)
    reports_downloaded = models.IntegerField(default=0)
    reports_shared = models.IntegerField(default=0)

    # Performance metrics
    avg_csv_size_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_processing_time_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Report type breakdown (stored as JSON)
    report_type_breakdown = models.JSONField(
        default=dict,
        help_text="Count of reports by type"
    )

    # Error statistics
    failed_uploads = models.IntegerField(default=0)
    failed_generations = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_report_usage_stats'
        unique_together = ['date', 'hour']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['date', 'hour']),
        ]

    def __str__(self):
        time_period = f"{self.date}"
        if self.hour is not None:
            time_period += f" {self.hour}:00"
        return f"Usage Stats - {time_period}"


class SystemHealthMetrics(models.Model):
    """
    Track system health and performance metrics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Timestamp
    recorded_at = models.DateTimeField(default=timezone.now)

    # Database metrics
    database_connections = models.IntegerField(default=0)
    database_query_avg_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Queue metrics
    celery_active_tasks = models.IntegerField(default=0)
    celery_pending_tasks = models.IntegerField(default=0)
    celery_failed_tasks_24h = models.IntegerField(default=0)

    # Storage metrics
    blob_storage_usage_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    local_storage_usage_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Application metrics
    active_user_sessions = models.IntegerField(default=0)
    memory_usage_mb = models.IntegerField(default=0)
    cpu_usage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Error rates
    error_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    response_time_avg_ms = models.IntegerField(default=0)

    class Meta:
        db_table = 'analytics_system_health_metrics'
        indexes = [
            models.Index(fields=['recorded_at']),
        ]

    def __str__(self):
        return f"System Health - {self.recorded_at}"

    @property
    def is_healthy(self):
        """
        Determine if the system is in a healthy state based on metrics.
        """
        return (
            self.error_rate_percentage < 5 and
            self.cpu_usage_percentage < 80 and
            self.response_time_avg_ms < 2000 and
            self.celery_failed_tasks_24h < 10
        )