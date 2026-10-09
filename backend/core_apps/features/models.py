import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from core_apps.common.models import TimeStampedModel


class IdempotencyRecord(TimeStampedModel):
    class RecoveryStatus(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        PENDING = "pending", "Pending"
        UNKNOWN = "unknown", "Unknown"
        ABSENT_FINAL = "absent_final", "Absent final"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    operation = models.CharField(max_length=80)
    request_key = models.CharField(max_length=100)
    fingerprint = models.CharField(max_length=64)
    response_data = models.JSONField(default=dict)
    response_status = models.PositiveSmallIntegerField(default=200)
    is_rental_operation = models.BooleanField(default=False)
    request_subject_id = models.UUIDField(null=True, blank=True)
    result_subject_id = models.UUIDField(null=True, blank=True)
    result_revision = models.PositiveIntegerField(null=True, blank=True)
    recovery_status = models.CharField(
        max_length=20,
        choices=RecoveryStatus.choices,
        default=RecoveryStatus.CONFIRMED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "operation", "request_key"],
                name="unique_feature_request_key",
            )
        ]


class BoostCampaign(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boost_campaigns",
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="boost_campaigns"
    )
    option_id = models.CharField(max_length=50)
    duration_days = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    impressions = models.PositiveIntegerField(null=True, blank=True)


class SearchAlert(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_alerts"
    )
    name = models.CharField(max_length=150)
    cadence = models.CharField(
        max_length=20, choices=[("instant", "Instant"), ("daily", "Daily")]
    )
    filters = models.JSONField(default=dict)
    enabled = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)
    last_matched_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class ListingSuggestion(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listing_suggestions",
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, null=True, blank=True
    )
    language = models.CharField(max_length=2)
    facts = models.JSONField(default=dict)
    suggested_title = models.CharField(max_length=150)
    suggested_description = models.TextField(max_length=5000)
    warnings = models.JSONField(default=list)


class LeaseEligibleTenant(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="lease_eligible_tenants",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lease_eligibilities",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_lease_eligibilities",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "tenant"], name="unique_property_lease_tenant"
            )
        ]


class Lease(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_SIGNATURES = "pending_signatures", "Pending signatures"
        PENDING = "pending", "Pending"
        SIGNED = "signed", "Signed"
        ACTIVE = "active", "Active"
        TERMINATION_PENDING = "termination_pending", "Termination pending"
        ENDED = "ended", "Ended"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    class OccupancyStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        HANDOVER_PENDING = "handover_pending", "Handover pending"
        OCCUPIED = "occupied", "Occupied"
        MOVE_OUT_PENDING = "move_out_pending", "Move-out pending"
        RETURNED = "returned", "Returned"
        HANDOVER_DISPUTED = "handover_disputed", "Handover disputed"

    class FinancialClosureStatus(models.TextChoices):
        OPEN = "open", "Open"
        SETTLEMENT_PENDING = "settlement_pending", "Settlement pending"
        CLOSED = "closed", "Closed"
        REOPENED_FOR_ADJUSTMENT = (
            "reopened_for_adjustment",
            "Reopened for adjustment",
        )

    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="digital_leases"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_digital_leases",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tenant_digital_leases",
    )
    template_id = models.CharField(max_length=80)
    template_version = models.CharField(max_length=40)
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount_minor = models.PositiveBigIntegerField()
    rent_currency = models.CharField(max_length=3, default="EGP")
    rent_exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    revision = models.PositiveIntegerField(default=1)
    document_url = models.URLField(max_length=500, blank=True, default="")
    offer_id = models.CharField(max_length=64, blank=True, default="")
    offer_snapshot = models.JSONField(null=True, blank=True)
    tenancy_root_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    occupancy_status = models.CharField(
        max_length=24,
        choices=OccupancyStatus.choices,
        default=OccupancyStatus.NOT_STARTED,
    )
    financial_closure_status = models.CharField(
        max_length=32,
        choices=FinancialClosureStatus.choices,
        default=FinancialClosureStatus.OPEN,
    )
    legacy_read_only = models.BooleanField(default=True)
    terms = models.JSONField(default=dict, blank=True)
    policy_version = models.CharField(max_length=40, blank=True, default="")
    reviewed_by = models.JSONField(default=list, blank=True)
    document_id = models.UUIDField(null=True, blank=True)
    document_hash = models.CharField(max_length=64, blank=True, default="")
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "offer_id"],
                condition=Q(
                    legacy_read_only=True,
                    status__in=[
                        "draft",
                        "pending_signatures",
                        "pending",
                        "signed",
                        "active",
                        "termination_pending",
                    ]
                ),
                name="unique_live_lease_per_accommodation",
            )
        ]


