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
            name="Ticket",
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
                    "reference",
                    models.CharField(
                        db_index=True,
                        max_length=30,
                        unique=True,
                        verbose_name="Reference",
                    ),
                ),
                (
                    "workspace",
                    models.CharField(
                        choices=[("tenant", "Tenant"), ("owner", "Owner")],
                        db_index=True,
                        default="tenant",
                        max_length=20,
                        verbose_name="Workspace",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("visit", "Visit"),
                            ("payment", "Payment"),
                            ("verification", "Verification"),
                            ("property", "Property"),
                            ("report_owner", "Report Owner"),
                            ("report_tenant", "Report Tenant"),
                            ("other", "Other"),
                        ],
                        db_index=True,
                        default="other",
                        max_length=30,
                        verbose_name="Category",
                    ),
                ),
                ("subject", models.CharField(max_length=160, verbose_name="Subject")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("in_progress", "In Progress"),
                            ("resolved", "Resolved"),
                            ("closed", "Closed"),
                        ],
                        db_index=True,
                        default="open",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="support_tickets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Support Ticket",
                "verbose_name_plural": "Support Tickets",
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketMessage",
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
                    "sender",
                    models.CharField(
                        choices=[("user", "User"), ("support", "Support")],
                        db_index=True,
                        default="user",
                        max_length=20,
                        verbose_name="Sender",
                    ),
                ),
                ("body", models.TextField(verbose_name="Message Body")),
                (
                    "sender_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ticket_messages",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Sender User",
                    ),
                ),
                (
                    "ticket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="support.ticket",
                        verbose_name="Ticket",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ticket Message",
                "verbose_name_plural": "Ticket Messages",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketAttachment",
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
                ("name", models.CharField(max_length=255, verbose_name="File Name")),
                (
                    "file",
                    models.FileField(
                        upload_to="support/attachments/", verbose_name="File"
                    ),
                ),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="support.ticketmessage",
                        verbose_name="Message",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ticket Attachment",
                "verbose_name_plural": "Ticket Attachments",
                "ordering": ["created_at"],
            },
        ),
    ]
