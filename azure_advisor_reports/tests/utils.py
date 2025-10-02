"""
Test utilities for Azure Advisor Reports Platform
Provides helper functions and utilities for testing
"""

import json
import os
import tempfile
import uuid
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with common utilities for all tests."""

    def setUp(self):
        """Set up common test data."""
        super().setUp()
        self.maxDiff = None  # Show full diff in assertions

    def assertFieldError(self, form, field, error_code):
        """Assert that a form field has a specific error."""
        self.assertIn(field, form.errors)
        error_codes = [error.code for error in form.errors[field]]
        self.assertIn(error_code, error_codes)

    def assertValidationError(self, obj, field, error_message):
        """Assert that model validation raises specific error."""
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)
        self.assertIn(error_message, str(cm.exception.error_dict[field]))

    def assertQuerysetEqual(self, qs1, qs2, transform=repr, ordered=True):
        """Enhanced queryset comparison."""
        return super().assertQuerysetEqual(qs1, qs2, transform, ordered)

    def assertDictContainsSubset(self, subset, dictionary, msg=None):
        """Assert that dictionary contains all key-value pairs in subset."""
        for key, value in subset.items():
            if key not in dictionary:
                self.fail(f"Key '{key}' not found in dictionary")
            if dictionary[key] != value:
                self.fail(f"Key '{key}': expected {value}, got {dictionary[key]}")

    def assertDateTimeAlmostEqual(self, dt1, dt2, delta_seconds=1):
        """Assert that two datetimes are almost equal within delta seconds."""
        delta = abs((dt1 - dt2).total_seconds())
        self.assertLessEqual(delta, delta_seconds)


class BaseAPITestCase(APITestCase, BaseTestCase):
    """Base API test case with authentication utilities."""

    def setUp(self):
        """Set up API test case."""
        super().setUp()
        self.user = None
        self.refresh_token = None
        self.access_token = None

    def authenticate_user(self, user=None):
        """Authenticate a user for API testing."""
        if user is None:
            from tests.factories import UserFactory
            user = UserFactory()

        self.user = user
        self.refresh_token = RefreshToken.for_user(user)
        self.access_token = self.refresh_token.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        return user

    def assert_response_status(self, response, expected_status, msg=None):
        """Assert response status with helpful error message."""
        if response.status_code != expected_status:
            error_msg = (
                f"Expected status {expected_status}, got {response.status_code}. "
                f"Response data: {getattr(response, 'data', response.content)}"
            )
            if msg:
                error_msg = f"{msg}: {error_msg}"
            self.fail(error_msg)

    def assert_json_response(self, response, expected_data=None, status_code=200):
        """Assert JSON response format and optionally check data."""
        self.assert_response_status(response, status_code)
        self.assertEqual(response.content_type, 'application/json')

        if expected_data is not None:
            self.assertEqual(response.json(), expected_data)

    def assert_error_response(self, response, status_code, error_field=None, error_message=None):
        """Assert error response format."""
        self.assert_response_status(response, status_code)
        data = response.json()

        if error_field:
            self.assertIn(error_field, data)

        if error_message:
            if error_field:
                self.assertIn(error_message, str(data[error_field]))
            else:
                self.assertIn(error_message, str(data))

    def assert_pagination_response(self, response, expected_count=None):
        """Assert paginated response format."""
        self.assert_response_status(response, 200)
        data = response.json()

        # Check pagination structure
        required_fields = ['count', 'next', 'previous', 'results']
        for field in required_fields:
            self.assertIn(field, data, f"Missing pagination field: {field}")

        if expected_count is not None:
            self.assertEqual(data['count'], expected_count)

        return data['results']


class BaseTransactionTestCase(TransactionTestCase, BaseTestCase):
    """Base transaction test case for tests that need transaction control."""

    def setUp(self):
        """Set up transaction test case."""
        super().setUp()
        self.reset_sequences = True


class CSVTestUtils:
    """Utilities for CSV testing."""

    @staticmethod
    def create_azure_advisor_csv(num_rows=20, **kwargs) -> pd.DataFrame:
        """Create a realistic Azure Advisor CSV DataFrame."""
        data = {
            "Category": ["Cost", "Security", "Reliability", "OperationalExcellence"] * (num_rows // 4 + 1),
            "Business Impact": ["High", "Medium", "Low"] * (num_rows // 3 + 1),
            "Recommendation": [f"Recommendation {i+1}" for i in range(num_rows)],
            "Subscription ID": [str(uuid.uuid4()) for _ in range(num_rows)],
            "Subscription Name": [f"Subscription {i+1}" for i in range(num_rows)],
            "Resource Group": [f"rg-test-{i+1}" for i in range(num_rows)],
            "Resource Name": [f"resource-{i+1}" for i in range(num_rows)],
            "Resource Type": [
                "Microsoft.Compute/virtualMachines",
                "Microsoft.Storage/storageAccounts",
                "Microsoft.Sql/servers/databases",
                "Microsoft.Web/sites"
            ] * (num_rows // 4 + 1),
            "Potential Annual Cost Savings (USD)": [
                round(100 + i * 50.5, 2) for i in range(num_rows)
            ],
            "Currency": ["USD"] * num_rows,
            "Potential Benefits": [f"Benefits description {i+1}" for i in range(num_rows)],
            "Retirement Date": [None] * num_rows,
            "Retiring Feature": [None] * num_rows,
        }

        # Update with any provided kwargs
        data.update(kwargs)

        # Ensure all lists are the same length
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = value[:num_rows]

        return pd.DataFrame(data)

    @staticmethod
    def create_csv_file(data: pd.DataFrame, filename: str = "test.csv") -> SimpleUploadedFile:
        """Create a SimpleUploadedFile from DataFrame."""
        csv_content = data.to_csv(index=False)
        return SimpleUploadedFile(
            filename,
            csv_content.encode("utf-8"),
            content_type="text/csv"
        )

    @staticmethod
    def create_invalid_csv_file(filename: str = "invalid.csv") -> SimpleUploadedFile:
        """Create an invalid CSV file for testing error handling."""
        content = "Invalid,CSV,Headers\nMissing,Required,Columns"
        return SimpleUploadedFile(
            filename,
            content.encode("utf-8"),
            content_type="text/csv"
        )

    @staticmethod
    def create_empty_csv_file(filename: str = "empty.csv") -> SimpleUploadedFile:
        """Create an empty CSV file."""
        return SimpleUploadedFile(
            filename,
            b"",
            content_type="text/csv"
        )

    @staticmethod
    def create_large_csv_file(num_rows: int = 1000, filename: str = "large.csv") -> SimpleUploadedFile:
        """Create a large CSV file for performance testing."""
        data = CSVTestUtils.create_azure_advisor_csv(num_rows)
        return CSVTestUtils.create_csv_file(data, filename)


class MockUtils:
    """Utilities for mocking external services."""

    @staticmethod
    def mock_azure_auth_success():
        """Mock successful Azure AD authentication."""
        return patch("apps.authentication.services.AzureADService.validate_token", return_value={
            "sub": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["User"]
        })

    @staticmethod
    def mock_azure_auth_failure():
        """Mock failed Azure AD authentication."""
        from django.contrib.auth.exceptions import AuthenticationFailed
        return patch(
            "apps.authentication.services.AzureADService.validate_token",
            side_effect=AuthenticationFailed("Invalid token")
        )

    @staticmethod
    def mock_blob_storage():
        """Mock Azure Blob Storage operations."""
        mock_blob = Mock()
        mock_blob.upload_blob.return_value = Mock(url="https://test.blob.core.windows.net/test.csv")
        mock_blob.download_blob.return_value = Mock(readall=lambda: b"test,csv,content")

        return patch("azure.storage.blob.BlobServiceClient", return_value=mock_blob)

    @staticmethod
    def mock_celery_task_success(task_id="test-task-id", result=None):
        """Mock successful Celery task execution."""
        mock_result = Mock()
        mock_result.id = task_id
        mock_result.state = "SUCCESS"
        mock_result.result = result or {"status": "completed"}

        return patch("celery.Task.apply_async", return_value=mock_result)

    @staticmethod
    def mock_celery_task_failure(task_id="test-task-id", error="Task failed"):
        """Mock failed Celery task execution."""
        mock_result = Mock()
        mock_result.id = task_id
        mock_result.state = "FAILURE"
        mock_result.result = Exception(error)

        return patch("celery.Task.apply_async", return_value=mock_result)

    @staticmethod
    def mock_pdf_generation(pdf_path="/tmp/test_report.pdf"):
        """Mock PDF generation."""
        return patch("apps.reports.services.pdf_generator.generate_pdf", return_value=pdf_path)


class AssertionUtils:
    """Custom assertion utilities."""

    @staticmethod
    def assert_csv_data_equal(actual_df: pd.DataFrame, expected_df: pd.DataFrame):
        """Assert that two DataFrames are equal."""
        try:
            pd.testing.assert_frame_equal(actual_df, expected_df)
        except AssertionError as e:
            raise AssertionError(f"DataFrames are not equal: {str(e)}")

    @staticmethod
    def assert_analysis_data_structure(analysis_data: Dict[str, Any]):
        """Assert that analysis data has the expected structure."""
        required_fields = [
            "total_recommendations",
            "category_distribution",
            "business_impact_distribution",
            "estimated_monthly_savings",
            "advisor_score"
        ]

        for field in required_fields:
            if field not in analysis_data:
                raise AssertionError(f"Missing required field in analysis_data: {field}")

        # Validate specific field types
        if not isinstance(analysis_data["total_recommendations"], int):
            raise AssertionError("total_recommendations must be an integer")

        if not isinstance(analysis_data["category_distribution"], dict):
            raise AssertionError("category_distribution must be a dictionary")

        if not isinstance(analysis_data["business_impact_distribution"], dict):
            raise AssertionError("business_impact_distribution must be a dictionary")

    @staticmethod
    def assert_report_files_exist(report, check_html=True, check_pdf=True):
        """Assert that report files exist and are accessible."""
        if check_html and report.html_file:
            if not report.html_file.name:
                raise AssertionError("HTML file name is empty")

        if check_pdf and report.pdf_file:
            if not report.pdf_file.name:
                raise AssertionError("PDF file name is empty")

    @staticmethod
    def assert_security_headers(response, expected_headers: Dict[str, str]):
        """Assert that security headers are present in response."""
        for header, expected_value in expected_headers.items():
            if header not in response:
                raise AssertionError(f"Security header '{header}' is missing")

            actual_value = response.get(header)
            if actual_value != expected_value:
                raise AssertionError(
                    f"Security header '{header}': expected '{expected_value}', "
                    f"got '{actual_value}'"
                )


class PerformanceTestUtils:
    """Utilities for performance testing."""

    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of a function."""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def assert_execution_time(func, max_seconds, *args, **kwargs):
        """Assert that function executes within specified time."""
        result, execution_time = PerformanceTestUtils.measure_execution_time(func, *args, **kwargs)
        if execution_time > max_seconds:
            raise AssertionError(
                f"Function took {execution_time:.2f} seconds, "
                f"but should complete within {max_seconds} seconds"
            )
        return result

    @staticmethod
    def create_memory_tracker():
        """Create a memory usage tracker."""
        import tracemalloc
        tracemalloc.start()
        return tracemalloc

    @staticmethod
    def assert_memory_usage(tracker, max_mb):
        """Assert that memory usage is within limits."""
        current, peak = tracker.get_traced_memory()
        peak_mb = peak / 1024 / 1024

        if peak_mb > max_mb:
            raise AssertionError(
                f"Peak memory usage was {peak_mb:.2f} MB, "
                f"but should not exceed {max_mb} MB"
            )


