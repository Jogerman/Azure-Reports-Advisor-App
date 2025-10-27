"""
Test cases for reports models
Tests Report, Recommendation, ReportTemplate, and ReportShare models
"""

import pytest
import uuid
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from apps.reports.models import Report, Recommendation, ReportTemplate, ReportShare
from apps.clients.models import Client

User = get_user_model()


@pytest.mark.django_db
class TestReportModel:
    """Test suite for Report model"""

    def test_report_creation(self):
        """Test creating a report with all required fields"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed",
            title="Test Report"
        )

        assert report.id is not None
        assert isinstance(report.id, uuid.UUID)
        assert report.client == client
        assert report.created_by == user
        assert report.report_type == "detailed"
        assert report.title == "Test Report"
        assert report.status == "pending"

    def test_report_default_status(self):
        """Test that default status is 'pending'"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="executive"
        )

        assert report.status == "pending"

    def test_report_type_choices(self):
        """Test all valid report type choices"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report_types = ["detailed", "executive", "cost", "security", "operations"]

        for report_type in report_types:
            report = Report.objects.create(
                client=client,
                created_by=user,
                report_type=report_type
            )
            assert report.report_type == report_type
            assert report.get_report_type_display() in [
                "Detailed Report", "Executive Summary", "Cost Optimization",
                "Security Assessment", "Operational Excellence"
            ]

    def test_report_status_choices(self):
        """Test all valid status choices"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        statuses = ["pending", "uploaded", "processing", "generating", "completed", "failed", "cancelled"]

        for status in statuses:
            report = Report.objects.create(
                client=client,
                created_by=user,
                report_type="detailed",
                status=status
            )
            assert report.status == status

    def test_report_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed",
            title="Custom Report Title"
        )

        assert "Custom Report Title" in str(report)
        assert "Test Company" in str(report)

    def test_report_without_title(self):
        """Test report string representation without custom title"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="executive"
        )

        assert "Executive Summary Report" in str(report) or "Executive Summary" in str(report)

    def test_report_with_csv_file(self):
        """Test report with uploaded CSV file"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        csv_file = SimpleUploadedFile("test.csv", b"Category,Business Impact\nCost,High")

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed",
            csv_file=csv_file
        )

        assert report.csv_file is not None
        assert "test.csv" in report.csv_file.name

    def test_start_processing(self):
        """Test start_processing method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        before = timezone.now()
        report.start_processing()
        after = timezone.now()

        assert report.status == "processing"
        assert report.processing_started_at is not None
        assert before <= report.processing_started_at <= after

    def test_complete_processing(self):
        """Test complete_processing method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        report.start_processing()

        before = timezone.now()
        report.complete_processing()
        after = timezone.now()

        assert report.status == "completed"
        assert report.processing_completed_at is not None
        assert before <= report.processing_completed_at <= after

    def test_fail_processing(self):
        """Test fail_processing method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        report.start_processing()

        error_message = "Test error occurred"
        before = timezone.now()
        report.fail_processing(error_message)
        after = timezone.now()

        assert report.status == "failed"
        assert report.error_message == error_message
        assert report.processing_completed_at is not None
        assert before <= report.processing_completed_at <= after
        assert report.retry_count == 1

    def test_processing_duration(self):
        """Test processing_duration property"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        report.start_processing()
        import time
        time.sleep(0.1)
        report.complete_processing()

        duration = report.processing_duration
        assert duration is not None
        assert duration.total_seconds() >= 0.1

    def test_processing_duration_none_when_not_completed(self):
        """Test processing_duration is None when report is not completed"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        assert report.processing_duration is None

    def test_can_retry(self):
        """Test can_retry method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        report.fail_processing("Error 1")
        assert report.can_retry() is True
        assert report.retry_count == 1

        # Fail multiple times
        for i in range(2, 6):
            report.fail_processing(f"Error {i}")

        assert report.retry_count == 5
        assert report.can_retry() is False

    def test_report_analysis_data(self):
        """Test analysis_data JSON field"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        analysis_data = {
            "total_recommendations": 50,
            "category_distribution": {
                "Cost": 20,
                "Security": 15,
                "Reliability": 10,
                "OperationalExcellence": 5
            },
            "estimated_monthly_savings": "5000.00",
            "advisor_score": 85
        }

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed",
            analysis_data=analysis_data
        )

        assert report.analysis_data == analysis_data
        assert report.analysis_data["total_recommendations"] == 50

    def test_report_cascade_deletion(self):
        """Test that reports are deleted when client is deleted"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        report_id = report.id
        client.delete()

        assert Report.objects.filter(id=report_id).count() == 0

    def test_report_set_null_on_user_deletion(self):
        """Test that created_by is set to null when user is deleted"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        report_id = report.id
        user.delete()

        report = Report.objects.get(id=report_id)
        assert report.created_by is None


@pytest.mark.django_db
class TestRecommendationModel:
    """Test suite for Recommendation model"""

    def test_recommendation_creation(self):
        """Test creating a recommendation"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        recommendation = Recommendation.objects.create(
            report=report,
            category="cost",
            business_impact="high",
            recommendation="Test recommendation",
            resource_name="test-resource",
            potential_savings=Decimal("1000.00")
        )

        assert recommendation.id is not None
        assert isinstance(recommendation.id, uuid.UUID)
        assert recommendation.report == report
        assert recommendation.category == "cost"
        assert recommendation.business_impact == "high"
        assert recommendation.potential_savings == Decimal("1000.00")

    def test_recommendation_category_choices(self):
        """Test all valid category choices"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        categories = ["cost", "security", "reliability", "operational_excellence", "performance"]

        for category in categories:
            rec = Recommendation.objects.create(
                report=report,
                category=category,
                business_impact="medium",
                recommendation=f"Test {category} recommendation",
                resource_name="test-resource"
            )
            assert rec.category == category

    def test_recommendation_impact_choices(self):
        """Test all valid impact choices"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        impacts = ["high", "medium", "low"]

        for impact in impacts:
            rec = Recommendation.objects.create(
                report=report,
                category="cost",
                business_impact=impact,
                recommendation=f"Test {impact} impact recommendation",
                resource_name="test-resource"
            )
            assert rec.business_impact == impact

    def test_recommendation_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        recommendation = Recommendation.objects.create(
            report=report,
            category="cost",
            business_impact="high",
            recommendation="Test recommendation",
            resource_name="test-vm",
            potential_savings=Decimal("2500.50")
        )

        str_repr = str(recommendation)
        assert "Cost" in str_repr or "cost" in str_repr
        assert "test-vm" in str_repr
        assert "2500" in str_repr

    def test_monthly_savings_property(self):
        """Test monthly_savings property"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        recommendation = Recommendation.objects.create(
            report=report,
            category="cost",
            business_impact="high",
            recommendation="Test recommendation",
            resource_name="test-resource",
            potential_savings=Decimal("1200.00")
        )

        assert recommendation.monthly_savings == Decimal("100.00")

    def test_recommendation_with_azure_details(self):
        """Test recommendation with Azure resource details"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        subscription_id = str(uuid.uuid4())

        recommendation = Recommendation.objects.create(
            report=report,
            category="cost",
            business_impact="high",
            recommendation="Resize VM",
            subscription_id=subscription_id,
            subscription_name="Production Subscription",
            resource_group="rg-production",
            resource_name="vm-web-01",
            resource_type="Microsoft.Compute/virtualMachines",
            potential_savings=Decimal("3600.00"),
            currency="USD",
            potential_benefits="Reduce costs by 60%"
        )

        assert recommendation.subscription_id == subscription_id
        assert recommendation.subscription_name == "Production Subscription"
        assert recommendation.resource_group == "rg-production"
        assert recommendation.resource_name == "vm-web-01"
        assert recommendation.resource_type == "Microsoft.Compute/virtualMachines"
        assert recommendation.currency == "USD"

    def test_recommendation_count_property(self):
        """Test report's recommendation_count property"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        for i in range(5):
            Recommendation.objects.create(
                report=report,
                category="cost",
                business_impact="medium",
                recommendation=f"Recommendation {i}",
                resource_name=f"resource-{i}"
            )

        assert report.recommendation_count == 5

    def test_total_potential_savings_property(self):
        """Test report's total_potential_savings property"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        savings = [Decimal("1000.00"), Decimal("2000.00"), Decimal("1500.50")]

        for i, saving in enumerate(savings):
            Recommendation.objects.create(
                report=report,
                category="cost",
                business_impact="medium",
                recommendation=f"Recommendation {i}",
                resource_name=f"resource-{i}",
                potential_savings=saving
            )

        total = report.total_potential_savings
        assert total == sum(savings)

    def test_recommendation_cascade_deletion(self):
        """Test that recommendations are deleted when report is deleted"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        for i in range(3):
            Recommendation.objects.create(
                report=report,
                category="cost",
                business_impact="medium",
                recommendation=f"Recommendation {i}",
                resource_name=f"resource-{i}"
            )

        report_id = report.id
        report.delete()

        assert Recommendation.objects.filter(report_id=report_id).count() == 0

    def test_recommendation_advisor_score_impact(self):
        """Test advisor_score_impact field"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        recommendation = Recommendation.objects.create(
            report=report,
            category="security",
            business_impact="high",
            recommendation="Enable MFA",
            resource_name="security-policy",
            advisor_score_impact=Decimal("5.5")
        )

        assert recommendation.advisor_score_impact == Decimal("5.5")

    def test_recommendation_csv_row_number(self):
        """Test csv_row_number field"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        recommendation = Recommendation.objects.create(
            report=report,
            category="cost",
            business_impact="medium",
            recommendation="Test recommendation",
            resource_name="test-resource",
            csv_row_number=15
        )

        assert recommendation.csv_row_number == 15


@pytest.mark.django_db
class TestReportTemplateModel:
    """Test suite for ReportTemplate model"""

    def test_template_creation(self):
        """Test creating a report template"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        template = ReportTemplate.objects.create(
            name="Custom Executive Template",
            report_type="executive",
            html_template="<html><body>{{content}}</body></html>",
            created_by=user
        )

        assert template.id is not None
        assert template.name == "Custom Executive Template"
        assert template.report_type == "executive"
        assert template.is_active is True
        assert template.is_default is False

    def test_template_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        template = ReportTemplate.objects.create(
            name="Test Template",
            report_type="detailed",
            html_template="<html></html>",
            created_by=user
        )

        assert "Test Template" in str(template)
        assert "Detailed Report" in str(template)

    def test_default_template(self):
        """Test setting a template as default"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        template = ReportTemplate.objects.create(
            name="Default Executive Template",
            report_type="executive",
            html_template="<html></html>",
            is_default=True,
            created_by=user
        )

        assert template.is_default is True
        assert " (Default)" in str(template)

    def test_only_one_default_per_type(self):
        """Test that only one template can be default per report type"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        template1 = ReportTemplate.objects.create(
            name="First Default",
            report_type="cost",
            html_template="<html></html>",
            is_default=True,
            created_by=user
        )

        template2 = ReportTemplate.objects.create(
            name="Second Default",
            report_type="cost",
            html_template="<html></html>",
            is_default=True,
            created_by=user
        )

        # Refresh template1 from database
        template1.refresh_from_db()

        assert template2.is_default is True
        assert template1.is_default is False


