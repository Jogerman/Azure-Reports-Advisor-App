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
from django.utils import timezone
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

    total_commitment_savings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    is_long_term_commitment = serializers.BooleanField(read_only=True)

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
            # Saving Plans & Reserved Instances fields (v1.6.3)
            'is_reservation_recommendation',
            'reservation_type',
            'commitment_term_years',
            'total_commitment_savings',
            'is_long_term_commitment',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'monthly_savings',
            'total_commitment_savings',
            'is_long_term_commitment',
        ]


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
    created_by_name = serializers.SerializerMethodField()

    # v2.0 dual data source fields
    azure_subscription_detail = serializers.SerializerMethodField()

    def get_created_by_name(self, obj):
        """Get the full name of the user who created the report."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_azure_subscription_detail(self, obj):
        """Get Azure subscription details if using API data source."""
        if obj.azure_subscription:
            return {
                'id': str(obj.azure_subscription.id),
                'name': obj.azure_subscription.name,
                'subscription_id': obj.azure_subscription.subscription_id,
            }
        return None

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
            'data_source',
            'csv_file',
            'azure_subscription',
            'azure_subscription_detail',
            'api_sync_metadata',
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
            'data_source',
            'azure_subscription_detail',
            'api_sync_metadata',
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
    created_by_name = serializers.SerializerMethodField()
    recommendation_count = serializers.IntegerField(read_only=True)
    total_potential_savings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    def get_created_by_name(self, obj):
        """Get the full name of the user who created the report."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

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
            'data_source',
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
        read_only_fields = ['id', 'created_by', 'data_source', 'status', 'html_file', 'pdf_file', 'created_at', 'updated_at', 'processing_completed_at', 'error_message']


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


