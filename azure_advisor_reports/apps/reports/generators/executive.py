"""
Executive Summary Report Generator - High-level overview for leadership.
"""

from .base import BaseReportGenerator


class ExecutiveReportGenerator(BaseReportGenerator):
    """
    Generates an executive summary report with key metrics and insights.

    Target Audience: Executives, management, decision makers
    Features:
    - High-level summary
    - Key metrics dashboard
    - Top 10 recommendations
    - Visual charts (category distribution)
    - Business impact focus
    """

    def get_template_name(self):
        """Return executive summary template."""
        return 'reports/executive.html'

    def get_context_data(self):
        """
        Get executive report-specific context.

        Returns:
            dict: Context with summary metrics and top recommendations
        """
        # Calculate key metrics
        total_recs = self.recommendations.count()
        total_savings = self.calculate_total_savings()

        # Quick wins (high impact + high savings)
        quick_wins = self.recommendations.filter(
            business_impact='high',
            potential_savings__gte=1000  # $1000+ annual savings
        ).order_by('-potential_savings')[:5]

        # Resource type distribution
        from django.db.models import Count
        resource_distribution = self.recommendations.values(
            'resource_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Category summary with colors for charts
        category_colors = {
            'cost': '#FF6384',
            'security': '#36A2EB',
            'reliability': '#FFCE56',
            'operational_excellence': '#4BC0C0',
            'performance': '#9966FF',
        }

        category_data = []
        for item in self.calculate_category_distribution():
            category_data.append({
                'category': item['category_display'],
                'count': item['count'],
                'percentage': item['percentage'],
                'color': category_colors.get(item['category'], '#999999'),
            })

        return {
            'summary_metrics': {
                'total_recommendations': total_recs,
                'total_savings': total_savings,
                'monthly_savings': total_savings / 12 if total_savings else 0,
                'high_priority_count': self.get_impact_count('high'),
                'categories_affected': len(self.calculate_category_distribution()),
            },
            'quick_wins': quick_wins,
            'category_chart_data': category_data,
            'resource_distribution': resource_distribution,
            'top_10_recommendations': self.get_top_recommendations(limit=10),
            'show_charts': True,
            'executive_summary': True,
        }
