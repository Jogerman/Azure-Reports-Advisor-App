"""
Serializers for reports app.
"""

import os
import re
import csv
import logging
from io import StringIO
from rest_framework import serializers
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Report, Recommendation, ReportTemplate, ReportShare

# Try to import python-magic for enhanced file validation
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

# Security logger for file upload events
security_logger = logging.getLogger('security')


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
        Comprehensive CSV file validation with security controls.

        This method implements multiple layers of validation:
        1. File extension check
        2. File size validation
        3. Magic number validation (file signature)
        4. MIME type verification
        5. CSV structure validation
        6. Required columns check
        7. Filename sanitization

        Args:
            value: Uploaded file object

        Returns:
            File object if valid

        Raises:
            serializers.ValidationError: If file validation fails

        Security Notes:
            - Prevents file type spoofing attacks
            - Validates actual file content, not just extension
            - Prevents path traversal via filename sanitization
            - Limits file size to prevent DoS attacks
        """
        # 1. Check file extension
        file_name = value.name.lower()
        allowed_extensions = getattr(settings, 'ALLOWED_CSV_EXTENSIONS', ['.csv'])

        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            # SECURITY LOG: Invalid file extension attempt
            security_logger.warning(
                f"SECURITY: File upload rejected - invalid extension. "
                f"Filename: {value.name}, Size: {value.size} bytes"
            )
            raise serializers.ValidationError(
                f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
            )

        # 2. Check file size
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 52428800)  # 50MB default
        if value.size > max_size:
            # SECURITY LOG: File size exceeds maximum (potential DoS attack)
            security_logger.warning(
                f"SECURITY: File upload rejected - size exceeds maximum. "
                f"Filename: {value.name}, Size: {value.size} bytes, Max: {max_size} bytes"
            )
            raise serializers.ValidationError(
                f"File size exceeds maximum ({max_size / (1024*1024):.0f} MB)"
            )

        if value.size == 0:
            security_logger.warning(
                f"SECURITY: File upload rejected - empty file. Filename: {value.name}"
            )
            raise serializers.ValidationError("File is empty")

        # 3. Validate MIME type using magic numbers (if python-magic is available)
        if HAS_MAGIC:
            try:
                # Read first 2KB to detect file type
                file_type = magic.from_buffer(value.read(2048), mime=True)
                value.seek(0)  # Reset file pointer

                allowed_mime = ['text/plain', 'text/csv', 'application/csv',
                               'application/vnd.ms-excel', 'text/x-csv']
                if file_type not in allowed_mime:
                    # SECURITY LOG: MIME type mismatch (file type spoofing attempt)
                    security_logger.warning(
                        f"SECURITY: File upload rejected - MIME type mismatch. "
                        f"Filename: {value.name}, Detected type: {file_type}, Expected: CSV"
                    )
                    raise serializers.ValidationError(
                        f"Invalid file type: {file_type}. Expected CSV file."
                    )
            except Exception as e:
                raise serializers.ValidationError(
                    f"File type validation failed: {str(e)}"
                )
        else:
            # Fallback to basic content-type check if python-magic not available
            content_type = value.content_type
            allowed_mimetypes = getattr(settings, 'ALLOWED_CSV_MIMETYPES',
                                       ['text/csv', 'application/csv', 'text/plain'])

            if content_type not in allowed_mimetypes:
                raise serializers.ValidationError(
                    f"Invalid content type: {content_type}. Allowed: {', '.join(allowed_mimetypes)}"
                )

        # 4. Validate CSV structure
        try:
            value.seek(0)
            # Read first 1KB to validate structure
            sample = value.read(1024).decode('utf-8-sig', errors='ignore')
            value.seek(0)

            csv_reader = csv.reader(StringIO(sample))
            header = next(csv_reader, None)

            if not header:
                raise serializers.ValidationError("CSV file appears to be empty")

            # 5. Check for required columns (case-insensitive)
            required_columns = ['Category', 'Recommendation']
            header_lower = [col.lower().strip() for col in header if col]

            missing = [col for col in required_columns
                      if col.lower() not in header_lower]

            if missing:
                raise serializers.ValidationError(
                    f"CSV missing required columns: {', '.join(missing)}. "
                    f"Found columns: {', '.join(header[:10])}"
                )

            # 6. Validate at least one data row exists
            data_row = next(csv_reader, None)
            if not data_row:
                raise serializers.ValidationError("CSV file has no data rows")

        except UnicodeDecodeError:
            raise serializers.ValidationError(
                "File encoding is invalid. Please use UTF-8 encoding."
            )
        except csv.Error as e:
            raise serializers.ValidationError(f"Invalid CSV format: {str(e)}")
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(
                f"CSV validation failed: {str(e)}"
            )

        # 7. Sanitize filename (prevent path traversal)
        safe_name = re.sub(r'[^\w\s.-]', '', value.name)
        safe_name = safe_name[:255]  # Limit filename length
        value.name = safe_name

        # 8. Check for cell size limits
        max_cell_size = getattr(settings, 'CSV_MAX_CELL_SIZE', 10000)
        value.seek(0)
        try:
            content = value.read().decode('utf-8-sig', errors='ignore')
            value.seek(0)

            # Check if any cell exceeds max size
            for row in csv.reader(StringIO(content)):
                for cell in row:
                    if len(cell) > max_cell_size:
                        raise serializers.ValidationError(
                            f"CSV contains cells larger than {max_cell_size} characters. "
                            "Please reduce cell size."
                        )
        except UnicodeDecodeError:
            pass  # Already handled above

        # SECURITY LOG: File validation successful
        security_logger.info(
            f"SECURITY: CSV file upload validated successfully. "
            f"Filename: {value.name}, Size: {value.size} bytes"
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
