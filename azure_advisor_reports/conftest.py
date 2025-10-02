"""
Global pytest configuration and fixtures for Azure Advisor Reports Platform
Provides shared test utilities, fixtures, and configuration across all test modules
"""

import os
import tempfile
import pytest
import uuid
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch
from io import StringIO

# Configure Django settings before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "azure_advisor_reports.settings.testing")

import django
try:
    from django.apps import apps
    if not apps.ready:
        django.setup()
except:
    django.setup()

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient

# Test data imports will be done lazily to avoid circular imports
User = get_user_model()

# Lazy load factories to avoid import errors
def get_factories():
    """Lazy load factories to avoid issues during conftest loading."""
    try:
        from tests.factories import (
            UserFactory,
            ClientFactory,
            ReportFactory,
            RecommendationFactory,
        )
        return UserFactory, ClientFactory, ReportFactory, RecommendationFactory
    except ImportError:
        return None, None, None, None

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    pass


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on file location and naming patterns."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark API tests
        if "test_api" in item.name or "test_views" in item.name:
            item.add_marker(pytest.mark.api)

        # Mark slow tests
        if "test_large" in item.name or "test_performance" in item.name:
            item.add_marker(pytest.mark.slow)

        # Mark Celery tests
        if "test_task" in item.name or "celery" in str(item.fspath):
            item.add_marker(pytest.mark.celery)

        # Mark CSV processing tests
        if "csv" in item.name.lower() or "csv" in str(item.fspath):
            item.add_marker(pytest.mark.csv)

        # Mark report generation tests
        if "report" in item.name.lower() and "test_report" in item.name:
            item.add_marker(pytest.mark.report)


# ============================================================================
# DATABASE AND DJANGO FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def django_db_setup():
    """Setup test database configuration."""
    pass


@pytest.fixture
def transactional_db(db):
    """Provide transactional database access for tests that need it."""
    return db


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role='analyst'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='testpass123',
        first_name='Manager',
        last_name='User',
        role='manager'
    )


@pytest.fixture
def analyst_user(db):
    """Create an analyst user."""
    return User.objects.create_user(
        username='analyst',
        email='analyst@example.com',
        password='testpass123',
        first_name='Analyst',
        last_name='User',
        role='analyst'
    )


@pytest.fixture
def viewer_user(db):
    """Create a viewer user."""
    return User.objects.create_user(
        username='viewer',
        email='viewer@example.com',
        password='testpass123',
        first_name='Viewer',
        last_name='User',
        role='viewer'
    )


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()


