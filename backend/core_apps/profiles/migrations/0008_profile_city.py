# Generated manually to adhere to strict makemigrations exclusion rule

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0007_add_notification_settings_fields"),
        ("properties", "0011_governorate_city_property_locations"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="city",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="profiles",
                to="properties.city",
                verbose_name="City",
            ),
        ),
    ]
