"""
Root conftest.py for pytest configuration and shared fixtures.

This file provides common fixtures that can be used across all test modules.
"""

import pytest
import os
import sys
from decimal import Decimal
from datetime import datetime, date, timedelta


# ============================================================================
# Django Configuration (MUST BE FIRST - Before any Django imports)
# ============================================================================

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set Django settings module for pytest-django
# Use root settings.py (not settings package) for testing as it has proper test configuration
os.environ['DJANGO_SETTINGS_MODULE'] = 'azure_advisor_reports.settings'

# Import Django and setup immediately
# This runs during conftest import, before test collection
import django
from django.apps import apps
from django.conf import settings

# Check if Django is already configured
if not apps.ready:
    django.setup()


# ============================================================================
# Pytest Configuration
# ============================================================================
# Note: pytest-django will automatically configure Django using the
# DJANGO_SETTINGS_MODULE defined in pytest.ini


# ============================================================================
# Database and Django Settings
# ============================================================================

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Set up the test database with any required initial data.
    """
    with django_db_blocker.unblock():
        pass  # Add any session-level data here if needed


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def test_user(db):
    """Create a test user with analyst role."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email='testuser@example.com',
        username='testuser',
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
        email='admin@example.com',
        username='admin',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def test_manager_user(db):
    """Create a test manager user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email='manager@example.com',
        username='manager',
        password='managerpass123',
        first_name='Manager',
        last_name='User',
        role='manager',
        is_staff=True
    )


@pytest.fixture
def test_viewer_user(db):
    """Create a test viewer user (read-only)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email='viewer@example.com',
        username='viewer',
        password='viewerpass123',
        first_name='Viewer',
        last_name='User',
        role='viewer'
    )


# ============================================================================
# Client Fixtures
# ============================================================================

@pytest.fixture
def test_client_obj(db):
    """Create an active test client (renamed to avoid conflict with api_client)."""
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
        contact_phone="+1-555-0200",
        status='inactive'
    )


@pytest.fixture
def test_client_healthcare(db):
    """Create a healthcare industry client."""
    from apps.clients.models import Client
    return Client.objects.create(
        company_name="Healthcare Corp",
        industry="Healthcare",
        contact_email="contact@healthcarecorp.com",
        contact_phone="+1-555-0300",
        azure_subscription_ids=["sub-health-001"],
        status='active',
        notes="Healthcare industry test client"
    )


# ============================================================================
# Report Fixtures
# ============================================================================

@pytest.fixture
def test_report(db, test_client_obj, test_user):
    """Create a test report with pending status."""
    from apps.reports.models import Report
    return Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='detailed',
        status='pending',
        title="Test Detailed Report"
    )


@pytest.fixture
def test_report_executive(db, test_client_obj, test_user):
    """Create an executive summary report."""
    from apps.reports.models import Report
    return Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='executive',
        status='pending',
        title="Test Executive Summary"
    )


@pytest.fixture
def test_report_cost(db, test_client_obj, test_user):
    """Create a cost optimization report."""
    from apps.reports.models import Report
    return Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='cost',
        status='pending',
        title="Test Cost Optimization Report"
    )


@pytest.fixture
def test_report_with_csv(db, test_client_obj, test_user):
    """Create a test report with CSV file uploaded."""
    from apps.reports.models import Report
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.utils import timezone

    csv_content = b"""Category,Business Impact,Recommendation,Resource Name,Potential Annual Cost Savings,Currency
Cost,High,Reduce VM size,vm-test-01,1200.00,USD
Security,High,Enable MFA,security-policy,0.00,USD
"""
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

    return Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='detailed',
        status='uploaded',
        csv_file=csv_file,
        csv_uploaded_at=timezone.now(),
        title="Test Report with CSV"
    )


@pytest.fixture
def test_report_processing(db, test_client_obj, test_user):
    """Create a test report in processing status."""
    from apps.reports.models import Report
    report = Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='executive',
        status='processing',
        title="Test Processing Report"
    )
    report.start_processing()
    return report


@pytest.fixture
def test_report_completed(db, test_client_obj, test_user):
    """Create a completed test report with analysis data."""
    from apps.reports.models import Report
    report = Report.objects.create(
        client=test_client_obj,
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
    report.start_processing()
    report.complete_processing()
    return report


@pytest.fixture
def test_report_failed(db, test_client_obj, test_user):
    """Create a failed test report with error message."""
    from apps.reports.models import Report
    report = Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='security',
        status='failed',
        error_message="CSV parsing error: Invalid format",
        retry_count=1
    )
    return report


# ============================================================================
# Recommendation Fixtures
# ============================================================================

@pytest.fixture
def test_recommendation(db, test_report):
    """Create a single test recommendation."""
    from apps.reports.models import Recommendation
    return Recommendation.objects.create(
        report=test_report,
        category='cost',
        business_impact='high',
        recommendation='Reduce VM size from Standard_D4 to Standard_D2',
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
def test_recommendations_bulk(db, test_report):
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


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """Return Django REST framework API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, test_user):
    """Return authenticated API client with analyst user."""
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, test_admin_user):
    """Return authenticated API client with admin user."""
    api_client.force_authenticate(user=test_admin_user)
    return api_client


@pytest.fixture
def manager_api_client(api_client, test_manager_user):
    """Return authenticated API client with manager user."""
    api_client.force_authenticate(user=test_manager_user)
    return api_client


@pytest.fixture
def viewer_api_client(api_client, test_viewer_user):
    """Return authenticated API client with viewer user."""
    api_client.force_authenticate(user=test_viewer_user)
    return api_client


# ============================================================================
# CSV File Fixtures
# ============================================================================

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
def sample_csv_file_valid(tmp_path, sample_csv_valid):
    """Create a valid CSV file for testing."""
    file_path = tmp_path / "valid_test.csv"
    file_path.write_text(sample_csv_valid, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def sample_csv_empty(tmp_path):
    """Create an empty CSV file."""
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding='utf-8')
    return str(file_path)


@pytest.fixture
def sample_csv_missing_columns(tmp_path):
    """Create CSV with missing required columns."""
    file_path = tmp_path / "missing_columns.csv"
    content = """Impact,Resource Name
High,vm-01
Medium,vm-02
"""
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def sample_csv_utf8_bom(tmp_path):
    """Create CSV with UTF-8 BOM encoding."""
    file_path = tmp_path / "utf8_bom.csv"
    content = "Category,Recommendation,Business Impact,Resource Name,Potential Annual Cost Savings,Currency\n"
    content += "Cost,Test recommendation,High,vm-test,1000.00,USD\n"

    # Write with BOM
    with open(file_path, 'w', encoding='utf-8-sig') as f:
        f.write(content)

    return str(file_path)


# ============================================================================
# Time-related Fixtures
# ============================================================================

@pytest.fixture
def freeze_time(monkeypatch):
    """
    Fixture to freeze time at a specific datetime.
    Usage: freeze_time(datetime(2025, 1, 15, 12, 0, 0))
    """
    from django.utils import timezone

    def _freeze(frozen_datetime):
        class FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return frozen_datetime

        monkeypatch.setattr(timezone, 'now', lambda: frozen_datetime)
        return frozen_datetime

    return _freeze


# ============================================================================
# Mock Fixtures
# ============================================================================

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


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_sequences(db):
    """Reset database sequences after each test."""
    yield
    # Sequences are automatically reset by Django's test runner


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Django cache before each test."""
    from django.core.cache import cache
    try:
        cache.clear()
    except Exception:
        # Ignore cache errors in tests (Redis might not be available)
        pass
    yield
    try:
        cache.clear()
    except Exception:
        pass
