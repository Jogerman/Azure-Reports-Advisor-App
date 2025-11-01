"""
Operational Excellence Report Generator - Focus on reliability and best practices.
"""

from django.db.models import Count, Q
from .base import BaseReportGenerator


class OperationsReportGenerator(BaseReportGenerator):
    """
    Generates an operational excellence report focused on reliability and best practices.

    Target Audience: DevOps teams, SREs, operations managers
    Features:
    - Operational excellence and reliability recommendations
    - Performance optimization
    - Best practices adherence
    - Automation opportunities
    - Resource health indicators
    """

    def get_template_name(self):
        """Return operations template."""
        return 'reports/operations.html'

    def get_context_data(self):
        """
        Get operations report-specific context.

        Returns:
            dict: Context with operations-focused metrics and recommendations
        """
        # Filter operational recommendations
        ops_recs = self.recommendations.filter(
            Q(category='reliability') |
            Q(category='operational_excellence') |
            Q(category='performance')
        )

        # Reliability recommendations
        reliability_recs = self.recommendations.filter(
            category='reliability'
        ).order_by('-business_impact', '-advisor_score_impact')

        # Operational excellence
        opex_recs = self.recommendations.filter(
            category='operational_excellence'
        ).order_by('-business_impact', '-advisor_score_impact')

        # Performance recommendations
        performance_recs = self.recommendations.filter(
            category='performance'
        ).order_by('-business_impact', '-advisor_score_impact')

        # High priority operations items
        high_priority = ops_recs.filter(
            business_impact='high'
        ).order_by('-advisor_score_impact')

        # Automation opportunities (heuristic)
        automation_keywords = ['automate', 'automatic', 'scaling', 'backup', 'monitoring']
        automation_opportunities = []
        for rec in ops_recs:
            if any(keyword in rec.recommendation.lower() for keyword in automation_keywords):
                automation_opportunities.append(rec)

        # By subscription
        ops_by_subscription = ops_recs.values(
            'subscription_name'
        ).annotate(
            total_count=Count('id'),
            reliability_count=Count('id', filter=Q(category='reliability')),
            performance_count=Count('id', filter=Q(category='performance')),
            opex_count=Count('id', filter=Q(category='operational_excellence'))
        ).order_by('-total_count')

        # By resource type
        ops_by_resource = ops_recs.values(
            'resource_type'
        ).annotate(
            count=Count('id'),
            high_impact_count=Count('id', filter=Q(business_impact='high'))
        ).order_by('-high_impact_count', '-count')[:10]

        # Calculate operational health score
        total_ops = ops_recs.count()
        high_impact_count = high_priority.count()

        # Health score: 100 - (high * 10 + medium * 5 + low * 2)
        health_score = max(0, 100 - (
            ops_recs.filter(business_impact='high').count() * 10 +
            ops_recs.filter(business_impact='medium').count() * 5 +
            ops_recs.filter(business_impact='low').count() * 2
        ))

        # Health assessment
        if health_score >= 90:
            health_status = 'Excellent'
            health_color = 'success'
        elif health_score >= 70:
            health_status = 'Good'
            health_color = 'info'
        elif health_score >= 50:
            health_status = 'Fair'
            health_color = 'warning'
        else:
            health_status = 'Needs Attention'
            health_color = 'danger'

        # Best practices adherence
        total_possible_score = 100
        current_score = health_score
        adherence_percentage = current_score

        return {
            'operational_recommendations': ops_recs,
            'reliability_recommendations': reliability_recs,
            'opex_recommendations': opex_recs,
            'performance_recommendations': performance_recs,
            'high_priority_items': high_priority,
            'automation_opportunities': automation_opportunities[:10],
            'operational_summary': {
                'total_recommendations': total_ops,
                'reliability_count': reliability_recs.count(),
                'opex_count': opex_recs.count(),
                'performance_count': performance_recs.count(),
                'high_priority_count': high_impact_count,
                'health_score': health_score,
                'health_status': health_status,
                'health_color': health_color,
                'best_practices_adherence': round(adherence_percentage, 1),
            },
            'ops_by_subscription': ops_by_subscription,
            'ops_by_resource_type': ops_by_resource,
            'improvement_areas': {
                'reliability': {
                    'count': reliability_recs.count(),
                    'percentage': round(reliability_recs.count() / total_ops * 100, 1) if total_ops > 0 else 0,
                },
                'operational_excellence': {
                    'count': opex_recs.count(),
                    'percentage': round(opex_recs.count() / total_ops * 100, 1) if total_ops > 0 else 0,
                },
                'performance': {
                    'count': performance_recs.count(),
                    'percentage': round(performance_recs.count() / total_ops * 100, 1) if total_ops > 0 else 0,
                },
            },
            'operations_focused': True,
        }
