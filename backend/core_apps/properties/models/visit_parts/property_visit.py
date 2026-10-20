"""Visit: property visit."""

import builtins
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel


User = get_user_model()


class PropertyVisit(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = ("pending", _("Pending"))
        CONFIRMED = ("confirmed", _("Confirmed"))
        CANCELED = ("canceled", _("Canceled"))
        REJECTED = ("rejected", _("Rejected"))

    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("Property"),
    )
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("Tenant"),
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requested_viewings",
    )
    company = models.ForeignKey(
        "features.Company",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="viewings",
    )
    academic_plan = models.ForeignKey(
        "features.AcademicHousingPlan",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="viewings",
    )
    context_kind = models.CharField(max_length=24, default="personal")
    visit_date = models.DateField(_("Visit Date"))
    visit_time = models.TimeField(_("Visit Time"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    accepted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    note = models.TextField(_("Note"), blank=True, default="")
    offer_id = models.CharField(max_length=64, blank=True, default="")
    offer_snapshot = models.JSONField(null=True, blank=True)
    stay_preferences = models.JSONField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        # All ordinary ORM appointment changes share the decision's row lock.
        # There is no reschedule API today; admin/service edits still invalidate
        # an already-open decision form instead of accepting a stale schedule.
        if self._state.adding:
            return super().save(*args, **kwargs)
        with transaction.atomic():
            old = type(self).objects.select_for_update().get(pk=self.pk)
            fields = {
                "visit_date",
                "visit_time",
                "status",
                "property_id",
                "tenant_id",
                "offer_id",
                "offer_snapshot",
                "stay_preferences",
            }
            updated = kwargs.get("update_fields")
            changed = any(
                getattr(old, field) != getattr(self, field)
                for field in fields
                if updated is None
                or field in updated
                or field.removesuffix("_id") in updated
            )
            if changed:
                if PropertyVisitDecision.objects.filter(visit=old).exists():
                    from core_apps.properties.services.post_visit_decision import (
                        DecisionConflict,
                    )

                    raise DecisionConflict(
                        "An attended decision is already recorded.",
                        "decision_already_recorded",
                    )
                self.revision = old.revision + 1
                if updated is not None:
                    kwargs["update_fields"] = set(updated) | {"revision"}
            else:
                self.revision = max(self.revision, old.revision)
            return super().save(*args, **kwargs)

    @builtins.property
    def post_visit_decision(self):
        # Compatibility for the original single-attendee integrations.
        decision = self.participant_decisions.filter(tenant_id=self.tenant_id).first()
        if decision is None:
            raise AttributeError("No post-visit decision")
        return decision

    class Meta:
        verbose_name = _("Property Visit")
        verbose_name_plural = _("Property Visits")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "property", "visit_date", "visit_time"],
                name="unique_tenant_property_visit_slot",
            )
        ]

    def __str__(self):
        return f"Visit for {self.property.title} by {self.tenant.email} on {self.visit_date} at {self.visit_time}"


class PropertyVisitDecision(TimeStampedModel):
    """Immutable tenant statement, separate from public reviews and signing."""

    visit = models.ForeignKey(
        PropertyVisit, on_delete=models.CASCADE, related_name="participant_decisions"
    )
    tenant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="visit_decisions"
    )
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="received_visit_decisions"
    )
    value = models.CharField(
        max_length=10, choices=[("proceed", "Proceed"), ("decline", "Decline")]
    )
    reason = models.TextField(blank=True, default="", max_length=1000)
    attended = models.BooleanField(default=True)
    attendance_source = models.CharField(max_length=30, default="tenant_attestation")
    attested_at = models.DateTimeField()
    visit_revision = models.PositiveIntegerField()
    request_key = models.UUIDField()
    property_id_snapshot = models.UUIDField()
    offer_id = models.CharField(max_length=64, blank=True, default="")
    offer_snapshot = models.JSONField(null=True, blank=True)
    scheduled_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["visit", "tenant"], name="one_decision_per_visit_participant"
            ),
            models.UniqueConstraint(
                fields=["tenant", "request_key"], name="unique_visit_decision_request"
            ),
            models.CheckConstraint(
                check=models.Q(attended=True), name="visit_decision_attended"
            ),
            models.CheckConstraint(
                check=(
                    models.Q(value="proceed", reason="")
                    | (models.Q(value="decline") & ~models.Q(reason=""))
                ),
                name="visit_decision_reason_policy",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from django.core.exceptions import ValidationError

            raise ValidationError("Post-visit decisions are immutable.")
        return super().save(*args, **kwargs)


class OwnerAvailabilitySlot(TimeStampedModel):
    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="availability_slots",
        verbose_name=_("Property"),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="availability_slots",
        verbose_name=_("Owner"),
    )
    date = models.DateField(_("Date"))
    time = models.TimeField(_("Time"))
    is_enabled = models.BooleanField(_("Is Enabled"), default=True)

    class Meta:
        verbose_name = _("Owner Availability Slot")
        verbose_name_plural = _("Owner Availability Slots")
        ordering = ["date", "time"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "date", "time"],
                name="unique_property_availability_slot",
            )
        ]

    def __str__(self):
        return f"{self.property.title} on {self.date} at {self.time}"
