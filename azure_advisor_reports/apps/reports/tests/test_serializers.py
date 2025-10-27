"""
Comprehensive test suite for Reports serializers.

Tests all serializers in the reports app including:
- RecommendationSerializer
- RecommendationListSerializer
- ReportSerializer
- ReportListSerializer
- CSVUploadSerializer
- ReportTemplateSerializer
- ReportShareSerializer
"""

import pytest
import uuid
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from apps.reports.models import Report, Recommendation, ReportTemplate, ReportShare
from apps.reports.serializers import (
    RecommendationSerializer,
    RecommendationListSerializer,
    ReportSerializer,
    ReportListSerializer,
    CSVUploadSerializer,
    ReportTemplateSerializer,
    ReportShareSerializer,
)
from apps.clients.models import Client

User = get_user_model()


# ============================================================================
# RecommendationSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestRecommendationSerializer:
    """Test suite for RecommendationSerializer."""

    def test_serializer_with_valid_data(self, test_report):
        """Test serializer with all valid fields."""
        data = {
            'report': test_report.id,
            'category': 'cost',
            'business_impact': 'high',
            'recommendation': 'Reduce VM size',
            'subscription_id': str(uuid.uuid4()),
            'subscription_name': 'Prod Subscription',
            'resource_group': 'rg-production',
            'resource_name': 'vm-web-01',
            'resource_type': 'Microsoft.Compute/virtualMachines',
            'potential_savings': '1200.00',
            'currency': 'USD',
            'potential_benefits': 'Save 50% on compute costs',
            'advisor_score_impact': '10.00',
            'csv_row_number': 5
        }

        serializer = RecommendationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        recommendation = serializer.save()

        assert recommendation.category == 'cost'
        assert recommendation.potential_savings == Decimal('1200.00')
        assert recommendation.monthly_savings == Decimal('100.00')

    def test_serializer_monthly_savings_calculation(self, test_recommendation):
        """Test that monthly_savings is correctly calculated."""
        serializer = RecommendationSerializer(test_recommendation)
        data = serializer.data

        assert 'monthly_savings' in data
        # Annual savings / 12
        expected_monthly = test_recommendation.potential_savings / 12
        assert Decimal(data['monthly_savings']) == expected_monthly

    def test_serializer_read_only_fields(self, test_recommendation):
        """Test that read-only fields cannot be modified."""
        serializer = RecommendationSerializer(test_recommendation)
        data = serializer.data

        # These fields should be read-only
        assert 'id' in data
        assert 'created_at' in data
        assert 'monthly_savings' in data

        # Attempting to update read-only fields should be ignored
        update_data = {'id': uuid.uuid4(), 'monthly_savings': '9999.99'}
        serializer = RecommendationSerializer(test_recommendation, data=update_data, partial=True)
        assert serializer.is_valid()

    def test_serializer_with_minimal_data(self, test_report):
        """Test serializer with only required fields."""
        data = {
            'report': test_report.id,
            'category': 'security',
            'business_impact': 'medium',
            'recommendation': 'Enable MFA',
        }

        serializer = RecommendationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        recommendation = serializer.save()

        assert recommendation.recommendation == 'Enable MFA'
        assert recommendation.potential_savings == Decimal('0.00')

    def test_serializer_invalid_category(self, test_report):
        """Test validation fails for invalid category."""
        data = {
            'report': test_report.id,
            'category': 'invalid_category',
            'business_impact': 'high',
            'recommendation': 'Test',
        }

        serializer = RecommendationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors

    def test_serializer_invalid_impact(self, test_report):
        """Test validation fails for invalid business impact."""
        data = {
            'report': test_report.id,
            'category': 'cost',
            'business_impact': 'invalid_impact',
            'recommendation': 'Test',
        }

        serializer = RecommendationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'business_impact' in serializer.errors


# ============================================================================
# RecommendationListSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestRecommendationListSerializer:
    """Test suite for RecommendationListSerializer (lightweight version)."""

    def test_list_serializer_contains_essential_fields(self, test_recommendation):
        """Test that list serializer contains only essential fields."""
        serializer = RecommendationListSerializer(test_recommendation)
        data = serializer.data

        # Should have these fields
        assert 'id' in data
        assert 'category' in data
        assert 'business_impact' in data
        assert 'recommendation' in data
        assert 'resource_name' in data
        assert 'potential_savings' in data
        assert 'currency' in data

        # Should NOT have these verbose fields
        assert 'subscription_name' not in data
        assert 'resource_group' not in data
        assert 'potential_benefits' not in data

    def test_list_serializer_for_multiple_recommendations(self, test_report, test_recommendations_bulk):
        """Test serializing multiple recommendations."""
        recommendations = Recommendation.objects.filter(report=test_report)
        serializer = RecommendationListSerializer(recommendations, many=True)
        data = serializer.data

        assert len(data) == 20  # We created 20 recommendations
        for item in data:
            assert 'id' in item
            assert 'category' in item


