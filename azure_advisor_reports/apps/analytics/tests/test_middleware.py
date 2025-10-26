"""
Tests for UserActivityTrackingMiddleware
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from unittest.mock import Mock, patch

from apps.analytics.middleware import UserActivityTrackingMiddleware
from apps.analytics.models import UserActivity
from apps.clients.models import Client
from apps.reports.models import Report

User = get_user_model()


class UserActivityTrackingMiddlewareTestCase(TestCase):
    """Test cases for activity tracking middleware."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create test user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            role='analyst'
        )

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='test@company.com',
            status='active'
        )

        # Create mock get_response callable
        self.get_response = Mock(return_value=HttpResponse(status=200))

        # Initialize middleware
        self.middleware = UserActivityTrackingMiddleware(self.get_response)

    def test_middleware_initialization(self):
        """Test middleware initializes correctly."""
        self.assertIsNotNone(self.middleware)
        self.assertEqual(self.middleware.get_response, self.get_response)

    def test_should_track_authenticated_post(self):
        """Test that authenticated POST requests are tracked."""
        request = self.factory.post('/api/v1/reports/')
        request.user = self.user
        response = HttpResponse(status=201)

        should_track = self.middleware._should_track(request, response)
        self.assertTrue(should_track)

    def test_should_not_track_unauthenticated(self):
        """Test that unauthenticated requests are not tracked."""
        request = self.factory.post('/api/v1/reports/')
        request.user = Mock(is_authenticated=False)
        response = HttpResponse(status=201)

        should_track = self.middleware._should_track(request, response)
        self.assertFalse(should_track)

    def test_should_not_track_failed_requests(self):
        """Test that failed requests (4xx, 5xx) are not tracked."""
        request = self.factory.post('/api/v1/reports/')
        request.user = self.user
        response = HttpResponse(status=400)

        should_track = self.middleware._should_track(request, response)
        self.assertFalse(should_track)

    def test_should_not_track_get_requests(self):
        """Test that regular GET requests are not tracked."""
        request = self.factory.get('/api/v1/reports/')
        request.user = self.user
        response = HttpResponse(status=200)

        should_track = self.middleware._should_track(request, response)
        self.assertFalse(should_track)

    def test_should_track_download_requests(self):
        """Test that download GET requests are tracked."""
        request = self.factory.get('/api/v1/reports/123/download/')
        request.user = self.user
        response = HttpResponse(status=200)

        should_track = self.middleware._should_track(request, response)
        self.assertTrue(should_track)

    def test_track_report_generation(self):
        """Test tracking report generation."""
        request = self.factory.post('/api/v1/reports/')
        request.user = self.user
        request.data = {
            'client_id': str(self.test_client.id),
            'report_type': 'executive'
        }
        request.META = {
            'REMOTE_ADDR': '192.168.1.1',
            'HTTP_USER_AGENT': 'Test Browser'
        }

        # Call middleware
        response = self.middleware(request)

        # Verify activity was created
        activities = UserActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

        activity = activities.first()
        self.assertEqual(activity.action, 'generate_report')
        self.assertIn('Generated a new report', activity.description)
        self.assertEqual(activity.ip_address, '192.168.1.1')

    def test_track_client_creation(self):
        """Test tracking client creation."""
        request = self.factory.post('/api/v1/clients/')
        request.user = self.user
        request.data = {
            'company_name': 'New Company'
        }
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'Test Browser'
        }

        response = self.middleware(request)

        activities = UserActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

        activity = activities.first()
        self.assertEqual(activity.action, 'create_client')

    def test_get_client_ip_with_proxy(self):
        """Test IP address extraction with proxy headers."""
        request = self.factory.get('/')
        request.META = {
            'HTTP_X_FORWARDED_FOR': '203.0.113.1, 198.51.100.1',
            'REMOTE_ADDR': '192.168.1.1'
        }

        ip = self.middleware._get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')  # Should use first IP in X-Forwarded-For

    def test_get_client_ip_without_proxy(self):
        """Test IP address extraction without proxy."""
        request = self.factory.get('/')
        request.META = {
            'REMOTE_ADDR': '192.168.1.100'
        }

        ip = self.middleware._get_client_ip(request)
        self.assertEqual(ip, '192.168.1.100')

    def test_middleware_handles_exceptions_gracefully(self):
        """Test that middleware doesn't break request flow on errors."""
        request = self.factory.post('/api/v1/reports/')
        request.user = self.user
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        # Patch UserActivity.objects.create to raise exception
        with patch('apps.analytics.models.UserActivity.objects.create') as mock_create:
            mock_create.side_effect = Exception('Database error')

            # Should not raise exception
            try:
                response = self.middleware(request)
                # Middleware should complete successfully
                self.assertEqual(response.status_code, 200)
            except Exception:
                self.fail('Middleware should handle exceptions gracefully')

    def test_track_csv_upload(self):
        """Test tracking CSV upload."""
        client_id = str(self.test_client.id)
        request = self.factory.post(f'/api/v1/clients/{client_id}/upload-csv/')
        request.user = self.user
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'Test Browser'
        }

        response = self.middleware(request)

        activities = UserActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

        activity = activities.first()
        self.assertEqual(activity.action, 'upload_csv')
        self.assertIn(client_id, activity.description)

    def test_track_delete_operations(self):
        """Test tracking DELETE operations."""
        report_id = '123e4567-e89b-12d3-a456-426614174000'
        request = self.factory.delete(f'/api/v1/reports/{report_id}/')
        request.user = self.user
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'Test Browser'
        }

        response = self.middleware(request)

        activities = UserActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

        activity = activities.first()
        self.assertEqual(activity.action, 'delete_report')

    def test_user_agent_truncation(self):
        """Test that long user agents are truncated."""
        request = self.factory.post('/api/v1/reports/')
        request.user = self.user
        request.data = {}
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'A' * 600  # Very long user agent
        }

        response = self.middleware(request)

        activity = UserActivity.objects.filter(user=self.user).first()
        self.assertIsNotNone(activity)
        # User agent should be truncated to 500 chars
        self.assertLessEqual(len(activity.user_agent), 500)

    def test_metadata_captured(self):
        """Test that metadata is properly captured."""
        request = self.factory.post('/api/v1/reports/')
        request.user = self.user
        request.data = {
            'client_id': str(self.test_client.id),
            'report_type': 'cost'
        }
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'Test Browser'
        }

        response = self.middleware(request)

        activity = UserActivity.objects.filter(user=self.user).first()
        self.assertIsNotNone(activity.metadata)
        self.assertIn('path', activity.metadata)
        self.assertIn('method', activity.metadata)
        self.assertEqual(activity.metadata['method'], 'POST')
