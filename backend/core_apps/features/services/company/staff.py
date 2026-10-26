"""Deferred identity linking, revision-bound activation, and recoverable staff batches."""

import hashlib
from datetime import timedelta
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...company_models import Company, CompanyMembership
from ...company_staff_models import (
    CompanyStaffRecord,
    CompanyAccountProvisioning,
    CompanyStaffBatch,
    CompanyStaffBatchRow,
)
from ..rental_lifecycle.common import audit, require_actor, require_revision
from ..rental_phase2 import RentalConflict, fingerprint
from .access import company_for, member_for
from .membership import ROLES

FIELDS = (
    "employee_code",
    "display_name",
    "work_email",
    "mobile",
    "job_title",
    "department",
    "project_code",
)


def delivery_ready():
    return bool(getattr(settings, "COMPANY_ACTIVATION_EMAIL_ENABLED", False))


def activation_token(provisioning):
    """Reconstruct only in the delivery worker; database disclosure is insufficient."""
    value = f"{provisioning.id}:{provisioning.staff_id}:{provisioning.recipient_email}:{provisioning.proposal_revision}"
    secret = salted_hmac(
        "sokoun.company.activation.v1", value, algorithm="sha256"
    ).hexdigest()
    return f"{provisioning.id}.{secret}"


def staff_for(user, company_id, staff_id, lock=False):
    company = company_for(user, company_id, "admin", lock=lock)
    rows = (
        CompanyStaffRecord.objects.select_for_update()
        if lock
        else CompanyStaffRecord.objects
    )
    return get_object_or_404(rows, company=company, id=staff_id)


def create_staff(user, company, data):
    member_for(user, company, "admin")
    roles = sorted(set(data["roles"]))
    if not roles or set(roles) - ROLES:
        raise ValidationError({"roles": "Select supported company roles."})
    values = {key: data.get(key, "").strip() for key in FIELDS}
    values["work_email"] = values["work_email"].casefold()
    try:
        with transaction.atomic():
            staff = CompanyStaffRecord.objects.create(
                company=company, created_by=user, proposed_roles=roles, **values
            )
    except IntegrityError:
        raise RentalConflict(
            "The employee code or activation email already exists in this company.",
            code="staff_identity_conflict",
        )
    audit(
        staff,
        user,
        "company_staff_prepared",
        metadata={"company_id": str(company.id), "roles": roles},
    )
    return staff


@transaction.atomic
def update_pending(user, company_id, staff_id, data):
    staff = staff_for(user, company_id, staff_id, lock=True)
    require_revision(staff, data["expected_revision"])
    if staff.membership_id:
        raise RentalConflict(
            "Use membership controls for an activated staff record.",
            code="staff_already_linked",
        )
    roles = sorted(set(data["roles"]))
    changed = (
        staff.work_email != data["work_email"].strip().casefold()
        or staff.proposed_roles != roles
    )
    if not roles or set(roles) - ROLES:
        raise ValidationError({"roles": "Select supported company roles."})
    for field in FIELDS:
        setattr(staff, field, data.get(field, "").strip())
    staff.work_email = staff.work_email.casefold()
    staff.proposed_roles = roles
    if changed:
        staff.proposal_revision += 1
        staff.provisionings.filter(status="pending_activation").update(status="revoked")
    staff.revision += 1
    staff.save()
    audit(
        staff,
        user,
        "company_staff_updated",
        metadata={
            "company_id": str(staff.company.id),
            "proposal_revision": staff.proposal_revision,
        },
    )
    return staff


@transaction.atomic
def request_activation(user, company_id, staff_id, data):
    staff = staff_for(user, company_id, staff_id, lock=True)
    require_revision(staff, data["expected_revision"])
    if staff.membership_id or staff.employment_status != "active":
        raise RentalConflict(
            "Only unlinked active staff can receive an activation.",
            code="activation_unavailable",
        )
    if not delivery_ready():
        raise RentalConflict(
            "Company activation email delivery is not configured.",
            code="provider_not_ready",
        )
    from .grant_security import require_nonprivileged_onboarding

    require_nonprivileged_onboarding(staff.proposed_roles)
    now = timezone.now()
    if staff.provisionings.filter(created_at__gt=now - timedelta(seconds=60)).exists():
        raise RentalConflict(
            "Wait before requesting another activation email.",
            code="activation_cooldown",
        )
    staff.provisionings.filter(status="pending_activation").update(status="revoked")
    provisioning = CompanyAccountProvisioning(
        staff=staff,
        requested_by=user,
        recipient_email=staff.work_email,
        roles=staff.proposed_roles,
        proposal_revision=staff.proposal_revision,
        expires_at=now + timedelta(days=7),
    )
    provisioning.token_digest = hashlib.sha256(
        activation_token(provisioning).encode()
    ).hexdigest()
    provisioning.save()
    staff.revision += 1
    staff.save(update_fields=["revision", "updated_at"])
    audit(
        staff,
        user,
        "company_activation_queued",
        metadata={
            "company_id": str(staff.company.id),
            "provisioning_id": str(provisioning.id),
        },
    )
    return staff


