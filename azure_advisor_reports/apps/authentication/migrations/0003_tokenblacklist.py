# Generated migration for TokenBlacklist model
# This migration adds JWT token blacklisting capability for secure logout

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_user_role_user_auth_user_e_azure_o_ab0d80_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenBlacklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jti', models.CharField(db_index=True, help_text='JWT ID - unique identifier for this token', max_length=255, unique=True)),
                ('token_type', models.CharField(choices=[('access', 'Access Token'), ('refresh', 'Refresh Token')], help_text='Type of token (access or refresh)', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the token was created')),
                ('expires_at', models.DateTimeField(help_text='When the token expires')),
                ('is_revoked', models.BooleanField(default=False, help_text='Whether the token has been revoked')),
                ('revoked_at', models.DateTimeField(blank=True, help_text='When the token was revoked', null=True)),
                ('revoked_reason', models.CharField(blank=True, help_text='Reason for token revocation (logout, security, etc.)', max_length=100)),
                ('user', models.ForeignKey(help_text='User who owns this token', on_delete=django.db.models.deletion.CASCADE, related_name='jwt_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Token Blacklist Entry',
                'verbose_name_plural': 'Token Blacklist Entries',
                'db_table': 'auth_token_blacklist',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='tokenblacklist',
            index=models.Index(fields=['jti', 'is_revoked'], name='idx_jti_revoked'),
        ),
        migrations.AddIndex(
            model_name='tokenblacklist',
            index=models.Index(fields=['expires_at'], name='idx_expires_at'),
        ),
        migrations.AddIndex(
            model_name='tokenblacklist',
            index=models.Index(fields=['user', 'token_type'], name='idx_user_token_type'),
        ),
        migrations.AddIndex(
            model_name='tokenblacklist',
            index=models.Index(fields=['created_at'], name='idx_created_at'),
        ),
    ]
