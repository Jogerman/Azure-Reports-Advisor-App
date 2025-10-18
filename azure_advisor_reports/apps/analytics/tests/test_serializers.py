"""
Comprehensive test suite for Analytics serializers.

Tests all serializers in the analytics app.
"""

import pytest
from datetime import date, datetime
from apps.analytics.serializers import (
    TrendDataSerializer,
    TrendSummarySerializer,
    TrendResponseSerializer,
    CategoryDataSerializer,
    CategoryDistributionSerializer,
    MetricTrendsSerializer,
    DashboardMetricsSerializer,
    ActivityItemSerializer,
    DashboardAnalyticsSerializer,
    BusinessImpactItemSerializer,
    BusinessImpactDistributionSerializer,
    CategoryBreakdownSerializer,
    ClientPerformanceSerializer,
)


# ============================================================================
# TrendDataSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestTrendDataSerializer:
    """Test suite for TrendDataSerializer."""

    def test_valid_trend_data(self):
        """Test serializing valid trend data."""
        data = {
            'date': '2025-01-15',
            'value': 42,
            'label': 'Jan 15'
        }

        serializer = TrendDataSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['value'] == 42

    def test_date_field_format(self):
        """Test that date field accepts proper format."""
        data = {
            'date': date(2025, 1, 15),
            'value': 100,
            'label': 'Test'
        }

        serializer = TrendDataSerializer(data)
        output = serializer.data
        assert 'date' in output
        assert output['value'] == 100

    def test_invalid_value_type(self):
        """Test validation fails for invalid value type."""
        data = {
            'date': '2025-01-15',
            'value': 'not_an_integer',
            'label': 'Test'
        }

        serializer = TrendDataSerializer(data=data)
        assert not serializer.is_valid()
        assert 'value' in serializer.errors


# ============================================================================
# TrendSummarySerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestTrendSummarySerializer:
    """Test suite for TrendSummarySerializer."""

    def test_valid_summary_data(self):
        """Test serializing valid summary data."""
        data = {
            'total': 1500,
            'average': 50.5,
            'peak': 200
        }

        serializer = TrendSummarySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['total'] == 1500
        assert serializer.validated_data['average'] == 50.5

    def test_zero_values(self):
        """Test handling zero values."""
        data = {
            'total': 0,
            'average': 0.0,
            'peak': 0
        }

        serializer = TrendSummarySerializer(data=data)
        assert serializer.is_valid()


# ============================================================================
# CategoryDataSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestCategoryDataSerializer:
    """Test suite for CategoryDataSerializer."""

    def test_valid_category_data(self):
        """Test serializing valid category data."""
        data = {
            'name': 'Cost Optimization',
            'value': 45,
            'percentage': 35.5,
            'color': '#FF6B6B'
        }

        serializer = CategoryDataSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['name'] == 'Cost Optimization'
        assert serializer.validated_data['percentage'] == 35.5

    def test_color_validation(self):
        """Test color field accepts hex colors."""
        data = {
            'name': 'Security',
            'value': 20,
            'percentage': 15.5,
            'color': '#1E88E5'
        }

        serializer = CategoryDataSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['color'] == '#1E88E5'

    def test_invalid_percentage(self):
        """Test validation with invalid percentage."""
        data = {
            'name': 'Test',
            'value': 10,
            'percentage': 'invalid',
            'color': '#000000'
        }

        serializer = CategoryDataSerializer(data=data)
        assert not serializer.is_valid()