class SecurityTestUtils:
    """Utilities for security testing."""

    @staticmethod
    def get_sql_injection_payloads():
        """Get common SQL injection payloads."""
        return [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET password='hacked'; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin'/*",
            "' OR 1=1--",
            "' OR 1=1#",
            "' OR 1=1/*",
            ") OR '1'='1--",
            ") OR ('1'='1--",
        ]

    @staticmethod
    def get_xss_payloads():
        """Get common XSS payloads."""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<object data=\"javascript:alert('XSS')\">",
            "<embed src=\"javascript:alert('XSS')\">",
            "<link href=\"javascript:alert('XSS')\">",
            "<form><button formaction=javascript:alert('XSS')>",
            "<input autofocus onfocus=alert('XSS')>",
        ]

    @staticmethod
    def test_endpoint_for_sql_injection(test_case, endpoint_func, *args, **kwargs):
        """Test an endpoint for SQL injection vulnerabilities."""
        payloads = SecurityTestUtils.get_sql_injection_payloads()

        for payload in payloads:
            try:
                # Test with payload in different positions
                test_kwargs = kwargs.copy()
                for key, value in test_kwargs.items():
                    if isinstance(value, str):
                        test_kwargs[key] = payload

                response = endpoint_func(*args, **test_kwargs)

                # Response should not contain database errors
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8').lower()
                    dangerous_patterns = [
                        'sql syntax',
                        'mysql error',
                        'postgresql error',
                        'ora-',
                        'syntax error',
                        'unclosed quotation',
                    ]

                    for pattern in dangerous_patterns:
                        if pattern in content:
                            test_case.fail(
                                f"Potential SQL injection vulnerability detected with payload: {payload}"
                            )

            except Exception as e:
                # Exceptions are expected, but they shouldn't reveal database structure
                error_msg = str(e).lower()
                if any(pattern in error_msg for pattern in ['table', 'column', 'database']):
                    test_case.fail(
                        f"SQL injection payload revealed database structure: {payload}"
                    )

    @staticmethod
    def test_endpoint_for_xss(test_case, endpoint_func, *args, **kwargs):
        """Test an endpoint for XSS vulnerabilities."""
        payloads = SecurityTestUtils.get_xss_payloads()

        for payload in payloads:
            test_kwargs = kwargs.copy()
            for key, value in test_kwargs.items():
                if isinstance(value, str):
                    test_kwargs[key] = payload

            response = endpoint_func(*args, **test_kwargs)

            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')

                # Check if payload is reflected unescaped
                if payload in content:
                    test_case.fail(
                        f"Potential XSS vulnerability detected. "
                        f"Payload '{payload}' was reflected unescaped"
                    )


