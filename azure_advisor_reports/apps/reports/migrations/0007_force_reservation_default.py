# Migration to force database-level default for is_reservation_recommendation

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_set_reservation_field_default'),
    ]

    operations = [
        # Set database-level default for is_reservation_recommendation
        migrations.RunSQL(
            sql=[
                # First, update any NULL values to False
                "UPDATE recommendations SET is_reservation_recommendation = FALSE WHERE is_reservation_recommendation IS NULL;",
                # Set NOT NULL constraint with default
                "ALTER TABLE recommendations ALTER COLUMN is_reservation_recommendation SET DEFAULT FALSE;",
                "ALTER TABLE recommendations ALTER COLUMN is_reservation_recommendation SET NOT NULL;",
            ],
            reverse_sql=[
                "ALTER TABLE recommendations ALTER COLUMN is_reservation_recommendation DROP NOT NULL;",
                "ALTER TABLE recommendations ALTER COLUMN is_reservation_recommendation DROP DEFAULT;",
            ],
        ),
    ]
