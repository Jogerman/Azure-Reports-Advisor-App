"""
Django admin configuration for report management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone

from .models import Report, Recommendation, ReportTemplate, ReportShare


class RecommendationInline(admin.TabularInline):
    model = Recommendation
    extra = 0
    readonly_fields = ['id', 'created_at', 'csv_row_number']
    fields = [
        'category', 'business_impact', 'recommendation',
        'resource_name', 'potential_savings', 'currency'
    ]
    show_change_link = True


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'get_title',
        'client',
        'report_type',
        'status',
        'recommendation_count',
        'total_savings_display',
        'created_by',
        'created_at'
    ]
    list_filter = [
        'status',
        'report_type',
        'created_at',
        'client__industry'
    ]
    search_fields = [
        'title',
        'client__company_name',
        'created_by__username',
        'created_by__email'
    ]
    readonly_fields = [
        'id',
        'recommendation_count',
        'total_potential_savings',
        'processing_duration',
        'csv_uploaded_at',
        'processing_started_at',
        'processing_completed_at',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Report Information', {
            'fields': (
                'client',
                'report_type',
                'title',
                'created_by',
            )
        }),
        ('File Management', {
            'fields': (
                'csv_file',
                'html_file',
                'pdf_file',
            )
        }),
        ('Processing Status', {
            'fields': (
                'status',
                'error_message',
                'retry_count',
            )
        }),
        ('Analytics Data', {
            'fields': (
                'analysis_data',
                'recommendation_count',
                'total_potential_savings',
            ),
            'classes': ('collapse',)
        }),
        ('Processing Timeline', {
            'fields': (
                'csv_uploaded_at',
                'processing_started_at',
                'processing_completed_at',
                'processing_duration',
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

    inlines = [RecommendationInline]

    def get_title(self, obj):
        return obj.title or f"{obj.get_report_type_display()} Report"
    get_title.short_description = 'Title'
    get_title.admin_order_field = 'title'

    def recommendation_count(self, obj):
        count = obj.recommendation_count
        if count > 0:
            url = reverse('admin:reports_recommendation_changelist')
            return format_html(
                '<a href="{}?report__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    recommendation_count.short_description = 'Recommendations'

    def total_savings_display(self, obj):
        savings = obj.total_potential_savings
        if savings > 0:
            return f"${savings:,.2f}"
        return "-"
    total_savings_display.short_description = 'Total Savings'
    total_savings_display.admin_order_field = 'total_potential_savings'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'client', 'created_by'
        ).prefetch_related('recommendations')

    actions = ['retry_failed_reports', 'mark_as_completed']

    def retry_failed_reports(self, request, queryset):
        """Admin action to retry failed reports."""
        retryable = queryset.filter(status='failed', retry_count__lt=5)
        count = retryable.count()
        retryable.update(status='pending', error_message='')
        self.message_user(request, f"Marked {count} reports for retry.")
    retry_failed_reports.short_description = "Retry failed reports"

    def mark_as_completed(self, request, queryset):
        """Admin action to mark reports as completed."""
        count = queryset.update(
            status='completed',
            processing_completed_at=timezone.now()
        )
        self.message_user(request, f"Marked {count} reports as completed.")
    mark_as_completed.short_description = "Mark as completed"


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'get_short_recommendation',
        'report_client',
        'category',
        'business_impact',
        'resource_name',
        'potential_savings_display',
        'created_at'
    ]
    list_filter = [
        'category',
        'business_impact',
        'currency',
        'report__report_type',
        'created_at'
    ]
    search_fields = [
        'recommendation',
        'resource_name',
        'resource_type',
        'subscription_name',
        'report__client__company_name'
    ]
    readonly_fields = [
        'id',
        'csv_row_number',
        'monthly_savings',
        'created_at'
    ]

    fieldsets = (
        ('Recommendation Details', {
            'fields': (
                'report',
                'category',
                'business_impact',
                'recommendation',
                'potential_benefits',
            )
        }),
        ('Azure Resource Information', {
            'fields': (
                'subscription_id',
                'subscription_name',
                'resource_group',
                'resource_name',
                'resource_type',
            )
        }),
        ('Financial Impact', {
            'fields': (
                'potential_savings',
                'monthly_savings',
                'currency',
                'advisor_score_impact',
            )
        }),
        ('Additional Details', {
            'fields': (
                'retirement_date',
                'retiring_feature',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'id',
                'csv_row_number',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def get_short_recommendation(self, obj):
        return obj.recommendation[:100] + "..." if len(obj.recommendation) > 100 else obj.recommendation
    get_short_recommendation.short_description = 'Recommendation'

    def report_client(self, obj):
        return obj.report.client.company_name
    report_client.short_description = 'Client'
    report_client.admin_order_field = 'report__client__company_name'

    def potential_savings_display(self, obj):
        if obj.potential_savings > 0:
            return f"${obj.potential_savings:,.2f}"
        return "-"
    potential_savings_display.short_description = 'Potential Savings'
    potential_savings_display.admin_order_field = 'potential_savings'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'report__client'
        )


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'report_type',
        'is_default',
        'is_active',
        'created_by',
        'created_at'
    ]
    list_filter = ['report_type', 'is_default', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Template Information', {
            'fields': (
                'name',
                'report_type',
                'is_default',
                'is_active',
            )
        }),
        ('Template Content', {
            'fields': (
                'html_template',
                'css_styles',
            )
        }),
        ('Metadata', {
            'fields': (
                'id',
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReportShare)
class ReportShareAdmin(admin.ModelAdmin):
    list_display = [
        'report_title',
        'shared_with_email',
        'permission_level',
        'is_active',
        'is_expired_display',
        'access_count',
        'created_at'
    ]
    list_filter = [
        'permission_level',
        'is_active',
        'expires_at',
        'created_at'
    ]
    search_fields = [
        'shared_with_email',
        'report__title',
        'report__client__company_name'
    ]
    readonly_fields = [
        'id',
        'access_token',
        'access_count',
        'last_accessed_at',
        'is_expired_display',
        'created_at'
    ]

    fieldsets = (
        ('Share Information', {
            'fields': (
                'report',
                'shared_with_email',
                'permission_level',
                'shared_by',
            )
        }),
        ('Access Control', {
            'fields': (
                'access_token',
                'expires_at',
                'is_active',
                'is_expired_display',
            )
        }),
        ('Usage Statistics', {
            'fields': (
                'access_count',
                'last_accessed_at',
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

    def report_title(self, obj):
        return obj.report.title or f"{obj.report.get_report_type_display()} Report"
    report_title.short_description = 'Report'

    def is_expired_display(self, obj):
        is_expired = obj.is_expired
        return format_html(
            '<span style="color: {};">{}</span>',
            'red' if is_expired else 'green',
            'Yes' if is_expired else 'No'
        )
    is_expired_display.short_description = 'Expired'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'report__client', 'shared_by'
        )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set shared_by on creation
            obj.shared_by = request.user
        super().save_model(request, obj, form, change)