@pytest.fixture
def authenticated_client(user):
    """Create an authenticated API client."""
    client = APIClient()
    # Use JWT authentication instead of RefreshToken
    import jwt
    from datetime import datetime, timedelta
    from django.conf import settings

    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def admin_client(admin_user):
    """Create an admin authenticated API client."""
    client = APIClient()
    # Use JWT authentication instead of RefreshToken
    import jwt
    from datetime import datetime, timedelta
    from django.conf import settings

    payload = {
        'user_id': str(admin_user.id),
        'email': admin_user.email,
        'role': admin_user.role,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
def client_model():
    """Create a test client."""
    return ClientFactory()


@pytest.fixture
def multiple_clients():
    """Create multiple test clients."""
    return ClientFactory.create_batch(5)


@pytest.fixture
def report(client_model, user):
    """Create a test report."""
    return ReportFactory(client=client_model, created_by=user)


@pytest.fixture
def completed_report(client_model, user):
    """Create a completed test report with recommendations."""
    report = ReportFactory(
        client=client_model,
        created_by=user,
        status="completed",
        analysis_data={
            "total_recommendations": 25,
            "category_distribution": {
                "Cost": 10,
                "Security": 8,
                "Reliability": 4,
                "OperationalExcellence": 3
            },
            "estimated_monthly_savings": "1250.00",
            "advisor_score": 85
        }
    )
    # Create recommendations for the report
    RecommendationFactory.create_batch(25, report=report)
    return report


@pytest.fixture
def recommendations(report):
    """Create test recommendations."""
    return RecommendationFactory.create_batch(10, report=report)


# ============================================================================
# FILE FIXTURES
# ============================================================================

@pytest.fixture
def temp_media_root():
    """Create temporary media root for file testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with override_settings(MEDIA_ROOT=temp_dir):
            yield temp_dir


@pytest.fixture
def sample_csv_data():
    """Generate sample Azure Advisor CSV data."""
    import random
    return pd.DataFrame({
        "Category": ["Cost", "Security", "Reliability", "OperationalExcellence"] * 5,
        "Business Impact": ["High", "Medium", "Low"] * 7,  # 21 items, need only 20
        "Recommendation": [f"Recommendation {i}" for i in range(20)],
        "Subscription ID": [str(uuid.uuid4()) for _ in range(20)],
        "Subscription Name": [f"Subscription {i}" for i in range(20)],
        "Resource Group": [f"rg-test-{i}" for i in range(20)],
        "Resource Name": [f"resource-{i}" for i in range(20)],
        "Resource Type": ["Virtual Machine", "Storage Account", "SQL Database", "App Service"] * 5,
        "Potential Annual Cost Savings (USD)": [round(random.uniform(100, 5000), 2) for _ in range(20)],
        "Currency": ["USD"] * 20,
        "Potential Benefits": [f"Benefits description {i}" for i in range(20)],
        "Retirement Date": [None] * 20,
        "Retiring Feature": [None] * 20,
    })[:20]  # Take only first 20 rows


@pytest.fixture
def sample_csv_file(sample_csv_data):
    """Create a sample CSV file for testing."""
    csv_content = sample_csv_data.to_csv(index=False)
    return SimpleUploadedFile(
        "test_advisor_data.csv",
        csv_content.encode("utf-8"),
        content_type="text/csv"
    )


@pytest.fixture
def large_csv_file():
    """Create a large CSV file for performance testing."""
    import random
    # Generate 1000 recommendations for performance testing
    data = pd.DataFrame({
        "Category": ["Cost", "Security", "Reliability", "OperationalExcellence"] * 250,
        "Business Impact": ["High", "Medium", "Low"] * 334,  # Cycle through values
        "Recommendation": [f"Large dataset recommendation {i}" for i in range(1000)],
        "Subscription ID": [str(uuid.uuid4()) for _ in range(1000)],
        "Subscription Name": [f"Subscription {i}" for i in range(1000)],
        "Resource Group": [f"rg-large-{i}" for i in range(1000)],
        "Resource Name": [f"resource-large-{i}" for i in range(1000)],
        "Resource Type": ["Virtual Machine", "Storage Account", "SQL Database", "App Service"] * 250,
        "Potential Annual Cost Savings (USD)": [round(random.uniform(100, 5000), 2) for _ in range(1000)],
        "Currency": ["USD"] * 1000,
        "Potential Benefits": [f"Benefits for large dataset {i}" for i in range(1000)],
        "Retirement Date": [None] * 1000,
        "Retiring Feature": [None] * 1000,
    })[:1000]

    csv_content = data.to_csv(index=False)
    return SimpleUploadedFile(
        "large_advisor_data.csv",
        csv_content.encode("utf-8"),
        content_type="text/csv"
    )


@pytest.fixture
def invalid_csv_file():
    """Create an invalid CSV file for testing error handling."""
    invalid_content = "Invalid,CSV,Header\nMissing,Required,Columns"
    return SimpleUploadedFile(
        "invalid.csv",
        invalid_content.encode("utf-8"),
        content_type="text/csv"
    )


@pytest.fixture
def empty_csv_file():
    """Create an empty CSV file for testing."""
    return SimpleUploadedFile(
        "empty.csv",
        b"",
        content_type="text/csv"
    )


@pytest.fixture
def malformed_csv_file():
    """Create a malformed CSV file for testing."""
    malformed_content = 'Category,Business Impact\n"Unclosed quote,High\nNo closing quote'
    return SimpleUploadedFile(
        "malformed.csv",
        malformed_content.encode("utf-8"),
        content_type="text/csv"
    )


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_azure_auth():
    """Mock Azure AD authentication."""
    with patch("apps.authentication.services.AzureADService") as mock:
        mock_instance = Mock()
        mock_instance.validate_token.return_value = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["User"]
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def azure_token_mock():
    """Mock Azure AD access token."""
    return "mock_azure_ad_access_token_" + "x" * 100


@pytest.fixture
def azure_user_info():
    """Mock Azure AD user information."""
    return {
        'id': 'azure-object-id-12345',
        'mail': 'testuser@example.com',
        'userPrincipalName': 'testuser@example.com',
        'givenName': 'Test',
        'surname': 'User',
        'jobTitle': 'Software Engineer',
        'department': 'Engineering',
        'mobilePhone': '+1234567890',
        'displayName': 'Test User'
    }


@pytest.fixture
def mock_azure_ad_service(azure_user_info):
    """Mock AzureADService for testing without actual Azure AD calls."""
    with patch('apps.authentication.services.AzureADService') as mock_service:
        instance = mock_service.return_value
        instance.validate_token.return_value = (True, azure_user_info)
        instance.create_or_update_user.return_value = None  # Will be set in tests
        yield instance


@pytest.fixture
def mock_graph_api_success(azure_user_info):
    """Mock successful Microsoft Graph API response."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = azure_user_info
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_graph_api_failure():
    """Mock failed Microsoft Graph API response."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'Unauthorized'}
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def jwt_access_token(user):
    """Generate a valid JWT access token for testing."""
    import jwt
    from datetime import datetime, timedelta
    from django.conf import settings

    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


@pytest.fixture
def jwt_refresh_token(user):
    """Generate a valid JWT refresh token for testing."""
    import jwt
    from datetime import datetime, timedelta
    from django.conf import settings

    payload = {
        'user_id': str(user.id),
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


@pytest.fixture
def expired_jwt_token(user):
    """Generate an expired JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta
    from django.conf import settings

    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        'iat': datetime.utcnow() - timedelta(hours=2),
        'type': 'access'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


@pytest.fixture
def invalid_jwt_token():
    """Generate an invalid JWT token (wrong secret)."""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        'user_id': 'some-user-id',
        'email': 'test@example.com',
        'role': 'analyst',
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, 'wrong-secret-key', algorithm='HS256')


