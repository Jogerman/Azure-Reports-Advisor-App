"""
Application Insights Telemetry Integration

This module provides comprehensive monitoring and observability using
Azure Application Insights, including custom events, metrics, and tracing.
"""

import logging
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Global telemetry client
_telemetry_client = None


def get_telemetry_client():
    """
    Get or create the Application Insights telemetry client
    """
    global _telemetry_client

    if _telemetry_client is None:
        try:
            from applicationinsights import TelemetryClient

            instrumentation_key = getattr(settings, 'APPINSIGHTS_INSTRUMENTATION_KEY', None)
            connection_string = getattr(settings, 'APPLICATIONINSIGHTS_CONNECTION_STRING', None)

            if connection_string:
                _telemetry_client = TelemetryClient(connection_string=connection_string)
            elif instrumentation_key:
                _telemetry_client = TelemetryClient(instrumentation_key)
            else:
                logger.warning('Application Insights not configured. Telemetry will be disabled.')
                return None

            logger.info('Application Insights telemetry initialized')

        except ImportError:
            logger.warning('applicationinsights package not installed. Run: pip install applicationinsights')
            return None
        except Exception as e:
            logger.error(f'Failed to initialize Application Insights: {str(e)}')
            return None

    return _telemetry_client


def setup_telemetry():
    """
    Initialize telemetry on application startup
    """
    client = get_telemetry_client()
    if client:
        # Track application start event
        track_event(
            'ApplicationStarted',
            properties={
                'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
                'debug': settings.DEBUG,
                'version': getattr(settings, 'VERSION', '1.0.0'),
            }
        )


# =============================================================================
# Event Tracking
# =============================================================================

def track_event(
    name: str,
    properties: Optional[Dict[str, Any]] = None,
    measurements: Optional[Dict[str, float]] = None
) -> None:
    """
    Track a custom event

    Args:
        name: Event name
        properties: Custom properties (dimensions)
        measurements: Custom measurements (metrics)

    Example:
        track_event(
            'ReportGenerated',
            properties={
                'client_id': str(client.id),
                'report_type': 'detailed',
                'user': request.user.username
            },
            measurements={
                'processing_time_seconds': 45.2,
                'recommendation_count': 125
            }
        )
    """
    client = get_telemetry_client()
    if client:
        try:
            client.track_event(
                name,
                properties=properties or {},
                measurements=measurements or {}
            )
            client.flush()
        except Exception as e:
            logger.error(f'Failed to track event {name}: {str(e)}')


def track_metric(
    name: str,
    value: float,
    properties: Optional[Dict[str, str]] = None
) -> None:
    """
    Track a custom metric

    Args:
        name: Metric name
        value: Metric value
        properties: Custom properties for filtering

    Example:
        track_metric(
            'ReportProcessingTime',
            value=45.2,
            properties={'report_type': 'detailed'}
        )
    """
    client = get_telemetry_client()
    if client:
        try:
            client.track_metric(
                name,
                value,
                properties=properties or {}
            )
            client.flush()
        except Exception as e:
            logger.error(f'Failed to track metric {name}: {str(e)}')


def track_exception(
    exception: Exception,
    properties: Optional[Dict[str, str]] = None,
    measurements: Optional[Dict[str, float]] = None
) -> None:
    """
    Track an exception

    Args:
        exception: The exception to track
        properties: Additional properties
        measurements: Additional measurements

    Example:
        try:
            process_report()
        except Exception as e:
            track_exception(
                e,
                properties={
                    'report_id': str(report.id),
                    'operation': 'csv_processing'
                }
            )
            raise
    """
    client = get_telemetry_client()
    if client:
        try:
            client.track_exception(
                type(exception),
                exception,
                None,
                properties=properties or {},
                measurements=measurements or {}
            )
            client.flush()
        except Exception as e:
            logger.error(f'Failed to track exception: {str(e)}')


