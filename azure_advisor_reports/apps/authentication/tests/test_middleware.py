"""
Test cases for authentication middleware
Tests all middleware classes in apps.authentication.middleware
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

from apps.authentication.middleware import (
    JWTAuthenticationMiddleware,
    RequestLoggingMiddleware,
    SessionTrackingMiddleware,
    APIVersionMiddleware,
)
from apps.authentication.services import JWTService

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.middleware
class TestJWTAuthenticationMiddleware:
    """Test suite for JWTAuthenticationMiddleware"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()
        self.middleware = JWTAuthenticationMiddleware(get_response=lambda r: HttpResponse())

    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'process_request')

    def test_excluded_paths_skip_authentication(self):
        """Test that excluded paths skip JWT authentication"""
        excluded_paths = [
            '/admin/',
            '/static/css/style.css',
            '/media/images/logo.png',
            '/health/',
            '/api/auth/login/',
            '/api/auth/refresh/',
        ]

        for path in excluded_paths:
            request = self.factory.get(path)
            result = self.middleware.process_request(request)

            # Should return None (no processing)
            assert result is None

    def test_request_without_authorization_header(self):
        """Test request without Authorization header"""
        request = self.factory.get('/api/clients/')
        result = self.middleware.process_request(request)

        # Should return None (no JWT to process)
        assert result is None

    def test_request_with_malformed_authorization_header(self):
        """Test request with malformed Authorization header"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'InvalidFormat token'

        result = self.middleware.process_request(request)

        # Should return None
        assert result is None

    def test_request_with_valid_jwt_token(self, user):
        """Test request with valid JWT token"""
        # Generate valid token
        tokens = JWTService.generate_token(user)
        access_token = tokens['access_token']

        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        result = self.middleware.process_request(request)

        # Should attach user to request
        assert result is None
        assert hasattr(request, 'user')
        assert request.user.id == user.id
        assert request.user.email == user.email

    def test_request_with_invalid_jwt_token(self):
        """Test request with invalid JWT token"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid_token_123'

        result = self.middleware.process_request(request)

        # Should return None without setting user
        assert result is None

    def test_request_with_expired_jwt_token(self, expired_jwt_token):
        """Test request with expired JWT token"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {expired_jwt_token}'

        result = self.middleware.process_request(request)

        # Should return None without setting user
        assert result is None

    def test_request_with_token_for_nonexistent_user(self):
        """Test request with JWT token for user that doesn't exist"""
        import jwt
        from datetime import datetime, timedelta
        from django.conf import settings

        # Create token for non-existent user
        payload = {
            'user_id': '00000000-0000-0000-0000-000000000000',
            'email': 'deleted@example.com',
            'role': 'analyst',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        fake_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {fake_token}'

        result = self.middleware.process_request(request)

        # Should return None without setting user
        assert result is None

    def test_middleware_handles_exceptions_gracefully(self):
        """Test that middleware doesn't crash on exceptions"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer malformed.token.here'

        # Should not raise exception
        result = self.middleware.process_request(request)
        assert result is None

    def test_bearer_token_extraction(self, user):
        """Test that Bearer token is correctly extracted from header"""
        tokens = JWTService.generate_token(user)
        access_token = tokens['access_token']

        # Test with proper formatting
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        result = self.middleware.process_request(request)

        assert result is None
        assert hasattr(request, 'user')
        assert request.user.id == user.id

    def test_case_sensitivity_of_bearer_prefix(self):
        """Test that 'Bearer' prefix is case-sensitive"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'bearer some_token'

        result = self.middleware.process_request(request)

        # Should return None (lowercase 'bearer' not accepted)
        assert result is None


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.middleware
class TestRequestLoggingMiddleware:
    """Test suite for RequestLoggingMiddleware"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse())

    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'process_request')
        assert hasattr(self.middleware, 'process_response')

    def test_non_api_requests_not_logged(self):
        """Test that non-API requests are not logged"""
        non_api_paths = [
            '/',
            '/admin/',
            '/static/css/style.css',
            '/media/image.png',
        ]

        for path in non_api_paths:
            request = self.factory.get(path)
            result = self.middleware.process_request(request)

            # Should return None without logging
            assert result is None

    @patch('apps.authentication.middleware.logger')
    def test_api_request_logged_for_anonymous_user(self, mock_logger):
        """Test that API requests are logged for anonymous users"""
        request = self.factory.get('/api/clients/')
        request.user = AnonymousUser()

        self.middleware.process_request(request)

        # Should log with "Anonymous" user info
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'API Request' in call_args
        assert 'Anonymous' in call_args
        assert 'GET' in call_args
        assert '/api/clients/' in call_args

    @patch('apps.authentication.middleware.logger')
    def test_api_request_logged_for_authenticated_user(self, mock_logger, user):
        """Test that API requests are logged for authenticated users"""
        request = self.factory.get('/api/reports/')
        request.user = user

        self.middleware.process_request(request)

        # Should log with user email and role
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'API Request' in call_args
        assert user.email in call_args
        assert user.role in call_args
        assert 'GET' in call_args
        assert '/api/reports/' in call_args

    @patch('apps.authentication.middleware.logger')
    def test_response_logging_for_success(self, mock_logger):
        """Test that successful responses are not logged as warnings"""
        request = self.factory.get('/api/clients/')
        response = HttpResponse(status=200)

        self.middleware.process_response(request, response)

        # Should not log warning for successful response
        mock_logger.warning.assert_not_called()

    @patch('apps.authentication.middleware.logger')
    def test_response_logging_for_client_error(self, mock_logger):
        """Test that 4xx responses are logged as warnings"""
        request = self.factory.get('/api/clients/')
        response = HttpResponse(status=404)

        self.middleware.process_response(request, response)

        # Should log warning for 404
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert 'API Response' in call_args
        assert '404' in call_args
        assert '/api/clients/' in call_args

    @patch('apps.authentication.middleware.logger')
    def test_response_logging_for_server_error(self, mock_logger):
        """Test that 5xx responses are logged as warnings"""
        request = self.factory.get('/api/reports/')
        response = HttpResponse(status=500)

        self.middleware.process_response(request, response)

        # Should log warning for 500
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert 'API Response' in call_args
        assert '500' in call_args

    def test_get_client_ip_from_remote_addr(self):
        """Test client IP extraction from REMOTE_ADDR"""
        request = self.factory.get('/api/clients/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        ip = self.middleware.get_client_ip(request)
        assert ip == '192.168.1.100'

    def test_get_client_ip_from_x_forwarded_for(self):
        """Test client IP extraction from X-Forwarded-For header"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        ip = self.middleware.get_client_ip(request)
        # Should return first IP from X-Forwarded-For
        assert ip == '10.0.0.1'

    def test_get_client_ip_prioritizes_x_forwarded_for(self):
        """Test that X-Forwarded-For takes precedence over REMOTE_ADDR"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.45'
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        ip = self.middleware.get_client_ip(request)
        assert ip == '203.0.113.45'

    def test_non_api_response_not_logged(self):
        """Test that non-API responses are not logged"""
        request = self.factory.get('/admin/')
        response = HttpResponse(status=500)

        # Should return response without logging
        result = self.middleware.process_response(request, response)
        assert result == response


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.middleware
class TestSessionTrackingMiddleware:
    """Test suite for SessionTrackingMiddleware"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()
        self.middleware = SessionTrackingMiddleware(get_response=lambda r: HttpResponse())

    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'process_request')

    def test_anonymous_user_not_tracked(self):
        """Test that anonymous users are not tracked"""
        request = self.factory.get('/api/clients/')
        request.user = AnonymousUser()

        result = self.middleware.process_request(request)

        # Should return None without tracking
        assert result is None

    def test_authenticated_user_ip_updated(self, user):
        """Test that authenticated user's IP is updated"""
        request = self.factory.get('/api/clients/')
        request.user = user
        request.META['REMOTE_ADDR'] = '192.168.1.50'

        # Set different initial IP
        user.last_login_ip = '10.0.0.1'
        user.save()

        result = self.middleware.process_request(request)

        # Should update last_login_ip
        user.refresh_from_db()
        assert result is None
        assert user.last_login_ip == '192.168.1.50'

    def test_ip_not_updated_if_same(self, user):
        """Test that IP is not updated if it's the same"""
        current_ip = '192.168.1.100'
        user.last_login_ip = current_ip
        user.save()

        request = self.factory.get('/api/clients/')
        request.user = user
        request.META['REMOTE_ADDR'] = current_ip

        result = self.middleware.process_request(request)

        # Should not update if IP is the same
        user.refresh_from_db()
        assert result is None
        assert user.last_login_ip == current_ip

    def test_ip_extracted_from_x_forwarded_for(self, user):
        """Test IP extraction from X-Forwarded-For header"""
        request = self.factory.get('/api/clients/')
        request.user = user
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.10, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        user.last_login_ip = None
        user.save()

        result = self.middleware.process_request(request)

        # Should use first IP from X-Forwarded-For
        user.refresh_from_db()
        assert result is None
        assert user.last_login_ip == '203.0.113.10'

    def test_get_client_ip_static_method(self):
        """Test the static get_client_ip method"""
        request = self.factory.get('/api/clients/')
        request.META['REMOTE_ADDR'] = '192.168.1.200'

        ip = SessionTrackingMiddleware.get_client_ip(request)
        assert ip == '192.168.1.200'

    def test_get_client_ip_with_multiple_proxies(self):
        """Test IP extraction with multiple proxies in chain"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 172.16.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        ip = SessionTrackingMiddleware.get_client_ip(request)
        # Should return first (client) IP
        assert ip == '10.0.0.1'

    def test_ipv6_address_handling(self, user):
        """Test handling of IPv6 addresses"""
        ipv6_address = '2001:0db8:85a3:0000:0000:8a2e:0370:7334'

        request = self.factory.get('/api/clients/')
        request.user = user
        request.META['REMOTE_ADDR'] = ipv6_address

        user.last_login_ip = None
        user.save()

        result = self.middleware.process_request(request)

        user.refresh_from_db()
        assert result is None
        assert user.last_login_ip == ipv6_address

    def test_request_without_user_attribute(self):
        """Test request without user attribute doesn't crash"""
        request = self.factory.get('/api/clients/')
        # No user attribute

        result = self.middleware.process_request(request)

        # Should handle gracefully
        assert result is None