@transaction.atomic
def revoke_activation(user, company_id, staff_id, data):
    staff = staff_for(user, company_id, staff_id, lock=True)
    require_revision(staff, data["expected_revision"])
    staff.provisionings.filter(status="pending_activation").update(status="revoked")
    staff.revision += 1
    staff.save(update_fields=["revision", "updated_at"])
    audit(
        staff,
        user,
        "company_activation_revoked",
        metadata={"company_id": str(staff.company.id)},
    )
    return staff


def resolve_token(token):
    digest = hashlib.sha256(token.encode()).hexdigest()
    provisioning = (
        CompanyAccountProvisioning.objects.select_related("staff__company")
        .filter(token_digest=digest)
        .first()
    )
    if not provisioning or not constant_time_compare(
        activation_token(provisioning), token
    ):
        raise PermissionDenied("The activation is invalid or unavailable.")
    return provisioning


def validate_proposal(provisioning):
    staff = provisioning.staff
    if (
        provisioning.status != "pending_activation"
        or provisioning.expires_at <= timezone.now()
        or staff.employment_status != "active"
        or staff.membership_id
        or staff.proposal_revision != provisioning.proposal_revision
        or staff.work_email != provisioning.recipient_email
        or staff.proposed_roles != provisioning.roles
        or not CompanyMembership.objects.filter(
            company=staff.company,
            user=provisioning.requested_by,
            user__is_active=True,
            user__is_verified=True,
            is_active=True,
            is_admin=True,
        ).exists()
    ):
        raise RentalConflict(
            "The activation expired or changed. Request a current invitation.",
            code="activation_expired",
        )


def preview(user, token):
    provisioning = resolve_token(token)
    validate_proposal(provisioning)
    from .contact_proof import verified

    can_accept = bool(
        user.is_verified
        and (
            user.email.casefold() == provisioning.recipient_email
            or verified(provisioning, user)
        )
    )
    return {
        "id": str(provisioning.id),
        "revision": provisioning.revision,
        "company_id": str(provisioning.staff.company.id),
        "company_name": provisioning.staff.company.name,
        "roles": provisioning.roles,
        "proposal_revision": provisioning.proposal_revision,
        "expires_at": provisioning.expires_at.isoformat(),
        "can_accept": can_accept,
        "can_verify_work_contact": bool(
            user.is_verified and delivery_ready() and not can_accept
        ),
        "requires_verified_recipient_contact": True,
    }


@transaction.atomic
def respond(user, data, accept=True):
    require_actor(user)
    initial = resolve_token(data["token"])
    Company.objects.select_for_update().get(pk=initial.staff.company_id)
    staff = CompanyStaffRecord.objects.select_for_update().get(pk=initial.staff_id)
    provisioning = CompanyAccountProvisioning.objects.select_for_update().get(
        pk=initial.pk
    )
    provisioning.staff = staff
    from .contact_proof import verified

    if user.email.casefold() != provisioning.recipient_email and not verified(
        provisioning, user
    ):
        raise PermissionDenied(
            "Sign in with the verified email that received this activation."
        )
    outcome = "accepted" if accept else "declined"
    if provisioning.status == outcome and provisioning.consumed_by_id == user.pk:
        # A replay cannot reactivate an offboarded membership or restore its roles.
        return provisioning
    require_revision(provisioning, data["expected_revision"])
    validate_proposal(provisioning)
    if data["proposal_revision"] != staff.proposal_revision:
        raise RentalConflict(
            "Review the current role proposal before accepting.", code="stale_revision"
        )
    if accept:
        from .grant_security import require_nonprivileged_onboarding

        require_nonprivileged_onboarding(provisioning.roles)
        member, created = CompanyMembership.objects.get_or_create(
            company=staff.company, user=user
        )
        if not created and (
            member.is_active
            or CompanyStaffRecord.objects.filter(membership=member).exists()
        ):
            raise RentalConflict(
                "This account already has a company relationship. Ask the administrator to review it.",
                code="membership_exists",
            )
        member.is_active = True
        for role in ROLES:
            setattr(member, "is_" + role, role in provisioning.roles)
        member.can_execute_payments = False
        member.signing_verified_until = None
        member.signing_reference = ""
        member.revision += 1
        member.save()
        staff.membership = member
    provisioning.status = outcome
    provisioning.consumed_by = user
    provisioning.consumed_at = timezone.now()
    provisioning.revision += 1
    provisioning.save()
    staff.revision += 1
    staff.save()
    audit(
        staff,
        user,
        "company_access_" + outcome,
        metadata={
            "company_id": str(staff.company.id),
            "roles": provisioning.roles,
            "provisioning_id": str(provisioning.id),
        },
    )
    return provisioning


