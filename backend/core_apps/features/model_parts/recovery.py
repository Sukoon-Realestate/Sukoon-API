"""Recovery models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease


class IdempotencyRecord(TimeStampedModel):
    class RecoveryStatus(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        PENDING = "pending", "Pending"
        UNKNOWN = "unknown", "Unknown"
        ABSENT_FINAL = "absent_final", "Absent final"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    operation = models.CharField(max_length=160)
    request_key = models.CharField(max_length=100)
    fingerprint = models.CharField(max_length=64)
    response_data = models.JSONField(default=dict)
    response_status = models.PositiveSmallIntegerField(default=200)
    is_rental_operation = models.BooleanField(default=False)
    request_subject_id = models.UUIDField(null=True, blank=True)
    result_subject_id = models.UUIDField(null=True, blank=True)
    result_revision = models.PositiveIntegerField(null=True, blank=True)
    recovery_status = models.CharField(
        max_length=20,
        choices=RecoveryStatus.choices,
        default=RecoveryStatus.CONFIRMED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "operation", "request_key"],
                name="unique_feature_request_key",
            )
        ]


class RentalInventoryDayLock(TimeStampedModel):
    class Kind(models.TextChoices):
        HOLD = "hold", "Hold"
        OCCUPIED = "occupied", "Occupied"

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="rental_day_locks",
    )
    offer_id = models.CharField(max_length=64)
    stay_on = models.DateField()
    kind = models.CharField(max_length=12, choices=Kind.choices)
    lease = models.ForeignKey(
        Lease,
        on_delete=models.CASCADE,
        related_name="inventory_day_locks",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    unit = models.ForeignKey(
        "RentalInventoryUnit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="day_locks",
    )
    hold = models.ForeignKey(
        "ReservationHold",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="day_locks",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "stay_on"],
                condition=Q(unit__isnull=False),
                name="unique_rental_unit_stay_day",
            ),
            models.UniqueConstraint(
                fields=["property", "offer_id", "stay_on"],
                condition=Q(unit__isnull=True),
                name="unique_legacy_rental_stay_day",
            ),
        ]


class RentalTimelineEvent(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.CASCADE, related_name="timeline_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rental_timeline_events",
    )
    kind = models.CharField(max_length=40)
    label = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")
    resource_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-occurred_at", "-id"]
