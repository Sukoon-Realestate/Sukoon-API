"""Immutable corporate planning inputs; never an occupancy or booking ledger."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class HousingScenario(TimeStampedModel):
    company = models.ForeignKey("features.Company", on_delete=models.PROTECT)
    request = models.ForeignKey(
        "features.CompanyHousingRequest", on_delete=models.PROTECT
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    source_scenario = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    title = models.CharField(max_length=200)
    revision = models.PositiveIntegerField(default=1)
    input_snapshot = models.JSONField()
    input_digest = models.CharField(max_length=64)
    change_summary = models.JSONField(default=list)


class HousingScenarioRun(TimeStampedModel):
    scenario = models.ForeignKey(
        HousingScenario, on_delete=models.PROTECT, related_name="runs"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    input_digest = models.CharField(max_length=64)
    solver_version = models.CharField(max_length=60, default="bounded-offer-subsets-v1")
    result_status = models.CharField(max_length=24)
    result = models.JSONField(default=dict)
    state = models.CharField(max_length=24, default="completed")
    progress = models.PositiveSmallIntegerField(default=100)
    cancellation_requested = models.BooleanField(default=False)
    failure_code = models.CharField(max_length=60, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class HousingScenarioDecision(TimeStampedModel):
    scenario = models.ForeignKey(
        HousingScenario, on_delete=models.PROTECT, related_name="decisions"
    )
    run = models.ForeignKey(HousingScenarioRun, on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    approver = models.ForeignKey("features.CompanyMembership", on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, default="pending")
    plan_id = models.CharField(max_length=60)
    snapshot = models.JSONField()
    snapshot_digest = models.CharField(max_length=64)
    reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    booking_items = models.ManyToManyField(
        "features.CompanyBookingItem", blank=True, related_name="scenario_decisions"
    )


class HousingScenarioComparison(TimeStampedModel):
    scenario = models.ForeignKey(
        HousingScenario, on_delete=models.PROTECT, related_name="comparisons"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField()
