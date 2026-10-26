"""Typed private records. A ledger statement is never a signed agreement."""

import hashlib
import json
import uuid
from django.core import signing
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils import timezone
from core_apps.users.models import User, AuthSession
from ..models import (
    RentalDocument,
    PaymentReceipt,
    FinalSettlement,
    PrivateAccessRevocation,
)

SALT = "sokoun.private-rental-document.v1"


def fail(document, reason):
    document.status, document.failure_code = "failed", reason
    document.revision += 1
    document.save(update_fields=["status", "failure_code", "revision", "updated_at"])
    return False


def generate(document):
    lease = document.lease
    payload = {
        "type": document.document_type,
        "lease_id": str(lease.id),
        "generated_at": timezone.now().isoformat(),
    }
    if lease.renter_company_id:
        payload["renter"] = {
            "kind": "company",
            "company_id": str(lease.renter_company.id),
            "name": lease.renter_company.name,
            "employees_are_debtors": False,
        }
    if document.document_type in {"contract", "change"}:
        from ..models import RentalSigningDocument
        from django.db import transaction
        from .signing_jobs import persist_original

        lookup = {"id": document.source_reference} if document.document_type == "contract" else {"change__id": document.source_reference}
        try:
            uuid.UUID(document.source_reference)
        except (ValueError, TypeError):
            return fail(document, "signed_source_artifact_unavailable")
        source = RentalSigningDocument.objects.filter(lease=lease, **lookup).exclude(completed_hash="").order_by("-source_revision").first()
        if source is None or not source.completed_content:
            return fail(document, "signed_source_artifact_unavailable")
        with transaction.atomic():
            persist_original(source)
        document.refresh_from_db()
        return document.status == "ready"
    if document.document_type == "receipt":
        try:
            uuid.UUID(document.source_reference)
        except (ValueError, TypeError):
            return fail(document, "receipt_source_unavailable")
        receipt = (
            PaymentReceipt.objects.select_related("payment_attempt__invoice")
            .filter(id=document.source_reference, payment_attempt__invoice__lease=lease)
            .first()
            if document.source_reference
            else None
        )
        if not receipt or not hasattr(receipt.payment_attempt, "invoice_allocation"):
            return fail(document, "receipt_source_unavailable")
        attempt = receipt.payment_attempt
        payload.update(
            {
                "receipt_id": str(receipt.id),
                "invoice_id": str(attempt.invoice.id),
                "payment_attempt_id": str(attempt.id),
                "payer_id": str(attempt.payer.id),
                "recorded_at": receipt.created_at.isoformat(),
                "payment_status_at_export": attempt.payment_status,
                "amount_minor": attempt.invoice_allocation.amount_minor,
                "currency": attempt.currency,
                "exponent": attempt.exponent,
                "components": attempt.invoice_allocation.components,
            }
        )
    elif document.document_type == "settlement":
        settlement = FinalSettlement.objects.filter(
            lease=lease, status="accepted"
        ).first()
        if not settlement:
            return fail(document, "accepted_settlement_unavailable")
        payload.update(
            {
                "adjustments": [
                    {
                        "id": str(a.id),
                        "original_settlement_id": str(settlement.id),
                        "reason": a.company_change.reason,
                        "lines": a.lines,
                        "accepted_by": a.accepted_by,
                        "execution_status": a.execution_status,
                        "execution_plan": a.execution_plan,
                        "executed_at": a.executed_at,
                    }
                    for a in settlement.adjustments.order_by("created_at")
                ],
                "settlement_id": str(settlement.id),
                "revision": settlement.revision,
                "lines": settlement.lines,
                "accepted_by": settlement.accepted_by,
                "execution_status": settlement.execution_status,
                "execution_plan": settlement.execution_plan,
                "currency": "EGP",
                "exponent": 2,
                "rent_balance_minor": settlement.rent_balance_minor,
                "deposit_to_return_minor": settlement.deposit_to_return_minor,
                "refund_due_minor": settlement.refund_due_minor,
                "total_due_minor": settlement.total_due_minor,
            }
        )
    elif document.document_type == "statement":
        rows = lease.ledger_transactions.prefetch_related("entries").order_by(
            "occurred_at", "pk"
        )
        if document.starts_on:
            rows = rows.filter(occurred_at__date__gte=document.starts_on)
        if document.ends_on_exclusive:
            rows = rows.filter(occurred_at__date__lt=document.ends_on_exclusive)
        payload.update(
            {
                "starts_on": str(document.starts_on) if document.starts_on else None,
                "ends_on_exclusive": (
                    str(document.ends_on_exclusive)
                    if document.ends_on_exclusive
                    else None
                ),
                "ledger": [
                    {
                        "reference": row.reference,
                        "kind": row.kind,
                        "occurred_at": row.occurred_at.isoformat(),
                        "entries": list(
                            row.entries.values(
                                "account",
                                "direction",
                                "amount_minor",
                                "currency",
                                "exponent",
                            )
                        ),
                    }
                    for row in rows
                ],
            }
        )
    else:
        return fail(document, "document_type_unsupported")
    content = json.dumps(
        payload, sort_keys=True, default=str, separators=(",", ":")
    ).encode()
    document.private_content = content
    document.sha256 = hashlib.sha256(content).hexdigest()
    document.storage_key = f"database:rental-document:{document.id}:{document.sha256}"
    document.status, document.failure_code, document.media_type = (
        "ready",
        "",
        "application/json",
    )
    document.revision += 1
    document.save()
    return True


def download_url(request, document):
    token = signing.dumps(
        {
            "document": str(document.id),
            "user": str(request.user.id),
            "epoch": request.user.security_epoch,
            "revision": document.revision,
            "digest": document.sha256,
            "session": (request.auth or {}).get("session_id"),
        },
        salt=SALT,
    )
    return (
        request.build_absolute_uri(
            reverse("rental-document-content", args=[document.id])
        )
        + "?token="
        + token
    )


def content_response(document_id, token):
    try:
        claims = signing.loads(token, salt=SALT, max_age=300)
        if claims["document"] != str(document_id):
            raise ValueError()
        user = User.objects.get(
            id=claims["user"], is_active=True, security_epoch=claims["epoch"]
        )
        if (
            claims.get("session")
            and not AuthSession.objects.filter(
                id=claims["session"],
                user=user,
                security_epoch=user.security_epoch,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).exists()
        ):
            raise ValueError()
        document = RentalDocument.objects.select_related("lease").get(
            id=document_id,
            status="ready",
            revision=claims["revision"],
            sha256=claims["digest"],
        )
        if document.lease.renter_company_id:
            from .company.tenancy_access import commercial_read

            if not commercial_read(document.lease, user):
                raise ValueError()
        elif user.pk not in {document.lease.owner_id, document.lease.tenant_id}:
            raise ValueError()
        if PrivateAccessRevocation.objects.filter(
            lease=document.lease, user=user
        ).exists():
            raise ValueError()
        content = bytes(document.private_content or b"")
        if not content or hashlib.sha256(content).hexdigest() != document.sha256:
            raise ValueError()
    except (
        signing.BadSignature,
        ValueError,
        KeyError,
        TypeError,
        User.DoesNotExist,
        RentalDocument.DoesNotExist,
    ):
        raise Http404()
    response = HttpResponse(content, content_type=document.media_type)
    response["Content-Disposition"] = (
        f'attachment; filename="{document.document_type}-{document.id}.{"pdf" if document.media_type == "application/pdf" else "json"}"'
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response
