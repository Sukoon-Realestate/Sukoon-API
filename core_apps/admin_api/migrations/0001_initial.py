import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StaffProfile",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "role_name",
                    models.CharField(
                        choices=[
                            ("system_owner", "System Owner"),
                            ("main_admin", "Main Admin"),
                            ("kyc_reviewer", "KYC Reviewer"),
                            ("property_reviewer", "Property Reviewer"),
                            ("support", "Customer Support"),
                        ],
                        db_index=True,
                        default="kyc_reviewer",
                        max_length=50,
                        verbose_name="Role Name",
                    ),
                ),
                (
                    "display_role",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=100,
                        verbose_name="Display Role",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Is Active"),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="staff_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Staff Profile",
                "verbose_name_plural": "Staff Profiles",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="UserReport",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reason", models.CharField(max_length=255, verbose_name="Reason")),
                (
                    "reason_type",
                    models.CharField(
                        choices=[
                            ("spam", "Spam"),
                            ("fraud", "Fraud / Scam"),
                            ("abusive", "Abusive Language"),
                            ("misleading", "Misleading Info"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=50,
                        verbose_name="Reason Type",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("banned", "Banned"),
                            ("dismissed", "Dismissed"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "automation_level",
                    models.CharField(
                        choices=[
                            ("high", "High Risk"),
                            ("auto", "Auto Detected"),
                            ("low", "Low Risk"),
                        ],
                        default="auto",
                        max_length=20,
                        verbose_name="Automation Level",
                    ),
                ),
                (
                    "reviewed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Reviewed At"
                    ),
                ),
                (
                    "notes",
                    models.TextField(blank=True, default="", verbose_name="Notes"),
                ),
                (
                    "reported_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports_received",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Reported User",
                    ),
                ),
                (
                    "reporter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reports_filed",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Reporter",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_reports",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Reviewed By",
                    ),
                ),
            ],
            options={
                "verbose_name": "User Report",
                "verbose_name_plural": "User Reports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="KYCSubmission",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending Review"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "reviewed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Reviewed At"
                    ),
                ),
                (
                    "rejection_reason",
                    models.TextField(
                        blank=True, default="", verbose_name="Rejection Reason"
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True, default="", verbose_name="Admin Notes"
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="kyc_submissions",
                        to="profiles.profile",
                        verbose_name="Profile",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_kycs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Reviewer",
                    ),
                ),
            ],
            options={
                "verbose_name": "KYC Submission",
                "verbose_name_plural": "KYC Submissions",
                "ordering": ["-created_at"],
            },
        ),
    ]
