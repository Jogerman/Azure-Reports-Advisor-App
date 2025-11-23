"""
Django management command to analyze database performance
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.monitoring.database_optimization import (
    QueryAnalyzer,
    apply_recommended_indexes,
    print_optimization_tips
)
import json


class Command(BaseCommand):
    help = 'Analyze database performance and provide optimization recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply-indexes',
            action='store_true',
            help='Apply recommended indexes to database',
        )
        parser.add_argument(
            '--show-tips',
            action='store_true',
            help='Show optimization tips',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'json'],
            default='text',
            help='Output format',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Database Performance Analysis ==='))
        self.stdout.write(f'Time: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

        analyzer = QueryAnalyzer()

        # Get table statistics
        self.stdout.write(self.style.MIGRATE_HEADING('\n1. Table Statistics'))
        self.stdout.write(self.style.MIGRATE_LABEL('-' * 80))

        table_stats = analyzer.get_table_stats()

        if options['format'] == 'json':
            self.stdout.write(json.dumps(table_stats, indent=2, default=str))
        else:
            for stat in table_stats[:10]:  # Top 10 tables
                self.stdout.write(
                    f"\nTable: {stat['tablename']}"
                )
                self.stdout.write(f"  Live tuples: {stat['live_tuples']:,}")
                self.stdout.write(f"  Dead tuples: {stat['dead_tuples']:,}")
                self.stdout.write(f"  Inserts: {stat['inserts']:,}")
                self.stdout.write(f"  Updates: {stat['updates']:,}")
                self.stdout.write(f"  Deletes: {stat['deletes']:,}")

                if stat['dead_tuples'] > stat['live_tuples'] * 0.1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ High dead tuple ratio! Consider running VACUUM"
                        )
                    )

        # Get index usage
        self.stdout.write(self.style.MIGRATE_HEADING('\n\n2. Index Usage Statistics'))
        self.stdout.write(self.style.MIGRATE_LABEL('-' * 80))

        index_usage = analyzer.get_index_usage()
        unused_indexes = [idx for idx in index_usage if idx['index_scans'] == 0]

        if options['format'] == 'json':
            self.stdout.write(json.dumps(index_usage, indent=2, default=str))
        else:
            if unused_indexes:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nFound {len(unused_indexes)} unused indexes:"
                    )
                )
                for idx in unused_indexes[:5]:
                    self.stdout.write(
                        f"  - {idx['tablename']}.{idx['indexname']} ({idx['index_size']})"
                    )
            else:
                self.stdout.write(self.style.SUCCESS("\n✓ All indexes are being used"))

            # Show most used indexes
            most_used = sorted(index_usage, key=lambda x: x['index_scans'], reverse=True)[:5]
            self.stdout.write("\nMost used indexes:")
            for idx in most_used:
                self.stdout.write(
                    f"  - {idx['tablename']}.{idx['indexname']}: "
                    f"{idx['index_scans']:,} scans"
                )

        # Check for missing indexes
        self.stdout.write(self.style.MIGRATE_HEADING('\n\n3. Potential Missing Indexes'))
        self.stdout.write(self.style.MIGRATE_LABEL('-' * 80))

        missing_indexes = analyzer.get_missing_indexes()

        if options['format'] == 'json':
            self.stdout.write(json.dumps(missing_indexes, indent=2, default=str))
        else:
            if missing_indexes:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nFound {len(missing_indexes)} tables with high sequential scans:"
                    )
                )
                for stat in missing_indexes[:5]:
                    self.stdout.write(f"\nTable: {stat['tablename']}")
                    self.stdout.write(f"  Sequential scans: {stat['sequential_scans']:,}")
                    self.stdout.write(f"  Index scans: {stat['index_scans']:,}")
                    self.stdout.write(f"  Index usage: {stat['index_usage_percentage']}%")

                    if stat['index_usage_percentage'] < 50:
                        self.stdout.write(
                            self.style.WARNING(
                                "  ⚠ Consider adding indexes to frequently queried columns"
                            )
                        )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✓ All tables have good index usage"
                    )
                )

        # Apply indexes if requested
        if options['apply_indexes']:
            self.stdout.write(self.style.MIGRATE_HEADING('\n\n4. Applying Recommended Indexes'))
            self.stdout.write(self.style.MIGRATE_LABEL('-' * 80))
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ This operation may take several minutes and lock tables."
                )
            )
            confirm = input("Continue? (yes/no): ")

            if confirm.lower() == 'yes':
                apply_recommended_indexes()
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✓ Recommended indexes applied successfully"
                    )
                )
            else:
                self.stdout.write("\nOperation cancelled")

        # Show optimization tips
        if options['show_tips']:
            self.stdout.write(self.style.MIGRATE_HEADING('\n\n5. Optimization Tips'))
            self.stdout.write(self.style.MIGRATE_LABEL('-' * 80))
            print_optimization_tips()

        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING('\n\n=== Summary ==='))
        self.stdout.write(self.style.MIGRATE_LABEL('-' * 80))
        self.stdout.write(f"\nTotal tables analyzed: {len(table_stats)}")
        self.stdout.write(f"Total indexes: {len(index_usage)}")
        self.stdout.write(f"Unused indexes: {len(unused_indexes)}")
        self.stdout.write(f"Tables needing indexes: {len(missing_indexes)}")

        if unused_indexes or missing_indexes:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ Action required: Review and optimize database indexes"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✓ Database indexes are optimized"
                )
            )

        self.stdout.write('\n')