class TenancyInvitation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="tenancy_invitations",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_tenancy_invitations",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_tenancy_invitations",
    )
    offer_id = models.CharField(max_length=64, blank=True, default="")
    offer_snapshot = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    revision = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initiated_tenancy_invitations",
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responded_tenancy_invitations",
        null=True,
        blank=True,
    )
    lease = models.OneToOneField(
        Lease,
        on_delete=models.PROTECT,
        related_name="tenancy_invitation",
        null=True,
        blank=True,
    )
    interest = models.ForeignKey(
        "RentalInterest",
        on_delete=models.PROTECT,
        related_name="invitations",
        null=True,
        blank=True,
    )
    terms_proposal = models.ForeignKey(
        "TermsProposal",
        on_delete=models.PROTECT,
        related_name="invitations",
        null=True,
        blank=True,
    )
    eligibility_snapshot = models.JSONField(default=dict, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["owner", "-created_at"], name="invite_owner_created_idx"),
            models.Index(fields=["tenant", "-created_at"], name="invite_tenant_created_idx"),
            models.Index(
                fields=["property", "offer_id", "status"],
                name="invite_eligibility_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(owner=F("tenant")), name="invitation_participants_distinct"
            ),
            models.CheckConstraint(
                check=Q(revision__gte=1), name="invitation_revision_positive"
            ),
            models.UniqueConstraint(
                fields=["owner", "property", "tenant", "offer_id"],
                condition=Q(status__in=["pending", "accepted"], lease__isnull=True),
                name="unique_live_tenancy_invitation",
            ),
        ]


class SigningSession(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.CASCADE, related_name="signing_sessions"
    )
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    hosted_url = models.URLField(max_length=500)
    expires_at = models.DateTimeField()
    request_key = models.UUIDField(null=True, blank=True)
    lease_revision = models.PositiveIntegerField(default=1)
    document_id = models.UUIDField(null=True, blank=True)
    document_hash = models.CharField(max_length=64, blank=True, default="")
    provider_session_id = models.CharField(max_length=120, blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)


class RentalCommercialPolicy(TimeStampedModel):
    version = models.CharField(max_length=40, unique=True)
    commission_rate_bps = models.PositiveIntegerField(default=1000)
    commission_payer = models.CharField(max_length=20, default="owner")
    commission_basis = models.CharField(
        max_length=40, default="first_period_base_rent"
    )
    processing_fee_payer = models.CharField(max_length=20, default="platform")
    renewal_commission_rate_bps = models.PositiveIntegerField(default=0)
    timezone = models.CharField(max_length=40, default="Africa/Cairo")
    billing_cycle = models.CharField(max_length=20, default="monthly")
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    summary = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)