class IntegrationTestUtils:
    """Utilities for integration testing."""

    @staticmethod
    def create_test_environment():
        """Create a complete test environment."""
        from tests.factories import create_comprehensive_test_data
        return create_comprehensive_test_data()

    @staticmethod
    def simulate_full_report_workflow(client, csv_data, report_type="detailed"):
        """Simulate the complete report generation workflow."""
        # Upload CSV
        csv_file = CSVTestUtils.create_csv_file(csv_data)
        upload_response = client.post('/api/v1/reports/upload/', {
            'csv_file': csv_file,
            'client_id': str(uuid.uuid4())
        })

        if upload_response.status_code != 201:
            raise AssertionError(f"CSV upload failed: {upload_response.data}")

        report_id = upload_response.data['id']

        # Generate report
        generate_response = client.post(f'/api/v1/reports/{report_id}/generate/', {
            'report_type': report_type
        })

        if generate_response.status_code != 202:
            raise AssertionError(f"Report generation failed: {generate_response.data}")

        return report_id

    @staticmethod
    def wait_for_celery_task(task_id, timeout=30):
        """Wait for a Celery task to complete."""
        import time
        from celery.result import AsyncResult

        result = AsyncResult(task_id)
        start_time = time.time()

        while not result.ready():
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
            time.sleep(0.5)

        return result.result