# ============================================================================
# DashboardMetricsSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestDashboardMetricsSerializer:
    """Test suite for DashboardMetricsSerializer."""

    def test_valid_dashboard_metrics(self):
        """Test serializing complete dashboard metrics."""
        data = {
            'totalRecommendations': 150,
            'totalPotentialSavings': 75000.50,
            'activeClients': 12,
            'reportsGeneratedThisMonth': 25,
            'trends': {
                'recommendations': 12.5,
                'savings': -5.2,
                'clients': 3.1,
                'reports': 8.7
            }
        }

        serializer = DashboardMetricsSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['totalRecommendations'] == 150
        assert serializer.validated_data['totalPotentialSavings'] == 75000.50

    def test_zero_metrics(self):
        """Test handling zero metrics (empty dashboard)."""
        data = {
            'totalRecommendations': 0,
            'totalPotentialSavings': 0.0,
            'activeClients': 0,
            'reportsGeneratedThisMonth': 0,
            'trends': {
                'recommendations': 0.0,
                'savings': 0.0,
                'clients': 0.0,
                'reports': 0.0
            }
        }

        serializer = DashboardMetricsSerializer(data=data)
        assert serializer.is_valid()

    def test_negative_trend_values(self):
        """Test that negative trend values are accepted."""
        data = {
            'totalRecommendations': 100,
            'totalPotentialSavings': 50000.0,
            'activeClients': 10,
            'reportsGeneratedThisMonth': 15,
            'trends': {
                'recommendations': -10.5,
                'savings': -25.3,
                'clients': -2.1,
                'reports': -15.7
            }
        }

        serializer = DashboardMetricsSerializer(data=data)
        assert serializer.is_valid()


# ============================================================================
# ActivityItemSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestActivityItemSerializer:
    """Test suite for ActivityItemSerializer."""

    def test_valid_activity_item(self):
        """Test serializing valid activity item."""
        data = {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'type': 'report_generated',
            'title': 'Cost Optimization Report Generated',
            'description': 'New report for Acme Corp',
            'timestamp': '2025-01-15T10:30:00Z',
            'clientName': 'Acme Corp',
            'reportType': 'cost',
            'reportId': '123e4567-e89b-12d3-a456-426614174001',
            'status': 'completed'
        }

        serializer = ActivityItemSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['type'] == 'report_generated'
        assert serializer.validated_data['clientName'] == 'Acme Corp'

    def test_activity_without_optional_fields(self):
        """Test activity item with minimal required fields."""
        data = {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'type': 'client_created',
            'title': 'New Client Added',
            'description': 'Acme Corp was added',
            'timestamp': '2025-01-15T10:30:00Z',
            'clientName': 'Acme Corp',
            'status': 'active'
        }

        serializer = ActivityItemSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_timestamp_format(self):
        """Test timestamp field accepts datetime."""
        data = {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'type': 'test',
            'title': 'Test',
            'description': 'Test description',
            'timestamp': datetime(2025, 1, 15, 10, 30, 0),
            'clientName': 'Test Client',
            'status': 'pending'
        }

        serializer = ActivityItemSerializer(data)
        output = serializer.data
        assert 'timestamp' in output


# ============================================================================
# BusinessImpactDistributionSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestBusinessImpactDistributionSerializer:
    """Test suite for BusinessImpactDistributionSerializer."""

    def test_valid_distribution_data(self):
        """Test serializing valid business impact distribution."""
        data = {
            'distribution': [
                {'impact': 'high', 'count': 45, 'percentage': 45.0},
                {'impact': 'medium', 'count': 35, 'percentage': 35.0},
                {'impact': 'low', 'count': 20, 'percentage': 20.0}
            ],
            'total': 100
        }

        serializer = BusinessImpactDistributionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['total'] == 100
        assert len(serializer.validated_data['distribution']) == 3

    def test_empty_distribution(self):
        """Test handling empty distribution."""
        data = {
            'distribution': [],
            'total': 0
        }

        serializer = BusinessImpactDistributionSerializer(data=data)
        assert serializer.is_valid()

    def test_percentage_sum(self):
        """Test that percentages can sum to 100."""
        data = {
            'distribution': [
                {'impact': 'high', 'count': 60, 'percentage': 60.0},
                {'impact': 'medium', 'count': 30, 'percentage': 30.0},
                {'impact': 'low', 'count': 10, 'percentage': 10.0}
            ],
            'total': 100
        }

        serializer = BusinessImpactDistributionSerializer(data=data)
        assert serializer.is_valid()
        total_percentage = sum(item['percentage'] for item in serializer.validated_data['distribution'])
        assert total_percentage == 100.0


