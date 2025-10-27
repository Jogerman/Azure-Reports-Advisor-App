"""
Serializers for reports app.
"""

import os
from rest_framework import serializers
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Report, Recommendation, ReportTemplate, ReportShare


class RecommendationSerializer(serializers.ModelSerializer):
    """Serializer for Recommendation model."""

    monthly_savings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Recommendation
        fields = [
            'id',
            'report',
            'category',
            'business_impact',
            'recommendation',
            'subscription_id',
            'subscription_name',
            'resource_group',
            'resource_name',
            'resource_type',
            'potential_savings',
            'monthly_savings',
            'currency',
            'potential_benefits',
            'retirement_date',
            'retiring_feature',
            'advisor_score_impact',
            'csv_row_number',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'monthly_savings']


class RecommendationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing recommendations."""

    class Meta:
        model = Recommendation
        fields = [
            'id',
            'category',
            'business_impact',
            'recommendation',
            'resource_name',
            'potential_savings',
            'currency',
        ]
        read_only_fields = ['id']


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model with full details."""

    recommendations = RecommendationSerializer(many=True, read_only=True)
    recommendation_count = serializers.IntegerField(read_only=True)
    total_potential_savings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    processing_duration = serializers.DurationField(read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True, allow_null=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'client',
            'client_name',
            'created_by',
            'created_by_name',
            'report_type',
            'title',
            'csv_file',
            'html_file',
            'pdf_file',
            'status',
            'analysis_data',
            'error_message',
            'retry_count',
            'csv_uploaded_at',
            'processing_started_at',
            'processing_completed_at',
            'processing_duration',
            'created_at',
            'updated_at',
            'recommendations',
            'recommendation_count',
            'total_potential_savings',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'html_file',
            'pdf_file',
            'status',
            'analysis_data',
            'error_message',
            'retry_count',
            'csv_uploaded_at',
            'processing_started_at',
            'processing_completed_at',
            'processing_duration',
            'created_at',
            'updated_at',
            'recommendation_count',
            'total_potential_savings',
        ]


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reports."""

    client_name = serializers.CharField(source='client.company_name', read_only=True)
    recommendation_count = serializers.IntegerField(read_only=True)
    total_potential_savings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Report
        fields = [
            'id',
            'client',
            'client_name',
            'report_type',
            'title',
            'status',
            'html_file',
            'pdf_file',
            'recommendation_count',
            'total_potential_savings',
            'created_at',
            'updated_at',
            'processing_completed_at',
            'error_message',
        ]
        read_only_fields = ['id', 'status', 'html_file', 'pdf_file', 'created_at', 'updated_at', 'processing_completed_at', 'error_message']


class CSVUploadSerializer(serializers.Serializer):
    """Serializer for CSV file upload."""

    csv_file = serializers.FileField(required=True)
    client_id = serializers.UUIDField(required=True)
    report_type = serializers.ChoiceField(
        choices=Report.REPORT_TYPES,
        default='detailed',
        required=False
    )
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_csv_file(self, value):
        """
        Validate the uploaded CSV file.

        Args:
            value: Uploaded file object

        Returns:
            File object if valid

        Raises:
            serializers.ValidationError: If file validation fails
        """
        # Check file extension
        file_name = value.name.lower()
        allowed_extensions = getattr(settings, 'ALLOWED_CSV_EXTENSIONS', ['.csv'])

        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Invalid file extension. Allowed extensions: {', '.join(allowed_extensions)}"
            )

        # Check file size
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 52428800)
        if value.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size ({value.size / (1024 * 1024):.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
            )

        if value.size == 0:
            raise serializers.ValidationError("File is empty")

        # Check MIME type
        content_type = value.content_type
        allowed_mimetypes = getattr(settings, 'ALLOWED_CSV_MIMETYPES', ['text/csv'])

        if content_type not in allowed_mimetypes:
            raise serializers.ValidationError(
                f"Invalid content type: {content_type}. Allowed types: {', '.join(allowed_mimetypes)}"
            )

        return value

    def validate_client_id(self, value):
        """
        Validate that the client exists.

        Args:
            value: Client UUID

        Returns:
            UUID if valid

        Raises:
            serializers.ValidationError: If client doesn't exist
        """
        from apps.clients.models import Client

        try:
            Client.objects.get(id=value)
        except Client.DoesNotExist:
            raise serializers.ValidationError(f"Client with ID {value} does not exist")

        return value

    def create(self, validated_data):
        """
        Create a Report instance from validated data.

        Args:
            validated_data: Validated data dictionary

        Returns:
            Report instance
        """
        from apps.clients.models import Client
        from django.utils import timezone
        from .tasks import process_csv_file as process_csv_task
        import logging

        logger = logging.getLogger(__name__)

        client = Client.objects.get(id=validated_data['client_id'])
        user = self.context.get('request').user if self.context.get('request') else None

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type=validated_data.get('report_type', 'detailed'),
            title=validated_data.get('title', ''),
            csv_file=validated_data['csv_file'],
            status='uploaded',
            csv_uploaded_at=timezone.now(),
        )

        # Automatically trigger CSV processing via Celery
        try:
            logger.info(f"Triggering async CSV processing for report {report.id}")
            process_csv_task.delay(str(report.id))
        except Exception as e:
            logger.error(f"Failed to trigger CSV processing task for report {report.id}: {str(e)}")

        return report


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model."""

    created_by_name = serializers.CharField(source='created_by.name', read_only=True, allow_null=True)

    class Meta:
        model = ReportTemplate
        fields = [
            'id',
            'name',
            'report_type',
            'html_template',
            'css_styles',
            'is_default',
            'is_active',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ReportShareSerializer(serializers.ModelSerializer):
    """Serializer for ReportShare model."""

    report_title = serializers.CharField(source='report.title', read_only=True)
    shared_by_name = serializers.CharField(source='shared_by.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReportShare
        fields = [
            'id',
            'report',
            'report_title',
            'shared_by',
            'shared_by_name',
            'shared_with_email',
            'permission_level',
            'access_token',
            'expires_at',
            'is_active',
            'is_expired',
            'access_count',
            'last_accessed_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'shared_by',
            'access_token',
            'access_count',
            'last_accessed_at',
            'created_at',
        ]
