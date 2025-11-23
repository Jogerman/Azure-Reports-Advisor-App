"""
Views for Azure Integration app.

Provides REST API endpoints for managing Azure subscriptions and testing connections.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.core.cache import cache

from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.serializers import (
    AzureSubscriptionSerializer,
    AzureSubscriptionCreateSerializer,
    AzureSubscriptionUpdateSerializer,
    AzureSubscriptionListSerializer,
)
from apps.azure_integration.tasks import (
    test_azure_connection,
    sync_azure_statistics,
)

logger = logging.getLogger(__name__)


class AzureSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Azure subscriptions.

    Provides CRUD operations and custom actions for:
    - Testing Azure credentials and connectivity
    - Fetching Azure Advisor statistics
    - Forcing subscription synchronization
    - Listing reports created from this subscription

    Permissions:
        - Users can only view/manage their own subscriptions
        - All endpoints require authentication

    Filtering:
        - is_active: Filter by active status
        - sync_status: Filter by sync status (never_synced, success, failed)

    Search:
        - Search by subscription name or subscription ID

    Ordering:
        - created_at, last_sync_at, name (default: -created_at)
    """

    queryset = AzureSubscription.objects.select_related('created_by', 'client')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'sync_status', 'client']
    search_fields = ['name', 'subscription_id', 'client__company_name']
    ordering_fields = ['created_at', 'last_sync_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter queryset based on user permissions.

        Returns subscriptions that are visible to the current user:
        - All subscriptions for all clients (users can see all clients' subscriptions)
        - Optionally filtered by client_id query parameter
        """
        queryset = super().get_queryset()

        # Allow filtering by client via query parameter
        client_id = self.request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AzureSubscriptionListSerializer
        elif self.action == 'create':
            return AzureSubscriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AzureSubscriptionUpdateSerializer
        return AzureSubscriptionSerializer

    def perform_create(self, serializer):
        """Set created_by to current user when creating subscription."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Soft delete: deactivate subscription instead of deleting.

        This preserves historical data and reports created from this subscription.
        """
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        logger.info(
            f"Subscription {instance.id} deactivated by user {self.request.user.email}"
        )

    @action(detail=True, methods=['post'], url_path='test-connection')
    def test_connection(self, request, pk=None):
        """
        Test Azure subscription credentials and connectivity.

        POST /api/v1/azure/subscriptions/{id}/test-connection/

        This endpoint triggers an async Celery task that:
        1. Validates Azure credentials
        2. Tests API connectivity
        3. Verifies subscription access
        4. Updates subscription sync_status

        Returns:
            200 OK: Connection test completed successfully
            {
                "status": "success",
                "message": "Connection test completed",
                "task_id": "celery-task-uuid",
                "subscription": {...},
                "test_result": {
                    "success": true,
                    "subscription_id": "...",
                    "subscription_name": "...",
                    "error_message": null
                }
            }

            400 Bad Request: Connection test failed
            {
                "status": "error",
                "message": "Connection test failed: ...",
                "task_id": "celery-task-uuid"
            }
        """
        subscription = self.get_object()

        logger.info(
            f"Testing connection for subscription {subscription.id} "
            f"by user {request.user.email}"
        )

        # Trigger async test task
        task = test_azure_connection.delay(str(subscription.id))

        # Wait for result (max 10 seconds to keep request responsive)
        try:
            result = task.get(timeout=10)

            if result.get('success'):
                logger.info(
                    f"Connection test successful for subscription {subscription.id}"
                )
                return Response({
                    'status': 'success',
                    'message': 'Connection test completed',
                    'task_id': task.id,
                    'subscription': self.get_serializer(subscription).data,
                    'test_result': result,
                })
            else:
                logger.warning(
                    f"Connection test failed for subscription {subscription.id}: "
                    f"{result.get('error_message')}"
                )
                return Response({
                    'status': 'error',
                    'message': f"Connection test failed: {result.get('error_message')}",
                    'task_id': task.id,
                    'subscription': self.get_serializer(subscription).data,
                    'test_result': result,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(
                f"Connection test error for subscription {subscription.id}: {str(e)}",
                exc_info=True
            )
            return Response({
                'status': 'error',
                'message': f'Connection test failed: {str(e)}',
                'task_id': task.id,
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='statistics')
    def get_statistics(self, request, pk=None):
        """
        Get Azure Advisor statistics for this subscription.

        GET /api/v1/azure/subscriptions/{id}/statistics/

        Fetches aggregated statistics from Azure Advisor API including:
        - Total recommendation count
        - Breakdown by category (Cost, Security, Performance, etc.)
        - Breakdown by impact level (High, Medium, Low)
        - Total potential savings (if available)

        Statistics are cached for 1 hour to reduce API calls.

        Returns:
            200 OK: Statistics fetched successfully
            {
                "status": "success",
                "subscription": {...},
                "statistics": {
                    "total_recommendations": 42,
                    "by_category": {
                        "Cost": 15,
                        "Security": 10,
                        "Performance": 8,
                        "HighAvailability": 5,
                        "OperationalExcellence": 4
                    },
                    "by_impact": {
                        "High": 12,
                        "Medium": 20,
                        "Low": 10
                    },
                    "total_potential_savings": 15000.50,
                    "currency": "USD"
                },
                "cached": true
            }

            500 Internal Server Error: Failed to fetch statistics
        """
        subscription = self.get_object()

        logger.info(
            f"Fetching statistics for subscription {subscription.id} "
            f"by user {request.user.email}"
        )

        # Trigger async statistics sync
        task = sync_azure_statistics.delay(str(subscription.id))

        try:
            stats = task.get(timeout=30)

            if stats.get('success'):
                logger.info(
                    f"Statistics fetched successfully for subscription {subscription.id}: "
                    f"{stats.get('total_recommendations')} recommendations"
                )
                return Response({
                    'status': 'success',
                    'subscription': self.get_serializer(subscription).data,
                    'statistics': stats,
                    'cached': True,
                })
            else:
                logger.error(
                    f"Failed to fetch statistics for subscription {subscription.id}: "
                    f"{stats.get('error_message')}"
                )
                return Response({
                    'status': 'error',
                    'message': f"Failed to fetch statistics: {stats.get('error_message')}",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(
                f"Statistics fetch error for subscription {subscription.id}: {str(e)}",
                exc_info=True
            )
            return Response({
                'status': 'error',
                'message': f'Failed to fetch statistics: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='sync-now')
    def sync_now(self, request, pk=None):
        """
        Force immediate sync of Azure statistics (bypasses cache).

        POST /api/v1/azure/subscriptions/{id}/sync-now/

        Clears cached statistics and triggers a fresh sync from Azure API.
        Useful when users need up-to-date information immediately.

        Returns:
            202 Accepted: Sync initiated successfully
            {
                "status": "success",
                "message": "Sync initiated",
                "task_id": "celery-task-uuid"
            }
        """
        subscription = self.get_object()

        logger.info(
            f"Force sync requested for subscription {subscription.id} "
            f"by user {request.user.email}"
        )

        # Clear cache to force fresh fetch
        cache_key = f'azure_advisor:{subscription.subscription_id}:statistics'
        cache.delete(cache_key)
        logger.debug(f"Cleared cache key: {cache_key}")

        # Trigger async sync task
        task = sync_azure_statistics.delay(str(subscription.id))

        return Response({
            'status': 'success',
            'message': 'Sync initiated',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], url_path='reports')
    def list_reports(self, request, pk=None):
        """
        List all reports created from this Azure subscription.

        GET /api/v1/azure/subscriptions/{id}/reports/

        Returns paginated list of reports that were generated using
        this subscription's Azure API data.

        Query Parameters:
            - page: Page number (pagination)
            - page_size: Items per page

        Returns:
            200 OK: Reports list
            {
                "count": 10,
                "next": "...",
                "previous": null,
                "results": [
                    {
                        "id": "...",
                        "client_name": "...",
                        "report_type": "detailed",
                        "status": "completed",
                        "created_at": "2024-01-15T10:30:00Z",
                        ...
                    }
                ]
            }
        """
        subscription = self.get_object()

        logger.info(
            f"Listing reports for subscription {subscription.id} "
            f"by user {request.user.email}"
        )

        # Get reports for this subscription
        reports = subscription.reports.all().order_by('-created_at')

        # Paginate results
        page = self.paginate_queryset(reports)
        if page is not None:
            from apps.reports.serializers import ReportListSerializer
            serializer = ReportListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback without pagination
        from apps.reports.serializers import ReportListSerializer
        serializer = ReportListSerializer(reports, many=True)
        return Response(serializer.data)