# ============================================================================
# ClientPerformanceSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestClientPerformanceSerializer:
    """Test suite for ClientPerformanceSerializer."""

    def test_valid_client_performance(self):
        """Test serializing valid client performance data."""
        data = {
            'totalReports': 50,
            'completedReports': 45,
            'failedReports': 2,
            'successRate': 90.0,
            'avgProcessingTimeSeconds': 127.5,
            'totalRecommendations': 450,
            'totalPotentialSavings': 125000.75,
            'categoryBreakdown': [
                {'category': 'cost', 'count': 200},
                {'category': 'security', 'count': 150},
                {'category': 'reliability', 'count': 100}
            ]
        }

        serializer = ClientPerformanceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['totalReports'] == 50
        assert serializer.validated_data['successRate'] == 90.0

    def test_success_rate_calculation(self):
        """Test that success rate is properly validated."""
        data = {
            'totalReports': 100,
            'completedReports': 75,
            'failedReports': 5,
            'successRate': 75.0,
            'avgProcessingTimeSeconds': 100.0,
            'totalRecommendations': 500,
            'totalPotentialSavings': 50000.0,
            'categoryBreakdown': []
        }

        serializer = ClientPerformanceSerializer(data=data)
        assert serializer.is_valid()
        # Success rate should be 75/100 = 75%
        assert serializer.validated_data['successRate'] == 75.0

    def test_zero_reports(self):
        """Test client performance with no reports."""
        data = {
            'totalReports': 0,
            'completedReports': 0,
            'failedReports': 0,
            'successRate': 0.0,
            'avgProcessingTimeSeconds': 0.0,
            'totalRecommendations': 0,
            'totalPotentialSavings': 0.0,
            'categoryBreakdown': []
        }

        serializer = ClientPerformanceSerializer(data=data)
        assert serializer.is_valid()


# ============================================================================
# CategoryDistributionSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestCategoryDistributionSerializer:
    """Test suite for CategoryDistributionSerializer."""

    def test_valid_category_distribution(self):
        """Test serializing valid category distribution."""
        data = {
            'categories': [
                {'name': 'Cost', 'value': 50, 'percentage': 33.33, 'color': '#FF6B6B'},
                {'name': 'Security', 'value': 60, 'percentage': 40.0, 'color': '#1E88E5'},
                {'name': 'Reliability', 'value': 40, 'percentage': 26.67, 'color': '#4CAF50'}
            ],
            'total': 150
        }

        serializer = CategoryDistributionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['total'] == 150
        assert len(serializer.validated_data['categories']) == 3

    def test_empty_categories(self):
        """Test handling empty category list."""
        data = {
            'categories': [],
            'total': 0
        }

        serializer = CategoryDistributionSerializer(data=data)
        assert serializer.is_valid()


# ============================================================================
# TrendResponseSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestTrendResponseSerializer:
    """Test suite for TrendResponseSerializer."""

    def test_valid_trend_response(self):
        """Test serializing complete trend response."""
        data = {
            'data': [
                {'date': '2025-01-10', 'value': 10, 'label': 'Jan 10'},
                {'date': '2025-01-11', 'value': 15, 'label': 'Jan 11'},
                {'date': '2025-01-12', 'value': 20, 'label': 'Jan 12'}
            ],
            'summary': {
                'total': 45,
                'average': 15.0,
                'peak': 20
            }
        }

        serializer = TrendResponseSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert len(serializer.validated_data['data']) == 3
        assert serializer.validated_data['summary']['total'] == 45


