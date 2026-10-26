"""Private portfolio terms reviewed by the owner and assigned company coordinator."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class CompanyTermsNegotiation(TimeStampedModel):
    booking = models.OneToOneField(
        "CompanyBookingItem", on_delete=models.PROTECT, related_name="negotiation"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="company_terms_owned",
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="company_terms_coordinated",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="company_terms_authored",
    )
    revision = models.PositiveIntegerField(default=1)
    content_revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, default="proposed")
    terms = models.JSONField()
    source_snapshot = models.JSONField()
    terms_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="company_terms_accepted",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    followed_at = models.DateTimeField(null=True, blank=True)


class CompanyTermsVersion(TimeStampedModel):
    negotiation = models.ForeignKey(
        CompanyTermsNegotiation, on_delete=models.PROTECT, related_name="versions"
    )
    version = models.PositiveIntegerField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    terms = models.JSONField()
    terms_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["negotiation", "version"], name="unique_company_terms_version"
            )
        ]
