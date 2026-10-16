"""Revocable read grants over existing rental records; no delegated authority."""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from core_apps.common.models import TimeStampedModel


class RentalSummaryGrant(TimeStampedModel):
    lease = models.ForeignKey("features.Lease", on_delete=models.PROTECT)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_summary_grants",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_rental_summaries",
    )
    revision = models.PositiveIntegerField(default=1)
    scopes = models.JSONField(default=list)
    invoice = models.ForeignKey(
        "features.RentInvoice", on_delete=models.PROTECT, null=True, blank=True
    )
    receipt = models.ForeignKey(
        "features.PaymentReceipt", on_delete=models.PROTECT, null=True, blank=True
    )
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(granted_by=F("recipient")),
                name="summary_grant_distinct_recipient",
            )
        ]
