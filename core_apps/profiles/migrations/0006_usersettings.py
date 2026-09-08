# Generated manually to adhere to strict makemigrations exclusion rule

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("profiles", "0005_profile_phone_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserSettings",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "visit_notifications",
                    models.BooleanField(
                        default=True,
                        help_text="Notifications for property visits",
                        verbose_name="Visit Notifications",
                    ),
                ),
                (
                    "new_properties_in_area",
                    models.BooleanField(
                        default=True,
                        help_text="Alerts for new properties in user's area",
                        verbose_name="New Properties in Area",
                    ),
                ),
                (
                    "owner_messages",
                    models.BooleanField(
                        default=True,
                        help_text="Notifications for messages from property owners",
                        verbose_name="Owner Messages",
                    ),
                ),
                (
                    "promotions_and_updates",
                    models.BooleanField(
                        default=False,
                        help_text="Marketing promotions, news, and special offers",
                        verbose_name="Updates and Offers",
                    ),
                ),
                (
                    "always_hide_mobile_number",
                    models.BooleanField(
                        default=True,
                        help_text="Always hide mobile number for privacy protection (fixed)",
                        verbose_name="Always Hide Mobile Number",
                    ),
                ),
                (
                    "share_location_for_search",
                    models.BooleanField(
                        default=True,
                        help_text="Allow location access for search optimization",
                        verbose_name="Share My Location for Search",
                    ),
                ),
                (
                    "show_profile_in_search",
                    models.BooleanField(
                        default=False,
                        help_text="Allow account to appear in search results",
                        verbose_name="Appear in Search",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="settings",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "User Settings",
                "verbose_name_plural": "User Settings",
                "ordering": ["-created_at"],
            },
        ),
    ]
