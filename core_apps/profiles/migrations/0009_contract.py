# Generated manually to adhere to strict makemigrations exclusion rule

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("profiles", "0008_profile_city"),
        ("properties", "0017_property_video_property_video_duration"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contract",
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
                    "property_title",
                    models.CharField(max_length=255, verbose_name="Property Title"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("start_date", models.DateField(verbose_name="Start Date")),
                ("end_date", models.DateField(verbose_name="End Date")),
                (
                    "document_url",
                    models.URLField(
                        blank=True,
                        default="",
                        max_length=500,
                        verbose_name="Document URL",
                    ),
                ),
                (
                    "property",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contracts",
                        to="properties.property",
                        verbose_name="Property",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contracts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contract",
                "verbose_name_plural": "Contracts",
                "ordering": ["-created_at"],
            },
        ),
    ]
