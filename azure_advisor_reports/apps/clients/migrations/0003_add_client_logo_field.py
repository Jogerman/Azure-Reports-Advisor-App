# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='logo',
            field=models.ImageField(blank=True, help_text='Client company logo for report customization', null=True, upload_to='client_logos/'),
        ),
    ]
