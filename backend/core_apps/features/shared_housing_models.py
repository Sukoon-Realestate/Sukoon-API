"""Two-person planning; canonical rental records remain authoritative."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class SharedHousingPlan(TimeStampedModel):
    connection = models.ForeignKey(
        "features.RoommateConnection", on_delete=models.PROTECT
    )
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, default="invited")
    criteria = models.JSONField(default=dict)
    publication_consents = models.JSONField(default=list)
    published = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    history = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connection"],
                condition=~Q(status__in=["closed", "handed_off"]),
                name="one_open_shared_plan_per_pair",
            )
        ]


class SharedHousingProposal(TimeStampedModel):
    plan = models.ForeignKey(
        SharedHousingPlan, on_delete=models.PROTECT, related_name="proposals"
    )
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, default="candidate")
    note = models.TextField(blank=True)


class SharedHousingAllocation(TimeStampedModel):
    proposal = models.ForeignKey(
        SharedHousingProposal, on_delete=models.PROTECT, related_name="allocations"
    )
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    selection = models.JSONField()
    interest = models.OneToOneField(
        "features.RentalInterest",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="shared_allocation",
    )
    terms = models.OneToOneField(
        "features.TermsProposal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="shared_allocation",
    )
    invitation = models.OneToOneField(
        "features.TenancyInvitation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="shared_allocation",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "tenant"], name="one_shared_allocation_per_person"
            )
        ]


class SharedHousingConsent(TimeStampedModel):
    proposal = models.ForeignKey(
        SharedHousingProposal, on_delete=models.PROTECT, related_name="consents"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    kind = models.CharField(max_length=24)
    digest = models.CharField(max_length=64)
    snapshot = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "actor", "revision", "kind"],
                name="shared_consent_once",
            )
        ]
