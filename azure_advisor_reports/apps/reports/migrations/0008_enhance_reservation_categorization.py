# Generated migration for Enhanced Reservation & Saving Plans Analysis

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_force_reservation_default'),
    ]

    operations = [
        # Add new boolean field for Savings Plan identification
        migrations.AddField(
            model_name='recommendation',
            name='is_savings_plan',
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text="TRUE if this is a Savings Plan (Azure Compute Savings Plan), "
                          "FALSE if traditional reservation (VM, capacity, etc.)"
            ),
        ),

        # Add new categorization field
        migrations.AddField(
            model_name='recommendation',
            name='commitment_category',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('pure_reservation_1y', 'Pure Reservation - 1 Year'),
                    ('pure_reservation_3y', 'Pure Reservation - 3 Years'),
                    ('pure_savings_plan', 'Pure Savings Plan'),
                    ('combined_sp_1y', 'Savings Plan + 1Y Reservation'),
                    ('combined_sp_3y', 'Savings Plan + 3Y Reservation'),
                    ('uncategorized', 'Uncategorized'),
                ],
                default='uncategorized',
                db_index=True,
                help_text="Granular categorization for multi-dimensional analysis"
            ),
        ),

        # Add indexes to existing fields for performance
        migrations.AlterField(
            model_name='recommendation',
            name='is_reservation_recommendation',
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text="Indicates if this is a reservation/savings plan recommendation"
            ),
        ),
        migrations.AlterField(
            model_name='recommendation',
            name='reservation_type',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('reserved_instance', 'Reserved VM Instance'),
                    ('savings_plan', 'Savings Plan'),
                    ('reserved_capacity', 'Reserved Capacity'),
                    ('other', 'Other Reservation'),
                ],
                null=True,
                blank=True,
                db_index=True,
                help_text="Specific type of reservation or commitment"
            ),
        ),
        migrations.AlterField(
            model_name='recommendation',
            name='commitment_term_years',
            field=models.IntegerField(
                null=True,
                blank=True,
                choices=[(1, '1 Year'), (3, '3 Years')],
                db_index=True,
                help_text="Duration of the reservation commitment"
            ),
        ),
    ]