class OwnerPaymentProfile(TimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        RESTRICTED = "restricted", "Restricted"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_payment_profile",
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    provider = models.CharField(max_length=40, default="")
    provider_account_id = models.CharField(max_length=120, blank=True, default="")
    masked_beneficiary = models.JSONField(default=dict, blank=True)
    requirements = models.JSONField(default=list, blank=True)
    accepted_policy_versions = models.JSONField(default=list, blank=True)
    payout_ready = models.BooleanField(default=False)


class OwnerOnboardingSession(TimeStampedModel):
    owner_profile = models.ForeignKey(
        OwnerPaymentProfile,
        on_delete=models.PROTECT,
        related_name="onboarding_sessions",
    )
    request_key = models.UUIDField()
    profile_revision = models.PositiveIntegerField()
    provider_session_id = models.CharField(max_length=120)
    hosted_url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, default="created")
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner_profile", "request_key"],
                name="unique_owner_onboarding_request",
            )
        ]


class RentalInterest(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
        PROPOSED = "proposed", "Proposed"
        INVITED = "invited", "Invited"

    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="rental_interests"
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_interests",
    )
    offer_id = models.CharField(max_length=64)
    offer_revision = models.PositiveIntegerField()
    offer_snapshot = models.JSONField()
    desired_start = models.DateField()
    months = models.PositiveSmallIntegerField()
    occupants = models.PositiveSmallIntegerField(default=1)
    message = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED
    )
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                check=Q(revision__gte=1), name="rental_interest_revision_positive"
            ),
            models.CheckConstraint(
                check=Q(months__gte=1), name="rental_interest_months_positive"
            ),
        ]


class TermsProposal(TimeStampedModel):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        SUPERSEDED = "superseded", "Superseded"

    interest = models.ForeignKey(
        RentalInterest, on_delete=models.PROTECT, related_name="terms_proposals"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_terms_proposals",
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PROPOSED
    )
    terms = models.JSONField()
    previous_terms = models.JSONField(default=list, blank=True)
    offer_snapshot = models.JSONField()
    accepted_by = models.JSONField(default=list, blank=True)


class RentalInventoryDayLock(TimeStampedModel):
    class Kind(models.TextChoices):
        HOLD = "hold", "Hold"
        OCCUPIED = "occupied", "Occupied"

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="rental_day_locks",
    )
    offer_id = models.CharField(max_length=64)
    stay_on = models.DateField()
    kind = models.CharField(max_length=12, choices=Kind.choices)
    lease = models.ForeignKey(
        Lease,
        on_delete=models.CASCADE,
        related_name="inventory_day_locks",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "offer_id", "stay_on"],
                name="unique_rental_offer_stay_day",
            )
        ]


class RentalTimelineEvent(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.CASCADE, related_name="timeline_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rental_timeline_events",
    )
    kind = models.CharField(max_length=40)
    label = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")
    resource_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-occurred_at", "-id"]


class BillingPeriod(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="billing_periods"
    )
    sequence = models.PositiveIntegerField()
    start = models.DateField()
    end_exclusive = models.DateField()
    issue_at = models.DateTimeField()
    due_at = models.DateTimeField()
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    class Meta:
        ordering = ["start", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "sequence"], name="unique_lease_billing_sequence"
            ),
            models.UniqueConstraint(
                fields=["lease", "start", "end_exclusive"],
                name="unique_lease_billing_period",
            ),
        ]


class RentInvoice(TimeStampedModel):
    class InvoiceType(models.TextChoices):
        RENT = "rent", "Rent"
        DEPOSIT = "deposit", "Deposit"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        DUE = "due", "Due"
        OVERDUE = "overdue", "Overdue"
        PARTIALLY_PAID = "partially_paid", "Partially paid"
        PAID = "paid", "Paid"
        SETTLED = "settled", "Settled"
        CANCELLED = "cancelled", "Cancelled"
        WRITTEN_OFF = "written_off", "Written off"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="invoices")
    reference = models.CharField(max_length=50, unique=True)
    due_date = models.DateField()
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DUE)
    receipt_url = models.URLField(max_length=500, blank=True, default="")
    revision = models.PositiveIntegerField(default=1)
    invoice_type = models.CharField(
        max_length=20, choices=InvoiceType.choices, default=InvoiceType.RENT
    )
    billing_period = models.OneToOneField(
        BillingPeriod,
        on_delete=models.PROTECT,
        related_name="invoice",
        null=True,
        blank=True,
    )
    period_start = models.DateField(null=True, blank=True)
    period_end_exclusive = models.DateField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    deferred_until = models.DateTimeField(null=True, blank=True)
    charges_minor = models.PositiveBigIntegerField(default=0)
    credits_minor = models.PositiveBigIntegerField(default=0)
    applied_minor = models.PositiveBigIntegerField(default=0)
    receipt_id = models.UUIDField(null=True, blank=True)


