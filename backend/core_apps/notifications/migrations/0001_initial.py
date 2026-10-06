# Generated manually to adhere to strict makemigrations exclusion rule

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
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
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("visit_request", "Visit Request"),
                            ("visit_accepted", "Visit Accepted"),
                            ("visit_rejected", "Visit Rejected"),
                            ("new_message", "New Message"),
                            ("property_update", "Property Update"),
                            ("property_verified", "Property Verified"),
                            ("property_views", "Property Views"),
                            ("daily_bump", "Daily Bump"),
                            ("new_property", "New Property In Area"),
                            ("security_alert", "Security Alert"),
                            ("account_verification", "Account Verification"),
                            ("visit_review", "Visit Review"),
                            ("promotion", "Promotion"),
                            ("general", "General Notification"),
                        ],
                        default="general",
                        max_length=50,
                        verbose_name="Notification Type",
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                ("body", models.TextField(blank=True, default="", verbose_name="Body")),
                (
                    "category",
                    models.CharField(
                        blank=True, default="", max_length=100, verbose_name="Category"
                    ),
                ),
                (
                    "icon_type",
                    models.CharField(
                        blank=True, default="bell", max_length=50, verbose_name="Icon Type"
                    ),
                ),
                ("is_read", models.BooleanField(default=False, verbose_name="Is Read")),
                ("read_at", models.DateTimeField(blank=True, null=True, verbose_name="Read At")),
                (
                    "data",
                    models.JSONField(
                        blank=True, default=dict, verbose_name="Data Payload"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notification",
                "verbose_name_plural": "Notifications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DeviceToken",
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
                    "token",
                    models.CharField(
                        max_length=512, unique=True, verbose_name="FCM Token"
                    ),
                ),
                (
                    "device_type",
                    models.CharField(
                        choices=[("ios", "iOS"), ("android", "Android"), ("web", "Web")],
                        default="android",
                        max_length=20,
                        verbose_name="Device Type",
                    ),
                ),
                (
                    "device_name",
                    models.CharField(
                        blank=True, default="", max_length=100, verbose_name="Device Name"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Is Active"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="device_tokens",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Device Token",
                "verbose_name_plural": "Device Tokens",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["user", "is_read"], name="notif_user_read_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["user", "-created_at"], name="notif_user_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="devicetoken",
            index=models.Index(
                fields=["user", "is_active"], name="devtok_user_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="devicetoken",
            index=models.Index(
                fields=["token"], name="devtok_token_idx"
            ),
        ),
    ]
