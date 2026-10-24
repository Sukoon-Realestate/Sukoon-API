"""Issue immutable purchases into the existing invoice/line domain."""

import uuid
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import (
    AccountSubscription,
    IdempotencyRecord,
    BillingSourceLink,
    InvoiceLine,
    RentInvoice,
    SubscriptionPlan,
)
from .billing_catalog import plan_snapshot, workspace_for
from .rental_phase2 import RentalConflict, fingerprint as _fingerprint


def require_actor(user):
    if not user.is_active:
        raise PermissionDenied("An active account is required.")


def invoice_queryset(user, workspace, organization=None):
    require_actor(user)
    if organization:
        return (
            RentInvoice.objects.filter(organization=organization, workspace=workspace)
            .select_related("lease", "payer")
            .order_by("-created_at", "-id")
        )
    purchases = Q(
        payer=user,
        organization__isnull=True,
        purpose__in=[
            "subscription",
            "advertising",
            "maintenance",
            "promotion",
            "settlement",
            "adjustment",
            "deposit",
        ],
    ) & (Q(workspace=workspace) | Q(purchase_snapshot__workspace="both"))
    # Rent receivables remain in owner financial screens, not own purchases.
    if workspace == "tenant":
        purchases |= Q(
            lease__tenant=user, lease__renter_company__isnull=True, purpose="rent"
        )
    return (
        RentInvoice.objects.filter(purchases)
        .select_related("lease", "payer")
        .order_by("-created_at", "-id")
    )


def authorized_invoice(user, invoice_id, lock=False):
    query = RentInvoice.objects.select_related("lease", "payer")
    if lock:
        query = query.select_for_update(of=("self",))
    invoice = get_object_or_404(query, id=invoice_id)
    require_actor(user)
    if invoice.organization_id:
        from .commerce_access import organization_for

        organization_for(user, invoice.organization.id)
        return invoice
    if invoice.lease_id and invoice.lease.renter_company_id:
        from .company.tenancy_access import commercial_read
        from rest_framework.exceptions import NotFound

        if not commercial_read(invoice.lease, user):
            raise NotFound()
        return invoice
    payer_id = (
        invoice.lease.tenant_id if invoice.purpose == "rent" else invoice.payer_id
    )
    if payer_id != user.pk:
        from rest_framework.exceptions import NotFound

        raise NotFound()
    return invoice


@transaction.atomic
def issue_purchase(user, body):
    require_actor(user)
    get_user_model().objects.select_for_update().get(pk=user.pk)
    key, workspace = body["request_key"], workspace_for(body["workspace"])
    from .commerce_access import organization_for

    organization = organization_for(
        user, body.get("organization_id"), lock=True, pay=True
    )
    fingerprint = _fingerprint(body)
    record = IdempotencyRecord.objects.filter(
        user=user, operation="billing.issue", request_key=key
    ).first()
    if record:
        if record.fingerprint != fingerprint:
            raise RentalConflict(
                "This request key was used for different data.",
                code="idempotency_conflict",
            )
        return authorized_invoice(user, record.result_subject_id), False
    if body["purpose"] == "subscription":
        plan = get_object_or_404(
            SubscriptionPlan.objects.select_for_update(), id=body.get("plan_id")
        )
        if (plan.audience == "organization") != bool(organization):
            raise ValidationError(
                {"organization_id": "The plan audience does not match this context."}
            )
        if organization:
            organization_for(user, organization.id, pay=True, amount=plan.amount_minor)
        if not plan.active or plan.workspace not in (workspace, "both"):
            raise ValidationError("The selected plan is unavailable.")
        if plan.revision != body.get("plan_revision"):
            raise RentalConflict(
                "The selected plan changed. Review it again.", code="stale_revision"
            )
        scopes = (
            ("tenant", "owner", "both")
            if plan.workspace == "both"
            else (workspace, "both")
        )
        if (
            AccountSubscription.objects.filter(
                **(
                    {"organization": organization}
                    if organization
                    else {"user": user, "organization__isnull": True}
                ),
                workspace__in=scopes,
                store_status__in=["", "active", "grace"],
            )
            .filter(
                Q(ends_at__gt=timezone.now())
                | Q(store_status="grace", grace_ends_at__gt=timezone.now())
            )
            .exists()
        ):
            raise RentalConflict(
                "A subscription is already active for this workspace.",
                code="subscription_active",
            )
        if (
            RentInvoice.objects.filter(
                **(
                    {"organization": organization}
                    if organization
                    else {"payer": user, "organization__isnull": True}
                ),
                purpose="subscription",
                status__in=["due", "partially_paid"],
            )
            .filter(Q(workspace__in=scopes) | Q(purchase_snapshot__workspace="both"))
            .exists()
        ):
            raise RentalConflict(
                "Review or cancel your existing unpaid subscription invoice.",
                code="invoice_exists",
            )
        snapshot = plan_snapshot(plan)
        reference = f"subscription:{user.id}:{key}"
    elif body["purpose"] == "advertising":
        if organization:
            raise ValidationError(
                {"organization_id": "Organization advertising is not configured."}
            )
        reference = f"advertising:{body.get('advertisement_id')}"
        existing = RentInvoice.objects.filter(
            purpose="advertising", business_reference=reference, payer=user
        ).first()
        if existing:
            if existing.workspace != workspace:
                raise RentalConflict(
                    "The existing advertisement invoice belongs to another workspace.",
                    code="idempotency_conflict",
                )
            IdempotencyRecord.objects.create(
                user=user,
                operation="billing.issue",
                request_key=key,
                fingerprint=fingerprint,
                response_data={"invoice_id": str(existing.id)},
                response_status=200,
                result_subject_id=existing.id,
                result_revision=existing.revision,
            )
            return existing, False
        from .billing_advertising import advertising_snapshot

        snapshot = advertising_snapshot(user, body)
    else:
        raise ValidationError("Unsupported purchase purpose.")
    invoice = RentInvoice.objects.create(
        purpose=body["purpose"],
        payer=user,
        organization=organization,
        workspace=workspace,
        reference=f"INV-{uuid.uuid4().hex[:20].upper()}",
        business_reference=reference,
        amount_minor=snapshot["amount_minor"],
        charges_minor=snapshot["amount_minor"],
        currency=snapshot["currency"],
        exponent=snapshot["exponent"],
        due_date=timezone.localdate(),
        purchase_snapshot=snapshot,
    )
    if body["purpose"] == "advertising":
        BillingSourceLink.objects.create(
            invoice=invoice,
            source_kind="advertising",
            source_id=body["advertisement_id"],
        )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type=body["purpose"],
        description=snapshot["name_en"],
        amount_minor=invoice.amount_minor,
        currency=invoice.currency,
        exponent=invoice.exponent,
        source={"description_ar": snapshot["name_ar"], "quantity": 1},
    )
    IdempotencyRecord.objects.create(
        user=user,
        operation="billing.issue",
        request_key=key,
        fingerprint=fingerprint,
        response_data={"invoice_id": str(invoice.id)},
        response_status=201,
        result_subject_id=invoice.id,
        result_revision=invoice.revision,
    )
    return invoice, True