class InvoiceLine(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="lines"
    )
    line_type = models.CharField(max_length=40)
    description = models.CharField(max_length=255)
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    source = models.JSONField(default=dict, blank=True)


class PaymentQuote(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="payment_quotes"
    )
    request_key = models.UUIDField()
    invoice_revision = models.PositiveIntegerField()
    payer_amount_minor = models.PositiveBigIntegerField()
    tenant_service_fee_minor = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    policy_version = models.CharField(max_length=40)
    fingerprint = models.CharField(max_length=64)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "request_key"], name="unique_invoice_quote_request"
            )
        ]


class PaymentAttempt(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        CHARGEDBACK = "chargedback", "Charged back"

    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="payment_attempts"
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_payment_attempts",
    )
    quote = models.ForeignKey(
        PaymentQuote, on_delete=models.PROTECT, related_name="payment_attempts"
    )
    request_key = models.UUIDField()
    revision = models.PositiveIntegerField(default=1)
    invoice_revision = models.PositiveIntegerField()
    policy_version = models.CharField(max_length=40)
    quote_fingerprint = models.CharField(max_length=64)
    payment_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    settlement_status = models.CharField(max_length=20, default="pending")
    payout_status = models.CharField(max_length=24, default="held")
    provider_attempt_id = models.CharField(max_length=120, blank=True, default="")
    failure_code = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payer", "invoice", "request_key"],
                name="unique_payment_attempt_request",
            ),
            models.UniqueConstraint(
                fields=["invoice"],
                condition=Q(payment_status__in=["created", "pending", "authorized"]),
                name="unique_live_invoice_payment_attempt",
            ),
        ]


class CheckoutSession(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.CASCADE, related_name="checkout_sessions"
    )
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    hosted_url = models.URLField(max_length=500)
    expires_at = models.DateTimeField()
    attempt = models.OneToOneField(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="checkout_session",
        null=True,
        blank=True,
    )
    quote = models.ForeignKey(
        PaymentQuote,
        on_delete=models.PROTECT,
        related_name="checkout_sessions",
        null=True,
        blank=True,
    )
    request_key = models.UUIDField(null=True, blank=True)
    navigation = models.JSONField(default=dict, blank=True)
    return_state = models.CharField(max_length=128, blank=True, default="")
    provider_session_id = models.CharField(max_length=120, blank=True, default="")


class ProviderWebhookEvent(TimeStampedModel):
    provider = models.CharField(max_length=40)
    provider_event_id = models.CharField(max_length=120)
    event_type = models.CharField(max_length=60)
    payment_attempt = models.ForeignKey(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="provider_events",
        null=True,
        blank=True,
    )
    sequence = models.PositiveBigIntegerField(default=0)
    payload_digest = models.CharField(max_length=64)
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="unique_provider_webhook_event",
            )
        ]


class LedgerTransaction(TimeStampedModel):
    reference = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=40)
    lease = models.ForeignKey(
        Lease,
        on_delete=models.PROTECT,
        related_name="ledger_transactions",
        null=True,
        blank=True,
    )
    invoice = models.ForeignKey(
        RentInvoice,
        on_delete=models.PROTECT,
        related_name="ledger_transactions",
        null=True,
        blank=True,
    )
    payment_attempt = models.ForeignKey(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="ledger_transactions",
        null=True,
        blank=True,
    )
    occurred_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)


