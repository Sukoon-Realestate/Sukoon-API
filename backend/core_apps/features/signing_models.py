"""Private immutable signing input and provider facts, independent of delivery."""

from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class RentalSigningDocument(TimeStampedModel):
    lease = models.ForeignKey(
        "features.Lease", on_delete=models.PROTECT, related_name="signing_documents"
    )
    change = models.ForeignKey(
        "features.RentalChange",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="signing_documents",
    )
    source_revision = models.PositiveIntegerField()
    source_hash = models.CharField(max_length=64)
    snapshot = models.JSONField()
    source_content = models.BinaryField(editable=False)
    recipients = models.JSONField()
    provider_document_id = models.UUIDField(null=True, blank=True, unique=True)
    status = models.CharField(max_length=24, default="prepared", db_index=True)
    failure_code = models.CharField(max_length=80, blank=True, default="")
    attempts = models.PositiveIntegerField(default=0)
    claimed_at = models.DateTimeField(null=True, blank=True)
    next_check_at = models.DateTimeField(null=True, blank=True, db_index=True)
    provider_result = models.JSONField(default=dict)
    completed_content = models.BinaryField(null=True, blank=True, editable=False)
    completed_hash = models.CharField(max_length=64, blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "source_revision"],
                condition=Q(change__isnull=True),
                name="unique_lease_signing_source",
            ),
            models.UniqueConstraint(
                fields=["change", "source_revision"],
                condition=Q(change__isnull=False),
                name="unique_change_signing_source",
            ),
        ]


class RentalSigningHint(TimeStampedModel):
    document = models.ForeignKey(
        RentalSigningDocument, on_delete=models.CASCADE, related_name="hints"
    )
    provider_document_id = models.UUIDField()
    checked_at = models.DateTimeField(null=True, blank=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "provider_document_id"],
                name="unique_signing_provider_hint",
            )
        ]
