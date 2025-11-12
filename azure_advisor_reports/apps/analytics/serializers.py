"""
Serializers for analytics data.
"""

from rest_framework import serializers


class ReportTypeCountSerializer(serializers.Serializer):
    """Serializer for report counts by type."""
    cost = serializers.IntegerField()
    security = serializers.IntegerField()
    operations = serializers.IntegerField()
    detailed = serializers.IntegerField()
    executive = serializers.IntegerField()


class TrendDataSerializer(serializers.Serializer):
    """Serializer for trend data points."""
    date = serializers.CharField()  # ISO date string
    total = serializers.IntegerField()
    by_type = ReportTypeCountSerializer()


class TrendSummarySerializer(serializers.Serializer):
    """Serializer for trend summary statistics."""
    total = serializers.IntegerField()
    average = serializers.FloatField()
    peak = serializers.IntegerField()


class TrendResponseSerializer(serializers.Serializer):
    """Complete trend data response."""
    data = TrendDataSerializer(many=True)
    summary = TrendSummarySerializer()


class CategoryDataSerializer(serializers.Serializer):
    """Serializer for category distribution data."""
    name = serializers.CharField(max_length=100)
    value = serializers.IntegerField()
    percentage = serializers.FloatField()
    color = serializers.CharField(max_length=7)  # Hex color


class CategoryDistributionSerializer(serializers.Serializer):
    """Complete category distribution response."""
    categories = CategoryDataSerializer(many=True)
    total = serializers.IntegerField()


class MetricTrendsSerializer(serializers.Serializer):
    """Serializer for metric trends (percentage changes)."""
    recommendations = serializers.FloatField()
    savings = serializers.FloatField()
    clients = serializers.FloatField()
    reports = serializers.FloatField()


class DashboardMetricsSerializer(serializers.Serializer):
    """Serializer for dashboard metrics (Analytics page)."""
    total_reports = serializers.IntegerField()
    total_reports_change = serializers.FloatField()
    active_users = serializers.IntegerField()
    active_users_change = serializers.FloatField()
    total_cost_analyzed = serializers.FloatField()
    total_cost_analyzed_change = serializers.FloatField()
    avg_generation_time = serializers.FloatField()
    avg_generation_time_change = serializers.FloatField()
    storage_used = serializers.IntegerField()
    storage_used_formatted = serializers.CharField(max_length=50)
    success_rate = serializers.FloatField()


class ActivityItemSerializer(serializers.Serializer):
    """Serializer for activity items."""
    id = serializers.CharField(max_length=36)  # UUID
    type = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=500)
    timestamp = serializers.DateTimeField()
    clientName = serializers.CharField(max_length=255)
    reportType = serializers.CharField(max_length=100, required=False, allow_null=True)
    reportId = serializers.CharField(max_length=36, required=False, allow_null=True)
    status = serializers.CharField(max_length=20)


class DashboardAnalyticsSerializer(serializers.Serializer):
    """Complete dashboard analytics response."""
    metrics = DashboardMetricsSerializer()
    categoryDistribution = CategoryDataSerializer(many=True)
    trendData = TrendDataSerializer(many=True)
    recentActivity = ActivityItemSerializer(many=True)


class BusinessImpactItemSerializer(serializers.Serializer):
    """Serializer for business impact distribution item."""
    impact = serializers.CharField(max_length=20)
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class BusinessImpactDistributionSerializer(serializers.Serializer):
    """Complete business impact distribution response."""
    distribution = BusinessImpactItemSerializer(many=True)
    total = serializers.IntegerField()


class CategoryBreakdownSerializer(serializers.Serializer):
    """Serializer for category breakdown in client performance."""
    category = serializers.CharField(max_length=50)
    count = serializers.IntegerField()


class ClientPerformanceSerializer(serializers.Serializer):
    """Serializer for client performance metrics."""
    totalReports = serializers.IntegerField()
    completedReports = serializers.IntegerField()
    failedReports = serializers.IntegerField()
    successRate = serializers.FloatField()
    avgProcessingTimeSeconds = serializers.FloatField()
    totalRecommendations = serializers.IntegerField()
    totalPotentialSavings = serializers.FloatField()
    categoryBreakdown = CategoryBreakdownSerializer(many=True)


class UserInfoSerializer(serializers.Serializer):
    """Serializer for user information in activities."""
    id = serializers.CharField(max_length=36, allow_null=True)
    username = serializers.CharField(max_length=255)
    full_name = serializers.CharField(max_length=500, required=False)


class UserActivityItemSerializer(serializers.Serializer):
    """Serializer for individual user activity items."""
    id = serializers.CharField(max_length=36)
    user = UserInfoSerializer()
    activity_type = serializers.CharField(max_length=30)
    description = serializers.CharField(max_length=255)
    metadata = serializers.JSONField()
    timestamp = serializers.DateTimeField()


class UserActivityResponseSerializer(serializers.Serializer):
    """Complete user activity response with pagination."""
    activities = UserActivityItemSerializer(many=True)
    total_count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()


class ActivitySummaryItemSerializer(serializers.Serializer):
    """Serializer for activity summary items."""
    activity_type = serializers.CharField(max_length=30, required=False)
    user_id = serializers.CharField(max_length=36, required=False)
    username = serializers.CharField(max_length=255, required=False)
    date = serializers.CharField(max_length=10, required=False)
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class DateRangeSerializer(serializers.Serializer):
    """Serializer for date range information."""
    from_ = serializers.CharField(max_length=10, source='from', allow_null=True)
    to = serializers.CharField(max_length=10, allow_null=True)


class ActivitySummaryResponseSerializer(serializers.Serializer):
    """Complete activity summary response."""
    summary = ActivitySummaryItemSerializer(many=True)
    total_activities = serializers.IntegerField()
    date_range = DateRangeSerializer()
    group_by = serializers.CharField(max_length=20)


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health metrics."""
    database_size = serializers.IntegerField()
    database_size_formatted = serializers.CharField(max_length=50)
    total_reports = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    active_users_this_week = serializers.IntegerField()
    avg_report_generation_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    storage_used = serializers.IntegerField()
    storage_used_formatted = serializers.CharField(max_length=50)
    uptime = serializers.CharField(max_length=100)
    last_calculated = serializers.CharField(max_length=50)


class CostTrendSerializer(serializers.Serializer):
    """Serializer for cost trend data points."""
    month = serializers.CharField(max_length=7)  # Format: YYYY-MM
    cost = serializers.FloatField()


class CostInsightsSerializer(serializers.Serializer):
    """Serializer for cost insights data."""
    total_cost_analyzed = serializers.FloatField()
    potential_savings = serializers.FloatField()
    savings_percentage = serializers.FloatField()
    trends = CostTrendSerializer(many=True)
