"""
Security Assessment Report Generator - Focus on security recommendations.
"""

from django.db.models import Count, Q
from .base import BaseReportGenerator


class SecurityReportGenerator(BaseReportGenerator):
    """
    Generates a security assessment report focused on security recommendations.

    Target Audience: Security teams, compliance officers, CISOs
    Features:
    - Security recommendations only
    - Risk level indicators
    - Compliance implications
    - Remediation priority
    - Resource security posture
    """

    def get_template_name(self):
        """Return security assessment template (HTML version)."""
        return 'reports/security_enhanced.html'

    def get_pdf_template_name(self):
        """
        Return PDF template for Playwright generation.
        Uses the enhanced template for full Chart.js support.
        """
        return 'reports/security_enhanced.html'

    def get_context_data(self):
        """
        Get security report-specific context.

        Returns:
            dict: Context with security-focused metrics and recommendations
        """
        # Filter security recommendations
        security_recs = self.recommendations.filter(category='security')

        # Critical security issues (high impact)
        critical_issues = security_recs.filter(
            business_impact='high'
        ).order_by('-advisor_score_impact')

        # Medium priority
        medium_priority = security_recs.filter(
            business_impact='medium'
        ).order_by('-advisor_score_impact')

        # Low priority
        low_priority = security_recs.filter(
            business_impact='low'
        ).order_by('-advisor_score_impact')

        # Security by subscription
        security_by_subscription = security_recs.values(
            'subscription_name'
        ).annotate(
            total_count=Count('id'),
            critical_count=Count('id', filter=Q(business_impact='high')),
            medium_count=Count('id', filter=Q(business_impact='medium')),
            low_count=Count('id', filter=Q(business_impact='low'))
        ).order_by('-critical_count', '-total_count')

        # Security by resource type
        security_by_resource = security_recs.values(
            'resource_type'
        ).annotate(
            count=Count('id'),
            critical_count=Count('id', filter=Q(business_impact='high'))
        ).order_by('-critical_count', '-count')[:10]

        # Calculate security score (simplified)
        total_security_recs = security_recs.count()
        critical_count = critical_issues.count()

        # Security score: 100 - (critical * 15 + medium * 5 + low * 1)
        security_score = max(0, 100 - (
            critical_count * 15 +
            medium_priority.count() * 5 +
            low_priority.count() * 1
        ))

        # Security posture assessment
        if security_score >= 90:
            posture = 'Excellent'
            posture_color = 'success'
        elif security_score >= 70:
            posture = 'Good'
            posture_color = 'info'
        elif security_score >= 50:
            posture = 'Fair'
            posture_color = 'warning'
        else:
            posture = 'Needs Improvement'
            posture_color = 'danger'

        return {
            'security_recommendations': security_recs,
            'critical_issues': critical_issues,
            'high_priority_issues': critical_issues,  # Alias for template compatibility
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'security_summary': {
                'total_issues': total_security_recs,
                'critical_count': critical_count,
                'medium_count': medium_priority.count(),
                'low_count': low_priority.count(),
                'security_score': security_score,
                'security_posture': posture,
                'posture_color': posture_color,
            },
            'security_by_subscription': security_by_subscription,
            'security_by_resource_type': security_by_resource,
            'remediation_timeline': {
                'immediate': critical_count,  # Critical - within 24 hours
                'short_term': medium_priority.count(),  # Medium - within 1 week
                'medium_term': low_priority.count(),  # Low - within 1 month
            },
            # Additional context for enhanced template
            'security_score': security_score,
            'total_security_findings': total_security_recs,
            'critical_count': critical_count,
            'high_count': critical_count,  # Alias for compatibility
            'medium_count': medium_priority.count(),
            'security_focused': True,
        }
