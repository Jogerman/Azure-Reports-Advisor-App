"""
Detailed Report Generator - Full comprehensive report with all recommendations.
"""

from .base import BaseReportGenerator


class DetailedReportGenerator(BaseReportGenerator):
    """
    Generates a detailed report with complete recommendation data.

    Target Audience: Technical teams, cloud architects
    Features:
    - All recommendations listed
    - Grouped by category
    - Full technical details
    - Complete resource information
    """

    def get_template_name(self):
        """Return detailed report template."""
        return 'reports/detailed.html'

    def get_context_data(self):
        """
        Get detailed report-specific context.

        Returns:
            dict: Context with grouped recommendations and statistics
        """
        # Group recommendations by category
        recommendations_by_category = self.group_by_category()

        # Calculate category-specific statistics
        category_stats = []
        for category, recs in recommendations_by_category.items():
            total_savings = sum(r.potential_savings for r in recs)
            category_stats.append({
                'category': category,
                'count': len(recs),
                'total_savings': total_savings,
                'avg_savings': total_savings / len(recs) if recs else 0,
                'high_impact': sum(1 for r in recs if r.business_impact == 'high'),
            })

        # Sort by total savings
        category_stats.sort(key=lambda x: x['total_savings'], reverse=True)

        return {
            'recommendations_by_category': recommendations_by_category,
            'category_stats': category_stats,
            'show_all_details': True,
            'include_technical_details': True,
        }
