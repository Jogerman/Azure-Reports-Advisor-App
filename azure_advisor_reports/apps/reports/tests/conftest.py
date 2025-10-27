"""
Pytest fixtures for reports app testing.

Provides reusable test data and objects for report generation tests.
"""

import pytest
import os
from decimal import Decimal
from datetime import datetime, date, timedelta


@pytest.fixture
def test_user(db):
    """Create a test user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role='analyst'
    )


@pytest.fixture
def test_admin_user(db):
    """Create a test admin user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def test_client(db):
    """Create a test client."""
    from apps.clients.models import Client
    return Client.objects.create(
        company_name="Test Company Inc.",
        industry="Technology",
        contact_email="contact@testcompany.com",
        contact_phone="+1-555-0100",
        azure_subscription_ids=["sub-123-456", "sub-789-012"],
        status='active',
        notes="Test client for unit testing"
    )


@pytest.fixture
def test_client_inactive(db):
    """Create an inactive test client."""
    from apps.clients.models import Client
    return Client.objects.create(
        company_name="Inactive Company",
        industry="Healthcare",
        contact_email="contact@inactive.com",
        status='inactive'
    )


@pytest.fixture
def test_report(db, test_client, test_user):
    """Create a test report with pending status."""
    from apps.reports.models import Report
    return Report.objects.create(
        client=test_client,
        created_by=test_user,
        report_type='detailed',
        status='pending',
        title="Test Detailed Report"
    )


@pytest.fixture
def test_report_with_csv(db, test_client, test_user):
    """Create a test report with CSV file uploaded."""
    from apps.reports.models import Report
    from django.core.files.uploadedfile import SimpleUploadedFile

    csv_content = b"Category,Recommendation,Impact\nCost,Reduce VM size,High"
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

    return Report.objects.create(
        client=test_client,
        created_by=test_user,
        report_type='detailed',
        status='uploaded',
        csv_file=csv_file,
        title="Test Report with CSV"
    )


@pytest.fixture
def test_report_processing(db, test_client, test_user):
    """Create a test report in processing status."""
    from apps.reports.models import Report
    report = Report.objects.create(
        client=test_client,
        created_by=test_user,
        report_type='executive',
        status='processing',
        title="Test Processing Report"
    )
    report.start_processing()
    return report


@pytest.fixture
def test_report_completed(db, test_client, test_user):
    """Create a completed test report with analysis data."""
    from apps.reports.models import Report
    report = Report.objects.create(
        client=test_client,
        created_by=test_user,
        report_type='cost',
        status='completed',
        title="Test Completed Report",
        analysis_data={
            'total_recommendations': 25,
            'category_distribution': {
                'cost': 10,
                'security': 8,
                'reliability': 5,
                'performance': 2
            },
            'business_impact_distribution': {
                'high': 8,
                'medium': 12,
                'low': 5
            },
            'total_potential_savings': 15000.00,
            'average_potential_savings': 600.00,
            'estimated_monthly_savings': 1250.00
        }
    )
    report.complete_processing()
    return report


@pytest.fixture
def test_report_failed(db, test_client, test_user):
    """Create a failed test report with error message."""
    from apps.reports.models import Report
    report = Report.objects.create(
        client=test_client,
        created_by=test_user,
        report_type='security',
        status='failed',
        error_message="CSV parsing error: Invalid format",
        retry_count=1
    )
    return report


@pytest.fixture
def test_recommendations(db, test_report):
    """Create 20 test recommendations for a report."""
    from apps.reports.models import Recommendation

    recommendations = []

    categories = ['cost', 'security', 'reliability', 'operational_excellence', 'performance']
    impacts = ['high', 'medium', 'low']

    for i in range(20):
        category = categories[i % len(categories)]
        impact = impacts[i % len(impacts)]

        rec = Recommendation(
            report=test_report,
            category=category,
            business_impact=impact,
            recommendation=f'Test recommendation {i+1}: Optimize {category} for better performance',
            subscription_id=f'sub-{1000+i}',
            subscription_name=f'Test Subscription {i%3 + 1}',
            resource_group=f'rg-test-{i%5 + 1}',
            resource_name=f'test-resource-{i+1}',
            resource_type='Microsoft.Compute/virtualMachines',
            potential_savings=Decimal(str(100.00 * (i + 1))),
            currency='USD',
            potential_benefits=f'Save costs and improve {category}',
            advisor_score_impact=Decimal(str(5.00 + (i % 10))),
            csv_row_number=i + 2
        )
        recommendations.append(rec)

    return Recommendation.objects.bulk_create(recommendations)


