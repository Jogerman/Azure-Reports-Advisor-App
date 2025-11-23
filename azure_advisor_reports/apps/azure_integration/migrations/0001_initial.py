# Generated manually for azure_integration initial migration

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AzureSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text="User-friendly name for this subscription (e.g., 'Production Account')", max_length=200)),
                ('subscription_id', models.CharField(help_text='Azure Subscription ID (UUID format)', max_length=36, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_uuid', message='Enter a valid UUID.', regex='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')])),
                ('tenant_id', models.CharField(help_text='Azure Tenant ID (UUID format)', max_length=36, validators=[django.core.validators.RegexValidator(code='invalid_uuid', message='Enter a valid UUID.', regex='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')])),
                ('client_id', models.CharField(help_text='Azure Service Principal Client ID (UUID format)', max_length=36, validators=[django.core.validators.RegexValidator(code='invalid_uuid', message='Enter a valid UUID.', regex='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')])),
                ('client_secret_encrypted', models.BinaryField(help_text='Encrypted client secret (stored using Fernet encryption)')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this subscription is active for syncing')),
                ('sync_status', models.CharField(choices=[('never_synced', 'Never Synced'), ('success', 'Success'), ('failed', 'Failed')], default='never_synced', help_text='Status of the last synchronization attempt', max_length=20)),
                ('sync_error_message', models.TextField(blank=True, help_text='Error message from last failed sync')),
                ('last_sync_at', models.DateTimeField(blank=True, help_text='Timestamp of last successful API sync', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who added this subscription', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='azure_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Azure Subscription',
                'verbose_name_plural': 'Azure Subscriptions',
                'db_table': 'azure_subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='azuresubscription',
            index=models.Index(fields=['subscription_id'], name='azure_subsc_subscri_5d4d0e_idx'),
        ),
        migrations.AddIndex(
            model_name='azuresubscription',
            index=models.Index(fields=['is_active'], name='azure_subsc_is_acti_6a8c0f_idx'),
        ),
        migrations.AddIndex(
            model_name='azuresubscription',
            index=models.Index(fields=['last_sync_at'], name='azure_subsc_last_sy_7b9d1e_idx'),
        ),
        migrations.AddIndex(
            model_name='azuresubscription',
            index=models.Index(fields=['sync_status'], name='azure_subsc_sync_st_8c0e2f_idx'),
        ),
    ]