def response_payload(provisioning):
    return {
        "id": str(provisioning.id),
        "revision": provisioning.revision,
        "company_id": str(provisioning.staff.company.id),
        "status": provisioning.status,
    }


def staff_payload(staff):
    from core_apps.users.services.new_business import restricted_accounts

    latest = staff.provisionings.order_by("-created_at").first()
    status = latest.status if latest else "prepared"
    if (
        latest
        and status == "pending_activation"
        and latest.expires_at <= timezone.now()
    ):
        status = "expired"
    if staff.membership_id:
        status = "active" if staff.membership.is_active else "offboarded"
    return {
        "id": str(staff.id),
        "company_id": str(staff.company.id),
        "revision": staff.revision,
        **{key: getattr(staff, key) for key in FIELDS},
        "proposed_roles": staff.proposed_roles,
        "proposal_revision": staff.proposal_revision,
        "access_status": status,
        "employment_status": staff.employment_status,
        "account_closure_blocked": bool(
            staff.membership_id and restricted_accounts(staff.membership.user_id)
        ),
        "activation_delivery_status": (
            latest.delivery_status if latest else "not_requested"
        ),
        "activation_delivery_ready": delivery_ready(),
        "activation_expires_at": latest.expires_at.isoformat() if latest else None,
        "membership_id": str(staff.membership.id) if staff.membership_id else None,
        "allowed_actions": (
            ["edit_pending_staff", "revoke_activation"]
            + (["request_activation"] if delivery_ready() else [])
            if not staff.membership_id and staff.employment_status == "active"
            else []
        ),
    }


@transaction.atomic
def create_batch(user, company_id, data):
    company = company_for(user, company_id, "admin", lock=True)
    batch, created = CompanyStaffBatch.objects.get_or_create(
        id=data["batch_key"], defaults={"company": company, "created_by": user}
    )
    if batch.company_id != company.pk or batch.created_by_id != user.pk:
        raise PermissionDenied("The batch belongs to another workspace or submitter.")
    if not created:
        require_revision(batch, data["expected_revision"])
        if set(row["row_key"] for row in data["rows"]) - set(
            batch.rows.values_list("row_key", flat=True)
        ):
            raise RentalConflict(
                "A submitted staff batch cannot add new rows. Prepare a new batch.",
                code="batch_changed",
            )
    elif data["expected_revision"] != 0:
        raise RentalConflict(
            "A new batch starts at revision zero.", code="stale_revision"
        )
    for row in data["rows"]:
        values = {k: v for k, v in row.items() if k != "row_key"}
        digest = fingerprint(values)
        existing = batch.rows.filter(row_key=row["row_key"]).first()
        if existing and existing.fingerprint != digest:
            raise RentalConflict(
                "A submitted staff row changed. Use a new row identity for a correction.",
                code="idempotency_conflict",
            )
        if existing and existing.staff_id:
            continue
        record = existing or CompanyStaffBatchRow.objects.create(
            batch=batch,
            row_key=row["row_key"],
            fingerprint=digest,
            input_payload=values,
        )
        try:
            with transaction.atomic():
                staff = create_staff(user, company, values)
        except RentalConflict as error:
            if error.get_codes() != "staff_identity_conflict":
                raise
            record.error_code = "staff_identity_conflict"
        else:
            record.staff = staff
            record.error_code = ""
        record.save()
    batch.revision += 1
    batch.save()
    audit(
        batch,
        user,
        "company_staff_batch_processed",
        metadata={"company_id": str(company.id)},
    )
    return batch


def batch_payload(batch):
    rows = list(batch.rows.select_related("staff").order_by("created_at", "id"))
    return {
        "id": str(batch.id),
        "company_id": str(batch.company.id),
        "revision": batch.revision,
        "complete": bool(rows) and all(row.staff_id for row in rows),
        "draft": {
            "batch_key": str(batch.id),
            "expected_revision": batch.revision,
            "rows": [
                {**row.input_payload, "row_key": str(row.row_key)}
                for row in rows
                if not row.staff_id
            ],
        },
        "results": [
            {
                "row_key": str(row.row_key),
                "staff_id": str(row.staff.id) if row.staff_id else None,
                "display_name": row.input_payload.get("display_name", ""),
                "status": "created" if row.staff_id else "rejected",
                "error_code": row.error_code,
            }
            for row in rows
        ],
    }
