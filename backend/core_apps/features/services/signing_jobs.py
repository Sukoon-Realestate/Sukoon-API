"""Durable creation and read-only reconciliation; an unknown POST is never resent."""

import hashlib
import json
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException
from ..models import (
    RentalSigningDocument,
    SigningSession,
    ChangeSigningSession,
    RentalDocument,
)
from . import signwell_client
from .signing_documents import recipients_for


def _result(result):
    fields = {
        key: result.get(key)
        for key in ("id", "status", "test_mode", "metadata", "created_at", "updated_at")
    }
    fields["recipients"] = [
        {
            key: row.get(key)
            for key in (
                "id",
                "name",
                "email",
                "embedded_signing_url",
                "status",
                "signed_at",
                "completed_at",
            )
        }
        for row in result["recipients"]
    ]
    fields["checked_at"] = timezone.now().isoformat()
    return fields


def _source_current(document):
    source = document.change or document.lease
    if not (
        source.document_id == document.id
        and source.document_hash == document.source_hash
        and source.status == "pending_signatures"
    ):
        return False
    if json.loads(json.dumps(source.terms, default=str)) != document.snapshot["terms"]:
        return False
    try:
        parties = recipients_for(document.lease, document.change)
    except APIException:
        return False
    return {row["id"] for row in parties} == {row["id"] for row in document.recipients}


def _store_fact(identity, result, content=None):
    with transaction.atomic():
        row = RentalSigningDocument.objects.select_for_update().get(pk=identity)
        provider_id = signwell_client.verified(row, result)
        if row.applied_at or (
            row.completed_hash and str(result.get("status", "")).lower() != "completed"
        ):
            return row
        row.provider_document_id = provider_id
        row.provider_result = _result(result)
        row.claimed_at = None
        row.failure_code = ""
        row.next_check_at = timezone.now() + timedelta(minutes=1)
        status = str(result.get("status", "")).lower()
        if status == "completed":
            row.status = "completed" if content else "awaiting_pdf"
            row.completed_at = row.completed_at or timezone.now()
            if content:
                digest = hashlib.sha256(content).hexdigest()
                if row.completed_hash and row.completed_hash != digest:
                    raise signwell_client.SigningTransportError(
                        "signed_original_changed"
                    )
                row.completed_content, row.completed_hash = content, digest
        elif status in {"canceled", "cancelled", "declined", "expired"}:
            row.status = "closed"
            row.failure_code = "provider_document_" + status
        elif status in {"sent", "viewed", "pending"}:
            row.status = "pending"
        else:
            row.status, row.failure_code = "unknown", "provider_document_not_ready"
        row.save()
    return row


def _claim(identity):
    with transaction.atomic():
        # Match business mutations: property/company -> lease -> document.
        from .rental_lifecycle.locks import lock_financial_lease

        initial = RentalSigningDocument.objects.get(id=identity)
        lock_financial_lease(initial.lease)
        row = RentalSigningDocument.objects.select_for_update().get(id=identity)
        now = timezone.now()
        if row.status in {"closed", "failed", "applied", "review_required"}:
            return None, None
        if row.claimed_at and row.claimed_at > now - timedelta(minutes=2):
            return None, None
        if row.status == "requesting":
            # The worker can die after provider acceptance but before receipt persistence.
            row.status, row.failure_code = "unknown", "creation_result_unknown"
        if row.status == "completed":
            return row, "apply"
        if row.next_check_at and row.next_check_at > now:
            return None, None
        if row.status == "prepared":
            from .rental_lifecycle.inventory import hold_coverage

            current = _source_current(row) and (
                row.change_id or hold_coverage(row.lease)
            )
            if current and row.lease.renter_company_id:
                try:
                    if row.change_id:
                        from .company.tenancy_continuation_signing import (
                            validate_review,
                        )

                        validate_review(
                            row.lease.company_tenancy, row.change.company_review
                        )
                    else:
                        from .company.tenancy_contracts import validate_unsigned

                        validate_unsigned(row.lease.company_tenancy)
                except APIException:
                    current = False
            if not current:
                row.status, row.failure_code = "closed", "source_changed_before_send"
                row.save()
                return None, None
            row.status = "requesting"
            operation = "create"
        elif row.provider_document_id:
            operation = "query"
        else:
            operation = "hints"
        row.attempts += 1
        row.claimed_at = now
        row.save()
        return row, operation


