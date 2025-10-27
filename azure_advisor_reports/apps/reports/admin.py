"""
Admin configuration for Reports app.
"""

from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'report_type', 'status', 'generated_at', 'completed_at')
    list_filter = ('status', 'report_type', 'generated_at')
    search_fields = ('client__name', 'id')
    readonly_fields = ('id', 'generated_at', 'completed_at')
    date_hierarchy = 'generated_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'client', 'report_type', 'status')
        }),
        ('File Information', {
            'fields': ('file_url', 'file_path')
        }),
        ('Metadata', {
            'fields': ('subscription_ids', 'date_range_start', 'date_range_end', 'parameters')
        }),
        ('Statistics', {
            'fields': ('total_recommendations', 'high_impact_count', 'medium_impact_count',
                      'low_impact_count', 'estimated_savings')
        }),
        ('Timestamps', {
            'fields': ('generated_by', 'generated_at', 'completed_at', 'error_message')
        }),
    )
