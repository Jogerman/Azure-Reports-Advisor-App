"""
Base report generator class with common functionality for all report types.
"""

import os
from abc import ABC, abstractmethod
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """
    Abstract base class for all report generators.

    Provides common functionality for:
    - Data aggregation and analysis
    - HTML template rendering
    - File management
    - Context preparation
    """

    def __init__(self, report):
        """
        Initialize generator with a Report instance.

        Args:
            report: Report model instance
        """
        self.report = report
        self.recommendations = report.recommendations.all()
        self.client = report.client

    @abstractmethod
    def get_template_name(self):
        """
        Return the template path for this report type (HTML version).

        Returns:
            str: Template path (e.g., 'reports/detailed.html')
        """
        pass

    def get_pdf_template_name(self):
        """
        Return the template path for PDF generation.
        By default, uses the same template as HTML.
        Override this method to use a PDF-specific template.

        Returns:
            str: Template path for PDF (e.g., 'reports/detailed_pdf.html')
        """
        return self.get_template_name()

    @abstractmethod
    def get_context_data(self):
        """
        Return report-specific context data for template rendering.

        Returns:
            dict: Context data specific to this report type
        """
        pass

    def generate_html(self):
        """
        Generate HTML report file.

        Returns:
            str: Path to generated HTML file

        Raises:
            Exception: If HTML generation fails
        """
        try:
            logger.info(f"Generating HTML report for {self.report.id}")

            # Get base and specific context
            context = self.get_base_context()
            context.update(self.get_context_data())

            # Render template
            html_content = render_to_string(
                self.get_template_name(),
                context
            )

            # Save HTML file
            html_path = self.save_html(html_content)

            logger.info(f"HTML report generated successfully: {html_path}")
            return html_path

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {str(e)}")
            raise

    def get_base_context(self):
        """
        Get common context data for all report types.

        Returns:
            dict: Base context data
        """
        return {
            'report': self.report,
            'client': self.client,
            'recommendations': self.recommendations,
            'generated_date': timezone.now(),
            'total_recommendations': self.recommendations.count(),
            'report_type_display': self.report.get_report_type_display(),

            # Calculated metrics
            'category_distribution': self.calculate_category_distribution(),
            'impact_distribution': self.calculate_impact_distribution(),
            'total_savings': self.calculate_total_savings(),
            'monthly_savings': self.calculate_total_savings() / 12 if self.calculate_total_savings() else 0,
            'top_recommendations': self.get_top_recommendations(limit=10),

            # Subscription metrics
            'subscriptions': self.get_subscription_metrics(),

            # Saving Plans & Reserved Instances metrics (v2.0 - Enhanced Multi-Dimensional)
            'reservation_metrics': self.get_reservation_metrics(),  # Keep for backward compatibility
            'pure_reservation_metrics': self.get_pure_reservation_metrics_by_term(),  # NEW
            'savings_plan_metrics': self.get_savings_plan_metrics(),  # NEW
            'combined_commitment_metrics': self.get_combined_commitment_metrics(),  # NEW

            # Summary statistics
            'high_impact_count': self.get_impact_count('high'),
            'medium_impact_count': self.get_impact_count('medium'),
            'low_impact_count': self.get_impact_count('low'),
        }

    def calculate_category_distribution(self):
        """
        Calculate recommendation distribution by category.

        Returns:
            list: List of dicts with category, count, and percentage
        """
        total = self.recommendations.count()
        if total == 0:
            return []

        distribution = self.recommendations.values('category').annotate(
            count=Count('id')
        ).order_by('-count')

        # Add percentage
        for item in distribution:
            item['percentage'] = round((item['count'] / total) * 100, 1)
            item['category_display'] = dict(
                self.report._meta.get_field('recommendations').related_model.CATEGORY_CHOICES
            ).get(item['category'], item['category'])

        return list(distribution)

    def calculate_impact_distribution(self):
        """
        Calculate recommendation distribution by business impact.

        Returns:
            dict: Impact levels with counts
        """
        return {
            'high': self.recommendations.filter(business_impact='high').count(),
            'medium': self.recommendations.filter(business_impact='medium').count(),
            'low': self.recommendations.filter(business_impact='low').count(),
        }

    def calculate_total_savings(self):
        """
        Calculate total potential cost savings.

        Returns:
            Decimal: Total potential annual savings
        """
        total = self.recommendations.aggregate(
            total=Sum('potential_savings')
        )['total']
        return total or 0

    def get_top_recommendations(self, limit=10):
        """
        Get top N recommendations by potential savings and impact.

        Args:
            limit: Maximum number of recommendations to return

        Returns:
            QuerySet: Top recommendations ordered by savings and impact
        """
        return self.recommendations.filter(
            Q(business_impact='high') | Q(potential_savings__gt=0)
        ).order_by('-business_impact', '-potential_savings')[:limit]

    def get_impact_count(self, impact_level):
        """
        Get count of recommendations by impact level.

        Args:
            impact_level: 'high', 'medium', or 'low'

        Returns:
            int: Count of recommendations
        """
        return self.recommendations.filter(business_impact=impact_level).count()

    def get_subscription_metrics(self):
        """
        Get metrics grouped by Azure subscription.

        Returns:
            list: List of subscriptions with metrics
        """
        subscriptions = self.recommendations.values(
            'subscription_id', 'subscription_name'
        ).annotate(
            rec_count=Count('id'),
            total_savings=Sum('potential_savings')
        ).order_by('-total_savings')

        return list(subscriptions)

    def get_reservation_metrics(self):
        """
        Get metrics for Saving Plans & Reserved Instances recommendations (v1.6.3 - Memory Optimized).

        Analyzes reservation-based recommendations and calculates:
        - Total count of reservation recommendations
        - Breakdown by reservation type
        - Breakdown by commitment term
        - Total commitment savings over the full term
        - Average savings per reservation

        Returns:
            dict: Dictionary containing reservation metrics and grouped data
        """
        from django.db.models import F, Case, When, DecimalField, Value

        # Filter only reservation recommendations and annotate with commitment savings
        reservations = self.recommendations.filter(
            is_reservation_recommendation=True
        ).annotate(
            commitment_savings=Case(
                When(
                    commitment_term_years__isnull=False,
                    potential_savings__isnull=False,
                    then=F('potential_savings') * F('commitment_term_years')
                ),
                default=F('potential_savings'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )

        reservation_count = reservations.count()

        if reservation_count == 0:
            return {
                'has_reservations': False,
                'total_count': 0,
                'total_annual_savings': 0,
                'total_commitment_savings': 0,
                'by_type': [],
                'by_term': [],
                'recommendations': [],
            }

        # Calculate totals using database aggregation (memory efficient)
        totals = reservations.aggregate(
            total_annual=Sum('potential_savings'),
            total_commitment=Sum('commitment_savings')
        )
        total_annual_savings = totals['total_annual'] or 0
        total_commitment_savings = float(totals['total_commitment'] or 0)

        # Group by reservation type using database aggregation
        by_type = []
        type_groups = reservations.values('reservation_type').annotate(
            count=Count('id'),
            annual_savings=Sum('potential_savings'),
            commitment_savings=Sum('commitment_savings')
        ).order_by('-annual_savings')

        for group in type_groups:
            if group['reservation_type']:
                # Get display name for type
                type_display = {
                    'reserved_instance': 'Reserved VM Instance',
                    'savings_plan': 'Savings Plan',
                    'reserved_capacity': 'Reserved Capacity',
                    'other': 'Other Reservation',
                }.get(group['reservation_type'], group['reservation_type'])

                by_type.append({
                    'type': group['reservation_type'],
                    'type_display': type_display,
                    'count': group['count'],
                    'annual_savings': float(group['annual_savings'] or 0),
                    'commitment_savings': float(group['commitment_savings'] or 0),
                })

        # Group by commitment term using database aggregation
        by_term = []
        term_groups = reservations.values('commitment_term_years').annotate(
            count=Count('id'),
            annual_savings=Sum('potential_savings'),
            commitment_savings=Sum('commitment_savings')
        ).order_by('commitment_term_years')

        for group in term_groups:
            if group['commitment_term_years']:
                term_display = f"{group['commitment_term_years']}-Year Commitment"

                by_term.append({
                    'term_years': group['commitment_term_years'],
                    'term_display': term_display,
                    'count': group['count'],
                    'annual_savings': float(group['annual_savings'] or 0),
                    'commitment_savings': float(group['commitment_savings'] or 0),
                })

        # Get top reservation recommendations using database ordering (memory efficient)
        top_reservations = list(
            reservations.order_by('-commitment_savings')[:10]
        )

        return {
            'has_reservations': True,
            'total_count': reservation_count,
            'total_annual_savings': float(total_annual_savings),
            'total_commitment_savings': total_commitment_savings,
            'average_annual_savings': float(total_annual_savings / reservation_count) if reservation_count > 0 else 0,
            'by_type': by_type,
            'by_term': by_term,
            'recommendations': top_reservations,
        }

    def get_pure_reservation_metrics_by_term(self):
        """
        Get metrics for PURE RESERVATIONS ONLY (excluding Savings Plans).
        Separated by commitment term (1-year vs 3-year).

        Version 2.0 - Enhanced Multi-Dimensional Analysis

        Returns:
            dict: Nested structure with separate 1-year and 3-year data
        """
        from django.db.models import F, Sum, Count, DecimalField, Case, When, Q

        # Filter only pure traditional reservations (NOT Savings Plans)
        pure_reservations = self.recommendations.filter(
            Q(commitment_category='pure_reservation_1y') |
            Q(commitment_category='pure_reservation_3y')
        ).annotate(
            commitment_savings=Case(
                When(
                    commitment_term_years__isnull=False,
                    potential_savings__isnull=False,
                    then=F('potential_savings') * F('commitment_term_years')
                ),
                default=F('potential_savings'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )

        # Separate 1-year and 3-year reservations
        one_year_reservations = pure_reservations.filter(commitment_term_years=1)
        three_year_reservations = pure_reservations.filter(commitment_term_years=3)

        # Calculate 1-year metrics
        one_year_totals = one_year_reservations.aggregate(
            count=Count('id'),
            total_annual=Sum('potential_savings'),
            total_commitment=Sum('commitment_savings')
        )

        # Calculate 3-year metrics
        three_year_totals = three_year_reservations.aggregate(
            count=Count('id'),
            total_annual=Sum('potential_savings'),
            total_commitment=Sum('commitment_savings')
        )

        # Get top recommendations for each term
        top_1y = list(one_year_reservations.order_by('-commitment_savings')[:10])
        top_3y = list(three_year_reservations.order_by('-commitment_savings')[:10])

        # Group by resource type for each term
        one_year_by_type = one_year_reservations.values('reservation_type').annotate(
            count=Count('id'),
            annual_savings=Sum('potential_savings'),
            commitment_savings=Sum('commitment_savings')
        ).order_by('-annual_savings')

        three_year_by_type = three_year_reservations.values('reservation_type').annotate(
            count=Count('id'),
            annual_savings=Sum('potential_savings'),
            commitment_savings=Sum('commitment_savings')
        ).order_by('-annual_savings')

        return {
            'has_pure_reservations': pure_reservations.exists(),
            'total_count': pure_reservations.count(),

            # 1-Year Reservations
            'one_year': {
                'count': one_year_totals['count'] or 0,
                'total_annual_savings': float(one_year_totals['total_annual'] or 0),
                'total_commitment_savings': float(one_year_totals['total_commitment'] or 0),
                'average_annual_savings': (
                    float(one_year_totals['total_annual'] / one_year_totals['count'])
                    if one_year_totals['count'] else 0
                ),
                'by_type': [
                    {
                        'type': item['reservation_type'],
                        'type_display': self._get_reservation_type_display(item['reservation_type']),
                        'count': item['count'],
                        'annual_savings': float(item['annual_savings'] or 0),
                        'commitment_savings': float(item['commitment_savings'] or 0),
                    }
                    for item in one_year_by_type
                ],
                'top_recommendations': top_1y,
            },

            # 3-Year Reservations
            'three_year': {
                'count': three_year_totals['count'] or 0,
                'total_annual_savings': float(three_year_totals['total_annual'] or 0),
                'total_commitment_savings': float(three_year_totals['total_commitment'] or 0),
                'average_annual_savings': (
                    float(three_year_totals['total_annual'] / three_year_totals['count'])
                    if three_year_totals['count'] else 0
                ),
                'by_type': [
                    {
                        'type': item['reservation_type'],
                        'type_display': self._get_reservation_type_display(item['reservation_type']),
                        'count': item['count'],
                        'annual_savings': float(item['annual_savings'] or 0),
                        'commitment_savings': float(item['commitment_savings'] or 0),
                    }
                    for item in three_year_by_type
                ],
                'top_recommendations': top_3y,
            },
        }

    def get_savings_plan_metrics(self):
        """
        Get metrics for PURE SAVINGS PLANS ONLY (excluding traditional reservations).

        Savings Plans are flexible compute commitments across VM families.

        Version 2.0 - Enhanced Multi-Dimensional Analysis

        Returns:
            dict: Savings Plan specific metrics
        """
        from django.db.models import F, Sum, Count, DecimalField, Case, When

        # Filter only pure Savings Plans
        savings_plans = self.recommendations.filter(
            commitment_category='pure_savings_plan'
        ).annotate(
            commitment_savings=Case(
                When(
                    commitment_term_years__isnull=False,
                    potential_savings__isnull=False,
                    then=F('potential_savings') * F('commitment_term_years')
                ),
                default=F('potential_savings'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )

        count = savings_plans.count()

        if count == 0:
            return {
                'has_savings_plans': False,
                'count': 0,
                'total_annual_savings': 0,
                'total_commitment_savings': 0,
                'average_annual_savings': 0,
                'by_term': [],
                'top_recommendations': [],
            }

        # Calculate totals
        totals = savings_plans.aggregate(
            total_annual=Sum('potential_savings'),
            total_commitment=Sum('commitment_savings')
        )

        # Group by commitment term
        by_term = savings_plans.values('commitment_term_years').annotate(
            count=Count('id'),
            annual_savings=Sum('potential_savings'),
            commitment_savings=Sum('commitment_savings')
        ).order_by('commitment_term_years')

        # Get top recommendations
        top_recommendations = list(savings_plans.order_by('-commitment_savings')[:10])

        return {
            'has_savings_plans': True,
            'count': count,
            'total_annual_savings': float(totals['total_annual'] or 0),
            'total_commitment_savings': float(totals['total_commitment'] or 0),
            'average_annual_savings': float(totals['total_annual'] / count) if count else 0,
            'by_term': [
                {
                    'term_years': item['commitment_term_years'],
                    'term_display': f"{item['commitment_term_years']}-Year" if item['commitment_term_years'] else 'Unspecified',
                    'count': item['count'],
                    'annual_savings': float(item['annual_savings'] or 0),
                    'commitment_savings': float(item['commitment_savings'] or 0),
                }
                for item in by_term
            ],
            'top_recommendations': top_recommendations,
        }

    def get_combined_commitment_metrics(self):
        """
        Get metrics for COMBINED COMMITMENTS (Savings Plans + Reservations together).

        Some recommendations suggest combining both for optimal savings.

        Version 2.0 - Enhanced Multi-Dimensional Analysis

        Returns:
            dict: Combined commitment metrics separated by term
        """
        from django.db.models import F, Sum, Count, DecimalField, Case, When, Q

        # Filter combined commitments
        combined = self.recommendations.filter(
            Q(commitment_category='combined_sp_1y') |
            Q(commitment_category='combined_sp_3y')
        ).annotate(
            commitment_savings=Case(
                When(
                    commitment_term_years__isnull=False,
                    potential_savings__isnull=False,
                    then=F('potential_savings') * F('commitment_term_years')
                ),
                default=F('potential_savings'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )

        # Separate by term
        combined_1y = combined.filter(commitment_category='combined_sp_1y')
        combined_3y = combined.filter(commitment_category='combined_sp_3y')

        # Calculate metrics for each
        totals_1y = combined_1y.aggregate(
            count=Count('id'),
            total_annual=Sum('potential_savings'),
            total_commitment=Sum('commitment_savings')
        )

        totals_3y = combined_3y.aggregate(
            count=Count('id'),
            total_annual=Sum('potential_savings'),
            total_commitment=Sum('commitment_savings')
        )

        # Get top recommendations
        top_1y = list(combined_1y.order_by('-commitment_savings')[:5])
        top_3y = list(combined_3y.order_by('-commitment_savings')[:5])

        return {
            'has_combined_commitments': combined.exists(),
            'total_count': combined.count(),

            # Savings Plan + 1-Year Reservations
            'sp_plus_1y': {
                'count': totals_1y['count'] or 0,
                'total_annual_savings': float(totals_1y['total_annual'] or 0),
                'total_commitment_savings': float(totals_1y['total_commitment'] or 0),
                'top_recommendations': top_1y,
            },

            # Savings Plan + 3-Year Reservations
            'sp_plus_3y': {
                'count': totals_3y['count'] or 0,
                'total_annual_savings': float(totals_3y['total_annual'] or 0),
                'total_commitment_savings': float(totals_3y['total_commitment'] or 0),
                'top_recommendations': top_3y,
            },
        }

    def _get_reservation_type_display(self, reservation_type):
        """Helper to get human-readable reservation type."""
        type_map = {
            'reserved_instance': 'Reserved VM Instance',
            'savings_plan': 'Savings Plan',
            'reserved_capacity': 'Reserved Capacity',
            'other': 'Other Reservation',
        }
        return type_map.get(reservation_type, reservation_type or 'Unknown')

    def group_by_category(self):
        """
        Group recommendations by category.

        Returns:
            dict: Dictionary with category as key and list of recommendations as value
        """
        categories = {}
        for rec in self.recommendations.select_related():
            cat = rec.get_category_display()
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rec)
        return categories

    def save_html(self, content):
        """
        Save HTML content to Azure Blob Storage using Django's storage backend.

        Args:
            content: HTML content string

        Returns:
            str: Relative path to saved file (for Django FileField)

        Raises:
            Exception: If file save fails
        """
        # Generate filename
        filename = f"{self.report.id}_{self.report.report_type}.html"

        # Determine file path (relative to storage root)
        relative_path = os.path.join('reports', 'html', filename)

        # Delete existing file if it exists
        if default_storage.exists(relative_path):
            logger.info(f"Deleting existing HTML file: {relative_path}")
            default_storage.delete(relative_path)

        # Save file to Azure Blob Storage using Django's storage backend
        logger.info(f"Saving HTML file to Azure Blob Storage: {relative_path}")
        saved_path = default_storage.save(
            relative_path,
            ContentFile(content.encode('utf-8'))
        )

        logger.info(f"HTML file saved successfully: {saved_path}")

        # Return the saved path for Django FileField
        return saved_path

    def generate_pdf(self):
        """
        Generate PDF using Playwright (primary) with WeasyPrint fallback.

        Tries Playwright first for best rendering quality. If Playwright fails,
        falls back to WeasyPrint for reliable PDF generation.

        Returns:
            str: Relative path to generated PDF file (for Django FileField)

        Raises:
            Exception: If both PDF engines fail
        """
        logger.info(f"Starting PDF generation for report {self.report.id}")

        # Try Playwright first (primary method)
        try:
            logger.info(f"Attempting PDF generation with Playwright (primary method)")
            return self.generate_pdf_with_playwright()
        except Exception as playwright_error:
            logger.warning(
                f"Playwright PDF generation failed for report {self.report.id}: {str(playwright_error)}"
            )
            logger.info(f"Falling back to WeasyPrint...")

            # Fallback to WeasyPrint
            try:
                logger.info(f"Attempting PDF generation with WeasyPrint (fallback method)")
                return self.generate_pdf_with_weasyprint()
            except Exception as weasyprint_error:
                logger.error(
                    f"Both PDF engines failed for report {self.report.id}. "
                    f"Playwright error: {str(playwright_error)}, "
                    f"WeasyPrint error: {str(weasyprint_error)}"
                )
                raise Exception(
                    f"PDF generation failed with both engines. "
                    f"Playwright: {str(playwright_error)}. "
                    f"WeasyPrint: {str(weasyprint_error)}"
                )

    def generate_pdf_with_playwright(self):
        """
        Generate PDF using Playwright headless browser and save to Azure Blob Storage.

        This method renders the HTML report with all Chart.js visualizations
        and modern CSS, then captures it as a PDF using a headless browser.

        Returns:
            str: Relative path to generated PDF file (for Django FileField)

        Raises:
            Exception: If PDF generation fails
        """
        import tempfile

        try:
            from apps.reports.services.pdf_service import SyncPlaywrightPDFGenerator

            logger.info(f"Generating PDF with Playwright for {self.report.id}")

            # Generate PDF filename and path
            pdf_filename = f"{self.report.id}_{self.report.report_type}.pdf"
            pdf_relative_path = os.path.join('reports', 'pdf', pdf_filename)

            # Get context data - use the enhanced HTML template (not PDF-specific)
            context = self.get_base_context()
            context.update(self.get_context_data())

            # Render HTML template (the one with Chart.js)
            html_template = self.get_template_name()
            logger.info(f"Rendering HTML template for PDF: {html_template}")
            html_content = render_to_string(html_template, context)

            # Configure PDF options (use snake_case for Python Playwright API)
            pdf_options = {
                'format': 'A4',
                'print_background': True,
                'display_header_footer': True,
                'header_template': self._get_pdf_header_template(),
                'footer_template': self._get_pdf_footer_template(),
                'margin': {
                    'top': '25mm',
                    'right': '15mm',
                    'bottom': '25mm',
                    'left': '15mm',
                },
                'prefer_css_page_size': False,
            }

            # Generate PDF to a temporary file first
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp_file:
                temp_pdf_path = tmp_file.name

            logger.info(f"Converting HTML to PDF with Playwright: {temp_pdf_path}")
            generator = SyncPlaywrightPDFGenerator(headless=True, timeout=30000)
            generator.generate_pdf_from_html(
                html_content=html_content,
                output_path=temp_pdf_path,
                options=pdf_options,
                wait_for_charts=True,
                wait_for_fonts=True,
            )

            logger.info(f"PDF generated successfully in temporary file")

            # Read the temporary PDF file and upload to Azure Blob Storage
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()

            # Delete existing file if it exists
            if default_storage.exists(pdf_relative_path):
                logger.info(f"Deleting existing PDF file: {pdf_relative_path}")
                default_storage.delete(pdf_relative_path)

            # Save to Azure Blob Storage
            logger.info(f"Saving PDF file to Azure Blob Storage: {pdf_relative_path}")
            saved_path = default_storage.save(
                pdf_relative_path,
                ContentFile(pdf_content)
            )

            # Clean up temporary file
            try:
                os.unlink(temp_pdf_path)
                logger.info(f"Temporary PDF file deleted: {temp_pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_pdf_path}: {e}")

            logger.info(f"PDF report saved successfully to Azure Blob Storage: {saved_path}")

            # Return the saved path for Django FileField
            return saved_path

        except ImportError as e:
            logger.error(f"Playwright not installed: {str(e)}")
            raise Exception(
                "Playwright is required for PDF generation. "
                "Install it with: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            logger.error(f"Failed to generate PDF report with Playwright: {str(e)}")
            raise

    def generate_pdf_with_weasyprint(self):
        """
        Generate PDF using PDF-optimized template with WeasyPrint and save to Azure Blob Storage.

        This is the legacy method using WeasyPrint for PDF generation.
        It uses a PDF-specific template without Chart.js.

        Returns:
            str: Relative path to generated PDF file (for Django FileField)

        Raises:
            Exception: If PDF generation fails
        """
        import tempfile

        try:
            # Import WeasyPrint
            from weasyprint import HTML
            from weasyprint.text.fonts import FontConfiguration

            logger.info(f"Generating PDF report with WeasyPrint for {self.report.id}")

            # Generate PDF filename and path
            pdf_filename = f"{self.report.id}_{self.report.report_type}.pdf"
            pdf_relative_path = os.path.join('reports', 'pdf', pdf_filename)

            # Get context data using PDF template
            context = self.get_base_context()
            context.update(self.get_context_data())

            # Render PDF-specific template
            pdf_template = self.get_pdf_template_name()
            logger.info(f"Rendering PDF template: {pdf_template}")
            html_content = render_to_string(pdf_template, context)

            # Configure fonts
            font_config = FontConfiguration()

            # Generate PDF to a temporary file first
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp_file:
                temp_pdf_path = tmp_file.name
                logger.info(f"Generating PDF to temporary file: {temp_pdf_path}")

                # Generate PDF from rendered HTML
                html_doc = HTML(string=html_content)
                html_doc.write_pdf(temp_pdf_path, font_config=font_config)

            logger.info(f"PDF generated successfully in temporary file")

            # Read the temporary PDF file and upload to Azure Blob Storage
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()

            # Delete existing file if it exists
            if default_storage.exists(pdf_relative_path):
                logger.info(f"Deleting existing PDF file: {pdf_relative_path}")
                default_storage.delete(pdf_relative_path)

            # Save to Azure Blob Storage
            logger.info(f"Saving PDF file to Azure Blob Storage: {pdf_relative_path}")
            saved_path = default_storage.save(
                pdf_relative_path,
                ContentFile(pdf_content)
            )

            # Clean up temporary file
            try:
                os.unlink(temp_pdf_path)
                logger.info(f"Temporary PDF file deleted: {temp_pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_pdf_path}: {e}")

            logger.info(f"PDF report saved successfully to Azure Blob Storage: {saved_path}")

            # Return the saved path for Django FileField
            return saved_path

        except ImportError as e:
            logger.error(f"WeasyPrint not installed: {str(e)}")
            raise Exception(
                "WeasyPrint is required for PDF generation. "
                "Install it with: pip install weasyprint"
            )
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {str(e)}")
            raise

    def _get_pdf_header_template(self):
        """
        Get HTML template for PDF header.

        Returns:
            str: HTML string for header
        """
        return """
        <div style="width: 100%; font-size: 9px; padding: 10px 15px;
                    border-bottom: 1px solid #0078D4; color: #333;
                    display: flex; justify-content: space-between;">
            <span style="font-weight: bold;">Azure Advisor Report</span>
            <span class="date"></span>
        </div>
        """

    def _get_pdf_footer_template(self):
        """
        Get HTML template for PDF footer.

        Returns:
            str: HTML string for footer
        """
        return """
        <div style="width: 100%; font-size: 9px; padding: 10px 15px;
                    border-top: 1px solid #0078D4; color: #666;
                    text-align: center;">
            <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
            <span style="margin-left: 20px;">Generated with Azure Advisor Reports Platform</span>
        </div>
        """
