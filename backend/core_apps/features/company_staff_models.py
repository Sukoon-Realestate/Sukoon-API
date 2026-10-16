"""Company-owned directory data; no authentication identity is created here."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class CompanyStaffRecord(TimeStampedModel):
    company = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, related_name="staff_records"
    )
    employee_code = models.CharField(max_length=60, blank=True)
    display_name = models.CharField(max_length=200)
    work_email = models.EmailField()
    mobile = models.CharField(max_length=32, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=100, blank=True)
    project_code = models.CharField(max_length=100, blank=True)
    proposed_roles = models.JSONField(default=list)
    proposal_revision = models.PositiveIntegerField(default=1)
    revision = models.PositiveIntegerField(default=1)
    employment_status = models.CharField(max_length=20, default="active")
    membership = models.OneToOneField(
        "features.CompanyMembership",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff_record",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "employee_code"],
                condition=~Q(employee_code=""),
                name="unique_company_employee_code",
            ),
            models.UniqueConstraint(
                fields=["company", "work_email"], name="unique_company_staff_email"
            ),
        ]


class CompanyAccountProvisioning(TimeStampedModel):
    staff = models.ForeignKey(
        CompanyStaffRecord, on_delete=models.PROTECT, related_name="provisionings"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    recipient_email = models.EmailField()
    roles = models.JSONField(default=list)
    proposal_revision = models.PositiveIntegerField()
    revision = models.PositiveIntegerField(default=1)
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, default="pending_activation")
    consumed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    consumed_at = models.DateTimeField(null=True, blank=True)
    # This record is also the durable delivery intention. Secrets are derived
    # using the server signing key, never stored in a receipt or roster export.
    delivery_status = models.CharField(max_length=24, default="queued")
    delivery_claimed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


class CompanyStaffBatch(TimeStampedModel):
    company = models.ForeignKey("features.Company", on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    revision = models.PositiveIntegerField(default=1)


class CompanyWorkContactProof(TimeStampedModel):
    provisioning = models.ForeignKey(
        CompanyAccountProvisioning,
        on_delete=models.PROTECT,
        related_name="contact_proofs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    expires_at = models.DateTimeField()
    code_digest = models.CharField(max_length=64)
    attempts = models.PositiveSmallIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)
    delivery_status = models.CharField(max_length=24, default="queued")
    delivery_claimed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


class CompanyStaffBatchRow(TimeStampedModel):
    batch = models.ForeignKey(
        CompanyStaffBatch, on_delete=models.PROTECT, related_name="rows"
    )
    row_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    input_payload = models.JSONField(default=dict)
    staff = models.ForeignKey(
        CompanyStaffRecord, on_delete=models.PROTECT, null=True, blank=True
    )
    error_code = models.CharField(max_length=60, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "row_key"], name="unique_company_staff_batch_row"
            )
        ]