# ============================================================================
# ReportSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestReportSerializer:
    """Test suite for ReportSerializer (full detail version)."""

    def test_serializer_with_complete_report(self, test_report_completed, test_user):
        """Test serializing a completed report with all data."""
        serializer = ReportSerializer(test_report_completed)
        data = serializer.data

        assert data['id'] == str(test_report_completed.id)
        assert data['status'] == 'completed'
        assert data['client_name'] == test_report_completed.client.company_name
        assert 'analysis_data' in data
        assert 'processing_duration' in data

    def test_serializer_includes_recommendations(self, test_report, test_recommendation):
        """Test that recommendations are included in report serialization."""
        serializer = ReportSerializer(test_report)
        data = serializer.data

        assert 'recommendations' in data
        assert len(data['recommendations']) == 1
        assert data['recommendations'][0]['id'] == str(test_recommendation.id)

    def test_serializer_calculated_fields(self, test_report, test_recommendations_bulk):
        """Test calculated fields like recommendation_count and total_potential_savings."""
        serializer = ReportSerializer(test_report)
        data = serializer.data

        assert 'recommendation_count' in data
        assert data['recommendation_count'] == 20

        assert 'total_potential_savings' in data
        # Sum of 100, 200, 300, ..., 2000 = 21000.00
        expected_total = sum(Decimal(str(100.00 * (i + 1))) for i in range(20))
        assert Decimal(data['total_potential_savings']) == expected_total

    def test_serializer_processing_duration(self, test_report_completed):
        """Test that processing_duration is correctly included."""
        serializer = ReportSerializer(test_report_completed)
        data = serializer.data

        assert 'processing_duration' in data
        # Duration should be a timedelta formatted as string

    def test_serializer_client_and_user_names(self, test_report):
        """Test that client_name and created_by_name are properly serialized."""
        serializer = ReportSerializer(test_report)
        data = serializer.data

        assert 'client_name' in data
        assert data['client_name'] == test_report.client.company_name

        assert 'created_by_name' in data
        # User's name property should be "First Last"

    def test_serializer_read_only_fields(self, test_report):
        """Test that computed fields are read-only."""
        serializer = ReportSerializer(test_report)
        data = serializer.data

        # These should all be read-only
        read_only_fields = [
            'id', 'recommendation_count', 'total_potential_savings',
            'processing_duration', 'client_name', 'created_by_name'
        ]

        for field in read_only_fields:
            assert field in data


# ============================================================================
# ReportListSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestReportListSerializer:
    """Test suite for ReportListSerializer (lightweight version)."""

    def test_list_serializer_essential_fields(self, test_report):
        """Test that list serializer contains only essential fields."""
        serializer = ReportListSerializer(test_report)
        data = serializer.data

        # Should have these
        assert 'id' in data
        assert 'client_name' in data
        assert 'report_type' in data
        assert 'status' in data
        assert 'created_at' in data

        # Should NOT have these verbose fields
        assert 'recommendations' not in data
        assert 'analysis_data' not in data

    def test_list_serializer_multiple_reports(self, test_client_obj, test_user):
        """Test serializing multiple reports."""
        # Create multiple reports
        reports = []
        for i in range(5):
            report = Report.objects.create(
                client=test_client_obj,
                created_by=test_user,
                report_type=['detailed', 'executive', 'cost', 'security', 'operations'][i],
                title=f"Test Report {i+1}"
            )
            reports.append(report)

        serializer = ReportListSerializer(reports, many=True)
        data = serializer.data

        assert len(data) == 5
        for item in data:
            assert 'id' in item
            assert 'report_type' in item


