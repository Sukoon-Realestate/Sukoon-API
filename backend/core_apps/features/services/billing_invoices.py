"""Issue immutable purchases into the existing invoice/line domain."""
import uuid
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import AccountSubscription, IdempotencyRecord, InvoiceLine, RentInvoice, SubscriptionPlan
from .billing_catalog import plan_snapshot, workspace_for
from .rental_phase2 import RentalConflict, fingerprint as _fingerprint


def require_actor(user):
    if not user.is_active:
        raise PermissionDenied("An active account is required.")


def invoice_queryset(user, workspace):
    require_actor(user)
    purchases = Q(payer=user, purpose__in=["subscription", "advertising"]) & (
        Q(workspace=workspace) | Q(purchase_snapshot__workspace="both"))
    # Rent receivables remain in owner financial screens, not own purchases.
    if workspace == "tenant":
        purchases |= Q(lease__tenant=user, purpose="rent")
    return RentInvoice.objects.filter(purchases).select_related("lease", "payer").order_by("-created_at", "-id")


def authorized_invoice(user, invoice_id, lock=False):
    query = RentInvoice.objects.select_related("lease", "payer")
    if lock:
        query = query.select_for_update(of=("self",))
    invoice = get_object_or_404(query, id=invoice_id)
    payer_id = invoice.lease.tenant_id if invoice.purpose == "rent" else invoice.payer_id
    if payer_id != user.pk:
        from rest_framework.exceptions import NotFound
        raise NotFound()
    return invoice


@transaction.atomic
def issue_purchase(user, body):
    require_actor(user)
    get_user_model().objects.select_for_update().get(pk=user.pk)
    key, workspace = body["request_key"], workspace_for(body["workspace"])
    fingerprint = _fingerprint(body)
    record = IdempotencyRecord.objects.filter(user=user, operation="billing.issue", request_key=key).first()
    if record:
        if record.fingerprint != fingerprint:
            raise RentalConflict("This request key was used for different data.", code="idempotency_conflict")
        return authorized_invoice(user, record.result_subject_id), False
    if body["purpose"] == "subscription":
        plan = get_object_or_404(SubscriptionPlan.objects.select_for_update(), id=body.get("plan_id"))
        if not plan.active or plan.workspace not in (workspace, "both"):
            raise ValidationError("The selected plan is unavailable.")
        if plan.revision != body.get("plan_revision"):
            raise RentalConflict("The selected plan changed. Review it again.", code="stale_revision")
        scopes = ("tenant", "owner", "both") if plan.workspace == "both" else (workspace, "both")
        if AccountSubscription.objects.filter(user=user, workspace__in=scopes, cancelled_at__isnull=True, ends_at__gt=timezone.now()).exists():
            raise RentalConflict("A subscription is already active for this workspace.", code="subscription_active")
        if RentInvoice.objects.filter(payer=user, purpose="subscription", status__in=["due", "partially_paid"]).filter(Q(workspace__in=scopes) | Q(purchase_snapshot__workspace="both")).exists():
            raise RentalConflict("Review or cancel your existing unpaid subscription invoice.", code="invoice_exists")
        snapshot = plan_snapshot(plan)
        reference = f"subscription:{user.id}:{key}"
    elif body["purpose"] == "advertising":
        reference = f"advertising:{body.get('advertisement_id')}"
        existing = RentInvoice.objects.filter(purpose="advertising", business_reference=reference, payer=user).first()
        if existing:
            IdempotencyRecord.objects.create(user=user, operation="billing.issue", request_key=key,
                fingerprint=fingerprint, response_data={"invoice_id": str(existing.id)}, response_status=200,
                result_subject_id=existing.id, result_revision=existing.revision)
            return existing, False
        from .billing_advertising import advertising_snapshot
        snapshot = advertising_snapshot(user, body)
    else:
        raise ValidationError("Unsupported purchase purpose.")
    invoice = RentInvoice.objects.create(
        purpose=body["purpose"], payer=user, workspace=workspace,
        reference=f"INV-{uuid.uuid4().hex[:20].upper()}", business_reference=reference,
        amount_minor=snapshot["amount_minor"], charges_minor=snapshot["amount_minor"],
        currency=snapshot["currency"], exponent=snapshot["exponent"],
        due_date=timezone.localdate(), purchase_snapshot=snapshot,
    )
    InvoiceLine.objects.create(invoice=invoice, line_type=body["purpose"],
        description=snapshot["name_en"], amount_minor=invoice.amount_minor,
        currency=invoice.currency, exponent=invoice.exponent,
        source={"description_ar": snapshot["name_ar"], "quantity": 1})
    IdempotencyRecord.objects.create(user=user, operation="billing.issue", request_key=key,
        fingerprint=fingerprint, response_data={"invoice_id": str(invoice.id)}, response_status=201,
        result_subject_id=invoice.id, result_revision=invoice.revision)
    return invoice, True


@transaction.atomic
def cancel_invoice(user, invoice_id, body):
    invoice = authorized_invoice(user, invoice_id, lock=True)
    operation = f"billing.cancel.{invoice.id}"
    fingerprint = _fingerprint(body)
    record = IdempotencyRecord.objects.filter(user=user, operation=operation, request_key=body["request_key"]).first()
    if record:
        if record.fingerprint != fingerprint:
            raise RentalConflict("This request key was used for different data.", code="idempotency_conflict")
        return invoice
    if invoice.purpose == "rent":
        raise RentalConflict("Rental obligations cannot be cancelled here.")
    if invoice.status != "cancelled":
        if invoice.revision != body["expected_revision"] or invoice.status != "due":
            raise RentalConflict("This invoice cannot be cancelled.", code="stale_revision")
        invoice.status = "cancelled"
        invoice.revision += 1
        invoice.save(update_fields=["status", "revision", "updated_at"])
    IdempotencyRecord.objects.create(user=user, operation=operation, request_key=body["request_key"],
        fingerprint=fingerprint, response_data={"invoice_id": str(invoice.id)}, response_status=200,
        result_subject_id=invoice.id, result_revision=invoice.revision)
    return invoice
