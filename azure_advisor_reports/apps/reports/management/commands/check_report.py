"""
Management command to check a specific report's categorization status.

Usage:
    python manage.py check_report <report_id>
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from apps.reports.models import Report, Recommendation


class Command(BaseCommand):
    help = 'Check a specific report\'s categorization status'

    def add_arguments(self, parser):
        parser.add_argument(
            'report_id',
            type=str,
            help='The UUID of the report to check'
        )

    def handle(self, *args, **options):
        report_id = options['report_id']

        self.stdout.write('=' * 80)
        self.stdout.write(f'REPORT DIAGNOSTIC: {report_id}')
        self.stdout.write('=' * 80)
        self.stdout.write('')

        try:
            report = Report.objects.get(id=report_id)

            # Basic info
            self.stdout.write(self.style.SUCCESS('📋 REPORT DETAILS:'))
            self.stdout.write(f'   ID: {report.id}')
            self.stdout.write(f'   Title: {report.title if report.title else "(No title)"}')
            self.stdout.write(f'   Type: {report.report_type}')
            self.stdout.write(f'   Status: {report.status}')
            self.stdout.write(f'   Data Source: {report.data_source}')
            self.stdout.write(f'   Created: {report.created_at}')
            self.stdout.write('')

            # Recommendation counts
            total_recs = report.recommendations.count()
            self.stdout.write(self.style.SUCCESS(f'📊 RECOMMENDATIONS: {total_recs}'))
            self.stdout.write('')

            # Check categorization
            categories = report.recommendations.values('commitment_category').annotate(
                count=Count('id')
            ).order_by('-count')

            self.stdout.write(self.style.SUCCESS('🏷️  CATEGORIZATION:'))
            for cat in categories:
                category = cat['commitment_category'] or 'NULL'
                count = cat['count']
                self.stdout.write(f'   {category:35s}: {count:3} recommendations')
            self.stdout.write('')

            # Check if we have categorized data for sections
            pure_res = report.recommendations.filter(
                Q(commitment_category='pure_reservation_1y') |
                Q(commitment_category='pure_reservation_3y')
            ).count()

            savings = report.recommendations.filter(
                commitment_category='pure_savings_plan'
            ).count()

            combined = report.recommendations.filter(
                Q(commitment_category='combined_sp_1y') |
                Q(commitment_category='combined_sp_3y')
            ).count()

            uncategorized = report.recommendations.filter(
                Q(commitment_category='uncategorized') | Q(commitment_category__isnull=True)
            ).count()

            self.stdout.write(self.style.SUCCESS('✅ CATEGORIZATION STATUS:'))
            self.stdout.write(f'   Pure Reservations:  {pure_res:3} recommendations')
            self.stdout.write(f'   Savings Plans:      {savings:3} recommendations')
            self.stdout.write(f'   Combined:           {combined:3} recommendations')
            self.stdout.write(f'   Uncategorized:      {uncategorized:3} recommendations')
            self.stdout.write('')

            # Show sample recommendations
            self.stdout.write(self.style.SUCCESS('🔍 SAMPLE RECOMMENDATIONS (first 3):'))
            for i, rec in enumerate(report.recommendations.all()[:3], 1):
                self.stdout.write(f'   {i}. Category: {rec.commitment_category or "NULL"}')
                self.stdout.write(f'      Text: {rec.recommendation[:80]}...')
                self.stdout.write(f'      Savings: ${rec.estimated_monthly_savings or 0:,.2f}/month')
                self.stdout.write('')

            # DIAGNOSIS
            self.stdout.write('=' * 80)
            self.stdout.write(self.style.SUCCESS('🔍 DIAGNOSIS:'))
            self.stdout.write('=' * 80)
            self.stdout.write('')

            if report.report_type != 'cost':
                self.stdout.write(self.style.WARNING('⚠️  ISSUE: This is NOT a cost optimization report!'))
                self.stdout.write(f'   Report Type: {report.report_type.upper()}')
                self.stdout.write('')
                self.stdout.write('   Savings/Reservations sections ONLY appear in COST reports.')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('💡 SOLUTION:'))
                self.stdout.write('   Generate a new report with type="cost" to see Savings/Reservations sections.')
                self.stdout.write('')
                self.stdout.write('   Available report types:')
                self.stdout.write('      - cost: Cost Optimization (shows Savings/Reservations)')
                self.stdout.write('      - detailed: Detailed Report')
                self.stdout.write('      - executive: Executive Summary')
                self.stdout.write('      - security: Security Assessment')
                self.stdout.write('      - operations: Operational Excellence')
            elif uncategorized == total_recs:
                self.stdout.write(self.style.ERROR('❌ ISSUE: All recommendations are UNCATEGORIZED!'))
                self.stdout.write('')
                self.stdout.write('   ReservationAnalyzer didn\'t detect any reservation/savings plan keywords.')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('💡 POSSIBLE CAUSES:'))
                self.stdout.write('   1. CSV doesn\'t contain reservation/savings plan recommendations')
                self.stdout.write('   2. Keywords don\'t match ReservationAnalyzer patterns')
                self.stdout.write('')
                self.stdout.write('   Check if CSV contains terms like:')
                self.stdout.write('      - "reserved instance", "reserved vm", "reservation"')
                self.stdout.write('      - "savings plan", "compute savings plan"')
                self.stdout.write('      - "1 year", "3 year", "commitment"')
            elif pure_res > 0 or savings > 0 or combined > 0:
                self.stdout.write(self.style.SUCCESS('✅ Database has categorized recommendations!'))
                self.stdout.write('')
                self.stdout.write(f'   - {pure_res} Pure Reservation recommendations')
                self.stdout.write(f'   - {savings} Savings Plan recommendations')
                self.stdout.write(f'   - {combined} Combined recommendations')
                self.stdout.write('')
                self.stdout.write('   Savings/Reservations sections SHOULD appear in the report.')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('💡 If tables still don\'t show:'))
                self.stdout.write('   1. Try hard refresh (Ctrl+Shift+R or Cmd+Shift+R)')
                self.stdout.write('   2. Check browser console for JavaScript errors')
                self.stdout.write('   3. Check if sections are in HTML but hidden (inspect element)')
                self.stdout.write('   4. Regenerate the report (old cached version may be showing)')
            else:
                self.stdout.write(self.style.WARNING('⚠️  No categorized reservations/savings plans found'))
                self.stdout.write('')
                self.stdout.write('   All recommendations are in "other" categories.')

            self.stdout.write('')
            self.stdout.write('=' * 80)
            self.stdout.write(self.style.SUCCESS('Diagnostic completed!'))
            self.stdout.write('=' * 80)

        except Report.DoesNotExist:
            raise CommandError(f'Report with ID "{report_id}" not found in database!')
        except Exception as e:
            raise CommandError(f'Error checking report: {str(e)}')