@pytest.mark.django_db
class TestReportShareModel:
    """Test suite for ReportShare model"""

    def test_share_creation(self):
        """Test creating a report share"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        expires_at = timezone.now() + timedelta(days=7)

        share = ReportShare.objects.create(
            report=report,
            shared_by=user,
            shared_with_email="recipient@example.com",
            permission_level="view",
            access_token="test_token_123",
            expires_at=expires_at
        )

        assert share.id is not None
        assert share.report == report
        assert share.shared_by == user
        assert share.shared_with_email == "recipient@example.com"
        assert share.permission_level == "view"
        assert share.is_active is True
        assert share.access_count == 0

    def test_share_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        share = ReportShare.objects.create(
            report=report,
            shared_by=user,
            shared_with_email="recipient@example.com",
            permission_level="view",
            access_token="test_token",
            expires_at=timezone.now() + timedelta(days=7)
        )

        assert "recipient@example.com" in str(share)

    def test_is_expired_property(self):
        """Test is_expired property"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        # Create expired share
        expired_share = ReportShare.objects.create(
            report=report,
            shared_by=user,
            shared_with_email="expired@example.com",
            permission_level="view",
            access_token="expired_token",
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Create valid share
        valid_share = ReportShare.objects.create(
            report=report,
            shared_by=user,
            shared_with_email="valid@example.com",
            permission_level="view",
            access_token="valid_token",
            expires_at=timezone.now() + timedelta(days=7)
        )

        assert expired_share.is_expired is True
        assert valid_share.is_expired is False

    def test_record_access(self):
        """Test record_access method"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        share = ReportShare.objects.create(
            report=report,
            shared_by=user,
            shared_with_email="recipient@example.com",
            permission_level="download",
            access_token="test_token",
            expires_at=timezone.now() + timedelta(days=7)
        )

        assert share.access_count == 0
        assert share.last_accessed_at is None

        share.record_access()

        assert share.access_count == 1
        assert share.last_accessed_at is not None

        share.record_access()
        assert share.access_count == 2

    def test_unique_token(self):
        """Test that access_token must be unique"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        ReportShare.objects.create(
            report=report,
            shared_by=user,
            shared_with_email="user1@example.com",
            permission_level="view",
            access_token="unique_token",
            expires_at=timezone.now() + timedelta(days=7)
        )

        with pytest.raises(IntegrityError):
            ReportShare.objects.create(
                report=report,
                shared_by=user,
                shared_with_email="user2@example.com",
                permission_level="view",
                access_token="unique_token",
                expires_at=timezone.now() + timedelta(days=7)
            )

    def test_permission_level_choices(self):
        """Test permission level choices"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        client = Client.objects.create(
            company_name="Test Company",
            contact_email="client@example.com"
        )

        report = Report.objects.create(
            client=client,
            created_by=user,
            report_type="detailed"
        )

        permissions = ["view", "download"]

        for i, permission in enumerate(permissions):
            share = ReportShare.objects.create(
                report=report,
                shared_by=user,
                shared_with_email=f"user{i}@example.com",
                permission_level=permission,
                access_token=f"token_{i}",
                expires_at=timezone.now() + timedelta(days=7)
            )
            assert share.permission_level == permission
