"""
Filters for Reports app.
"""

from django.db import models
from django_filters import rest_framework as filters
from .models import Report, Recommendation


class ReportFilter(filters.FilterSet):
    """Filter set for Report model."""

    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    date_range_start_after = filters.DateFilter(field_name='date_range_start', lookup_expr='gte')
    date_range_start_before = filters.DateFilter(field_name='date_range_start', lookup_expr='lte')
    date_range_end_after = filters.DateFilter(field_name='date_range_end', lookup_expr='gte')
    date_range_end_before = filters.DateFilter(field_name='date_range_end', lookup_expr='lte')

    # Choice filters
    report_type = filters.MultipleChoiceFilter(
        field_name='report_type',
        choices=Report.REPORT_TYPE_CHOICES
    )
    status = filters.MultipleChoiceFilter(
        field_name='status',
        choices=Report.STATUS_CHOICES
    )

    # Relationship filters
    client = filters.UUIDFilter(field_name='client__id')
    client_name = filters.CharFilter(field_name='client__company_name', lookup_expr='icontains')
    created_by = filters.UUIDFilter(field_name='created_by__id')

    # Number range filters
    total_recommendations_min = filters.NumberFilter(field_name='total_recommendations', lookup_expr='gte')
    total_recommendations_max = filters.NumberFilter(field_name='total_recommendations', lookup_expr='lte')
    estimated_savings_min = filters.NumberFilter(field_name='estimated_savings', lookup_expr='gte')
    estimated_savings_max = filters.NumberFilter(field_name='estimated_savings', lookup_expr='lte')

    # Text search
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Report
        fields = [
            'report_type', 'status', 'client', 'created_by',
            'created_after', 'created_before', 'title'
        ]

    def filter_search(self, queryset, name, value):
        """
        Custom search filter that searches across multiple fields.
        """
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(client__company_name__icontains=value) |
            models.Q(subscription_ids__icontains=value)
        )


class RecommendationFilter(filters.FilterSet):
    """Filter set for Recommendation model."""

    # Choice filters
    category = filters.MultipleChoiceFilter(
        field_name='category',
        choices=Recommendation.CATEGORY_CHOICES
    )
    impact = filters.MultipleChoiceFilter(
        field_name='impact',
        choices=Recommendation.IMPACT_CHOICES
    )

    # Relationship filters
    report = filters.UUIDFilter(field_name='report__id')

    # Text filters
    resource_name = filters.CharFilter(field_name='resource_name', lookup_expr='icontains')
    resource_type = filters.CharFilter(field_name='resource_type', lookup_expr='icontains')
    resource_group = filters.CharFilter(field_name='resource_group', lookup_expr='icontains')
    subscription_id = filters.CharFilter(field_name='subscription_id', lookup_expr='icontains')

    # Number range filters
    potential_savings_min = filters.NumberFilter(field_name='potential_savings', lookup_expr='gte')
    potential_savings_max = filters.NumberFilter(field_name='potential_savings', lookup_expr='lte')

    # Search
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Recommendation
        fields = ['category', 'impact', 'report', 'resource_type']

    def filter_search(self, queryset, name, value):
        """
        Custom search filter that searches across multiple fields.
        """
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(resource_name__icontains=value) |
            models.Q(resource_type__icontains=value)
        )
