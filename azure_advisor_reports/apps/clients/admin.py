"""
Django admin configuration for client management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Client, ClientContact, ClientNote


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'company_name',
        'industry',
        'status',
        'subscription_count',
        'total_reports',
        'account_manager',
        'created_at'
    ]
    list_filter = ['status', 'industry', 'created_at', 'updated_at']
    search_fields = ['company_name', 'contact_email', 'contact_person']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_reports', 'latest_report_date']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'company_name',
                'industry',
                'status',
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_person',
                'contact_email',
                'contact_phone',
            )
        }),
        ('Azure Configuration', {
            'fields': (
                'azure_subscription_ids',
            )
        }),
        ('Contract & Billing', {
            'fields': (
                'contract_start_date',
                'contract_end_date',
                'billing_contact',
            )
        }),
        ('Relationship Management', {
            'fields': (
                'account_manager',
                'notes',
            )
        }),
        ('Metadata', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
                'created_by',
                'total_reports',
                'latest_report_date',
            ),
            'classes': ('collapse',)
        }),
    )

    def subscription_count(self, obj):
        return obj.subscription_count
    subscription_count.short_description = 'Subscriptions'

    def total_reports(self, obj):
        count = obj.total_reports
        if count > 0:
            url = reverse('admin:reports_report_changelist')
            return format_html(
                '<a href="{}?client__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    total_reports.short_description = 'Reports'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account_manager', 'created_by')


class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 1
    readonly_fields = ['id', 'created_at', 'updated_at']


class ClientNoteInline(admin.TabularInline):
    model = ClientNote
    extra = 0
    readonly_fields = ['id', 'created_at', 'updated_at']
    fields = ['note_type', 'subject', 'content', 'author']


@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'email', 'role', 'is_primary', 'created_at']
    list_filter = ['role', 'is_primary', 'created_at']
    search_fields = ['name', 'email', 'client__company_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client')


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = ['subject', 'client', 'note_type', 'author', 'created_at']
    list_filter = ['note_type', 'created_at', 'author']
    search_fields = ['subject', 'content', 'client__company_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'author', 'related_report')

    def save_model(self, request, obj, form, change):
        if not change:  # Only set author on creation
            obj.author = request.user
        super().save_model(request, obj, form, change)