@transaction.atomic
def cancel_invoice(user, invoice_id, body):
    invoice = lock_purchase_invoice(user, invoice_id)
    if invoice.organization_id:
        from .commerce_access import organization_for

        organization_for(
            user,
            invoice.organization.id,
            lock=True,
            pay=True,
            amount=invoice.amount_minor,
        )
    operation = f"billing.cancel.{invoice.id}"
    fingerprint = _fingerprint(body)
    record = IdempotencyRecord.objects.filter(
        user=user, operation=operation, request_key=body["request_key"]
    ).first()
    if record:
        if record.fingerprint != fingerprint:
            raise RentalConflict(
                "This request key was used for different data.",
                code="idempotency_conflict",
            )
        return invoice
    if invoice.purpose not in {"subscription", "advertising", "promotion"}:
        raise RentalConflict(
            "Correct this obligation through its original workflow.",
            code="source_action_required",
        )
    if invoice.payment_attempts.filter(
        payment_status__in=["created", "pending", "authorized", "captured"]
    ).exists():
        raise RentalConflict(
            "Resolve the original payment before cancelling.",
            code="payment_in_progress",
        )
    if invoice.status != "cancelled":
        if invoice.revision != body["expected_revision"] or invoice.status != "due":
            raise RentalConflict(
                "This invoice cannot be cancelled.", code="stale_revision"
            )
        invoice.status = "cancelled"
        invoice.revision += 1
        invoice.save(update_fields=["status", "revision", "updated_at"])
        if invoice.purpose == "promotion":
            from ..models import BoostCampaign

            BoostCampaign.objects.filter(
                id=invoice.purchase_snapshot["subject_id"], status="pending"
            ).update(status="cancelled")
    IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=body["request_key"],
        fingerprint=fingerprint,
        response_data={"invoice_id": str(invoice.id)},
        response_status=200,
        result_subject_id=invoice.id,
        result_revision=invoice.revision,
    )
    return invoice


def lock_purchase_invoice(user, invoice_id):
    # Every commerce writer takes actor -> company -> invoice locks.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    candidate = get_object_or_404(RentInvoice, id=invoice_id)
    if candidate.organization_id:
        from .commerce_access import organization_for

        organization_for(user, candidate.organization.id, lock=True)
    if candidate.purpose == "promotion":
        from ..models import BoostCampaign
        from core_apps.properties.models import Property

        campaign = BoostCampaign.objects.filter(
            id=candidate.purchase_snapshot.get("subject_id")
        ).first()
        if campaign:
            Property.objects.select_for_update().get(pk=campaign.property_id)
    if candidate.purpose == "maintenance":
        from ..models import MaintenanceRequest
        from .rental_lifecycle.locks import lock_financial_lease

        source = (
            MaintenanceRequest.objects.select_related("lease")
            .filter(id=candidate.purchase_snapshot.get("subject_id"))
            .first()
        )
        if source:
            lock_financial_lease(source.lease)
    return authorized_invoice(user, invoice_id, lock=True)