class LedgerEntry(TimeStampedModel):
    class Direction(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"

    transaction = models.ForeignKey(
        LedgerTransaction, on_delete=models.PROTECT, related_name="entries"
    )
    account = models.CharField(max_length=60)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)


class InvoicePaymentAllocation(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="payment_allocations"
    )
    payment_attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="invoice_allocation"
    )
    amount_minor = models.PositiveBigIntegerField()


class PaymentReceipt(TimeStampedModel):
    payment_attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="receipt"
    )
    status = models.CharField(max_length=20, default="ready")
    title = models.CharField(max_length=160, default="Rent payment receipt")
    revision = models.PositiveIntegerField(default=1)


class OwnerPayable(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="owner_payables"
    )
    invoice = models.OneToOneField(
        RentInvoice, on_delete=models.PROTECT, related_name="owner_payable"
    )
    payment_attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="owner_payable"
    )
    billing_period = models.ForeignKey(
        BillingPeriod, on_delete=models.PROTECT, related_name="owner_payables"
    )
    revision = models.PositiveIntegerField(default=1)
    gross_minor = models.PositiveBigIntegerField()
    commission_minor = models.PositiveBigIntegerField(default=0)
    processing_fee_minor = models.PositiveBigIntegerField(default=0)
    net_minor = models.PositiveBigIntegerField()
    settlement_status = models.CharField(max_length=20, default="pending")
    payout_status = models.CharField(max_length=24, default="pending_eligibility")
    blocking_reasons = models.JSONField(default=list, blank=True)


class RentalEvidence(TimeStampedModel):
    class MalwareStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SAFE = "safe", "Safe"
        UNSAFE = "unsafe", "Unsafe"
        FAILED = "failed", "Failed"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="evidence")
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rental_evidence"
    )
    request_key = models.UUIDField()
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=80)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    storage_provider = models.CharField(max_length=40, default="fake")
    storage_key = models.CharField(max_length=255, unique=True)
    private_content = models.BinaryField(null=True, blank=True, editable=False)
    malware_status = models.CharField(
        max_length=20, choices=MalwareStatus.choices, default=MalwareStatus.PENDING
    )
    revision = models.PositiveIntegerField(default=1)
    retain_until = models.DateField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["uploader", "lease", "request_key"],
                name="unique_rental_evidence_request",
            )
        ]


class RentalHandover(TimeStampedModel):
    class Kind(models.TextChoices):
        MOVE_IN = "move_in", "Move in"
        MOVE_OUT = "move_out", "Move out"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending approval"
        ACCEPTED = "accepted", "Accepted"
        DISPUTED = "disputed", "Disputed"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="handovers")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    revision = models.PositiveIntegerField(default=1)
    possession_on = models.DateField()
    condition = models.JSONField(default=dict)
    keys = models.JSONField(default=dict)
    meters = models.JSONField(default=dict)
    inventory = models.JSONField(default=list)
    approvals = models.JSONField(default=list)
    evidence = models.ManyToManyField(RentalEvidence, related_name="handovers", blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lease", "kind"], name="unique_lease_handover_kind")
        ]


class DepositAgreement(TimeStampedModel):
    lease = models.OneToOneField(Lease, on_delete=models.PROTECT, related_name="deposit_agreement")
    invoice = models.OneToOneField(
        RentInvoice, on_delete=models.PROTECT, related_name="deposit_agreement", null=True, blank=True
    )
    revision = models.PositiveIntegerField(default=1)
    agreed_minor = models.PositiveBigIntegerField(default=0)
    due_minor = models.PositiveBigIntegerField(default=0)
    collected_minor = models.PositiveBigIntegerField(default=0)
    returned_minor = models.PositiveBigIntegerField(default=0)
    applied_minor = models.PositiveBigIntegerField(default=0)
    disputed_minor = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)


