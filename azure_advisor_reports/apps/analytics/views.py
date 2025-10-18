"""
Analytics API views.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services import AnalyticsService
from .serializers import (
    DashboardAnalyticsSerializer,
    DashboardMetricsSerializer,
    TrendResponseSerializer,
    CategoryDistributionSerializer,
    ActivityItemSerializer,
    ClientPerformanceSerializer,
    BusinessImpactDistributionSerializer,
)


class DashboardAnalyticsView(APIView):
    """
    Get complete dashboard analytics data.

    Returns all metrics, category distribution, trend data, and recent activity.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all dashboard analytics data."""
        try:
            # Get metrics with trends
            metrics = AnalyticsService.get_dashboard_metrics()

            # Get category distribution
            category_data = AnalyticsService.get_category_distribution()

            # Get trend data (default 30 days)
            trend_data = AnalyticsService.get_trend_data(days=30)

            # Get recent activity
            recent_activity = AnalyticsService.get_recent_activity(limit=10)

            response_data = {
                'metrics': metrics,
                'categoryDistribution': category_data.get('categories', []),
                'trendData': trend_data.get('data', []),
                'recentActivity': recent_activity
            }

            serializer = DashboardAnalyticsSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve dashboard analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardMetricsView(APIView):
    """
    Get dashboard metrics only (without charts data).

    Returns key metrics and trends for display in metric cards.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard metrics."""
        try:
            metrics = AnalyticsService.get_dashboard_metrics()
            serializer = DashboardMetricsSerializer(metrics)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrendDataView(APIView):
    """
    Get trend data for reports generated over time.

    Supports different time ranges: 7, 30, or 90 days.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get trend data."""
        try:
            # Get days parameter from query string
            days_param = request.query_params.get('days', '30')

            # Validate and convert to int
            try:
                days = int(days_param)
                if days not in [7, 30, 90]:
                    days = 30
            except ValueError:
                days = 30

            trend_data = AnalyticsService.get_trend_data(days=days)
            serializer = TrendResponseSerializer(trend_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve trend data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryDistributionView(APIView):
    """
    Get recommendation distribution by category.

    Returns category counts with percentages and colors.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get category distribution."""
        try:
            category_data = AnalyticsService.get_category_distribution()
            serializer = CategoryDistributionSerializer(category_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve category distribution'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecentActivityView(APIView):
    """
    Get recent report activity.

    Returns a list of recent reports with client information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get recent activity."""
        try:
            # Get limit parameter from query string
            limit_param = request.query_params.get('limit', '10')

            # Validate and convert to int
            try:
                limit = int(limit_param)
                if limit < 1:
                    limit = 10
                elif limit > 100:
                    limit = 100
            except ValueError:
                limit = 10

            activity_data = AnalyticsService.get_recent_activity(limit=limit)
            serializer = ActivityItemSerializer(activity_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve recent activity'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClientPerformanceView(APIView):
    """
    Get performance metrics for a specific client.

    Returns detailed performance statistics and recommendations breakdown.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get client performance metrics."""
        try:
            client_id = request.query_params.get('client_id', None)

            performance_data = AnalyticsService.get_client_performance(client_id=client_id)
            serializer = ClientPerformanceSerializer(performance_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve client performance'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessImpactDistributionView(APIView):
    """
    Get distribution of recommendations by business impact level.

    Returns impact levels with counts and percentages.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get business impact distribution."""
        try:
            impact_data = AnalyticsService.get_business_impact_distribution()
            serializer = BusinessImpactDistributionSerializer(impact_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to retrieve business impact distribution'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CacheInvalidationView(APIView):
    """
    Invalidate analytics caches.

    Useful when you need to force refresh of cached analytics data.
    Admin only.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Invalidate all analytics caches."""
        try:
            # Check if user is admin
            if not request.user.is_staff and request.user.role != 'admin':
                return Response(
                    {'error': 'Permission denied', 'message': 'Only admins can invalidate cache'},
                    status=status.HTTP_403_FORBIDDEN
                )

            AnalyticsService.invalidate_cache()

            return Response(
                {'message': 'Analytics cache invalidated successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': str(e), 'message': 'Failed to invalidate cache'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