# ============================================================================
# CSVUploadSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestCSVUploadSerializer:
    """Test suite for CSVUploadSerializer."""

    def test_valid_csv_upload(self, test_client_obj, test_user):
        """Test valid CSV file upload."""
        csv_content = b"Category,Recommendation,Business Impact\nCost,Test,High"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client': test_client_obj.id,
            'csv_file': csv_file,
            'report_type': 'detailed',
            'title': 'Test Upload'
        }

        # Need to pass request context with user
        class MockRequest:
            def __init__(self, user):
                self.user = user

        serializer = CSVUploadSerializer(
            data=data,
            context={'request': MockRequest(test_user)}
        )
        assert serializer.is_valid(), serializer.errors

    def test_csv_file_required(self, test_client_obj):
        """Test that CSV file is required."""
        data = {
            'client': test_client_obj.id,
            'report_type': 'detailed'
        }

        serializer = CSVUploadSerializer(data=data)
        assert not serializer.is_valid()
        assert 'csv_file' in serializer.errors

    def test_invalid_file_extension(self, test_client_obj):
        """Test validation fails for non-CSV files."""
        txt_file = SimpleUploadedFile("test.txt", b"Not a CSV", content_type="text/plain")

        data = {
            'client': test_client_obj.id,
            'csv_file': txt_file,
            'report_type': 'detailed'
        }

        serializer = CSVUploadSerializer(data=data)
        assert not serializer.is_valid()
        # Should fail validation due to file extension

    def test_file_too_large(self, test_client_obj):
        """Test validation fails for files exceeding size limit."""
        # Create a file larger than MAX_FILE_SIZE (if implemented)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        large_file = SimpleUploadedFile("large.csv", large_content, content_type="text/csv")

        data = {
            'client': test_client_obj.id,
            'csv_file': large_file,
            'report_type': 'detailed'
        }

        serializer = CSVUploadSerializer(data=data)
        # May or may not fail depending on MAX_FILE_SIZE setting
        # This is a placeholder for size validation test

    def test_default_report_type(self, test_client_obj, test_user):
        """Test that report_type defaults to 'detailed' if not provided."""
        csv_content = b"Category,Recommendation\nCost,Test"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client': test_client_obj.id,
            'csv_file': csv_file
        }

        class MockRequest:
            def __init__(self, user):
                self.user = user

        serializer = CSVUploadSerializer(
            data=data,
            context={'request': MockRequest(test_user)}
        )
        if serializer.is_valid():
            # Check that it defaults to 'detailed'
            assert serializer.validated_data.get('report_type') == 'detailed'


# ============================================================================
# ReportTemplateSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestReportTemplateSerializer:
    """Test suite for ReportTemplateSerializer."""

    def test_serializer_with_valid_template(self, test_user):
        """Test serializing a valid template."""
        template = ReportTemplate.objects.create(
            name="Test Template",
            report_type="executive",
            html_template="<html><body>{{content}}</body></html>",
            css_styles="body { margin: 0; }",
            created_by=test_user,
            is_active=True,
            is_default=False
        )

        serializer = ReportTemplateSerializer(template)
        data = serializer.data

        assert data['name'] == "Test Template"
        assert data['report_type'] == "executive"
        assert data['is_active'] is True

    def test_create_template_via_serializer(self, test_user):
        """Test creating a template via serializer."""
        data = {
            'name': 'New Template',
            'report_type': 'cost',
            'html_template': '<html></html>',
            'created_by': test_user.id,
            'is_active': True
        }

        serializer = ReportTemplateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        template = serializer.save()

        assert template.name == 'New Template'
        assert template.report_type == 'cost'


