"""
Django admin configuration for Azure Integration.
"""

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.forms.widgets import PasswordInput

from .models import AzureSubscription


class AzureSubscriptionAdminForm(forms.ModelForm):
    """
    Custom form for AzureSubscription admin to handle client_secret.

    Uses a PasswordInput widget and the model's property setter
    to encrypt the secret before saving.
    """
    client_secret = forms.CharField(
        required=False,
        widget=PasswordInput(render_value=False),
        help_text="Azure Service Principal client secret (will be encrypted)"
    )

    class Meta:
        model = AzureSubscription
        exclude = ['client_secret_encrypted']
        widgets = {
            'sync_error_message': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For existing objects, don't require the secret field
        # (only require if creating new or explicitly updating)
        if self.instance and self.instance.pk:
            self.fields['client_secret'].required = False
            self.fields['client_secret'].help_text = (
                "Leave blank to keep existing secret. "
                "Enter new value to update (will be encrypted)."
            )
        else:
            self.fields['client_secret'].required = True

    def save(self, commit=True):
        """Save the form, encrypting the client_secret if provided."""
        instance = super().save(commit=False)

        # Use the property setter to encrypt the secret
        client_secret = self.cleaned_data.get('client_secret')
        if client_secret:
            instance.client_secret = client_secret

        if commit:
            instance.save()

        return instance


@admin.register(AzureSubscription)
class AzureSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Azure Subscriptions.

    Features:
    - Custom form with encrypted secret handling
    - List view with key information and sync status
    - Filters for active status and sync status
    - Search by name and subscription ID
    - Readonly fields for security and tracking
    """

    form = AzureSubscriptionAdminForm

    list_display = [
        'name',
        'subscription_id',
        'is_active_display',
        'sync_status_display',
        'last_sync_at',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'sync_status',
        'created_at',
    ]

    search_fields = [
        'name',
        'subscription_id',
        'tenant_id',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_sync_at',
        'sync_status',
        'sync_error_message',
        'created_by',
    ]

    fieldsets = (
        ('Subscription Information', {
            'fields': (
                'name',
                'subscription_id',
                'is_active',
            )
        }),
        ('Azure Credentials', {
            'fields': (
                'tenant_id',
                'client_id',
                'client_secret',
            ),
            'description': 'Service Principal credentials for Azure API authentication. '
                          'Client secret is encrypted before storage.'
        }),
        ('Sync Status', {
            'fields': (
                'sync_status',
                'last_sync_at',
                'sync_error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                'id',
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def is_active_display(self, obj):
        """Display active status with color coding."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactive</span>'
        )
    is_active_display.short_description = 'Status'
    is_active_display.admin_order_field = 'is_active'

    def sync_status_display(self, obj):
        """Display sync status with color coding."""
        colors = {
            'never_synced': 'gray',
            'success': 'green',
            'failed': 'red',
        }
        icons = {
            'never_synced': '—',
            'success': '✓',
            'failed': '✗',
        }

        color = colors.get(obj.sync_status, 'black')
        icon = icons.get(obj.sync_status, '?')

        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_sync_status_display()
        )
    sync_status_display.short_description = 'Sync Status'
    sync_status_display.admin_order_field = 'sync_status'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('created_by')

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['mark_as_active', 'mark_as_inactive']

    def mark_as_active(self, request, queryset):
        """Admin action to mark subscriptions as active."""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Marked {count} subscription(s) as active.")
    mark_as_active.short_description = "Mark selected subscriptions as active"

    def mark_as_inactive(self, request, queryset):
        """Admin action to mark subscriptions as inactive."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Marked {count} subscription(s) as inactive.")
    mark_as_inactive.short_description = "Mark selected subscriptions as inactive"