@pytest.fixture
def test_recommendations_cost_focused(db, test_report):
    """Create recommendations focused on cost optimization."""
    from apps.reports.models import Recommendation
    recommendations = []

    for i in range(10):
        rec = Recommendation(
            report=test_report,
            category='cost',
            business_impact='high' if i < 5 else 'medium',
            recommendation=f'Cost optimization {i+1}: Right-size underutilized resources',
            resource_name=f'vm-prod-{i+1}',
            resource_type='Microsoft.Compute/virtualMachines',
            potential_savings=Decimal(str(500.00 * (10 - i))),
            currency='USD',
            advisor_score_impact=Decimal('10.00'),
            csv_row_number=i + 2
        )
        recommendations.append(rec)

    return Recommendation.objects.bulk_create(recommendations)


@pytest.fixture
def test_recommendations_security_focused(db, test_report):
    """Create recommendations focused on security."""
    from apps.reports.models import Recommendation
    recommendations = []

    for i in range(8):
        rec = Recommendation(
            report=test_report,
            category='security',
            business_impact='high',
            recommendation=f'Security recommendation {i+1}: Enable security features',
            resource_name=f'app-service-{i+1}',
            resource_type='Microsoft.Web/sites',
            potential_savings=Decimal('0.00'),
            currency='USD',
            potential_benefits='Improve security posture and compliance',
            advisor_score_impact=Decimal('15.00'),
            csv_row_number=i + 2
        )
        recommendations.append(rec)

    return Recommendation.objects.bulk_create(recommendations)


@pytest.fixture
def sample_csv_valid():
    """Return valid CSV content for testing."""
    return """Category,Recommendation,Impact,Business Impact,Resource Name,Resource Type,Resource Group,Subscription ID,Subscription Name,Potential Annual Cost Savings,Currency,Potential Benefits,Advisor Score Impact
Cost,Right-size underutilized virtual machines,High,High,vm-prod-01,Microsoft.Compute/virtualMachines,rg-production,12345678-1234-1234-1234-123456789012,Production Subscription,"1,200.00",USD,Reduce costs by 40%,10.5
Security,Enable Azure Defender for App Service,High,High,app-service-web,Microsoft.Web/sites,rg-web-apps,12345678-1234-1234-1234-123456789012,Production Subscription,0.00,USD,Improve security posture,15.0
Reliability,Enable geo-redundant backup,Medium,Medium,storage-account-01,Microsoft.Storage/storageAccounts,rg-storage,12345678-1234-1234-1234-123456789012,Production Subscription,0.00,USD,Increase data durability,8.0
Performance,Upgrade to Premium storage,Medium,Low,sql-database-01,Microsoft.Sql/servers/databases,rg-databases,12345678-1234-1234-1234-123456789012,Production Subscription,0.00,USD,Improve query performance,5.0
Cost,Delete unattached managed disks,High,Medium,disk-unattached-01,Microsoft.Compute/disks,rg-disks,12345678-1234-1234-1234-123456789012,Production Subscription,150.00,USD,Eliminate unnecessary costs,8.0
"""


