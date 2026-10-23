from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0005_user_is_email_verified")]
    operations = [
        migrations.AddField(
            "authsession",
            "client_platform",
            models.CharField(max_length=16, blank=True, null=True),
        ),
        migrations.AddField(
            "authsession",
            "device_model",
            models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            "authsession",
            "os_version",
            models.CharField(max_length=40, blank=True, null=True),
        ),
        migrations.AddField(
            "authsession",
            "app_version",
            models.CharField(max_length=40, blank=True, null=True),
        ),
        migrations.AddField(
            "authsession", "last_seen_at", models.DateTimeField(null=True, blank=True)
        ),
    ]
