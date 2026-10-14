"""Planning models: tenancy transition."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel
from .roommate_connection import HousingGroup


class ConditionReport(TimeStampedModel):
    lease = models.ForeignKey(
        "features.Lease", on_delete=models.PROTECT, related_name="condition_reports"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    content_revision = models.PositiveIntegerField(default=1)
    kind = models.CharField(max_length=20)
    status = models.CharField(max_length=24, default="submitted")
    inspected_on = models.DateField()
    selection = models.JSONField(default=dict)
    items = models.JSONField(default=list)
    evidence = models.ManyToManyField("features.RentalEvidence", blank=True)
    acknowledgements = models.JSONField(default=list)
    baseline = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    baseline_revision = models.PositiveIntegerField(default=0)
    history = models.JSONField(default=list)
    versions = models.JSONField(default=list)
    baseline_snapshot = models.JSONField(default=dict)
    objections = models.JSONField(default=list)
    supersedes = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="addenda"
    )


class TenancyTransition(TimeStampedModel):
    lease = models.ForeignKey(
        "features.Lease", on_delete=models.PROTECT, related_name="planning_transitions"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    kind = models.CharField(max_length=20)
    status = models.CharField(max_length=24, default="submitted")
    requested_on = models.DateField()
    effective_on = models.DateField(null=True, blank=True)
    reason = models.TextField()
    candidate = models.ForeignKey(
        "features.RentalInterest", on_delete=models.PROTECT, null=True, blank=True
    )
    candidate_revision = models.PositiveIntegerField(default=0)
    candidate_consented = models.BooleanField(default=False)
    availability_approved = models.BooleanField(default=False)
    candidate_approved = models.BooleanField(default=False)
    history = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "kind"],
                condition=~Q(
                    status__in=[
                        "withdrawn",
                        "declined",
                        "cancelled",
                        "expired",
                        "effective",
                    ]
                ),
                name="one_live_tenancy_transition_kind",
            )
        ]


class CommuteSearch(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField(default=1)
    query = models.JSONField(default=dict)
    coverage = models.CharField(max_length=30, default="unavailable")
    provider = models.CharField(max_length=60, default="unconfigured")
    matches = models.JSONField(default=list)
    unknown_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, default="succeeded")
    processed_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    failure_code = models.CharField(max_length=60, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)


class TenantAssistantTurn(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField(default=1)
    session_id = models.CharField(max_length=100)
    previous_turn = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    reply = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, default="succeeded")


class GroupJoinRequest(TimeStampedModel):
    group = models.ForeignKey(
        HousingGroup, on_delete=models.CASCADE, related_name="join_requests"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="pending")
    note = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"], name="unique_group_join_request"
            )
        ]


class PlanningEvent(TimeStampedModel):
    """Transactional notification outbox; contains IDs and generic copy only."""

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_key = models.CharField(max_length=200)
    destination = models.JSONField(default=dict)
    notification = models.OneToOneField(
        "notifications.Notification", on_delete=models.SET_NULL, null=True, blank=True
    )
    delivered_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "event_key"],
                name="unique_planning_event_recipient",
            )
        ]