@pytest.fixture
def sample_csv_large(tmp_path):
    """Create a large CSV file with 1000 rows for performance testing."""
    file_path = tmp_path / "large_test.csv"

    with open(file_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("Category,Recommendation,Business Impact,Resource Name,Resource Type,Potential Annual Cost Savings,Currency\n")

        # Write 1000 rows
        categories = ['Cost', 'Security', 'Reliability', 'Operational Excellence', 'Performance']
        impacts = ['High', 'Medium', 'Low']

        for i in range(1000):
            category = categories[i % len(categories)]
            impact = impacts[i % len(impacts)]
            savings = (i + 1) * 10.00

            f.write(f"{category},Test recommendation {i+1},{impact},resource-{i+1},Microsoft.Compute/virtualMachines,{savings:.2f},USD\n")

    return str(file_path)


@pytest.fixture
def sample_csv_empty(tmp_path):
    """Create an empty CSV file."""
    file_path = tmp_path / "empty.csv"
    file_path.write_text("")
    return str(file_path)


@pytest.fixture
def sample_csv_missing_columns(tmp_path):
    """Create CSV with missing required columns."""
    file_path = tmp_path / "missing_columns.csv"
    content = """Impact,Resource Name
High,vm-01
Medium,vm-02
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_csv_malformed(tmp_path):
    """Create a malformed CSV file."""
    file_path = tmp_path / "malformed.csv"
    content = """Category,Recommendation,Impact
Cost,"This is a quote that doesn't close
Security,This row is fine,High
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_csv_utf8_bom(tmp_path):
    """Create CSV with UTF-8 BOM encoding."""
    file_path = tmp_path / "utf8_bom.csv"
    content = "\ufeffCategory,Recommendation,Impact\nCost,Test recommendation,High\n"
    file_path.write_text(content, encoding='utf-8-sig')
    return str(file_path)


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing."""
    class MockTask:
        def __init__(self):
            self.id = 'mock-task-id-12345'
            self.state = 'PENDING'
            self.result = None

        def get(self, timeout=None):
            return self.result

        def ready(self):
            return self.state in ['SUCCESS', 'FAILURE']

        def successful(self):
            return self.state == 'SUCCESS'

        def failed(self):
            return self.state == 'FAILURE'

    return MockTask()


@pytest.fixture
def api_client():
    """Return Django REST framework API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, test_user):
    """Return authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, test_admin_user):
    """Return admin authenticated API client."""
    api_client.force_authenticate(user=test_admin_user)
    return api_client


@pytest.fixture
def test_report_template(db, test_user):
    """Create a test report template."""
    from apps.reports.models import ReportTemplate
    return ReportTemplate.objects.create(
        name="Test Template - Detailed",
        report_type='detailed',
        html_template='<html><head><title>{{ title }}</title></head><body>{{ content }}</body></html>',
        css_template='body { font-family: Arial; }',
        is_default=True,
        is_active=True,
        created_by=test_user
    )


@pytest.fixture
def test_report_share(db, test_report_completed, test_user):
    """Create a test report share."""
    from apps.reports.models import ReportShare
    from datetime import datetime, timedelta
    return ReportShare.objects.create(
        report=test_report_completed,
        shared_by=test_user,
        shared_with_email='recipient@example.com',
        permission_level='view',
        is_active=True,
        expires_at=datetime.now() + timedelta(days=7)
    )


@pytest.fixture
def test_recommendation(db, test_report):
    """Create a single test recommendation."""
    from apps.reports.models import Recommendation
    from decimal import Decimal
    return Recommendation.objects.create(
        report=test_report,
        category='cost',
        business_impact='high',
        recommendation='Test recommendation: Reduce VM size',
        subscription_id='sub-123-456',
        subscription_name='Production Subscription',
        resource_group='rg-production',
        resource_name='vm-web-01',
        resource_type='Microsoft.Compute/virtualMachines',
        potential_savings=Decimal('1200.00'),
        currency='USD',
        potential_benefits='Save 50% on compute costs',
        advisor_score_impact=Decimal('10.00'),
        csv_row_number=2
    )


@pytest.fixture
def sample_csv_file_valid(tmp_path, sample_csv_valid):
    """Create a valid CSV file for testing."""
    file_path = tmp_path / "valid_test.csv"
    file_path.write_text(sample_csv_valid, encoding='utf-8')
    return str(file_path)
