"""
Serializers for analytics data.
"""

from rest_framework import serializers


class TrendDataSerializer(serializers.Serializer):
    """Serializer for trend data points."""
    date = serializers.DateField()
    value = serializers.IntegerField()
    label = serializers.CharField(max_length=20)


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
    """Serializer for dashboard metrics."""
    totalRecommendations = serializers.IntegerField()
    totalPotentialSavings = serializers.FloatField()
    activeClients = serializers.IntegerField()
    reportsGeneratedThisMonth = serializers.IntegerField()
    trends = MetricTrendsSerializer()


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
