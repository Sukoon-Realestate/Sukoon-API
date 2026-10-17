"""Private, voluntary planning over canonical housing groups and inventory."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class SharedLivingLab(TimeStampedModel):
    group = models.ForeignKey(
        "features.HousingGroup", on_delete=models.PROTECT, related_name="living_labs"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    input_revision = models.PositiveIntegerField(default=1)
    public_revision = models.PositiveIntegerField(default=1)
    access_group_revision = models.PositiveIntegerField()
    roster_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=30, default="collecting_inputs")
    title = models.CharField(max_length=120)
    participant_periods = models.JSONField(default=list)
    shortlist_id = models.UUIDField()
    selection = models.JSONField(default=dict)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    house_rules = models.JSONField(default=list)
    allocation_policy = models.JSONField(default=dict)
    household_plan = models.JSONField(default=dict)
    scenario = models.JSONField(default=dict)
    parent_lab = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    parent_agreement = models.ForeignKey(
        "features.SharedArrangementSnapshot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField()
    handoff_proposal_id = models.UUIDField(null=True, blank=True)
    handoff_application_id = models.UUIDField(null=True, blank=True)
    handoff_tender_id = models.UUIDField(null=True, blank=True)
    purged_at = models.DateTimeField(null=True, blank=True)


class PrivateParticipantRequirement(TimeStampedModel):
    lab = models.ForeignKey(
        SharedLivingLab, on_delete=models.CASCADE, related_name="requirements"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership = models.ForeignKey("features.GroupMembership", on_delete=models.PROTECT)
    membership_period = models.PositiveIntegerField()
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="omitted")
    purpose_version = models.CharField(max_length=40, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    public_revision = models.PositiveIntegerField(default=1)
    # Never included in a shared DTO, run snapshot, audit event, or notification.
    private_values = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lab", "user"], name="living_lab_one_private_requirement"
            )
        ]


class LivingLabRun(TimeStampedModel):
    lab = models.ForeignKey(
        SharedLivingLab, on_delete=models.PROTECT, related_name="runs"
    )
    input_revision = models.PositiveIntegerField()
    input_digest = models.CharField(max_length=64)
    status = models.CharField(max_length=20)
    explanation_code = models.CharField(max_length=50)
    # Proposed public terms only. Raw private limits are deliberately excluded.
    candidates = models.JSONField(default=list)
    policy_version = models.CharField(max_length=40, default="equal-room-v1")
    examined_assignments = models.PositiveIntegerField(default=0)


class ArrangementResponse(TimeStampedModel):
    run = models.ForeignKey(
        LivingLabRun, on_delete=models.PROTECT, related_name="responses"
    )
    candidate_id = models.UUIDField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    membership_period = models.PositiveIntegerField()
    decision = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "candidate_id", "user"],
                name="living_lab_one_person_response",
            )
        ]


class SharedArrangementSnapshot(TimeStampedModel):
    lab = models.ForeignKey(
        SharedLivingLab, on_delete=models.PROTECT, related_name="agreements"
    )
    run = models.ForeignKey(LivingLabRun, on_delete=models.PROTECT)
    candidate_id = models.UUIDField()
    # Immutable planning agreement, never a lease, invoice, or payment.
    snapshot = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "candidate_id"], name="living_lab_one_agreed_snapshot"
            )
        ]


class LivingLabAuditEvent(TimeStampedModel):
    lab = models.ForeignKey(
        SharedLivingLab, on_delete=models.CASCADE, related_name="audit_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    event = models.CharField(max_length=40)
    # No requirement values, reasons, prices, or submitted payloads in audit logs.


class LivingPreferenceDisclosure(TimeStampedModel):
    lab = models.ForeignKey(
        SharedLivingLab, on_delete=models.CASCADE, related_name="disclosures"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    requirement_revision = models.PositiveIntegerField()
    public_revision = models.PositiveIntegerField()
    fields = models.JSONField(default=list)
    # Explicitly reviewed room/schedule values only. Financial maxima cannot be disclosed here.
    values = models.JSONField(default=dict)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lab", "user"], name="living_lab_one_disclosure"
            )
        ]
