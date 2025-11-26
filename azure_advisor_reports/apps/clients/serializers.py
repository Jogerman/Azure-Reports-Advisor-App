"""
Django REST Framework serializers for client management.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, ClientContact, ClientNote

User = get_user_model()


class ClientContactSerializer(serializers.ModelSerializer):
    """
    Serializer for ClientContact model.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = ClientContact
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'role',
            'role_display',
            'title',
            'is_primary',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for ClientNote model.
    """
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)

    class Meta:
        model = ClientNote
        fields = [
            'id',
            'note_type',
            'note_type_display',
            'subject',
            'content',
            'author',
            'author_name',
            'related_report',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class ClientListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for client lists.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    industry_display = serializers.CharField(source='get_industry_display', read_only=True)
    subscription_count = serializers.ReadOnlyField()
    total_reports = serializers.ReadOnlyField()
    account_manager_name = serializers.CharField(
        source='account_manager.full_name',
        read_only=True
    )
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id',
            'company_name',
            'industry',
            'industry_display',
            'status',
            'status_display',
            'contact_email',
            'contact_phone',
            'logo',
            'subscription_count',
            'total_reports',
            'account_manager_name',
            'created_at',
            'updated_at',
        ]

    def get_logo(self, obj):
        """
        Return backend URL for logo instead of direct blob storage URL.
        This ensures authenticated access through the backend.
        """
        if obj.logo:
            request = self.context.get('request')
            if request:
                # Build the URL to the backend logo endpoint
                return request.build_absolute_uri(
                    f'/api/v1/clients/{obj.id}/logo/'
                )
        return None


class ClientDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual client view.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    industry_display = serializers.CharField(source='get_industry_display', read_only=True)
    subscription_count = serializers.ReadOnlyField()
    total_reports = serializers.ReadOnlyField()
    latest_report_date = serializers.ReadOnlyField()
    account_manager_name = serializers.CharField(
        source='account_manager.full_name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )
    logo = serializers.SerializerMethodField()

    # Include related contacts and notes
    contacts = ClientContactSerializer(many=True, read_only=True)
    client_notes = ClientNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = [
            'id',
            'company_name',
            'industry',
            'industry_display',
            'status',
            'status_display',
            'contact_email',
            'contact_phone',
            'contact_person',
            'logo',
            'azure_subscription_ids',
            'subscription_count',
            'notes',
            'contract_start_date',
            'contract_end_date',
            'billing_contact',
            'account_manager',
            'account_manager_name',
            'total_reports',
            'latest_report_date',
            'contacts',
            'client_notes',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'created_by',
            'subscription_count',
            'total_reports',
            'latest_report_date',
        ]

    def get_logo(self, obj):
        """
        Return backend URL for logo instead of direct blob storage URL.
        This ensures authenticated access through the backend.
        """
        if obj.logo:
            request = self.context.get('request')
            if request:
                # Build the URL to the backend logo endpoint
                return request.build_absolute_uri(
                    f'/api/v1/clients/{obj.id}/logo/'
                )
        return None


class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating clients.
    """
    class Meta:
        model = Client
        fields = [
            'company_name',
            'industry',
            'status',
            'contact_email',
            'contact_phone',
            'contact_person',
            'logo',
            'azure_subscription_ids',
            'notes',
            'contract_start_date',
            'contract_end_date',
            'billing_contact',
            'account_manager',
        ]

    def validate_company_name(self, value):
        """Validate that company name is unique (case-insensitive)."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Company name cannot be empty.")

        # Check for duplicate company name (case-insensitive)
        # Exclude current instance if updating
        queryset = Client.objects.filter(company_name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                f"A client with company name '{value}' already exists."
            )

        return value.strip()

    def validate_contact_email(self, value):
        """Validate email format."""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format.")
        return value.lower() if value else value

    def validate_azure_subscription_ids(self, value):
        """Validate Azure subscription IDs format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Azure subscription IDs must be a list.")

        # Remove duplicates and empty values
        cleaned_ids = list(set([sid.strip() for sid in value if sid and sid.strip()]))
        return cleaned_ids

    def validate(self, attrs):
        """Cross-field validation."""
        contract_start = attrs.get('contract_start_date')
        contract_end = attrs.get('contract_end_date')

        if contract_start and contract_end and contract_end < contract_start:
            raise serializers.ValidationError({
                'contract_end_date': "Contract end date cannot be before start date."
            })

        return attrs


class ClientStatisticsSerializer(serializers.Serializer):
    """
    Serializer for client statistics.
    """
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    inactive_clients = serializers.IntegerField()
    suspended_clients = serializers.IntegerField()
    clients_by_industry = serializers.DictField()
    total_subscriptions = serializers.IntegerField()
    total_reports = serializers.IntegerField()
    clients_with_reports = serializers.IntegerField()
    clients_without_reports = serializers.IntegerField()