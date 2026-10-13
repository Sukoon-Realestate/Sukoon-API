"""Private tenancy documents, reviews and access-revocation records."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease
from .payments import PaymentAttempt
from .condition import RentalEvidence


class RentalDocument(TimeStampedModel):
    class DocumentType(models.TextChoices):
        CONTRACT = "contract", "Contract"
        CHANGE = "change", "Change"
        RECEIPT = "receipt", "Receipt"
        STATEMENT = "statement", "Statement"
        SETTLEMENT = "settlement", "Settlement"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="private_documents"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_rental_documents",
        null=True,
    )
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    title = models.CharField(max_length=160)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    revision = models.PositiveIntegerField(default=1)
    starts_on = models.DateField(null=True, blank=True)
    ends_on_exclusive = models.DateField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True, default="")
    storage_key = models.CharField(max_length=255, blank=True, default="")
    private_content = models.BinaryField(null=True, blank=True, editable=False)


class RentalReview(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="rental_reviews"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_rental_reviews",
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, default="")
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "author"], name="unique_lease_author_review"
            ),
            models.CheckConstraint(
                check=Q(rating__gte=1, rating__lte=5), name="rental_review_rating_1_5"
            ),
        ]


class PrivateAccessRevocation(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="private_access_revocations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_access_revocations",
    )
    reason = models.CharField(max_length=120)
    revoked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "user"], name="unique_lease_private_revocation"
            )
        ]
