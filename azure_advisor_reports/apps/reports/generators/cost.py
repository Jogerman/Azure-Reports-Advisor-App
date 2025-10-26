"""
Cost Optimization Report Generator - Focus on cost savings opportunities.
"""

from django.db.models import Sum, Q
from .base import BaseReportGenerator


class CostOptimizationReportGenerator(BaseReportGenerator):
    """
    Generates a cost optimization report focused on savings opportunities.

    Target Audience: Finance teams, procurement, cost managers
    Features:
    - Cost savings focus
    - ROI calculations
    - Quick wins section
    - Long-term savings opportunities
    - Cost breakdown by resource type
    """

    def get_template_name(self):
        """Return cost optimization template (HTML version)."""
        return 'reports/cost_enhanced.html'

    def get_pdf_template_name(self):
        """Return PDF-optimized cost template."""
        return 'reports/cost_pdf.html'

    def get_context_data(self):
        """
        Get cost optimization report-specific context.

        Returns:
            dict: Context with cost-focused metrics and recommendations
        """
        # Filter only cost-related recommendations
        cost_recs = self.recommendations.filter(
            Q(category='cost') | Q(potential_savings__gt=0)
        )

        # Calculate cost metrics
        total_savings = cost_recs.aggregate(
            total=Sum('potential_savings')
        )['total'] or 0

        monthly_savings = total_savings / 12 if total_savings else 0

        # Quick wins (high savings, easy to implement)
        quick_wins = cost_recs.filter(
            potential_savings__gte=1000,
            business_impact='high'
        ).order_by('-potential_savings')[:10]

        quick_wins_total = quick_wins.aggregate(
            total=Sum('potential_savings')
        )['total'] or 0

        # Long-term opportunities
        long_term = cost_recs.filter(
            potential_savings__gte=500,
            business_impact__in=['medium', 'low']
        ).order_by('-potential_savings')[:10]

        long_term_total = long_term.aggregate(
            total=Sum('potential_savings')
        )['total'] or 0

        # Cost by resource type with enhanced data
        from django.db.models import Count
        cost_by_resource = cost_recs.values('resource_type').annotate(
            count=Count('id'),
            total_savings=Sum('potential_savings')
        ).order_by('-total_savings')[:10]

        # Calculate percentages and monthly savings for each resource type
        cost_by_resource_enhanced = []
        for item in cost_by_resource:
            total_item_savings = item['total_savings'] or 0
            percentage = (total_item_savings / total_savings * 100) if total_savings > 0 else 0
            cost_by_resource_enhanced.append({
                'resource_type': item['resource_type'],
                'count': item['count'],
                'total_savings': total_item_savings,
                'monthly_savings': total_item_savings / 12,
                'percentage': round(percentage, 1)
            })

        # Top cost savers for visualization (return as queryset for template access)
        top_cost_savers = cost_recs.order_by('-potential_savings')[:10]
        top_cost_savers_total = top_cost_savers.aggregate(
            total=Sum('potential_savings')
        )['total'] or 0

        # Quick wins monthly total
        quick_wins_monthly = quick_wins_total / 12 if quick_wins_total else 0

        # Cost by subscription
        cost_by_subscription = cost_recs.values(
            'subscription_name'
        ).annotate(
            count=Count('id'),
            total_savings=Sum('potential_savings')
        ).order_by('-total_savings')

        # ROI estimation (assume 8 hours to implement average recommendation)
        avg_implementation_hours = 8
        avg_hourly_cost = 100  # $100/hour
        total_implementation_cost = cost_recs.count() * avg_implementation_hours * avg_hourly_cost
        roi_percentage = ((total_savings - total_implementation_cost) / total_implementation_cost * 100) if total_implementation_cost > 0 else 0

        # Additional calculations for PDF templates
        three_year_savings = total_savings * 3
        top_cost_savers_monthly = top_cost_savers_total / 12 if top_cost_savers_total else 0

        return {
            'cost_recommendations': cost_recs,
            'total_annual_savings': total_savings,
            'total_monthly_savings': monthly_savings,
            'three_year_savings': three_year_savings,
            'quick_wins': quick_wins,
            'quick_wins_total': quick_wins_total,
            'quick_wins_monthly': quick_wins_monthly,
            'long_term_opportunities': long_term,
            'long_term_total': long_term_total,
            'cost_by_resource_type': cost_by_resource_enhanced,
            'cost_by_subscription': cost_by_subscription,
            'top_cost_savers': top_cost_savers,
            'top_cost_savers_total': top_cost_savers_total,
            'top_cost_savers_monthly': top_cost_savers_monthly,
            'roi_analysis': {
                'estimated_implementation_cost': total_implementation_cost,
                'estimated_annual_savings': total_savings,
                'net_benefit': total_savings - total_implementation_cost,
                'roi_percentage': round(roi_percentage, 1),
                'payback_months': round(total_implementation_cost / monthly_savings, 1) if monthly_savings > 0 else 0,
            },
            'cost_focused': True,
        }