class PayoutBatch(TimeStampedModel):
    class Status(models.TextChoices):
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approved_payout_batches"
    )
    request_key = models.UUIDField(unique=True)
    provider_batch_id = models.CharField(max_length=120, blank=True, default="")
    revision = models.PositiveIntegerField(default=1)


class RentalPayout(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        HELD = "held", "Held"

    batch = models.ForeignKey(PayoutBatch, on_delete=models.PROTECT, related_name="payouts")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rental_payouts"
    )
    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="payouts")
    payables = models.ManyToManyField(OwnerPayable, related_name="payouts")
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    masked_beneficiary = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    provider_payout_id = models.CharField(max_length=120, blank=True, default="")
    hold_reason = models.CharField(max_length=255, blank=True, default="")
    failure_code = models.CharField(max_length=80, blank=True, default="")
    revision = models.PositiveIntegerField(default=1)


class PayoutAuditEvent(TimeStampedModel):
    payout = models.ForeignKey(RentalPayout, on_delete=models.PROTECT, related_name="audit_events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payout_audit_events"
    )
    action = models.CharField(max_length=40)
    metadata = models.JSONField(default=dict, blank=True)


class MaintenanceRequest(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        APPOINTMENT_PROPOSED = "appointment_proposed", "Appointment proposed"
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLUTION_REPORTED = "resolution_reported", "Resolution reported"
        RESOLVED = "resolved", "Resolved"
        CANCELLED = "cancelled", "Cancelled"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="maintenance_requests")
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_maintenance"
    )
    revision = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=160)
    description = models.TextField()
    category = models.CharField(max_length=40)
    priority = models.CharField(max_length=20)
    access_times = models.JSONField(default=list)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    appointment_at = models.DateTimeField(null=True, blank=True)
    proposed_cost_minor = models.PositiveBigIntegerField(null=True, blank=True)
    cost_version = models.PositiveIntegerField(default=0)
    approved_cost_version = models.PositiveIntegerField(null=True, blank=True)
    cost_payer = models.CharField(max_length=10, blank=True, default="")
    evidence = models.ManyToManyField(RentalEvidence, related_name="maintenance_requests", blank=True)


class MaintenanceEvent(TimeStampedModel):
    maintenance_request = models.ForeignKey(
        MaintenanceRequest, on_delete=models.PROTECT, related_name="events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="maintenance_events"
    )
    action = models.CharField(max_length=40)
    note = models.TextField(blank=True, default="")
    appointment_at = models.DateTimeField(null=True, blank=True)
    cost_minor = models.PositiveBigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class RentalChange(TimeStampedModel):
    class Kind(models.TextChoices):
        PAYMENT_EXTENSION = "payment_extension", "Payment extension"
        AMENDMENT = "amendment", "Amendment"
        RENEWAL = "renewal", "Renewal"
        TERMINATION = "termination", "Termination"
        EXTERNAL_PAYMENT = "external_payment", "External payment"

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        PENDING_SIGNATURES = "pending_signatures", "Pending signatures"
        SIGNED = "signed", "Signed"
        APPLIED = "applied", "Applied"
        REVIEW_REQUIRED = "review_required", "Operations review required"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="rental_changes")
    result_lease = models.OneToOneField(
        Lease, on_delete=models.PROTECT, related_name="source_rental_change", null=True, blank=True
    )
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="rental_changes", null=True, blank=True
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_rental_changes"
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PROPOSED)
    revision = models.PositiveIntegerField(default=1)
    reason = models.TextField(blank=True, default="")
    requested_date = models.DateField(null=True, blank=True)
    original_due_at = models.DateTimeField(null=True, blank=True)
    deferred_until = models.DateTimeField(null=True, blank=True)
    effective_on = models.DateField(null=True, blank=True)
    amount_minor = models.PositiveBigIntegerField(null=True, blank=True)
    method = models.CharField(max_length=40, blank=True, default="")
    terms = models.JSONField(default=dict, blank=True)
    previous_terms = models.JSONField(default=dict, blank=True)
    approvals = models.JSONField(default=list, blank=True)
    evidence = models.ManyToManyField(RentalEvidence, related_name="rental_changes", blank=True)
    document_id = models.UUIDField(null=True, blank=True)
    document_hash = models.CharField(max_length=64, blank=True, default="")
    signed_by = models.JSONField(default=list, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)


