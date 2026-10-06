# Generated manually — adds User.is_verified

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_socialaccount_socialaccount_uniq_provider_uid"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_verified",
            field=models.BooleanField(default=False, verbose_name="Is Verified"),
        ),
    ]
