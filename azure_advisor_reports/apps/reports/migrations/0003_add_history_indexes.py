"""
Add composite indexes for history filtering optimization.

This migration adds composite indexes to support the new history endpoints
for faster filtering by report_type, status, and created_at combinations.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_add_performance_indexes'),
    ]

    operations = [
        # Composite index for multi-field history filtering
        migrations.AddIndex(
            model_name='report',
            index=models.Index(
                fields=['report_type', 'status', '-created_at'],
                name='idx_report_type_status_date'
            ),
        ),
    ]