@pytest.fixture
def mock_blob_storage():
    """Mock Azure Blob Storage operations."""
    with patch("azure.storage.blob.BlobServiceClient") as mock:
        mock_instance = Mock()
        mock_instance.upload_blob.return_value = Mock(url="https://test.blob.core.windows.net/test.csv")
        mock_instance.download_blob.return_value = Mock(readall=lambda: b"test,csv,content")
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution."""
    with patch("celery.Task.apply_async") as mock:
        mock_result = Mock()
        mock_result.id = "test-task-id"
        mock_result.state = "SUCCESS"
        mock_result.result = {"status": "completed"}
        mock.return_value = mock_result
        yield mock


@pytest.fixture
def mock_pdf_generation():
    """Mock PDF generation."""
    with patch("apps.reports.services.pdf_generator.generate_pdf") as mock:
        mock.return_value = "/tmp/test_report.pdf"
        yield mock


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================

@pytest.fixture
def performance_mode():
    """Enable performance testing mode."""
    with override_settings(PERFORMANCE_TEST_MODE=True):
        yield


@pytest.fixture
def benchmark_settings():
    """Configure benchmarking for performance tests."""
    return {
        "min_rounds": 5,
        "max_time": 10.0,
        "warmup": False,
    }


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def live_server_url():
    """Provide live server URL for integration tests."""
    return "http://testserver"


@pytest.fixture
def integration_test_data():
    """Create comprehensive test data for integration tests."""
    # Create users
    admin = UserFactory(role="admin")
    manager = UserFactory(role="manager")
    analyst = UserFactory(role="analyst")

    # Create clients
    clients = ClientFactory.create_batch(3)

    # Create reports with different statuses
    pending_report = ReportFactory(client=clients[0], created_by=analyst, status="pending")
    processing_report = ReportFactory(client=clients[1], created_by=analyst, status="processing")
    completed_report = ReportFactory(client=clients[2], created_by=analyst, status="completed")

    # Create recommendations for completed report
    RecommendationFactory.create_batch(15, report=completed_report)

    return {
        "users": {"admin": admin, "manager": manager, "analyst": analyst},
        "clients": clients,
        "reports": {
            "pending": pending_report,
            "processing": processing_report,
            "completed": completed_report
        }
    }


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically cleanup temporary files after each test."""
    yield
    # Cleanup any temporary files created during tests
    import glob
    for pattern in ["/tmp/test_*.pdf", "/tmp/test_*.html", "/tmp/test_*.csv"]:
        for file_path in glob.glob(pattern):
            try:
                os.unlink(file_path)
            except OSError:
                pass


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def assert_num_queries():
    """Utility to assert the number of database queries."""
    from django.test import override_settings
    from django.db import connection
    from django.test.utils import override_settings

    def _assert_num_queries(num, func, *args, **kwargs):
        with override_settings(DEBUG=True):
            with connection.cursor() as cursor:
                initial_queries = len(connection.queries)
                result = func(*args, **kwargs)
                final_queries = len(connection.queries)
                executed_queries = final_queries - initial_queries

                if executed_queries != num:
                    msg = f"Expected {num} queries, but {executed_queries} were executed"
                    raise AssertionError(msg)

                return result

    return _assert_num_queries


@pytest.fixture
def capture_emails():
    """Capture emails sent during tests."""
    from django.core import mail
    mail.outbox = []
    return mail.outbox


# ============================================================================
# SECURITY TEST FIXTURES
# ============================================================================

@pytest.fixture
def security_headers():
    """Expected security headers for testing."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }


@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection payloads for security testing."""
    return [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; UPDATE users SET password='hacked'; --",
        "' UNION SELECT * FROM users --",
        "'; DELETE FROM clients; --",
    ]


@pytest.fixture
def xss_payloads():
    """Common XSS payloads for security testing."""
    return [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "';alert('XSS');//",
        "<svg onload=alert('XSS')>",
    ]