def track_trace(
    message: str,
    severity: str = 'INFO',
    properties: Optional[Dict[str, str]] = None
) -> None:
    """
    Track a trace/log message

    Args:
        message: Log message
        severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        properties: Additional properties

    Example:
        track_trace(
            'Report processing started',
            severity='INFO',
            properties={'report_id': str(report.id)}
        )
    """
    client = get_telemetry_client()
    if client:
        try:
            from applicationinsights.logging import LoggingHandler
            severity_map = {
                'DEBUG': 0,
                'INFO': 1,
                'WARNING': 2,
                'ERROR': 3,
                'CRITICAL': 4,
            }

            client.track_trace(
                message,
                severity=severity_map.get(severity.upper(), 1),
                properties=properties or {}
            )
            client.flush()
        except Exception as e:
            logger.error(f'Failed to track trace: {str(e)}')


def track_request(
    name: str,
    url: str,
    duration_ms: int,
    response_code: int,
    success: bool,
    properties: Optional[Dict[str, str]] = None,
    measurements: Optional[Dict[str, float]] = None
) -> None:
    """
    Track an HTTP request

    Args:
        name: Request name
        url: Request URL
        duration_ms: Duration in milliseconds
        response_code: HTTP response code
        success: Whether request succeeded
        properties: Additional properties
        measurements: Additional measurements
    """
    client = get_telemetry_client()
    if client:
        try:
            client.track_request(
                name,
                url,
                success,
                duration=duration_ms,
                response_code=response_code,
                properties=properties or {},
                measurements=measurements or {}
            )
            client.flush()
        except Exception as e:
            logger.error(f'Failed to track request: {str(e)}')


def track_dependency(
    name: str,
    dependency_type: str,
    data: str,
    duration_ms: int,
    success: bool,
    result_code: Optional[int] = None,
    properties: Optional[Dict[str, str]] = None
) -> None:
    """
    Track a dependency call (database, external API, etc.)

    Args:
        name: Dependency name
        dependency_type: Type (SQL, HTTP, Redis, etc.)
        data: Command or URL
        duration_ms: Duration in milliseconds
        success: Whether call succeeded
        result_code: Result code (optional)
        properties: Additional properties

    Example:
        track_dependency(
            'PostgreSQL Query',
            'SQL',
            'SELECT * FROM reports WHERE id = %s',
            duration_ms=125,
            success=True,
            properties={'database': 'azure_advisor_db'}
        )
    """
    client = get_telemetry_client()
    if client:
        try:
            client.track_dependency(
                name,
                data,
                dependency_type,
                duration=duration_ms,
                success=success,
                result_code=result_code,
                properties=properties or {}
            )
            client.flush()
        except Exception as e:
            logger.error(f'Failed to track dependency: {str(e)}')


# =============================================================================
# Decorators
# =============================================================================

def track_performance(
    event_name: Optional[str] = None,
    include_args: bool = False
):
    """
    Decorator to track function execution time

    Args:
        event_name: Custom event name (defaults to function name)
        include_args: Include function arguments in properties

    Example:
        @track_performance('ReportProcessing')
        def process_report(report_id: str):
            # Process report
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                track_exception(
                    e,
                    properties={
                        'function': func.__name__,
                        'module': func.__module__,
                    }
                )
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)

                properties = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'success': str(success),
                }

                if error_message:
                    properties['error'] = error_message

                if include_args:
                    properties['args'] = str(args)[:100]  # Limit length
                    properties['kwargs'] = str(kwargs)[:100]

                track_event(
                    event_name or f'Function.{func.__name__}',
                    properties=properties,
                    measurements={'duration_ms': duration_ms}
                )

        return wrapper
    return decorator


def track_celery_task(task_name: Optional[str] = None):
    """
    Decorator to track Celery task execution

    Example:
        @shared_task
        @track_celery_task('CSV Processing')
        def process_csv_task(report_id):
            # Process CSV
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None

            task_id = kwargs.get('task_id', 'unknown')

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                track_exception(
                    e,
                    properties={
                        'task_name': task_name or func.__name__,
                        'task_id': str(task_id),
                    }
                )
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)

                track_event(
                    f'CeleryTask.{task_name or func.__name__}',
                    properties={
                        'task_id': str(task_id),
                        'success': str(success),
                        'error': error_message or '',
                    },
                    measurements={'duration_ms': duration_ms}
                )

        return wrapper
    return decorator