class ReportCreateSerializer(serializers.Serializer):
    """
    Serializer for creating reports with dual data source support.

    Handles XOR validation between CSV upload and Azure API data sources.
    A report must have either a CSV file OR an Azure subscription, but not both.

    Fields:
        - client_id: Client UUID (required)
        - report_type: Type of report (default: 'detailed')
        - title: Custom report title (optional)
        - data_source: 'csv' or 'azure_api' (default: 'csv')
        - csv_file: CSV file (required if data_source='csv')
        - azure_subscription: Azure subscription ID (required if data_source='azure_api')
        - filters: Azure API filters (optional, only for azure_api)
    """

    client_id = serializers.UUIDField(required=True)
    report_type = serializers.ChoiceField(
        choices=Report.REPORT_TYPES,
        default='detailed',
        required=False
    )
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # Data source selection
    data_source = serializers.ChoiceField(
        choices=Report.DATA_SOURCE_CHOICES,
        default='csv',
        required=False,
        help_text="Source of report data: 'csv' or 'azure_api'"
    )

    # CSV upload fields
    csv_file = serializers.FileField(required=False, allow_null=True)

    # Azure API fields - queryset set dynamically in __init__
    azure_subscription = serializers.PrimaryKeyRelatedField(
        read_only=True,  # Temporarily set to read_only, overridden in __init__
        required=False,
        allow_null=True,
        help_text="Azure subscription for API-based reports"
    )

    filters = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Filters for Azure API queries (category, impact, resource_group)"
    )

    def __init__(self, *args, **kwargs):
        """Initialize with AzureSubscription queryset."""
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from apps.azure_integration.models import AzureSubscription
        # Override the field to make it writable with a queryset
        self.fields['azure_subscription'] = serializers.PrimaryKeyRelatedField(
            queryset=AzureSubscription.objects.filter(is_active=True),
            required=False,
            allow_null=True,
            help_text="Azure subscription for API-based reports"
        )

    def validate_client_id(self, value):
        """Validate that the client exists."""
        from apps.clients.models import Client

        try:
            Client.objects.get(id=value)
        except Client.DoesNotExist:
            raise serializers.ValidationError(f"Client with ID {value} does not exist")

        return value

    def validate_csv_file(self, value):
        """Validate CSV file using existing CSVUploadSerializer validation."""
        if value is None:
            return value

        # Use the comprehensive CSV validation from CSVUploadSerializer
        csv_serializer = CSVUploadSerializer(data={})
        validated_file = csv_serializer.validate_csv_file(value)
        return validated_file

    def validate_filters(self, value):
        """
        Validate filters for Azure API data source.

        Allowed filter keys: category, impact, resource_group
        Validates category and impact values against Azure Advisor spec.
        """
        if not value:
            return value

        if not isinstance(value, dict):
            raise serializers.ValidationError('Filters must be a JSON object.')

        allowed_keys = {'category', 'impact', 'resource_group'}
        invalid_keys = set(value.keys()) - allowed_keys

        if invalid_keys:
            raise serializers.ValidationError(
                f"Invalid filter keys: {', '.join(invalid_keys)}. "
                f"Allowed: {', '.join(allowed_keys)}"
            )

        # Validate category values
        if 'category' in value:
            valid_categories = [
                'Cost', 'HighAvailability', 'Performance',
                'Security', 'OperationalExcellence'
            ]
            if value['category'] not in valid_categories:
                raise serializers.ValidationError({
                    'category': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
                })

        # Validate impact values
        if 'impact' in value:
            valid_impacts = ['High', 'Medium', 'Low']
            if value['impact'] not in valid_impacts:
                raise serializers.ValidationError({
                    'impact': f'Invalid impact. Must be one of: {", ".join(valid_impacts)}'
                })

        return value

    def validate(self, data):
        """
        Validate XOR constraint between CSV and Azure API data sources.

        Rules:
        1. If data_source='csv': csv_file required, azure_subscription forbidden
        2. If data_source='azure_api': azure_subscription required, csv_file forbidden
        3. Azure subscription must be active
        4. Filters only allowed for azure_api data source
        """
        data_source = data.get('data_source', 'csv')
        csv_file = data.get('csv_file')
        azure_subscription = data.get('azure_subscription')
        filters = data.get('filters')

        if data_source == 'csv':
            # CSV data source validation
            if not csv_file:
                raise serializers.ValidationError({
                    'csv_file': 'CSV file is required when data_source is "csv".'
                })
            if azure_subscription:
                raise serializers.ValidationError({
                    'azure_subscription': 'Cannot specify Azure subscription when using CSV data source.'
                })
            if filters:
                raise serializers.ValidationError({
                    'filters': 'Filters are only applicable for Azure API data source.'
                })

        elif data_source == 'azure_api':
            # Azure API data source validation
            if not azure_subscription:
                raise serializers.ValidationError({
                    'azure_subscription': 'Azure subscription is required when data_source is "azure_api".'
                })
            if csv_file:
                raise serializers.ValidationError({
                    'csv_file': 'Cannot upload CSV when using Azure API data source.'
                })

            # Validate subscription is active
            if not azure_subscription.is_active:
                raise serializers.ValidationError({
                    'azure_subscription': 'Selected Azure subscription is not active.'
                })

        else:
            raise serializers.ValidationError({
                'data_source': 'Invalid data source. Must be "csv" or "azure_api".'
            })

        return data

    def create(self, validated_data):
        """
        Create a Report instance from validated data.

        For CSV reports: Creates report with uploaded file
        For Azure API reports: Creates report with subscription and filters

        Args:
            validated_data: Validated data dictionary

        Returns:
            Report instance
        """
        from apps.clients.models import Client

        client = Client.objects.get(id=validated_data['client_id'])
        user = self.context.get('request').user if self.context.get('request') else None

        # Extract optional fields
        filters = validated_data.get('filters')
        data_source = validated_data.get('data_source', 'csv')

        # Create report based on data source
        report = Report(
            client=client,
            created_by=user,
            report_type=validated_data.get('report_type', 'detailed'),
            title=validated_data.get('title', ''),
            data_source=data_source,
        )

        # Set data source-specific fields
        if data_source == 'csv':
            report.csv_file = validated_data['csv_file']
            report.status = 'uploaded'
            report.csv_uploaded_at = timezone.now()
        else:  # azure_api
            report.azure_subscription = validated_data['azure_subscription']
            report.status = 'pending'

            # Store filters in api_sync_metadata
            if filters:
                report.api_sync_metadata = {
                    'filters': filters,
                    'requested_at': timezone.now().isoformat(),
                }

        report.save()

        # Trigger processing for CSV reports
        if data_source == 'csv':
            try:
                from .tasks import process_csv_file as process_csv_task
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Triggering async CSV processing for report {report.id}")
                process_csv_task.delay(str(report.id))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to trigger CSV processing task for report {report.id}: {str(e)}")

        return report


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model."""

    created_by_name = serializers.SerializerMethodField()

    def get_created_by_name(self, obj):
        """Get the full name of the user who created the template."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

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
    shared_by_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    def get_shared_by_name(self, obj):
        """Get the full name of the user who shared the report."""
        if obj.shared_by:
            return obj.shared_by.get_full_name() or obj.shared_by.username
        return None

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


