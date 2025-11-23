# Manual migration to ensure is_reservation_recommendation has a database-level default

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_add_reservation_fields'),
    ]

    operations = [
        # First, update any existing NULL values to False
        migrations.RunSQL(
            sql="UPDATE recommendations SET is_reservation_recommendation = FALSE WHERE is_reservation_recommendation IS NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Then alter the field to set NOT NULL with default at database level
        migrations.AlterField(
            model_name='recommendation',
            name='is_reservation_recommendation',
            field=models.BooleanField(
                default=False,
                help_text='Indicates if this is a reservation/savings plan recommendation'
            ),
        ),
    ]
