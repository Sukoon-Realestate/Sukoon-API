"""Account-bound family sharing of exact redacted rental resources."""

from datetime import timedelta
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core_apps.users.models import User
from .models import Lease, RentInvoice, PaymentReceipt, RentalSummaryGrant
from .student_serializers import SummaryGrantBody, CommandBody
from .rental_lifecycle_views.common import validated
from .services.planning import planning_api, mutate, page
from .services.rental_lifecycle.common import audit
from .services.rental_phase2 import RentalConflict


def grant_queryset(user):
    return RentalSummaryGrant.objects.filter(
        Q(granted_by=user, lease__tenant=user)
        | Q(recipient=user, revoked_at__isnull=True, expires_at__gt=timezone.now())
    ).filter(lease__tenant_id=F("granted_by_id"))


def invoice_summary(item):
    return {
        "id": str(item.id),
        "amount_minor": item.amount_minor,
        "currency": item.currency,
        "exponent": item.exponent,
        "status": item.status,
        "due_on": str(item.due_date),
    }


def own_invoices(lease, user):
    return RentInvoice.objects.filter(lease=lease).filter(
        Q(payer=user) | Q(payer__isnull=True)
    )


def receipt_summary(item):
    attempt = item.payment_attempt
    return {
        "id": str(item.id),
        "title": item.title,
        "status": item.status,
        "payment_status": attempt.payment_status,
        "amount_minor": attempt.amount_minor,
        "currency": attempt.currency,
        "exponent": attempt.exponent,
        "confirmed_at": (
            attempt.confirmed_at.isoformat() if attempt.confirmed_at else None
        ),
    }


def payload(item, user):
    current = item.revoked_at is None and item.expires_at > timezone.now()
    lease = item.lease
    value = {
        "id": str(item.id),
        "revision": item.revision,
        "scopes": item.scopes,
        "status": "active" if current else "revoked" if item.revoked_at else "expired",
        "expires_at": item.expires_at.isoformat(),
        "student_name": item.granted_by.get_full_name,
        "recipient_name": (
            item.recipient.get_full_name if user.pk == item.granted_by_id else ""
        ),
        "allowed_actions": (
            ["revoke"] if current and user.pk == item.granted_by_id else []
        ),
        "blocking_reasons": [],
        "payment_authorized": False,
        "tenancy_authority": False,
    }
    if current and "booking" in item.scopes:
        value["booking"] = {
            "accommodation": lease.property.title,
            "space": lease.offer_snapshot.get("name", ""),
            "starts_on": str(lease.start_date),
            "ends_on_exclusive": str(lease.end_date),
            "status": lease.status,
            "monthly_rent": {
                "amount_minor": lease.rent_amount_minor,
                "currency": lease.rent_currency,
                "exponent": 2,
            },
        }
    if current and "invoice" in item.scopes:
        value["invoice"] = invoice_summary(item.invoice)
    if current and "receipt" in item.scopes:
        value["receipt"] = receipt_summary(item.receipt)
    return value


@planning_api(["GET"], "rental_summary_sharing")
def summary_options(request, lease_id):
    lease = get_object_or_404(
        Lease, id=lease_id, tenant=request.user, legacy_read_only=False
    )
    return Response(
        {
            "lease_id": str(lease.id),
            "revision": lease.revision,
            "invoices": [
                invoice_summary(row)
                for row in own_invoices(lease, request.user).order_by("due_date", "id")[
                    :100
                ]
            ],
            "receipts": [
                receipt_summary(row)
                for row in PaymentReceipt.objects.filter(
                    payment_attempt__invoice__lease=lease,
                    payment_attempt__payer=request.user,
                )
                .select_related("payment_attempt")
                .order_by("-created_at")[:100]
            ],
        }
    )


@planning_api(["GET", "POST"], "rental_summary_sharing")
def summary_grants(request, lease_id=None):
    if request.method == "GET":
        items = grant_queryset(request.user)
        if lease_id:
            get_object_or_404(Lease, id=lease_id, tenant=request.user)
            items = items.filter(lease__id=lease_id, granted_by=request.user)
        else:
            items = items.filter(recipient=request.user)
        return page(
            request,
            items.order_by("-created_at", "id"),
            lambda row: payload(row, request.user),
        )
    if not lease_id:
        raise ValidationError({"lease_id": "Choose your own rental."})
    data = validated(SummaryGrantBody, request.data)

    def load():
        get_object_or_404(
            Lease.objects.select_for_update(),
            id=lease_id,
            tenant=request.user,
            legacy_read_only=False,
        )
        return None

    def create(_, revision):
        if data["expected_revision"] != 0 or data["consent"] is not True:
            raise ValidationError(
                {"consent": "Explicit consent to the selected scopes is required."}
            )
        if (
            not timezone.now()
            < data["expires_at"]
            <= timezone.now() + timedelta(days=30)
        ):
            raise ValidationError({"expires_at": "Choose an expiry within 30 days."})
        lease = Lease.objects.get(id=lease_id, tenant=request.user)
        if lease.status not in {"signed", "active", "termination_pending", "ended"}:
            raise RentalConflict(
                "Use a supported signed agreement.", code="invalid_state"
            )
        recipient = get_object_or_404(
            User, email__iexact=data["recipient_email"], is_active=True
        )
        if recipient == request.user:
            raise ValidationError(
                {
                    "recipient_email": "Choose the intended recipient's registered account."
                }
            )
        invoice = (
            get_object_or_404(
                own_invoices(lease, request.user), id=data.get("invoice_id")
            )
            if "invoice" in data["scopes"]
            else None
        )
        receipt = (
            get_object_or_404(
                PaymentReceipt,
                id=data.get("receipt_id"),
                payment_attempt__invoice__lease=lease,
                payment_attempt__payer=request.user,
            )
            if "receipt" in data["scopes"]
            else None
        )
        item = RentalSummaryGrant.objects.create(
            lease=lease,
            granted_by=request.user,
            recipient=recipient,
            scopes=sorted(set(data["scopes"])),
            invoice=invoice,
            receipt=receipt,
            expires_at=data["expires_at"],
        )
        audit(
            item,
            request.user,
            "rental_summary.granted",
            metadata={"scopes": item.scopes},
        )
        return item

    return mutate(
        request,
        f"rental_summary.create.{lease_id}",
        load,
        create,
        lambda row: payload(row, request.user),
        creating=True,
    )


@planning_api(["POST"], "rental_summary_sharing")
def revoke_summary(request, grant_id):
    validated(CommandBody, request.data)

    def revoke(item, revision):
        item.revoked_at = timezone.now()
        item.revision += 1
        item.save(update_fields=["revoked_at", "revision", "updated_at"])
        audit(item, request.user, "rental_summary.revoked")
        return item

    return mutate(
        request,
        f"rental_summary.revoke.{grant_id}",
        lambda: get_object_or_404(
            grant_queryset(request.user).select_for_update(of=("self",)),
            id=grant_id,
            granted_by=request.user,
        ),
        revoke,
        lambda row: payload(row, request.user),
    )