@pytest.mark.unit
@pytest.mark.middleware
class TestAPIVersionMiddleware:
    """Test suite for APIVersionMiddleware"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()
        self.middleware = APIVersionMiddleware(get_response=lambda r: HttpResponse())

    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'process_response')

    def test_api_response_includes_version_headers(self):
        """Test that API responses include version headers"""
        request = self.factory.get('/api/clients/')
        response = HttpResponse()

        result = self.middleware.process_response(request, response)

        assert 'X-API-Version' in result
        assert result['X-API-Version'] == 'v1'
        assert 'X-API-Build' in result
        assert result['X-API-Build'] == '1.0.0'

    def test_non_api_response_no_version_headers(self):
        """Test that non-API responses don't include version headers"""
        request = self.factory.get('/admin/')
        response = HttpResponse()

        result = self.middleware.process_response(request, response)

        # Should not add headers for non-API paths
        assert 'X-API-Version' not in result
        assert 'X-API-Build' not in result

    def test_version_headers_for_different_api_paths(self):
        """Test version headers added for various API paths"""
        api_paths = [
            '/api/clients/',
            '/api/reports/',
            '/api/auth/login/',
            '/api/v1/users/',
            '/api/analytics/dashboard/',
        ]

        for path in api_paths:
            request = self.factory.get(path)
            response = HttpResponse()

            result = self.middleware.process_response(request, response)

            assert 'X-API-Version' in result, f"Version header missing for {path}"
            assert result['X-API-Version'] == 'v1'
            assert 'X-API-Build' in result, f"Build header missing for {path}"

    def test_version_headers_on_error_responses(self):
        """Test that version headers are added even on error responses"""
        request = self.factory.get('/api/clients/')
        response = HttpResponse(status=500)

        result = self.middleware.process_response(request, response)

        assert 'X-API-Version' in result
        assert 'X-API-Build' in result

    def test_version_headers_on_post_requests(self):
        """Test that version headers are added on POST requests"""
        request = self.factory.post('/api/clients/')
        response = HttpResponse(status=201)

        result = self.middleware.process_response(request, response)

        assert 'X-API-Version' in result
        assert result['X-API-Version'] == 'v1'

    def test_version_headers_on_all_http_methods(self):
        """Test version headers added for all HTTP methods"""
        methods = ['get', 'post', 'put', 'patch', 'delete']

        for method in methods:
            request = getattr(self.factory, method)('/api/clients/')
            response = HttpResponse()

            result = self.middleware.process_response(request, response)

            assert 'X-API-Version' in result, f"Version header missing for {method.upper()}"
            assert 'X-API-Build' in result, f"Build header missing for {method.upper()}"


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.middleware
class TestMiddlewareIntegration:
    """Integration tests for middleware stack"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()

    def test_middleware_chain_execution(self, user):
        """Test that all middleware execute in correct order"""
        # Create middleware stack
        def get_response(request):
            return HttpResponse()

        api_version_mw = APIVersionMiddleware(get_response)
        session_tracking_mw = SessionTrackingMiddleware(api_version_mw)
        logging_mw = RequestLoggingMiddleware(session_tracking_mw)
        jwt_mw = JWTAuthenticationMiddleware(logging_mw)

        # Create request with JWT token
        tokens = JWTService.generate_token(user)
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {tokens["access_token"]}'
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        # Execute middleware chain
        jwt_mw.process_request(request)
        logging_mw.process_request(request)
        session_tracking_mw.process_request(request)

        response = get_response(request)
        response = session_tracking_mw.process_response(request, response)
        response = logging_mw.process_response(request, response)
        response = api_version_mw.process_response(request, response)

        # Verify middleware effects
        assert hasattr(request, 'user')
        assert request.user.id == user.id
        assert 'X-API-Version' in response
        assert response['X-API-Version'] == 'v1'

    def test_middleware_handles_unauthenticated_requests(self):
        """Test middleware stack with unauthenticated request"""
        def get_response(request):
            return HttpResponse()

        api_version_mw = APIVersionMiddleware(get_response)
        logging_mw = RequestLoggingMiddleware(api_version_mw)
        jwt_mw = JWTAuthenticationMiddleware(logging_mw)

        request = self.factory.get('/api/clients/')
        request.user = AnonymousUser()

        # Execute middleware chain
        jwt_mw.process_request(request)
        logging_mw.process_request(request)

        response = get_response(request)
        response = logging_mw.process_response(request, response)
        response = api_version_mw.process_response(request, response)

        # Should complete without errors
        assert response.status_code == 200
        assert 'X-API-Version' in response

    @patch('apps.authentication.middleware.logger')
    def test_middleware_error_logging(self, mock_logger, user):
        """Test that middleware logs errors appropriately"""
        def get_response(request):
            return HttpResponse(status=500)

        logging_mw = RequestLoggingMiddleware(get_response)

        request = self.factory.get('/api/clients/')
        request.user = user

        logging_mw.process_request(request)
        response = get_response(request)
        logging_mw.process_response(request, response)

        # Should log the error response
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert '500' in call_args