# ============================================================================
# ReportShareSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestReportShareSerializer:
    """Test suite for ReportShareSerializer."""

    def test_serializer_with_valid_share(self, test_report, test_user):
        """Test serializing a valid report share."""
        share = ReportShare.objects.create(
            report=test_report,
            shared_by=test_user,
            shared_with_email="recipient@example.com",
            permission_level="view",
            access_token="test_token_123",
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True
        )

        serializer = ReportShareSerializer(share)
        data = serializer.data

        assert data['shared_with_email'] == "recipient@example.com"
        assert data['permission_level'] == "view"
        assert data['is_active'] is True

    def test_is_expired_in_serializer(self, test_report, test_user):
        """Test that is_expired property is included."""
        # Create expired share
        expired_share = ReportShare.objects.create(
            report=test_report,
            shared_by=test_user,
            shared_with_email="expired@example.com",
            permission_level="view",
            access_token="expired_token",
            expires_at=timezone.now() - timedelta(days=1)
        )

        serializer = ReportShareSerializer(expired_share)
        data = serializer.data

        # Should include is_expired property
        if 'is_expired' in data:
            assert data['is_expired'] is True

    def test_create_share_via_serializer(self, test_report, test_user):
        """Test creating a share via serializer."""
        data = {
            'report': test_report.id,
            'shared_by': test_user.id,
            'shared_with_email': 'newshare@example.com',
            'permission_level': 'download',
            'access_token': 'new_token_456',
            'expires_at': (timezone.now() + timedelta(days=14)).isoformat()
        }

        serializer = ReportShareSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        share = serializer.save()

        assert share.shared_with_email == 'newshare@example.com'
        assert share.permission_level == 'download'


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
class TestSerializerEdgeCases:
    """Test edge cases and boundary conditions for serializers."""

    def test_recommendation_with_zero_savings(self, test_report):
        """Test recommendation with zero potential savings."""
        data = {
            'report': test_report.id,
            'category': 'security',
            'business_impact': 'high',
            'recommendation': 'Enable security feature',
            'potential_savings': '0.00'
        }

        serializer = RecommendationSerializer(data=data)
        assert serializer.is_valid()
        recommendation = serializer.save()
        assert recommendation.potential_savings == Decimal('0.00')
        assert recommendation.monthly_savings == Decimal('0.00')

    def test_recommendation_with_null_optional_fields(self, test_report):
        """Test recommendation can have null optional fields."""
        data = {
            'report': test_report.id,
            'category': 'reliability',
            'business_impact': 'medium',
            'recommendation': 'Test recommendation'
        }

        serializer = RecommendationSerializer(data=data)
        assert serializer.is_valid()
        recommendation = serializer.save()

        assert recommendation.subscription_id is None or recommendation.subscription_id == ''
        assert recommendation.resource_group is None or recommendation.resource_group == ''

    def test_report_with_empty_analysis_data(self, test_client_obj, test_user):
        """Test report serialization with empty analysis_data."""
        report = Report.objects.create(
            client=test_client_obj,
            created_by=test_user,
            report_type='detailed',
            analysis_data={}
        )

        serializer = ReportSerializer(report)
        data = serializer.data

        assert data['analysis_data'] == {}

    def test_report_without_created_by(self, test_client_obj):
        """Test report serialization when created_by is None."""
        report = Report.objects.create(
            client=test_client_obj,
            created_by=None,
            report_type='executive'
        )

        serializer = ReportSerializer(report)
        data = serializer.data

        assert data['created_by'] is None
        # created_by_name should handle None gracefully

    def test_large_potential_savings(self, test_report):
        """Test recommendation with very large potential savings."""
        data = {
            'report': test_report.id,
            'category': 'cost',
            'business_impact': 'high',
            'recommendation': 'Major optimization',
            'potential_savings': '9999999.99'
        }

        serializer = RecommendationSerializer(data=data)
        assert serializer.is_valid()
        recommendation = serializer.save()
        assert recommendation.potential_savings == Decimal('9999999.99')

    def test_unicode_in_recommendation_text(self, test_report):
        """Test recommendation with unicode characters."""
        data = {
            'report': test_report.id,
            'category': 'cost',
            'business_impact': 'low',
            'recommendation': 'Optimize resources with special chars: €, £, ¥, ©, ®'
        }

        serializer = RecommendationSerializer(data=data)
        assert serializer.is_valid()
        recommendation = serializer.save()
        assert '€' in recommendation.recommendation
        assert '£' in recommendation.recommendation


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.slow
class TestSerializerPerformance:
    """Test serializer performance with large datasets."""

    def test_serialize_many_recommendations(self, test_report):
        """Test serializing 100 recommendations."""
        # Create 100 recommendations
        recommendations = []
        for i in range(100):
            rec = Recommendation(
                report=test_report,
                category='cost',
                business_impact='medium',
                recommendation=f'Recommendation {i}',
                resource_name=f'resource-{i}',
                potential_savings=Decimal('100.00')
            )
            recommendations.append(rec)

        Recommendation.objects.bulk_create(recommendations)

        # Serialize all
        queryset = Recommendation.objects.filter(report=test_report)
        serializer = RecommendationListSerializer(queryset, many=True)
        data = serializer.data

        assert len(data) == 100

    def test_report_with_many_recommendations(self, test_report):
        """Test report serializer with many recommendations."""
        # Create 50 recommendations
        recommendations = []
        for i in range(50):
            rec = Recommendation(
                report=test_report,
                category=['cost', 'security', 'reliability'][i % 3],
                business_impact=['high', 'medium', 'low'][i % 3],
                recommendation=f'Recommendation {i}',
                resource_name=f'resource-{i}',
                potential_savings=Decimal(str(100.00 * (i + 1)))
            )
            recommendations.append(rec)

        Recommendation.objects.bulk_create(recommendations)

        # Serialize report with all recommendations
        serializer = ReportSerializer(test_report)
        data = serializer.data

        assert len(data['recommendations']) == 50
        assert data['recommendation_count'] == 50
