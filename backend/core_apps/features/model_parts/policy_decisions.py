"""Versioned operational decisions; no migration invents an approval."""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from core_apps.common.models import TimeStampedModel


class PolicyDecision(TimeStampedModel):
    code = models.CharField(max_length=4)
    version = models.CharField(max_length=80)
    status = models.CharField(
        max_length=16,
        choices=[("draft", "Draft"), ("approved", "Approved"), ("retired", "Retired")],
        default="draft",
    )
    owner = models.CharField(max_length=120)
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    source = models.CharField(max_length=500)
    evidence_reference = models.CharField(max_length=500, blank=True, default="")
    scope = models.JSONField(default=list)
    effective_at = models.DateTimeField(null=True, blank=True)
    review_at = models.DateTimeField(null=True, blank=True)
    rules = models.JSONField(default=dict)
    evidence_requirements = models.JSONField(default=dict)
    actions_and_consequences = models.JSONField(default=dict)
    historical_treatment = models.TextField(blank=True, default="")
    audit_reason = models.TextField(blank=True, default="")
    disclosure = models.TextField(blank=True, default="")
    presentation = models.JSONField(default=dict, blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code", "version"], name="unique_policy_decision_version"
            )
        ]

    def clean(self):
        import re

        if self.status not in {"draft", "approved", "retired"}:
            raise ValidationError("Unsupported policy decision status.")

        if (
            not re.fullmatch(r"D(?:0[1-9]|[12][0-9]|3[0-5])", self.code)
            or not self.version.strip()
        ):
            raise ValidationError(
                "Use a stable D01-D35 decision and a nonempty version."
            )
        if not isinstance(self.scope, list) or any(
            not isinstance(item, str) or not item for item in self.scope
        ):
            raise ValidationError(
                "Policy scope must contain explicit action identifiers."
            )
        if any(
            not isinstance(value, dict)
            for value in (
                self.rules,
                self.evidence_requirements,
                self.actions_and_consequences,
            )
        ):
            raise ValidationError(
                "Policy rules and evidence must be structured records."
            )
        if self.status == "approved" and not (
            self.approver_id
            and self.source
            and self.evidence_reference
            and self.owner
            and self.effective_at
            and self.scope
        ):
            raise ValidationError(
                "Approved policies require authority, source, scope, effective time and approval evidence."
            )
        if self.status == "approved" and not (
            self.evidence_requirements
            and self.actions_and_consequences
            and self.historical_treatment
            and self.audit_reason
            and self.disclosure
        ):
            raise ValidationError(
                "Approved policies require evidence rules, consequences, historical treatment, disclosure and an audit reason."
            )

    def save(self, *args, **kwargs):
        self.clean()
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.status in {"approved", "retired"}:
                immutable = (
                    "code",
                    "version",
                    "owner",
                    "approver_id",
                    "source",
                    "evidence_reference",
                    "scope",
                    "effective_at",
                    "review_at",
                    "rules",
                    "disclosure",
                    "presentation",
                    "evidence_requirements",
                    "actions_and_consequences",
                    "historical_treatment",
                    "audit_reason",
                )
                if (
                    any(
                        getattr(previous, key) != getattr(self, key)
                        for key in immutable
                    )
                    or (previous.status == "retired" and self.status != "retired")
                    or self.status == "draft"
                ):
                    raise ValidationError(
                        "Publish a new policy version; approved evidence is immutable."
                    )
        super().save(*args, **kwargs)


class PolicyDecisionHead(models.Model):
    """Serialize publication of an existing policy family; never store rules here."""

    code = models.CharField(max_length=4, primary_key=True)
    revision = models.PositiveIntegerField(default=0)
    current = models.ForeignKey(
        PolicyDecision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="publication_heads",
    )