class ManualRecommendationInputSerializer(serializers.Serializer):
    """
    Serializer for manual input of recommendations (v1.7.0).

    Allows users to manually add recommendations to a report before generation.
    This is useful for adding data not captured by Azure Advisor or custom
    recommendations from other sources.

    All fields match the structure of the Recommendation model to maintain
    consistency with CSV-imported data.
    """

    # Required fields
    category = serializers.ChoiceField(
        choices=Recommendation.CATEGORY_CHOICES,
        required=True,
        help_text="Recommendation category"
    )
    business_impact = serializers.ChoiceField(
        choices=Recommendation.IMPACT_CHOICES,
        required=True,
        help_text="Business impact level"
    )
    recommendation = serializers.CharField(
        required=True,
        max_length=5000,
        help_text="Recommendation description"
    )

    # Azure resource information (optional)
    subscription_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default=''
    )
    subscription_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default=''
    )
    resource_group = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default=''
    )
    resource_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default=''
    )
    resource_type = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default=''
    )

    # Financial impact
    potential_savings = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Potential annual cost savings"
    )
    currency = serializers.CharField(
        required=False,
        max_length=3,
        default='USD'
    )

    # Additional details (optional)
    potential_benefits = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        default=''
    )
    retirement_date = serializers.DateField(
        required=False,
        allow_null=True,
        default=None
    )
    retiring_feature = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default=''
    )
    advisor_score_impact = serializers.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Impact on Azure Advisor Score"
    )

    def validate_potential_savings(self, value):
        """Ensure potential savings is non-negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Potential savings cannot be negative")
        return value

    def validate_advisor_score_impact(self, value):
        """Ensure advisor score impact is within valid range."""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Advisor score impact must be between 0 and 100")
        return value


class BulkManualRecommendationSerializer(serializers.Serializer):
    """
    Serializer for bulk adding manual recommendations to a report (v1.7.0).

    Accepts a list of recommendations and creates them all at once.
    Automatically analyzes each recommendation for reservation detection.
    """

    recommendations = ManualRecommendationInputSerializer(many=True, required=True)

    def validate_recommendations(self, value):
        """Ensure at least one recommendation is provided."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one recommendation must be provided")

        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 recommendations can be added at once")

        return value

    def create(self, validated_data):
        """
        Create multiple recommendations for a report.

        Automatically analyzes each recommendation using ReservationAnalyzer
        to detect Saving Plans and Reserved Instances.

        Args:
            validated_data: Dictionary with 'report' and 'recommendations' list

        Returns:
            List of created Recommendation instances
        """
        from .services.reservation_analyzer import ReservationAnalyzer
        import logging

        logger = logging.getLogger(__name__)

        report = self.context.get('report')
        if not report:
            raise serializers.ValidationError("Report context is required")

        recommendations_data = validated_data['recommendations']
        created_recommendations = []

        for idx, rec_data in enumerate(recommendations_data):
            try:
                # Analyze for reservations using ReservationAnalyzer
                reservation_analysis = ReservationAnalyzer.analyze_recommendation(
                    rec_data.get('recommendation', ''),
                    rec_data.get('potential_benefits', '')
                )

                # Create recommendation with analyzed data
                recommendation = Recommendation.objects.create(
                    report=report,
                    category=rec_data['category'],
                    business_impact=rec_data['business_impact'],
                    recommendation=rec_data['recommendation'],
                    subscription_id=rec_data.get('subscription_id', ''),
                    subscription_name=rec_data.get('subscription_name', ''),
                    resource_group=rec_data.get('resource_group', ''),
                    resource_name=rec_data.get('resource_name', ''),
                    resource_type=rec_data.get('resource_type', ''),
                    potential_savings=rec_data.get('potential_savings', 0),
                    currency=rec_data.get('currency', 'USD'),
                    potential_benefits=rec_data.get('potential_benefits', ''),
                    retirement_date=rec_data.get('retirement_date'),
                    retiring_feature=rec_data.get('retiring_feature', ''),
                    advisor_score_impact=rec_data.get('advisor_score_impact', 0),
                    # Reservation analysis results
                    is_reservation_recommendation=reservation_analysis['is_reservation'],
                    reservation_type=reservation_analysis['reservation_type'],
                    commitment_term_years=reservation_analysis['commitment_term_years'],
                    # Mark as manually added (use csv_row_number = -1 to indicate manual)
                    csv_row_number=-1,
                )

                created_recommendations.append(recommendation)

            except Exception as e:
                logger.error(f"Failed to create manual recommendation {idx}: {str(e)}")
                raise serializers.ValidationError(
                    f"Failed to create recommendation {idx + 1}: {str(e)}"
                )

        logger.info(
            f"Successfully created {len(created_recommendations)} manual recommendations "
            f"for report {report.id}"
        )

        return created_recommendations
