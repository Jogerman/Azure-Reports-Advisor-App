"""
Serializers for Reports app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Report, Recommendation, ReportTemplate, ReportShare

User = get_user_model()


class RecommendationSerializer(serializers.ModelSerializer):
    """Serializer for Recommendation model."""

    class Meta:
        model = Recommendation
        fields = [
            'id', 'category', 'impact', 'title', 'description',
            'recommendation', 'resource_name', 'resource_type',
            'resource_group', 'subscription_id', 'potential_savings',
            'currency', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RecommendationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for recommendation lists."""

    class Meta:
        model = Recommendation
        fields = [
            'id', 'category', 'impact', 'title', 'resource_name',
            'potential_savings', 'currency'
        ]
        read_only_fields = ['id']


class ReportSerializer(serializers.ModelSerializer):
    """Full serializer for Report model."""

    recommendations = RecommendationSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'client', 'client_name', 'title', 'report_type',
            'report_type_display', 'status', 'status_display', 'csv_file',
            'pdf_file', 'file_url', 'file_path', 'file_size', 'created_by',
            'created_by_email', 'created_at', 'updated_at',
            'processing_started_at', 'processing_completed_at',
            'error_message', 'celery_task_id', 'subscription_ids',
            'date_range_start', 'date_range_end', 'parameters',
            'total_recommendations', 'high_impact_count',
            'medium_impact_count', 'low_impact_count', 'estimated_savings',
            'recommendations'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'processing_started_at',
            'processing_completed_at', 'celery_task_id', 'file_size',
            'client_name', 'created_by_email', 'report_type_display',
            'status_display'
        ]


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for report lists."""

    client_name = serializers.CharField(source='client.company_name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recommendation_count = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'client', 'client_name', 'title', 'report_type',
            'report_type_display', 'status', 'status_display', 'created_at',
            'total_recommendations', 'recommendation_count', 'estimated_savings',
            'file_url', 'file_size'
        ]
        read_only_fields = ['id', 'created_at']

    def get_recommendation_count(self, obj):
        """Get total recommendation count."""
        return obj.total_recommendations


class CSVUploadSerializer(serializers.Serializer):
    """Serializer for CSV file upload."""

    csv_file = serializers.FileField(required=True)
    client = serializers.UUIDField(required=True)
    report_type = serializers.ChoiceField(
        choices=Report.REPORT_TYPE_CHOICES,
        default='detailed'
    )
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    subscription_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    date_range_start = serializers.DateField(required=False, allow_null=True)
    date_range_end = serializers.DateField(required=False, allow_null=True)

    def validate_csv_file(self, value):
        """Validate CSV file."""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV file.")
        if value.size > 50 * 1024 * 1024:  # 50MB limit
            raise serializers.ValidationError("File size must not exceed 50MB.")
        return value


class CSVExportRequestSerializer(serializers.Serializer):
    """Serializer for CSV export requests."""

    report_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    filters = serializers.DictField(required=False, allow_empty=True)
    export_type = serializers.ChoiceField(
        choices=['summary', 'detailed', 'recommendations'],
        default='summary'
    )


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model."""

    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'configuration',
            'created_by', 'created_by_email', 'created_at', 'updated_at',
            'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_email']


class ReportShareSerializer(serializers.ModelSerializer):
    """Serializer for ReportShare model."""

    shared_by_email = serializers.EmailField(source='shared_by.email', read_only=True)
    shared_with_email = serializers.EmailField(source='shared_with.email', read_only=True)
    report_title = serializers.CharField(source='report.title', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReportShare
        fields = [
            'id', 'report', 'report_title', 'shared_by', 'shared_by_email',
            'shared_with', 'shared_with_email', 'can_edit', 'can_delete',
            'shared_at', 'expires_at', 'accessed_at', 'access_count',
            'is_expired'
        ]
        read_only_fields = [
            'id', 'shared_at', 'accessed_at', 'access_count',
            'shared_by_email', 'shared_with_email', 'report_title', 'is_expired'
        ]


class HistoryStatisticsSerializer(serializers.Serializer):
    """Serializer for history statistics."""

    total_reports = serializers.IntegerField()
    completed_reports = serializers.IntegerField()
    failed_reports = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    total_recommendations = serializers.IntegerField()
    total_savings = serializers.DecimalField(max_digits=15, decimal_places=2)
    avg_processing_time = serializers.FloatField()
    reports_by_type = serializers.DictField()
    reports_by_client = serializers.ListField()


class TrendsResponseSerializer(serializers.Serializer):
    """Serializer for trends data."""

    period = serializers.CharField()
    report_count = serializers.IntegerField()
    total_recommendations = serializers.IntegerField()
    total_savings = serializers.DecimalField(max_digits=15, decimal_places=2)
    avg_processing_time = serializers.FloatField()
    high_impact_percentage = serializers.FloatField()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UsersListResponseSerializer(serializers.Serializer):
    """Serializer for users list response."""

    users = UserSerializer(many=True, read_only=True)
    count = serializers.IntegerField()
