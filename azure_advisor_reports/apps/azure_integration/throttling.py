"""
Custom throttling classes for Azure Integration API.

Provides rate limiting for Azure API operations to prevent abuse
and manage Azure API quota consumption.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AzureAPIThrottle(UserRateThrottle):
    """
    Throttle class for Azure API operations.

    Limits Azure API calls to 100 requests per hour per user to:
    1. Prevent abuse of the API
    2. Manage Azure API quota consumption
    3. Avoid hitting Azure rate limits

    Rate: 100 requests per hour

    Usage:
        @action(detail=True, methods=['post'], throttle_classes=[AzureAPIThrottle])
        def test_connection(self, request, pk=None):
            ...
    """

    rate = '100/hour'
    scope = 'azure_api'


class AzureConnectionTestThrottle(UserRateThrottle):
    """
    Throttle class specifically for Azure connection tests.

    More restrictive rate limit for connection tests since they:
    1. Are not time-critical
    2. Consume Azure API quota
    3. Should not be repeatedly triggered

    Rate: 20 requests per hour

    Usage:
        @action(detail=True, methods=['post'], throttle_classes=[AzureConnectionTestThrottle])
        def test_connection(self, request, pk=None):
            ...
    """

    rate = '20/hour'
    scope = 'azure_connection_test'


class AzureSyncThrottle(UserRateThrottle):
    """
    Throttle class for Azure sync operations.

    Moderate rate limit for sync operations (statistics, recommendations)
    since they can be resource-intensive.

    Rate: 50 requests per hour

    Usage:
        @action(detail=True, methods=['post'], throttle_classes=[AzureSyncThrottle])
        def sync_now(self, request, pk=None):
            ...
    """

    rate = '50/hour'
    scope = 'azure_sync'


class ReportCreationThrottle(UserRateThrottle):
    """
    Throttle class for report creation.

    Limits report creation to prevent abuse and manage system resources.
    Applies to both CSV and Azure API based reports.

    Rate: 100 requests per day

    Usage:
        class ReportViewSet(viewsets.ModelViewSet):
            def get_throttle_classes(self):
                if self.action == 'create':
                    return [ReportCreationThrottle]
                return []
    """

    rate = '100/day'
    scope = 'report_creation'