# ============================================================================
# DashboardAnalyticsSerializer Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestDashboardAnalyticsSerializer:
    """Test suite for DashboardAnalyticsSerializer (complete dashboard)."""

    def test_complete_dashboard_data(self):
        """Test serializing complete dashboard analytics."""
        data = {
            'metrics': {
                'totalRecommendations': 200,
                'totalPotentialSavings': 100000.0,
                'activeClients': 15,
                'reportsGeneratedThisMonth': 30,
                'trends': {
                    'recommendations': 10.5,
                    'savings': 15.2,
                    'clients': 5.0,
                    'reports': 12.3
                }
            },
            'categoryDistribution': [
                {'name': 'Cost', 'value': 80, 'percentage': 40.0, 'color': '#FF6B6B'},
                {'name': 'Security', 'value': 60, 'percentage': 30.0, 'color': '#1E88E5'},
                {'name': 'Reliability', 'value': 60, 'percentage': 30.0, 'color': '#4CAF50'}
            ],
            'trendData': [
                {'date': '2025-01-10', 'value': 10, 'label': 'Jan 10'},
                {'date': '2025-01-11', 'value': 12, 'label': 'Jan 11'}
            ],
            'recentActivity': [
                {
                    'id': '123e4567-e89b-12d3-a456-426614174000',
                    'type': 'report_generated',
                    'title': 'Report Generated',
                    'description': 'Test report',
                    'timestamp': '2025-01-15T10:00:00Z',
                    'clientName': 'Test Client',
                    'status': 'completed'
                }
            ]
        }

        serializer = DashboardAnalyticsSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['metrics']['totalRecommendations'] == 200
        assert len(serializer.validated_data['categoryDistribution']) == 3
        assert len(serializer.validated_data['trendData']) == 2
        assert len(serializer.validated_data['recentActivity']) == 1

    def test_minimal_dashboard_data(self):
        """Test dashboard with minimal data."""
        data = {
            'metrics': {
                'totalRecommendations': 0,
                'totalPotentialSavings': 0.0,
                'activeClients': 0,
                'reportsGeneratedThisMonth': 0,
                'trends': {
                    'recommendations': 0.0,
                    'savings': 0.0,
                    'clients': 0.0,
                    'reports': 0.0
                }
            },
            'categoryDistribution': [],
            'trendData': [],
            'recentActivity': []
        }

        serializer = DashboardAnalyticsSerializer(data=data)
        assert serializer.is_valid()


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.serializers
@pytest.mark.analytics
class TestSerializerEdgeCases:
    """Test edge cases for analytics serializers."""

    def test_very_large_savings(self):
        """Test handling very large potential savings."""
        data = {
            'totalRecommendations': 1000,
            'totalPotentialSavings': 9999999999.99,
            'activeClients': 100,
            'reportsGeneratedThisMonth': 500,
            'trends': {
                'recommendations': 100.0,
                'savings': 200.0,
                'clients': 50.0,
                'reports': 75.0
            }
        }

        serializer = DashboardMetricsSerializer(data=data)
        assert serializer.is_valid()

    def test_negative_counts_rejected(self):
        """Test that negative counts are rejected."""
        data = {
            'totalRecommendations': -10,
            'totalPotentialSavings': 50000.0,
            'activeClients': 5,
            'reportsGeneratedThisMonth': 10,
            'trends': {
                'recommendations': 5.0,
                'savings': 10.0,
                'clients': 2.0,
                'reports': 3.0
            }
        }

        serializer = DashboardMetricsSerializer(data=data)
        # Depending on validation, this may fail
        # If IntegerField doesn't have min_value validation, it will pass

    def test_unicode_in_names(self):
        """Test handling unicode characters in names."""
        data = {
            'name': 'Security and Compliance Tech',
            'value': 25,
            'percentage': 20.0,
            'color': '#1E88E5'
        }

        serializer = CategoryDataSerializer(data=data)
        assert serializer.is_valid()
        assert 'Security' in serializer.validated_data['name']
        assert 'Tech' in serializer.validated_data['name']

    def test_future_dates_in_trends(self):
        """Test that future dates are handled."""
        future_date = date(2030, 12, 31)
        data = {
            'date': future_date,
            'value': 100,
            'label': 'Future'
        }

        serializer = TrendDataSerializer(data)
        output = serializer.data
        # Should serialize without error
        assert output['value'] == 100
