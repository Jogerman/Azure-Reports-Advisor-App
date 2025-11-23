# Generated manually for reports dual data source support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('azure_integration', '0001_initial'),
        ('reports', '0003_add_history_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='data_source',
            field=models.CharField(
                choices=[('csv', 'CSV Upload'), ('azure_api', 'Azure API')],
                default='csv',
                help_text='Source of report data: CSV upload or Azure API',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='report',
            name='azure_subscription',
            field=models.ForeignKey(
                blank=True,
                help_text='Azure subscription for API-based reports',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reports',
                to='azure_integration.azuresubscription'
            ),
        ),
        migrations.AddField(
            model_name='report',
            name='api_sync_metadata',
            field=models.JSONField(
                blank=True,
                help_text='Metadata from API sync (filters, timestamp, etc.)',
                null=True
            ),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['data_source'], name='reports_dat_source_9c1d2e_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['azure_subscription'], name='reports_azu_subscr_0d2e3f_idx'),
        ),
    ]
