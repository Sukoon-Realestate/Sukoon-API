"""Physical identities project the existing property inventory; day locks allocate it."""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from core_apps.common.models import TimeStampedModel
from core_apps.users.services.new_business import NewAccountBusinessMixin


class RentalInventoryUnit(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="rental_units"
    )
    physical_key = models.CharField(max_length=90)
    topology_digest = models.CharField(max_length=64)
    is_current = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "physical_key"], name="unique_rental_physical_unit"
            )
        ]


class ReservationHold(NewAccountBusinessMixin, TimeStampedModel):
    @property
    def account_party_paths(self):
        return () if self.kind == "operational" else ("actor_id", "property.owner_id")

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RECONCILIATION = "reconciliation_pending", "Reconciliation pending"
        COMMITTED = "committed", "Committed"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="reservation_holds",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservation_holds",
    )
    proposal = models.ForeignKey(
        "TermsProposal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reservation_holds",
    )
    lease = models.OneToOneField(
        "Lease",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reservation",
    )
    offer_id = models.CharField(max_length=64)
    offer_revision = models.PositiveIntegerField()
    inventory_revision = models.PositiveIntegerField()
    selection_snapshot = models.JSONField()
    terms_digest = models.CharField(max_length=64)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    blocked_until_exclusive = models.DateField()
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.ACTIVE
    )
    kind = models.CharField(
        max_length=20,
        choices=[
            ("reservation", "Reservation"),
            ("external_booking", "External booking"),
            ("operational", "Operational block"),
        ],
        default="reservation",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    reconciliation_deadline = models.DateTimeField(null=True, blank=True)
    extension_count = models.PositiveSmallIntegerField(default=0)
    policy_version = models.CharField(max_length=40)
    policy_snapshot = models.JSONField()
    revision = models.PositiveIntegerField(default=1)
    released_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["status", "expires_at"], name="rental_hold_expiry_idx")
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(ends_on_exclusive__gt=F("starts_on")),
                name="rental_hold_nonempty_dates",
            ),
            models.CheckConstraint(
                check=Q(blocked_until_exclusive__gte=F("ends_on_exclusive")),
                name="rental_hold_buffer_valid",
            ),
        ]
