"""
Utility functions for Reports app.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone


def format_file_size(size_bytes):
    """
    Format file size from bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")
    """
    if size_bytes is None or size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def get_file_size_from_report(report):
    """
    Get file size from report object.

    Args:
        report: Report instance

    Returns:
        File size in bytes
    """
    if report.file_size:
        return report.file_size

    # Try to get size from file field
    if report.pdf_file:
        try:
            return report.pdf_file.size
        except (AttributeError, FileNotFoundError):
            pass

    if report.csv_file:
        try:
            return report.csv_file.size
        except (AttributeError, FileNotFoundError):
            pass

    return 0


def calculate_percentage_change(current, previous):
    """
    Calculate percentage change between two values.

    Args:
        current: Current value
        previous: Previous value

    Returns:
        Percentage change as float
    """
    if previous is None or previous == 0:
        return 0.0 if current == 0 else 100.0

    if current is None:
        current = 0

    change = ((current - previous) / previous) * 100
    return round(change, 2)


def calculate_period_comparison(queryset, period='week'):
    """
    Calculate comparison statistics for current vs previous period.

    Args:
        queryset: QuerySet of Report objects
        period: Time period ('day', 'week', 'month')

    Returns:
        Dictionary with current and previous period statistics
    """
    now = timezone.now()

    # Define time periods
    if period == 'day':
        current_start = now - timedelta(days=1)
        previous_start = now - timedelta(days=2)
        previous_end = now - timedelta(days=1)
    elif period == 'week':
        current_start = now - timedelta(weeks=1)
        previous_start = now - timedelta(weeks=2)
        previous_end = now - timedelta(weeks=1)
    elif period == 'month':
        current_start = now - timedelta(days=30)
        previous_start = now - timedelta(days=60)
        previous_end = now - timedelta(days=30)
    else:
        raise ValueError(f"Invalid period: {period}")

    # Get current period stats
    current_reports = queryset.filter(created_at__gte=current_start)
    current_stats = current_reports.aggregate(
        count=Count('id'),
        total_savings=Sum('estimated_savings'),
        total_recommendations=Sum('total_recommendations')
    )

    # Get previous period stats
    previous_reports = queryset.filter(
        created_at__gte=previous_start,
        created_at__lt=previous_end
    )
    previous_stats = previous_reports.aggregate(
        count=Count('id'),
        total_savings=Sum('estimated_savings'),
        total_recommendations=Sum('total_recommendations')
    )

    return {
        'current': {
            'count': current_stats['count'] or 0,
            'total_savings': float(current_stats['total_savings'] or 0),
            'total_recommendations': current_stats['total_recommendations'] or 0,
        },
        'previous': {
            'count': previous_stats['count'] or 0,
            'total_savings': float(previous_stats['total_savings'] or 0),
            'total_recommendations': previous_stats['total_recommendations'] or 0,
        },
        'change': {
            'count': calculate_percentage_change(
                current_stats['count'], previous_stats['count']
            ),
            'total_savings': calculate_percentage_change(
                current_stats['total_savings'], previous_stats['total_savings']
            ),
            'total_recommendations': calculate_percentage_change(
                current_stats['total_recommendations'],
                previous_stats['total_recommendations']
            ),
        }
    }


def get_report_type_breakdown(queryset):
    """
    Get breakdown of reports by type.

    Args:
        queryset: QuerySet of Report objects

    Returns:
        Dictionary with counts by report type
    """
    breakdown = queryset.values('report_type').annotate(
        count=Count('id'),
        total_savings=Sum('estimated_savings')
    ).order_by('-count')

    result = {}
    for item in breakdown:
        result[item['report_type']] = {
            'count': item['count'],
            'total_savings': float(item['total_savings'] or 0)
        }

    return result


def get_trends_data(queryset, period='week', limit=10):
    """
    Get trends data for reports over time.

    Args:
        queryset: QuerySet of Report objects
        period: Time period for grouping ('day', 'week', 'month')
        limit: Number of periods to return

    Returns:
        List of dictionaries with trend data
    """
    from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

    # Choose truncation function based on period
    if period == 'day':
        trunc_func = TruncDate
    elif period == 'week':
        trunc_func = TruncWeek
    elif period == 'month':
        trunc_func = TruncMonth
    else:
        raise ValueError(f"Invalid period: {period}")

    # Group by period and aggregate
    trends = queryset.annotate(
        period_date=trunc_func('created_at')
    ).values('period_date').annotate(
        report_count=Count('id'),
        total_recommendations=Sum('total_recommendations'),
        total_savings=Sum('estimated_savings'),
        completed_count=Count('id', filter=Q(status='completed')),
        failed_count=Count('id', filter=Q(status='failed')),
        high_impact_count=Sum('high_impact_count'),
    ).order_by('-period_date')[:limit]

    result = []
    for item in trends:
        result.append({
            'period': item['period_date'].isoformat() if item['period_date'] else None,
            'report_count': item['report_count'],
            'total_recommendations': item['total_recommendations'] or 0,
            'total_savings': float(item['total_savings'] or 0),
            'completed_count': item['completed_count'],
            'failed_count': item['failed_count'],
            'high_impact_count': item['high_impact_count'] or 0,
            'success_rate': (item['completed_count'] / item['report_count'] * 100)
                           if item['report_count'] > 0 else 0,
        })

    return result


def apply_filters_from_params(queryset, params):
    """
    Apply filters to queryset based on request parameters.

    Args:
        queryset: QuerySet to filter
        params: Dictionary of filter parameters

    Returns:
        Filtered queryset
    """
    # Date range filters
    if params.get('start_date'):
        queryset = queryset.filter(created_at__gte=params['start_date'])

    if params.get('end_date'):
        queryset = queryset.filter(created_at__lte=params['end_date'])

    # Status filter
    if params.get('status'):
        queryset = queryset.filter(status__in=params['status'])

    # Report type filter
    if params.get('report_type'):
        queryset = queryset.filter(report_type__in=params['report_type'])

    # Client filter
    if params.get('client'):
        queryset = queryset.filter(client__id=params['client'])

    # Search filter
    if params.get('search'):
        search_term = params['search']
        queryset = queryset.filter(
            Q(title__icontains=search_term) |
            Q(client__company_name__icontains=search_term)
        )

    return queryset


def get_impact_distribution(recommendations_queryset):
    """
    Get distribution of recommendations by impact level.

    Args:
        recommendations_queryset: QuerySet of Recommendation objects

    Returns:
        Dictionary with counts by impact level
    """
    distribution = recommendations_queryset.values('impact').annotate(
        count=Count('id'),
        total_savings=Sum('potential_savings')
    ).order_by('impact')

    result = {
        'High': {'count': 0, 'total_savings': 0},
        'Medium': {'count': 0, 'total_savings': 0},
        'Low': {'count': 0, 'total_savings': 0},
    }

    for item in distribution:
        result[item['impact']] = {
            'count': item['count'],
            'total_savings': float(item['total_savings'] or 0)
        }

    return result


def get_category_distribution(recommendations_queryset):
    """
    Get distribution of recommendations by category.

    Args:
        recommendations_queryset: QuerySet of Recommendation objects

    Returns:
        Dictionary with counts by category
    """
    distribution = recommendations_queryset.values('category').annotate(
        count=Count('id'),
        total_savings=Sum('potential_savings')
    ).order_by('-count')

    result = {}
    for item in distribution:
        result[item['category']] = {
            'count': item['count'],
            'total_savings': float(item['total_savings'] or 0)
        }

    return result
