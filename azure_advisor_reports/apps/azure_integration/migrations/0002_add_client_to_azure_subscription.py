# Generated manually for azure_integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('azure_integration', '0001_initial'),
    ]

    operations = [
        # Step 1: Rename client_id to azure_client_id
        migrations.RenameField(
            model_name='azuresubscription',
            old_name='client_id',
            new_name='azure_client_id',
        ),
        # Step 2: Add client ForeignKey field
        migrations.AddField(
            model_name='azuresubscription',
            name='client',
            field=models.ForeignKey(
                help_text='Client that owns this Azure subscription',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='azure_subscriptions',
                to='clients.client',
                null=True,  # Temporary null=True for existing data
                blank=True
            ),
        ),
    ]
