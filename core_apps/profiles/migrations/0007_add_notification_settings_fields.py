# Generated manually to adhere to strict makemigrations exclusion rule

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0006_usersettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="property_updates",
            field=models.BooleanField(
                default=False,
                help_text="Notifications for property price and status updates",
                verbose_name="Property Updates",
            ),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="security_alerts",
            field=models.BooleanField(
                default=True,
                help_text="Alerts for new logins and password changes",
                verbose_name="Security Alerts",
            ),
        ),
    ]
