"""Review records refer to canonical visits/leases, never a second occupancy store."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class ReviewCase(TimeStampedModel):
    experience_key = models.CharField(max_length=240, unique=True)
    context_type = models.CharField(max_length=24)
    visit = models.ForeignKey(
        "properties.PropertyVisit", on_delete=models.PROTECT, null=True
    )
    lease = models.ForeignKey(
        "features.Lease",
        on_delete=models.PROTECT,
        null=True,
        related_name="review_cases",
    )
    peer_lease = models.ForeignKey(
        "features.Lease",
        on_delete=models.PROTECT,
        null=True,
        related_name="peer_review_cases",
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    party_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="review_cases_a",
    )
    party_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_cases_b",
    )
    company = models.ForeignKey("features.Company", on_delete=models.PROTECT, null=True)
    landlord_company = models.ForeignKey(
        "features.Company",
        on_delete=models.PROTECT,
        null=True,
        related_name="landlord_review_cases",
    )
    company_binding = models.ForeignKey(
        "features.CompanyLeaseBinding", on_delete=models.PROTECT, null=True
    )
    employee_assignment = models.ForeignKey(
        "features.EmployeeAssignment", on_delete=models.PROTECT, null=True
    )
    source_snapshot = models.JSONField(default=dict)
    eligible_recorded_at = models.DateTimeField()
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField(db_index=True)
    policy_version = models.CharField(max_length=40, default="rating-v1")
    criteria_schema_version = models.CharField(
        max_length=40, default="rating-criteria-v1"
    )
    policy_snapshot = models.JSONField(default=dict)
    release_mode = models.CharField(max_length=24, default="mutual_or_deadline")
    gate_released_at = models.DateTimeField(null=True)
    revocation_reason = models.CharField(max_length=500, blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(party_a__isnull=False)
                | Q(company__isnull=False, company_binding__isnull=False),
                name="review_person_or_bound_company",
            ),
            models.CheckConstraint(
                check=~Q(party_a=models.F("party_b")), name="review_distinct_parties"
            ),
            models.CheckConstraint(
                check=Q(closes_at__gt=models.F("opens_at")),
                name="review_positive_window",
            ),
        ]


class ReviewOpportunity(TimeStampedModel):
    case = models.ForeignKey(
        ReviewCase, on_delete=models.PROTECT, related_name="opportunities"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    reviewer_company = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, null=True
    )
    reviewer_role = models.CharField(max_length=32)
    allowed_targets = models.JSONField(default=list)
    state = models.CharField(max_length=16, default="open")
    submitted_once_at = models.DateTimeField(null=True)
    revision = models.PositiveIntegerField(default=1)
    reminders_enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "reviewer"], name="review_case_person_once"
            ),
            models.UniqueConstraint(
                fields=["case", "reviewer_company"], name="review_case_company_once"
            ),
            models.CheckConstraint(
                check=Q(reviewer__isnull=False, reviewer_company__isnull=True)
                | Q(reviewer__isnull=True, reviewer_company__isnull=False),
                name="review_exact_reviewer",
            ),
        ]


class ReviewSubmission(TimeStampedModel):
    opportunity = models.OneToOneField(
        ReviewOpportunity, on_delete=models.PROTECT, related_name="submission"
    )
    acting_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.CharField(max_length=100)
    payload_hash = models.CharField(max_length=64)
    receipt = models.JSONField(default=dict)


class ReviewSection(TimeStampedModel):
    submission = models.ForeignKey(
        ReviewSubmission, on_delete=models.PROTECT, related_name="sections"
    )
    target_key = models.CharField(max_length=40)
    subject_kind = models.CharField(max_length=40)
    subject_id = models.UUIDField()
    audience = models.CharField(max_length=16)
    overall_score = models.PositiveSmallIntegerField()
    criteria = models.JSONField(default=dict)
    tag_codes = models.JSONField(default=list)
    original_comment = models.TextField(blank=True)
    public_comment = models.TextField(blank=True)
    content_state = models.CharField(max_length=16, default="pending", db_index=True)
    verification_basis = models.CharField(max_length=40)
    legacy_source = models.CharField(max_length=40, blank=True)
    legacy_id = models.UUIDField(null=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        permissions = [
            ("moderate_reviews", "Moderate review content with an audited reason"),
            ("review_eligibility", "Investigate review source eligibility"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "target_key"],
                name="review_submission_target_once",
            ),
            models.UniqueConstraint(
                fields=["legacy_source", "legacy_id"], name="review_legacy_once"
            ),
            models.CheckConstraint(
                check=Q(overall_score__gte=1, overall_score__lte=5),
                name="review_overall_1_5",
            ),
        ]
        indexes = [
            models.Index(
                fields=["subject_kind", "subject_id", "content_state"],
                name="review_subject_state_idx",
            )
        ]


class ReviewReply(TimeStampedModel):
    section = models.OneToOneField(
        ReviewSection, on_delete=models.PROTECT, related_name="reply"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    author_company = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, null=True
    )
    original_comment = models.TextField()
    public_comment = models.TextField()
    content_state = models.CharField(max_length=16, default="pending")
    revision = models.PositiveIntegerField(default=1)


class ReviewDraft(TimeStampedModel):
    opportunity = models.OneToOneField(
        ReviewOpportunity, on_delete=models.PROTECT, related_name="draft"
    )
    payload = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=1)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class ReviewReport(TimeStampedModel):
    section = models.ForeignKey(ReviewSection, on_delete=models.PROTECT)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason_code = models.CharField(max_length=40)
    detail = models.TextField(blank=True)
    state = models.CharField(max_length=20, default="open")
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "reporter", "reason_code"],
                name="review_report_dedup",
            )
        ]


class ReviewModerationDecision(TimeStampedModel):
    section = models.ForeignKey(
        ReviewSection, on_delete=models.PROTECT, related_name="decisions"
    )
    reply = models.ForeignKey(ReviewReply, on_delete=models.PROTECT, null=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=24)
    reason = models.TextField()
    before_state = models.CharField(max_length=16)
    after_state = models.CharField(max_length=16)
    policy_version = models.CharField(max_length=40)
    notified_at = models.DateTimeField(null=True)


class ReviewAppeal(TimeStampedModel):
    decision = models.ForeignKey(
        ReviewModerationDecision, on_delete=models.PROTECT, related_name="appeals"
    )
    appellant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    detail = models.TextField()
    state = models.CharField(max_length=20, default="open")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="resolved_review_appeals",
    )
    resolution = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["decision"],
                condition=Q(state="open"),
                name="review_one_open_appeal",
            )
        ]


class ReputationAccessGrant(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reputation_grants",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_reputation_grants",
    )
    subject_kind = models.CharField(max_length=40)
    purpose = models.CharField(max_length=200)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    revision = models.PositiveIntegerField(default=1)


class ReviewAuditEvent(TimeStampedModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    subject_id = models.UUIDField()
    action = models.CharField(max_length=40)
    reason = models.TextField(blank=True)
    policy_version = models.CharField(max_length=40, default="rating-v1")


class ReviewDecisionNotice(TimeStampedModel):
    decision = models.ForeignKey(
        ReviewModerationDecision, on_delete=models.PROTECT, related_name="notices"
    )
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    notified_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "recipient"], name="review_decision_notice_once"
            )
        ]