def run(identity):
    if not signwell_client.ready():
        if (
            RentalSigningDocument.objects.filter(id=identity, status="completed")
            .exclude(completed_hash="")
            .exists()
        ):
            return apply(identity)
        return "unavailable"
    row, operation = _claim(identity)
    if row is None:
        return "waiting"
    if operation == "apply":
        return apply(row.id)
    try:
        if operation == "create":
            result = signwell_client.create(row)
        elif operation == "query":
            result = signwell_client.retrieve(row.provider_document_id)
        else:
            for hint in row.hints.filter(checked_at__isnull=True).order_by("pk")[:5]:
                try:
                    result = signwell_client.retrieve(hint.provider_document_id)
                except signwell_client.SigningTransportError as error:
                    if error.code != "signing_provider_http_404":
                        raise
                    hint.checked_at = timezone.now()
                    hint.save(update_fields=["checked_at", "updated_at"])
                    continue
                try:
                    signwell_client.verified(row, result)
                except signwell_client.SigningTransportError:
                    hint.checked_at = timezone.now()
                    hint.save(update_fields=["checked_at", "updated_at"])
                    continue
                hint.accepted, hint.checked_at = True, timezone.now()
                hint.save(update_fields=["accepted", "checked_at", "updated_at"])
                break
            else:
                RentalSigningDocument.objects.filter(pk=row.pk).update(
                    claimed_at=None, next_check_at=timezone.now() + timedelta(minutes=1)
                )
                return "unknown"
        signwell_client.verified(row, result)
        # Save the provider identity before downloading; a PDF timeout only retries GET.
        row = _store_fact(row.pk, result)
        if str(result.get("status", "")).lower() == "completed":
            content = signwell_client.completed_pdf(row.provider_document_id)
            row = _store_fact(row.pk, result, content)
            return apply(row.id)
        return row.status
    except signwell_client.SigningTransportError as error:
        with transaction.atomic():
            current = RentalSigningDocument.objects.select_for_update().get(pk=row.pk)
            if current.applied_at:
                return "applied"
            if operation == "create" and not current.provider_document_id:
                current.status = (
                    "unknown"
                    if error.uncertain or error.code == "signing_document_mismatch"
                    else "failed"
                )
            current.failure_code = error.code
            current.claimed_at = None
            current.next_check_at = timezone.now() + timedelta(minutes=1)
            current.save()
        return "unknown" if error.uncertain else "waiting"


def persist_original(document):
    if not document.completed_content or not document.completed_hash:
        return
    artifact, _ = RentalDocument.objects.get_or_create(
        lease=document.lease,
        document_type="change" if document.change_id else "contract",
        source_reference=str(document.change.id if document.change_id else document.id),
        defaults={"title": "Signed agreement / العقد الموقع"},
    )
    artifact = RentalDocument.objects.select_for_update().get(pk=artifact.pk)
    if artifact.status == "ready" and artifact.sha256 == document.completed_hash:
        return
    if artifact.status == "ready" and artifact.private_content:
        raise signwell_client.SigningTransportError("signed_original_changed")
    artifact.private_content = document.completed_content
    artifact.sha256 = document.completed_hash
    artifact.media_type = "application/pdf"
    artifact.storage_key = f"database:rental-document:{artifact.id}:{artifact.sha256}"
    artifact.status, artifact.failure_code = "ready", ""
    artifact.revision += 1
    artifact.save()


def apply(identity):
    row = RentalSigningDocument.objects.get(id=identity)
    if row.applied_at:
        return "applied"
    from .rental_lifecycle.locks import lock_financial_lease
    from .rental_lifecycle.cases import open_system_case
    from .signing_completion import complete_signature
    from ..rental_phase5_views_parts.change_signing_session import (
        complete_change_signature,
    )

    # The immutable provider fact survives a failed business transition.
    with transaction.atomic():
        lock_financial_lease(row.lease)
        row = RentalSigningDocument.objects.select_for_update().get(pk=row.pk)
        if row.applied_at:
            return "applied"
        if not row.completed_content:
            return "waiting"
        persist_original(row)
        try:
            with transaction.atomic():
                if not _source_current(row):
                    from .rental_phase2 import RentalConflict

                    raise RentalConflict(
                        "The signed source changed; reconcile the original document."
                    )
                model = ChangeSigningSession if row.change_id else SigningSession
                for recipient in row.recipients:
                    session = (
                        model.objects.filter(
                            document_id=row.id,
                            document_hash=row.source_hash,
                            signer__id=recipient["id"],
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    if session is None:
                        from .rental_phase2 import RentalConflict

                        raise RentalConflict(
                            "A named signatory has no authorized signing session."
                        )
                    if row.change_id:
                        complete_change_signature(session.provider_session_id)
                    else:
                        complete_signature(session.provider_session_id)
                    session.refresh_from_db()
                    if session.status != "completed":
                        from .rental_phase2 import RentalConflict

                        raise RentalConflict(
                            "The provider fact requires review against current signing authority."
                        )
        except APIException:
            row.status, row.failure_code = (
                "review_required",
                "signed_source_requires_review",
            )
            open_system_case(
                kind=(
                    "company_tenancy_review"
                    if row.lease.renter_company_id
                    else "agreement_terms_review"
                ),
                source_key=f"signwell:{row.id}",
                lease=row.lease,
                reason="The provider confirmed the original signed document after its local signing conditions changed.",
                next_action="Review the original document and signing sessions. Do not create a replacement signature or repeat a payment.",
            )
        else:
            row.status, row.applied_at = "applied", timezone.now()
        row.save()
        return row.status


def drain(limit=5):
    from django.db.models import Q

    ids = (
        RentalSigningDocument.objects.filter(
            status__in=[
                "prepared",
                "requesting",
                "unknown",
                "pending",
                "awaiting_pdf",
                "completed",
            ]
        )
        .filter(Q(next_check_at__isnull=True) | Q(next_check_at__lte=timezone.now()))
        .order_by("updated_at")
        .values_list("id", flat=True)[:limit]
    )
    return {str(identity): run(identity) for identity in ids}