# =============================================================================
# Business Metrics
# =============================================================================

class BusinessMetrics:
    """
    Helper class for tracking business-specific metrics
    """

    @staticmethod
    def track_user_login(user, success: bool = True, method: str = 'azure_ad'):
        """Track user login event"""
        track_event(
            'UserLogin',
            properties={
                'user_id': str(user.id) if user else 'unknown',
                'username': user.username if user else 'unknown',
                'method': method,
                'success': str(success),
            }
        )

    @staticmethod
    def track_report_created(report, processing_time_seconds: Optional[float] = None):
        """Track report creation"""
        track_event(
            'ReportCreated',
            properties={
                'report_id': str(report.id),
                'client_id': str(report.client_id),
                'report_type': report.report_type,
                'status': report.status,
            },
            measurements={
                'processing_time_seconds': processing_time_seconds or 0,
            }
        )

    @staticmethod
    def track_report_downloaded(report, user, format_type: str = 'pdf'):
        """Track report download"""
        track_event(
            'ReportDownloaded',
            properties={
                'report_id': str(report.id),
                'user_id': str(user.id),
                'format': format_type,
            }
        )

    @staticmethod
    def track_csv_processed(report, row_count: int, processing_time_seconds: float):
        """Track CSV processing"""
        track_event(
            'CSVProcessed',
            properties={
                'report_id': str(report.id),
                'client_id': str(report.client_id),
            },
            measurements={
                'row_count': row_count,
                'processing_time_seconds': processing_time_seconds,
                'rows_per_second': row_count / processing_time_seconds if processing_time_seconds > 0 else 0,
            }
        )

    @staticmethod
    def track_api_call(
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: int,
        user=None
    ):
        """Track API call"""
        track_event(
            'APICall',
            properties={
                'endpoint': endpoint,
                'method': method,
                'status_code': str(status_code),
                'user_id': str(user.id) if user else 'anonymous',
                'success': str(200 <= status_code < 400),
            },
            measurements={
                'duration_ms': duration_ms,
            }
        )

    @staticmethod
    def track_error(error_type: str, error_message: str, severity: str = 'ERROR'):
        """Track application error"""
        track_event(
            'ApplicationError',
            properties={
                'error_type': error_type,
                'error_message': error_message[:200],  # Limit length
                'severity': severity,
            }
        )


# =============================================================================
# Performance Monitoring
# =============================================================================

class PerformanceMonitor:
    """
    Context manager for monitoring performance
    """

    def __init__(self, operation_name: str, properties: Optional[Dict[str, str]] = None):
        self.operation_name = operation_name
        self.properties = properties or {}
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration_ms = int((self.end_time - self.start_time) * 1000)

        success = exc_type is None

        properties = self.properties.copy()
        properties['success'] = str(success)

        if exc_type:
            properties['error_type'] = exc_type.__name__
            properties['error_message'] = str(exc_val)[:200]

        track_event(
            f'Performance.{self.operation_name}',
            properties=properties,
            measurements={'duration_ms': duration_ms}
        )

        return False  # Don't suppress exceptions


# =============================================================================
# Availability Monitoring
# =============================================================================

def track_availability(
    name: str,
    success: bool,
    duration_ms: int,
    message: Optional[str] = None,
    properties: Optional[Dict[str, str]] = None
):
    """
    Track availability test result

    Example:
        track_availability(
            'DatabaseConnection',
            success=True,
            duration_ms=50,
            message='Connection successful'
        )
    """
    track_event(
        f'Availability.{name}',
        properties={
            'success': str(success),
            'message': message or '',
            **(properties or {})
        },
        measurements={'duration_ms': duration_ms}
    )