class ChangeSigningSession(TimeStampedModel):
    change = models.ForeignKey(RentalChange, on_delete=models.PROTECT, related_name="signing_sessions")
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rental_change_signing_sessions"
    )
    request_key = models.UUIDField()
    change_revision = models.PositiveIntegerField()
    document_id = models.UUIDField()
    document_hash = models.CharField(max_length=64)
    provider_session_id = models.CharField(max_length=120, unique=True)
    hosted_url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, default="pending")
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["change", "signer", "request_key"], name="unique_change_signing_request"
            )
        ]


class FinalSettlement(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROPOSED = "proposed", "Proposed"
        ACCEPTED = "accepted", "Accepted"
        DISPUTED = "disputed", "Disputed"

    lease = models.OneToOneField(Lease, on_delete=models.PROTECT, related_name="final_settlement")
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    lines = models.JSONField(default=list)
    rent_balance_minor = models.BigIntegerField(default=0)
    deposit_to_return_minor = models.BigIntegerField(default=0)
    refund_due_minor = models.BigIntegerField(default=0)
    total_due_minor = models.BigIntegerField(default=0)
    accepted_by = models.JSONField(default=list)
    disputed_item_ids = models.JSONField(default=list)
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="proposed_settlements", null=True
    )


class RefundRequest(TimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REJECTED = "rejected", "Rejected"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="refund_requests")
    payment_attempt = models.ForeignKey(
        PaymentAttempt, on_delete=models.PROTECT, related_name="refund_requests"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rental_refund_requests"
    )
    revision = models.PositiveIntegerField(default=1)
    amount_minor = models.PositiveBigIntegerField()
    refundable_balance_snapshot_minor = models.PositiveBigIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    provider_refund_id = models.CharField(max_length=120, blank=True, default="")
    failure_code = models.CharField(max_length=80, blank=True, default="")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approved_refunds", null=True, blank=True
    )
    request_key = models.UUIDField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requester", "payment_attempt", "request_key"], name="unique_refund_request_key"
            )
        ]


class RentalDispute(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="disputes")
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_rental_disputes"
    )
    subject_kind = models.CharField(max_length=40)
    subject_id = models.UUIDField()
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reason = models.TextField()
    resolution = models.TextField(blank=True, default="")
    responses = models.JSONField(default=list)
    evidence = models.ManyToManyField(RentalEvidence, related_name="disputes", blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="resolved_rental_disputes", null=True, blank=True
    )


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

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="private_documents")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_rental_documents", null=True
    )
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    title = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    revision = models.PositiveIntegerField(default=1)
    starts_on = models.DateField(null=True, blank=True)
    ends_on_exclusive = models.DateField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True, default="")
    storage_key = models.CharField(max_length=255, blank=True, default="")
    private_content = models.BinaryField(null=True, blank=True, editable=False)


class RentalReview(TimeStampedModel):
    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="rental_reviews")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="authored_rental_reviews"
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, default="")
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lease", "author"], name="unique_lease_author_review"),
            models.CheckConstraint(check=Q(rating__gte=1, rating__lte=5), name="rental_review_rating_1_5"),
        ]


class PrivateAccessRevocation(TimeStampedModel):
    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="private_access_revocations")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rental_access_revocations"
    )
    reason = models.CharField(max_length=120)
    revoked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lease", "user"], name="unique_lease_private_revocation")
        ]
