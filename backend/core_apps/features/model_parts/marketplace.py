"""Marketplace models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel


class BoostCampaign(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boost_campaigns",
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="boost_campaigns"
    )
    option_id = models.CharField(max_length=50)
    duration_days = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    impressions = models.PositiveIntegerField(null=True, blank=True)


class SearchAlert(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_alerts"
    )
    name = models.CharField(max_length=150)
    cadence = models.CharField(
        max_length=20, choices=[("instant", "Instant"), ("daily", "Daily")]
    )
    filters = models.JSONField(default=dict)
    enabled = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)
    last_matched_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class ListingSuggestion(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listing_suggestions",
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, null=True, blank=True
    )
    language = models.CharField(max_length=2)
    facts = models.JSONField(default=dict)
    suggested_title = models.CharField(max_length=150)
    suggested_description = models.TextField(max_length=5000)
    warnings = models.JSONField(default=list)
