"""Company context extends canonical rentals; employees are never personal payers."""

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from core_apps.common.models import TimeStampedModel


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100)
    contact_email = models.EmailField()
    review_status = models.CharField(max_length=20, default="pending")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_companies",
    )
    review_reference = models.CharField(max_length=200, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)
    budget_limit_minor = models.PositiveBigIntegerField(null=True, blank=True)
    deposit_limit_minor = models.PositiveBigIntegerField(null=True, blank=True)


class CompanyMembership(TimeStampedModel):
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="company_memberships",
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_coordinator = models.BooleanField(default=False)
    is_approver = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    can_execute_payments = models.BooleanField(default=False)
    signing_verified_until = models.DateTimeField(null=True, blank=True)
    signing_reference = models.CharField(max_length=200, blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "user"], name="unique_company_member"
            )
        ]


class CompanyInvitation(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    recipient_email = models.EmailField()
    token_digest = models.CharField(max_length=64, unique=True)
    roles = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)


class PortfolioOffer(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    scope = models.CharField(
        max_length=24,
        choices=[
            (v, v)
            for v in [
                "selected_units",
                "entire_building",
                "selected_buildings",
                "entire_complex",
            ]
        ],
    )
    building = models.ForeignKey(
        "properties.ResidentialBuilding",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    complex = models.ForeignKey(
        "properties.ResidentialComplex", on_delete=models.PROTECT, null=True, blank=True
    )
    units = models.ManyToManyField(
        "properties.Property", blank=True, related_name="portfolio_offers"
    )
    buildings = models.ManyToManyField(
        "properties.ResidentialBuilding", blank=True, related_name="portfolio_offers"
    )
    revision = models.PositiveIntegerField(default=1)
    monthly_rent_minor = models.PositiveBigIntegerField()
    deposit_minor = models.PositiveBigIntegerField(default=0)
    included_services = models.JSONField(default=list)
    excluded_services = models.JSONField(default=list)
    occupancy_policy = models.CharField(
        max_length=30, default="named_occupants_required"
    )
    status = models.CharField(max_length=20, default="draft")


class CompanyHousingRequest(TimeStampedModel):
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="housing_requests"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    title = models.CharField(max_length=200)
    purpose = models.TextField()
    cost_center = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=300)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    headcount = models.PositiveSmallIntegerField()
    commitment_ceiling_minor = models.PositiveBigIntegerField()
    deposit_limit_minor = models.PositiveBigIntegerField()
    revision = models.PositiveIntegerField(default=1)
    commercial_revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(ends_on_exclusive__gt=F("starts_on")),
                name="company_request_valid_dates",
            ),
            models.CheckConstraint(
                check=Q(headcount__gte=1), name="company_headcount_positive"
            ),
        ]


class CompanyBookingItem(TimeStampedModel):
    request = models.ForeignKey(
        CompanyHousingRequest, on_delete=models.PROTECT, related_name="items"
    )
    offer = models.ForeignKey(PortfolioOffer, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    commercial_revision = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField()
    snapshot_digest = models.CharField(max_length=64)
    quote_expires_at = models.DateTimeField()
    full_term_rent_minor = models.PositiveBigIntegerField()
    deposit_minor = models.PositiveBigIntegerField()
    status = models.CharField(max_length=24, default="proposed")
    hold = models.OneToOneField(
        "ReservationHold", on_delete=models.PROTECT, null=True, blank=True
    )
    invitation = models.OneToOneField(
        "TenancyInvitation", on_delete=models.PROTECT, null=True, blank=True
    )
    lease = models.OneToOneField(
        "Lease", on_delete=models.PROTECT, null=True, blank=True
    )
    occupants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="company_booking_items"
    )


class CompanyApproval(TimeStampedModel):
    item = models.ForeignKey(
        CompanyBookingItem, on_delete=models.PROTECT, related_name="approvals"
    )
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    commercial_revision = models.PositiveIntegerField()
    snapshot = models.JSONField()
    snapshot_digest = models.CharField(max_length=64)
    decision = models.CharField(
        max_length=12, choices=[("approved", "Approved"), ("rejected", "Rejected")]
    )
    expires_at = models.DateTimeField()
    reason = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item", "commercial_revision"],
                name="unique_company_commercial_decision",
            )
        ]


class CompanyBudgetReservation(TimeStampedModel):
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="budget_reservations"
    )
    item = models.OneToOneField(CompanyBookingItem, on_delete=models.PROTECT)
    approval = models.OneToOneField(CompanyApproval, on_delete=models.PROTECT)
    rent_minor = models.PositiveBigIntegerField()
    deposit_minor = models.PositiveBigIntegerField()
    status = models.CharField(max_length=12, default="reserved")


class EmployeeAssignment(TimeStampedModel):
    item = models.ForeignKey(
        CompanyBookingItem, on_delete=models.PROTECT, related_name="assignments"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accommodation_assignments",
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    space_key = models.CharField(max_length=90, blank=True)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    revision = models.PositiveIntegerField(default=1)
    acknowledgment = models.CharField(max_length=20, default="pending")
    acknowledged_revision = models.PositiveIntegerField(null=True, blank=True)
    occupancy_status = models.CharField(max_length=20, default="arrival_pending")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(ends_on_exclusive__gt=F("starts_on")),
                name="assignment_valid_dates",
            )
        ]
