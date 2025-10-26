"""
Django management command to initialize analytics module.

Usage:
    python manage.py initialize_analytics
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.analytics.models import DashboardMetrics
from apps.analytics.services import AnalyticsService


class Command(BaseCommand):
    help = 'Initialize analytics module with initial metrics and cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-metrics',
            action='store_true',
            help='Skip calculating dashboard metrics',
        )
        parser.add_argument(
            '--skip-cache',
            action='store_true',
            help='Skip pre-warming cache',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to calculate historical metrics (default: 7)',
        )

    def handle(self, *args, **options):
        """Execute the initialization process."""
        self.stdout.write(self.style.SUCCESS('Initializing Analytics Module...'))
        self.stdout.write('')

        # Step 1: Calculate Dashboard Metrics
        if not options['skip_metrics']:
            self.calculate_dashboard_metrics(options['days'])
        else:
            self.stdout.write(self.style.WARNING('Skipping dashboard metrics calculation'))

        # Step 2: Pre-warm Cache
        if not options['skip_cache']:
            self.prewarm_cache()
        else:
            self.stdout.write(self.style.WARNING('Skipping cache pre-warming'))

        # Step 3: Verify Setup
        self.verify_setup()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Analytics module initialized successfully!'))
        self.stdout.write('')
        self.print_next_steps()

    def calculate_dashboard_metrics(self, days):
        """Calculate dashboard metrics for the past N days."""
        self.stdout.write('Step 1: Calculating Dashboard Metrics...')

        from datetime import timedelta

        today = timezone.now().date()
        metrics_created = 0

        with transaction.atomic():
            for i in range(days):
                target_date = today - timedelta(days=i)

                # Calculate daily metrics
                daily_metrics = DashboardMetrics.calculate_for_date(
                    target_date=target_date,
                    period_type='daily'
                )
                metrics_created += 1

                self.stdout.write(
                    f'  - Calculated daily metrics for {target_date}: '
                    f'{daily_metrics.total_reports} reports, '
                    f'{daily_metrics.active_clients} active clients'
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {metrics_created} daily metrics'))

        # Calculate weekly metrics
        weekly_metrics = DashboardMetrics.calculate_for_date(
            target_date=today,
            period_type='weekly'
        )
        self.stdout.write(f'  - Calculated weekly metrics: {weekly_metrics}')

        # Calculate monthly metrics
        monthly_metrics = DashboardMetrics.calculate_for_date(
            target_date=today,
            period_type='monthly'
        )
        self.stdout.write(f'  - Calculated monthly metrics: {monthly_metrics}')

        self.stdout.write('')

    def prewarm_cache(self):
        """Pre-warm the analytics cache."""
        self.stdout.write('Step 2: Pre-warming Cache...')

        try:
            # Dashboard metrics
            self.stdout.write('  - Caching dashboard metrics...')
            metrics = AnalyticsService.get_dashboard_metrics()
            self.stdout.write(
                f'    Total recommendations: {metrics.get("totalRecommendations", 0)}'
            )

            # Category distribution
            self.stdout.write('  - Caching category distribution...')
            categories = AnalyticsService.get_category_distribution()
            self.stdout.write(f'    Categories: {len(categories.get("categories", []))}')

            # Trend data
            for days in [7, 30, 90]:
                self.stdout.write(f'  - Caching {days}-day trend data...')
                trends = AnalyticsService.get_trend_data(days=days)
                self.stdout.write(f'    Data points: {len(trends.get("data", []))}')

            # Recent activity
            self.stdout.write('  - Caching recent activity...')
            activity = AnalyticsService.get_recent_activity(limit=10)
            self.stdout.write(f'    Activities: {len(activity)}')

            # Business impact
            self.stdout.write('  - Caching business impact distribution...')
            impact = AnalyticsService.get_business_impact_distribution()
            self.stdout.write(f'    Impact levels: {len(impact.get("distribution", []))}')

            # Activity summary
            self.stdout.write('  - Caching activity summary...')
            summary = AnalyticsService.get_activity_summary(days=7)
            self.stdout.write(
                f'    Total activities: {summary.get("total_activities", 0)}'
            )

            self.stdout.write(self.style.SUCCESS('  Cache pre-warmed successfully'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Error pre-warming cache: {str(e)}')
            )

        self.stdout.write('')

    def verify_setup(self):
        """Verify the analytics setup."""
        self.stdout.write('Step 3: Verifying Setup...')

        checks = []

        # Check 1: Middleware configured
        from django.conf import settings
        middleware_check = 'apps.analytics.middleware.UserActivityTrackingMiddleware' in settings.MIDDLEWARE
        checks.append(('Middleware configured', middleware_check))

        # Check 2: Database tables exist
        try:
            DashboardMetrics.objects.exists()
            db_check = True
        except Exception:
            db_check = False
        checks.append(('Database tables exist', db_check))

        # Check 3: Redis/Cache available
        try:
            from django.core.cache import cache
            cache.set('analytics_test', 'value', 1)
            cache_value = cache.get('analytics_test')
            cache_check = cache_value == 'value'
        except Exception:
            cache_check = False
        checks.append(('Cache backend available', cache_check))

        # Check 4: Celery configuration
        try:
            from apps.analytics.celery_config import ANALYTICS_CELERY_BEAT_SCHEDULE
            celery_check = len(ANALYTICS_CELERY_BEAT_SCHEDULE) > 0
        except Exception:
            celery_check = False
        checks.append(('Celery configuration available', celery_check))

        # Print results
        for check_name, passed in checks:
            if passed:
                self.stdout.write(
                    f'  {self.style.SUCCESS("✓")} {check_name}'
                )
            else:
                self.stdout.write(
                    f'  {self.style.ERROR("✗")} {check_name}'
                )

        all_passed = all(passed for _, passed in checks)

        if all_passed:
            self.stdout.write(self.style.SUCCESS('  All checks passed!'))
        else:
            self.stdout.write(
                self.style.WARNING('  Some checks failed - review configuration')
            )

        self.stdout.write('')

    def print_next_steps(self):
        """Print next steps for the user."""
        self.stdout.write(self.style.HTTP_INFO('Next Steps:'))
        self.stdout.write('')
        self.stdout.write('1. Start Celery worker and beat scheduler:')
        self.stdout.write('   celery -A azure_advisor_reports worker --beat --loglevel=info')
        self.stdout.write('')
        self.stdout.write('2. Test the analytics endpoints:')
        self.stdout.write('   GET /api/v1/analytics/dashboard/')
        self.stdout.write('   GET /api/v1/analytics/user-activity/')
        self.stdout.write('   GET /api/v1/analytics/system-health/')
        self.stdout.write('')
        self.stdout.write('3. Monitor Celery tasks in Flower (optional):')
        self.stdout.write('   celery -A azure_advisor_reports flower')
        self.stdout.write('   http://localhost:5555')
        self.stdout.write('')
        self.stdout.write('4. Review documentation:')
        self.stdout.write('   apps/analytics/README.md')
        self.stdout.write('   apps/analytics/ANALYTICS_API_DOCUMENTATION.md')
        self.stdout.write('')
