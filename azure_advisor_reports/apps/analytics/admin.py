"""
Django admin configuration for analytics.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json

from .models import (
    DashboardMetrics,
    UserActivity,
    ReportUsageStats,
    SystemHealthMetrics
)


@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'period_type',
        'total_clients',
        'active_clients',
        'total_reports',
        'reports_generated_today',
        'total_potential_savings_display',
        'success_rate_percentage',
        'calculated_at'
    ]
    list_filter = [
        'period_type',
        'date',
        'calculated_at'
    ]
    readonly_fields = [
        'id',
        'category_distribution_display',
        'impact_distribution_display',
        'industry_distribution_display',
        'calculated_at',
        'created_at'
    ]

    fieldsets = (
        ('Time Period', {
            'fields': (
                'date',
                'period_type',
            )
        }),
        ('Core Metrics', {
            'fields': (
                'total_clients',
                'active_clients',
                'total_reports',
                'reports_generated_today',
                'total_recommendations',
                'total_potential_savings',
            )
        }),
        ('Performance Metrics', {
            'fields': (
                'avg_processing_time_seconds',
                'success_rate_percentage',
            )
        }),
        ('Distributions', {
            'fields': (
                'category_distribution_display',
                'impact_distribution_display',
                'industry_distribution_display',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'id',
                'calculated_at',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def total_potential_savings_display(self, obj):
        return f"${obj.total_potential_savings:,.2f}" if obj.total_potential_savings else "-"
    total_potential_savings_display.short_description = 'Total Savings'
    total_potential_savings_display.admin_order_field = 'total_potential_savings'

    def category_distribution_display(self, obj):
        if obj.category_distribution:
            formatted_json = json.dumps(obj.category_distribution, indent=2)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No data"
    category_distribution_display.short_description = 'Category Distribution'

    def impact_distribution_display(self, obj):
        if obj.impact_distribution:
            formatted_json = json.dumps(obj.impact_distribution, indent=2)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No data"
    impact_distribution_display.short_description = 'Impact Distribution'

    def industry_distribution_display(self, obj):
        if obj.industry_distribution:
            formatted_json = json.dumps(obj.industry_distribution, indent=2)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No data"
    industry_distribution_display.short_description = 'Industry Distribution'

    actions = ['recalculate_metrics']

    def recalculate_metrics(self, request, queryset):
        """Admin action to recalculate selected metrics."""
        count = 0
        for metrics in queryset:
            DashboardMetrics.calculate_for_date(metrics.date, metrics.period_type)
            count += 1
        self.message_user(request, f"Recalculated {count} metrics.")
    recalculate_metrics.short_description = "Recalculate selected metrics"


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'action',
        'description',
        'client',
        'report',
        'ip_address',
        'created_at'
    ]
    list_filter = [
        'action',
        'created_at',
        'user'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'description',
        'ip_address'
    ]
    readonly_fields = [
        'id',
        'metadata_display',
        'created_at'
    ]

    fieldsets = (
        ('Activity Details', {
            'fields': (
                'user',
                'action',
                'description',
            )
        }),
        ('Related Objects', {
            'fields': (
                'client',
                'report',
            )
        }),
        ('Request Information', {
            'fields': (
                'ip_address',
                'user_agent',
            )
        }),
        ('Additional Data', {
            'fields': (
                'metadata_display',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'id',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def metadata_display(self, obj):
        if obj.metadata:
            formatted_json = json.dumps(obj.metadata, indent=2)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No additional data"
    metadata_display.short_description = 'Additional Metadata'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'client', 'report'
        )

    def has_add_permission(self, request):
        return False  # Prevent manual creation of activity logs

    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing of activity logs


@admin.register(ReportUsageStats)
class ReportUsageStatsAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'hour_display',
        'reports_generated',
        'csvs_uploaded',
        'reports_downloaded',
        'avg_processing_time_minutes',
        'failed_uploads',
        'failed_generations'
    ]
    list_filter = [
        'date',
        'hour'
    ]
    readonly_fields = [
        'id',
        'report_type_breakdown_display',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Time Period', {
            'fields': (
                'date',
                'hour',
            )
        }),
        ('Usage Metrics', {
            'fields': (
                'reports_generated',
                'csvs_uploaded',
                'reports_downloaded',
                'reports_shared',
            )
        }),
        ('Performance Metrics', {
            'fields': (
                'avg_csv_size_mb',
                'avg_processing_time_minutes',
            )
        }),
        ('Error Statistics', {
            'fields': (
                'failed_uploads',
                'failed_generations',
            )
        }),
        ('Report Type Breakdown', {
            'fields': (
                'report_type_breakdown_display',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def hour_display(self, obj):
        return f"{obj.hour:02d}:00" if obj.hour is not None else "All Day"
    hour_display.short_description = 'Hour'
    hour_display.admin_order_field = 'hour'

    def report_type_breakdown_display(self, obj):
        if obj.report_type_breakdown:
            formatted_json = json.dumps(obj.report_type_breakdown, indent=2)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No data"
    report_type_breakdown_display.short_description = 'Report Type Breakdown'


@admin.register(SystemHealthMetrics)
class SystemHealthMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'recorded_at',
        'is_healthy_display',
        'error_rate_percentage',
        'response_time_avg_ms',
        'cpu_usage_percentage',
        'memory_usage_mb',
        'celery_active_tasks',
        'celery_pending_tasks'
    ]
    list_filter = [
        'recorded_at',
    ]
    readonly_fields = [
        'id',
        'is_healthy_display',
        'recorded_at'
    ]

    fieldsets = (
        ('System Status', {
            'fields': (
                'recorded_at',
                'is_healthy_display',
            )
        }),
        ('Application Metrics', {
            'fields': (
                'active_user_sessions',
                'memory_usage_mb',
                'cpu_usage_percentage',
                'error_rate_percentage',
                'response_time_avg_ms',
            )
        }),
        ('Database Metrics', {
            'fields': (
                'database_connections',
                'database_query_avg_ms',
            )
        }),
        ('Queue Metrics', {
            'fields': (
                'celery_active_tasks',
                'celery_pending_tasks',
                'celery_failed_tasks_24h',
            )
        }),
        ('Storage Metrics', {
            'fields': (
                'blob_storage_usage_gb',
                'local_storage_usage_gb',
            )
        }),
        ('Metadata', {
            'fields': (
                'id',
            ),
            'classes': ('collapse',)
        }),
    )

    def is_healthy_display(self, obj):
        is_healthy = obj.is_healthy
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            'green' if is_healthy else 'red',
            '✓ Healthy' if is_healthy else '✗ Issues Detected'
        )
    is_healthy_display.short_description = 'System Health'

    def has_add_permission(self, request):
        return False  # Prevent manual creation of system metrics

    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing of system metrics