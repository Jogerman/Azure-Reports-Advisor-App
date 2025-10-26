"""
Analytics service layer for business logic and calculations.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from django.core.cache import cache

from apps.clients.models import Client
from apps.reports.models import Report, Recommendation
from apps.analytics.models import UserActivity


class AnalyticsService:
    """Service class for analytics calculations and data aggregation."""

    # Cache TTL (15 minutes)
    CACHE_TTL = 900

    @classmethod
    def get_dashboard_metrics(cls) -> Dict[str, Any]:
        """
        Calculate all dashboard metrics including trends.
        Returns metrics with percentage changes vs last month.
        """
        cache_key = 'dashboard_metrics'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Current period (this month)
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Last month for comparison
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            last_month_start = current_month_start.replace(month=current_month_start.month - 1)

        last_month_end = current_month_start

        # Calculate current metrics
        current_metrics = cls._calculate_period_metrics(current_month_start, now)

        # Calculate last month metrics for comparison
        last_month_metrics = cls._calculate_period_metrics(last_month_start, last_month_end)

        # Calculate percentage changes
        trends = {
            'recommendations': cls._calculate_percentage_change(
                current_metrics['total_recommendations'],
                last_month_metrics['total_recommendations']
            ),
            'savings': cls._calculate_percentage_change(
                float(current_metrics['total_savings']),
                float(last_month_metrics['total_savings'])
            ),
            'clients': cls._calculate_percentage_change(
                current_metrics['active_clients'],
                last_month_metrics['active_clients']
            ),
            'reports': cls._calculate_percentage_change(
                current_metrics['reports_generated'],
                last_month_metrics['reports_generated']
            ),
        }

        result = {
            'totalRecommendations': current_metrics['total_recommendations'],
            'totalPotentialSavings': float(current_metrics['total_savings']),
            'activeClients': current_metrics['active_clients'],
            'reportsGeneratedThisMonth': current_metrics['reports_generated'],
            'trends': trends
        }

        # Cache for 15 minutes
        cache.set(cache_key, result, cls.CACHE_TTL)

        return result

    @classmethod
    def _calculate_period_metrics(cls, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate metrics for a specific period."""

        # Active clients (status = active)
        active_clients = Client.objects.filter(status='active').count()

        # Reports generated in period
        reports_in_period = Report.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        )
        reports_generated = reports_in_period.count()

        # Total recommendations across all reports
        total_recommendations = Recommendation.objects.filter(
            report__created_at__gte=start_date,
            report__created_at__lt=end_date
        ).count()

        # Total potential savings
        total_savings = Recommendation.objects.filter(
            report__created_at__gte=start_date,
            report__created_at__lt=end_date
        ).aggregate(
            total=Sum('potential_savings')
        )['total'] or Decimal('0')

        return {
            'active_clients': active_clients,
            'reports_generated': reports_generated,
            'total_recommendations': total_recommendations,
            'total_savings': total_savings
        }

    @classmethod
    def _calculate_percentage_change(cls, current: float, previous: float) -> float:
        """Calculate percentage change between two values."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0

        change = ((current - previous) / previous) * 100
        return round(change, 1)

    @classmethod
    def get_category_distribution(cls) -> Dict[str, Any]:
        """
        Get recommendation distribution by category.
        Returns categories with counts and percentages.
        """
        cache_key = 'category_distribution'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Get category counts from all recommendations
        category_counts = Recommendation.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')

        total = sum(item['count'] for item in category_counts)

        # Map to frontend expected format with colors
        category_colors = {
            'cost': '#f59e0b',  # Orange
            'security': '#ef4444',  # Red
            'reliability': '#3b82f6',  # Blue
            'operational_excellence': '#8b5cf6',  # Purple
            'performance': '#10b981',  # Green
        }

        category_labels = {
            'cost': 'Cost',
            'security': 'Security',
            'reliability': 'Reliability',
            'operational_excellence': 'Operational Excellence',
            'performance': 'Performance',
        }

        categories = []
        for item in category_counts:
            category_key = item['category']
            count = item['count']
            percentage = round((count / total * 100), 1) if total > 0 else 0

            categories.append({
                'name': category_labels.get(category_key, category_key.title()),
                'value': count,
                'percentage': percentage,
                'color': category_colors.get(category_key, '#6b7280')
            })

        result = {
            'categories': categories,
            'total': total
        }

        # Cache for 15 minutes
        cache.set(cache_key, result, cls.CACHE_TTL)

        return result

    @classmethod
    def get_trend_data(cls, days: int = 30) -> Dict[str, Any]:
        """
        Get trend data for reports generated over time.

        Args:
            days: Number of days to retrieve (7, 30, or 90)

        Returns:
            Dictionary with trend data points and summary statistics
        """
        cache_key = f'trend_data_{days}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get reports grouped by date
        reports_by_date = Report.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Create a dictionary for quick lookup
        date_counts = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in reports_by_date}

        # Generate data points for all days (including days with 0 reports)
        data = []
        current_date = start_date.date()
        total = 0
        peak = 0

        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            count = date_counts.get(date_str, 0)

            data.append({
                'date': date_str,
                'value': count,
                'label': current_date.strftime('%b %d')
            })

            total += count
            if count > peak:
                peak = count

            current_date += timedelta(days=1)

        # Calculate average
        average = round(total / len(data), 1) if data else 0

        result = {
            'data': data,
            'summary': {
                'total': total,
                'average': average,
                'peak': peak
            }
        }

        # Cache for 15 minutes
        cache.set(cache_key, result, cls.CACHE_TTL)

        return result

    @classmethod
    def get_recent_activity(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent report activity with client information.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of recent activity items
        """
        cache_key = f'recent_activity_{limit}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Get recent reports with related client data
        recent_reports = Report.objects.select_related('client', 'created_by').order_by(
            '-created_at'
        )[:limit]

        activities = []
        for report in recent_reports:
            # Determine activity type based on status
            activity_type = 'report_generated' if report.status == 'completed' else f'report_{report.status}'

            # Create description based on report type and status
            report_type_labels = {
                'detailed': 'Detailed Report',
                'executive': 'Executive Summary',
                'cost': 'Cost Optimization',
                'security': 'Security Assessment',
                'operations': 'Operational Excellence',
            }

            status_descriptions = {
                'completed': 'Successfully generated',
                'processing': 'Processing',
                'pending': 'Pending',
                'failed': 'Failed to process',
            }

            report_type_label = report_type_labels.get(report.report_type, report.report_type.title())
            status_desc = status_descriptions.get(report.status, report.status.title())

            activities.append({
                'id': str(report.id),
                'type': activity_type,
                'title': f'{report_type_label} {status_desc}',
                'description': f'{status_desc} {report_type_label.lower()} for {report.client.company_name}.',
                'timestamp': report.created_at.isoformat(),
                'clientName': report.client.company_name,
                'reportType': report_type_label,
                'reportId': str(report.id),
                'status': report.status
            })

        # Cache for 5 minutes (shorter TTL for recent activity)
        cache.set(cache_key, activities, 300)

        return activities

    @classmethod
    def get_client_performance(cls, client_id: str = None) -> Dict[str, Any]:
        """
        Get performance metrics for a specific client or all clients.

        Args:
            client_id: Optional UUID of client to filter by

        Returns:
            Dictionary with client performance data
        """
        cache_key = f'client_performance_{client_id or "all"}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Base queryset
        reports_query = Report.objects.all()

        if client_id:
            reports_query = reports_query.filter(client_id=client_id)

        # Calculate metrics
        total_reports = reports_query.count()

        completed_reports = reports_query.filter(status='completed').count()

        failed_reports = reports_query.filter(status='failed').count()

        success_rate = round((completed_reports / total_reports * 100), 1) if total_reports > 0 else 0

        # Average processing time for completed reports
        avg_processing = reports_query.filter(
            status='completed',
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        ).annotate(
            duration=F('processing_completed_at') - F('processing_started_at')
        ).aggregate(
            avg=Avg('duration')
        )['avg']

        avg_processing_seconds = avg_processing.total_seconds() if avg_processing else 0

        # Total recommendations and savings for this client
        recommendations_query = Recommendation.objects.filter(report__in=reports_query)

        total_recommendations = recommendations_query.count()

        total_savings = recommendations_query.aggregate(
            total=Sum('potential_savings')
        )['total'] or Decimal('0')

        # Category breakdown
        category_breakdown = list(recommendations_query.values('category').annotate(
            count=Count('id')
        ).order_by('-count'))

        result = {
            'totalReports': total_reports,
            'completedReports': completed_reports,
            'failedReports': failed_reports,
            'successRate': success_rate,
            'avgProcessingTimeSeconds': round(avg_processing_seconds, 1),
            'totalRecommendations': total_recommendations,
            'totalPotentialSavings': float(total_savings),
            'categoryBreakdown': category_breakdown
        }

        # Cache for 15 minutes
        cache.set(cache_key, result, cls.CACHE_TTL)

        return result

    @classmethod
    def invalidate_cache(cls):
        """Invalidate all analytics caches."""
        cache_keys = [
            'dashboard_metrics',
            'category_distribution',
            'trend_data_7',
            'trend_data_30',
            'trend_data_90',
        ]

        # Also invalidate recent activity caches
        for limit in [5, 10, 15, 20]:
            cache_keys.append(f'recent_activity_{limit}')

        for key in cache_keys:
            cache.delete(key)

        # Invalidate client performance caches (harder to track all keys)
        # This is a limitation, consider using cache patterns or tags

    @classmethod
    def get_business_impact_distribution(cls) -> Dict[str, Any]:
        """Get distribution of recommendations by business impact level."""
        cache_key = 'business_impact_distribution'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        impact_counts = Recommendation.objects.values('business_impact').annotate(
            count=Count('id')
        ).order_by('-count')

        total = sum(item['count'] for item in impact_counts)

        impact_data = []
        for item in impact_counts:
            impact = item['business_impact'] or 'Unknown'
            count = item['count']
            percentage = round((count / total * 100), 1) if total > 0 else 0

            impact_data.append({
                'impact': impact,
                'count': count,
                'percentage': percentage
            })

        result = {
            'distribution': impact_data,
            'total': total
        }

        cache.set(cache_key, result, cls.CACHE_TTL)
        return result

    @classmethod
    def get_activity_history(
        cls,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        report_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get filtered and paginated activity history.

        Args:
            start_date: Filter activities after this date
            end_date: Filter activities before this date
            action: Filter by action type
            user_id: Filter by user
            client_id: Filter by client
            report_id: Filter by report
            limit: Number of results to return
            offset: Number of results to skip (for pagination)

        Returns:
            Dictionary with results and pagination info
        """
        # Build query
        query = UserActivity.objects.select_related('user', 'client', 'report')

        # Apply filters
        if start_date:
            query = query.filter(created_at__gte=start_date)

        if end_date:
            query = query.filter(created_at__lte=end_date)

        if action:
            query = query.filter(action=action)

        if user_id:
            query = query.filter(user_id=user_id)

        if client_id:
            query = query.filter(client_id=client_id)

        if report_id:
            query = query.filter(report_id=report_id)

        # Get total count before pagination
        total_count = query.count()

        # Apply ordering and pagination
        activities = query.order_by('-created_at')[offset:offset + limit]

        # Format results
        results = []
        for activity in activities:
            results.append({
                'id': str(activity.id),
                'action': activity.action,
                'description': activity.description,
                'user': {
                    'id': str(activity.user.id) if activity.user else None,
                    'username': activity.user.username if activity.user else 'System',
                    'email': activity.user.email if activity.user else None,
                } if activity.user else {'id': None, 'username': 'System', 'email': None},
                'client': {
                    'id': str(activity.client.id),
                    'company_name': activity.client.company_name,
                } if activity.client else None,
                'report': {
                    'id': str(activity.report.id),
                    'report_type': activity.report.report_type,
                    'status': activity.report.status,
                } if activity.report else None,
                'ip_address': activity.ip_address,
                'metadata': activity.metadata,
                'created_at': activity.created_at.isoformat(),
            })

        return {
            'results': results,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
        }

    @classmethod
    def get_entity_history(
        cls,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get activity history for a specific entity (client or report).

        Args:
            entity_type: 'client' or 'report'
            entity_id: UUID of the entity
            limit: Maximum number of results

        Returns:
            List of activity items for the entity
        """
        query = UserActivity.objects.select_related('user')

        if entity_type == 'client':
            query = query.filter(client_id=entity_id)
        elif entity_type == 'report':
            query = query.filter(report_id=entity_id)
        else:
            return []

        activities = query.order_by('-created_at')[:limit]

        results = []
        for activity in activities:
            results.append({
                'id': str(activity.id),
                'action': activity.action,
                'description': activity.description,
                'user': {
                    'username': activity.user.username if activity.user else 'System',
                    'email': activity.user.email if activity.user else None,
                } if activity.user else {'username': 'System', 'email': None},
                'ip_address': activity.ip_address,
                'metadata': activity.metadata,
                'created_at': activity.created_at.isoformat(),
            })

        return results

    @classmethod
    def log_activity(
        cls,
        action: str,
        description: str,
        user=None,
        client=None,
        report=None,
        ip_address: str = None,
        user_agent: str = None,
        metadata: dict = None
    ) -> UserActivity:
        """
        Log a user activity.

        Args:
            action: Action type (login, logout, create_client, etc.)
            description: Human-readable description
            user: User who performed the action
            client: Related client (optional)
            report: Related report (optional)
            ip_address: IP address of the user
            user_agent: User agent string
            metadata: Additional metadata as dict

        Returns:
            Created UserActivity instance
        """
        activity = UserActivity.objects.create(
            action=action,
            description=description,
            user=user,
            client=client,
            report=report,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )

        # Invalidate recent activity cache
        for limit in [5, 10, 15, 20]:
            cache.delete(f'recent_activity_{limit}')

        return activity

    @classmethod
    def get_activity_summary(cls, days: int = 7) -> Dict[str, Any]:
        """
        Get summary statistics of activities for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with activity summary statistics
        """
        cache_key = f'activity_summary_{days}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get activities in period
        activities = UserActivity.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Count by action type
        action_counts = activities.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        # Count by user
        user_counts = activities.filter(user__isnull=False).values(
            'user__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 users

        # Daily activity counts
        daily_counts = activities.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        result = {
            'total_activities': activities.count(),
            'by_action': list(action_counts),
            'top_users': list(user_counts),
            'daily_counts': list(daily_counts),
            'period_days': days,
        }

        # Cache for 1 hour
        cache.set(cache_key, result, 3600)

        return result

    @classmethod
    def get_user_activity_detailed(
        cls,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        activity_type: Optional[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get detailed user activity with filtering and pagination.

        Args:
            user_id: Filter by specific user UUID
            date_from: Start date for filtering
            date_to: End date for filtering
            activity_type: Filter by action type
            limit: Number of results per page
            offset: Pagination offset

        Returns:
            Dictionary with activities and pagination info
        """
        # Build query
        query = UserActivity.objects.select_related('user', 'client', 'report')

        # Apply filters
        if user_id:
            query = query.filter(user_id=user_id)

        if date_from:
            query = query.filter(created_at__gte=date_from)

        if date_to:
            query = query.filter(created_at__lte=date_to)

        if activity_type:
            query = query.filter(action=activity_type)

        # Get total count before pagination
        total_count = query.count()

        # Apply ordering and pagination
        activities = query.order_by('-created_at')[offset:offset + limit]

        # Format results
        results = []
        for activity in activities:
            user_data = {
                'id': str(activity.user.id) if activity.user else None,
                'username': activity.user.username if activity.user else 'System',
                'full_name': activity.user.full_name if activity.user and hasattr(activity.user, 'full_name') else (
                    activity.user.username if activity.user else 'System'
                ),
            }

            results.append({
                'id': str(activity.id),
                'user': user_data,
                'activity_type': activity.action,
                'description': activity.description,
                'metadata': activity.metadata,
                'timestamp': activity.created_at.isoformat(),
            })

        return {
            'activities': results,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
        }

    @classmethod
    def get_activity_summary_aggregated(
        cls,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        group_by: str = 'activity_type'
    ) -> Dict[str, Any]:
        """
        Get aggregated activity summary grouped by specified field.

        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            group_by: Field to group by ('activity_type', 'user', 'day')

        Returns:
            Dictionary with aggregated summary data
        """
        # Build base query
        query = UserActivity.objects.all()

        # Apply date filters
        if date_from:
            query = query.filter(created_at__gte=date_from)

        if date_to:
            query = query.filter(created_at__lte=date_to)

        # Get total activities
        total_activities = query.count()

        # Group and aggregate based on group_by parameter
        if group_by == 'activity_type':
            aggregated = query.values('action').annotate(
                count=Count('id')
            ).order_by('-count')

            summary = []
            for item in aggregated:
                count = item['count']
                percentage = round((count / total_activities * 100), 1) if total_activities > 0 else 0

                summary.append({
                    'activity_type': item['action'],
                    'count': count,
                    'percentage': percentage
                })

        elif group_by == 'user':
            aggregated = query.filter(user__isnull=False).values(
                'user__username', 'user__id'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:20]  # Top 20 users

            summary = []
            for item in aggregated:
                count = item['count']
                percentage = round((count / total_activities * 100), 1) if total_activities > 0 else 0

                summary.append({
                    'user_id': str(item['user__id']),
                    'username': item['user__username'],
                    'count': count,
                    'percentage': percentage
                })

        elif group_by == 'day':
            aggregated = query.extra(
                select={'date': 'DATE(created_at)'}
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            summary = []
            for item in aggregated:
                count = item['count']
                percentage = round((count / total_activities * 100), 1) if total_activities > 0 else 0

                summary.append({
                    'date': item['date'].strftime('%Y-%m-%d') if item['date'] else None,
                    'count': count,
                    'percentage': percentage
                })

        else:
            summary = []

        # Build response
        result = {
            'summary': summary,
            'total_activities': total_activities,
            'date_range': {
                'from': date_from.strftime('%Y-%m-%d') if date_from else None,
                'to': date_to.strftime('%Y-%m-%d') if date_to else None,
            },
            'group_by': group_by
        }

        return result

    @classmethod
    def get_system_health(cls) -> Dict[str, Any]:
        """
        Get current system health metrics.

        Returns:
            Dictionary with comprehensive system health information
        """
        from apps.reports.models import Report
        from django.db import connection
        import os
        import psutil
        from datetime import timedelta

        cache_key = 'system_health'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Database size calculation
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_database_size(current_database())"
            )
            db_size_bytes = cursor.fetchone()[0]

        # Format database size
        db_size_mb = db_size_bytes / (1024 * 1024)
        db_size_gb = db_size_bytes / (1024 * 1024 * 1024)

        if db_size_gb >= 1:
            db_size_formatted = f"{db_size_gb:.2f} GB"
        else:
            db_size_formatted = f"{db_size_mb:.2f} MB"

        # Total reports
        total_reports = Report.objects.count()

        # Active users today and this week
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        active_users_today = UserActivity.objects.filter(
            created_at__gte=today_start,
            user__isnull=False
        ).values('user').distinct().count()

        active_users_this_week = UserActivity.objects.filter(
            created_at__gte=week_start,
            user__isnull=False
        ).values('user').distinct().count()

        # Average report generation time
        completed_reports = Report.objects.filter(
            status='completed',
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        )

        avg_processing_time = 0
        if completed_reports.exists():
            processing_times = [
                (r.processing_completed_at - r.processing_started_at).total_seconds()
                for r in completed_reports[:100]  # Sample last 100
            ]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)

        # Error rate (last 24 hours)
        last_24h_start = now - timedelta(hours=24)
        reports_last_24h = Report.objects.filter(created_at__gte=last_24h_start)
        failed_reports_24h = reports_last_24h.filter(status='failed').count()
        total_reports_24h = reports_last_24h.count()

        error_rate = 0
        if total_reports_24h > 0:
            error_rate = (failed_reports_24h / total_reports_24h) * 100

        # Storage usage (approximate)
        try:
            # Get Django media root size
            from django.conf import settings
            media_root = getattr(settings, 'MEDIA_ROOT', None)

            storage_used_bytes = 0
            if media_root and os.path.exists(media_root):
                for dirpath, dirnames, filenames in os.walk(media_root):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            storage_used_bytes += os.path.getsize(filepath)

            storage_gb = storage_used_bytes / (1024 * 1024 * 1024)
            storage_mb = storage_used_bytes / (1024 * 1024)

            if storage_gb >= 1:
                storage_formatted = f"{storage_gb:.2f} GB"
            else:
                storage_formatted = f"{storage_mb:.2f} MB"

        except Exception:
            storage_used_bytes = 0
            storage_formatted = "N/A"

        # System uptime (process uptime approximation)
        try:
            process = psutil.Process(os.getpid())
            uptime_seconds = (now - datetime.fromtimestamp(process.create_time())).total_seconds()
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            uptime = f"{uptime_days} days, {uptime_hours} hours"
        except Exception:
            uptime = "N/A"

        result = {
            'database_size': db_size_bytes,
            'database_size_formatted': db_size_formatted,
            'total_reports': total_reports,
            'active_users_today': active_users_today,
            'active_users_this_week': active_users_this_week,
            'avg_report_generation_time': round(avg_processing_time, 1),
            'error_rate': round(error_rate, 2),
            'storage_used': storage_used_bytes,
            'storage_used_formatted': storage_formatted,
            'uptime': uptime,
            'last_calculated': now.isoformat()
        }

        # Cache for 5 minutes
        cache.set(cache_key, result, 300)

        return result
