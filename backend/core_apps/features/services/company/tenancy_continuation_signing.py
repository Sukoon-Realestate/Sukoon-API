"""Original-session recovery and authoritative signature completion for changes."""

from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ...models import CompanyTenancyChange, ChangeSigningSession, RentalChange
from ...providers import get_rental_provider, fake_provider_available
from ..rental_phase2 import RentalConflict
from ..rental_lifecycle.cases import open_system_case
from . import (
    tenancy_access as access,
    tenancy_changes as changes,
    tenancy_commercial as commercial,
)
from .tenancy_resolution import signing_role


def validate_review(item, change):
    commercial.revalidate(item, change)
    for role, identity in change.snapshot["required"].items():
        if change.decisions.get(role, {}).get("decision") != "accept":
            raise RentalConflict(
                "Every named participant must independently accept this exact revision."
            )
        changes.authorize_role(
            item, change, User.objects.get(id=identity), role, positive=True
        )


def get_change(item, data):
    change = get_object_or_404(
        CompanyTenancyChange,
        tenancy=item,
        id=data["change_id"],
        kind__in=commercial.KINDS,
    )
    if change.snapshot_digest != data["digest"]:
        raise RentalConflict("Review the exact continuation digest.")
    return change


def submit(item, user, data):
    access.require_role(item, user, {"owner"}, sensitive=True)
    change = get_change(item, data)
    if change.state != "accepted":
        raise RentalConflict("Complete all continuation reviews first.")
    validate_review(item, change)
    if not fake_provider_available():
        raise RentalConflict(
            "The signing provider is unavailable; accepted review is not a signature.",
            code="provider_unavailable",
        )
    event = change.rental_change
    generated = get_rental_provider().generate_agreement(
        event.id, event.revision, event.terms
    )
    event.document_id, event.document_hash = generated.document_id, generated.digest
    event.status = "pending_signatures"
    event.revision += 1
    event.save()
    change.state = "pending_signatures"
    change.save()
    return access.changed(item, user, "company_continuation_submitted")


def sign(item, user, data):
    change = get_change(item, data)
    role = data["role"]
    if not signing_role(role):
        raise PermissionDenied("Only actual contract signatories can sign this change.")
    changes.authorize_role(item, change, user, role, positive=True)
    event = change.rental_change
    if change.state != "pending_signatures":
        raise RentalConflict("This continuation is not awaiting signatures.")
    validate_review(item, change)
    # An expired URL is not proof of an unsigned document. Reuse the original
    # session until authoritative provider reconciliation resolves it.
    prior = event.signing_sessions.filter(signer=user).first()
    if prior:
        if prior.status != "completed" and prior.expires_at <= timezone.now():
            open_system_case(
                kind="company_continuation_signing",
                source_key=f"company-change-sign:{prior.id}",
                actor=user,
                lease=item.lease,
                reason="The original signing session needs reconciliation.",
                next_action="Query the original provider session; do not replace an unknown signature.",
            )
        return item
    if not fake_provider_available():
        raise RentalConflict(
            "The signing provider is unavailable.", code="provider_unavailable"
        )
    hosted = get_rental_provider().create_signing_session(
        event.id, user.id, data["request_key"]
    )
    ChangeSigningSession.objects.create(
        change=event,
        signer=user,
        request_key=data["request_key"],
        change_revision=event.revision,
        document_id=event.document_id,
        document_hash=event.document_hash,
        provider_session_id=hosted.provider_session_id,
        hosted_url=hosted.hosted_url,
        expires_at=timezone.now() + timedelta(minutes=30),
    )
    return access.changed(item, user, "company_continuation_signing_started")


@transaction.atomic
def complete(session):
    from core_apps.common.recovery import require_scope

    require_scope("company_authority")
    change = CompanyTenancyChange.objects.get(rental_change=session.change)
    item = change.tenancy
    item.lease = access.lock_lease(item.lease)
    change = CompanyTenancyChange.objects.select_for_update().get(pk=change.pk)
    event = RentalChange.objects.select_for_update().get(pk=change.rental_change_id)
    session = ChangeSigningSession.objects.select_for_update().get(pk=session.pk)
    if session.status == "completed":
        return event
    if (
        session.document_id != event.document_id
        or session.document_hash != event.document_hash
    ):
        raise RentalConflict("The provider result identifies a different document.")
    session.status, session.completed_at = "completed", timezone.now()
    session.save()
    event.signed_by = sorted(set(event.signed_by) | {str(session.signer.id)})
    required = {
        identity
        for role, identity in change.snapshot["required"].items()
        if signing_role(role)
    }
    resolving = change.state in {"resolution_pending", "resolved_unapplied"}
    if required.issubset(event.signed_by) and change.state != "resolved_unapplied":
        event.status = "signed"
    event.save()
    if resolving:
        return access.changed(
            item,
            session.signer,
            "company_original_signature_retained_during_resolution",
        ).lease.rental_changes.get(pk=event.pk)
    try:
        # Inner savepoint preserves the independently established signature
        # when a changed prerequisite prevents the business effect.
        with transaction.atomic():
            validate_review(item, change)
            if event.status == "signed":
                commercial.apply_signed(item, change)
    except (RentalConflict, PermissionDenied) as error:
        change.refresh_from_db()
        change.state = "review_required"
        change.save()
        open_system_case(
            kind="company_continuation_review",
            source_key=f"company-continuation:{change.id}",
            actor=session.signer,
            lease=item.lease,
            reason=str(error),
            next_action="Review retained signatures and exact source changes. Resume only after the same prerequisites are restored; never infer cancellation.",
        )
    return access.changed(
        item, session.signer, "company_continuation_signature_received"
    ).lease.rental_changes.get(pk=event.pk)


def resume(item, user, data):
    access.require_role(
        item, user, {"owner", "coordinator", "signer", "payer"}, sensitive=True
    )
    change = get_change(item, data)
    if change.state != "review_required":
        raise RentalConflict("Only a continuation awaiting review can resume.")
    validate_review(item, change)
    if change.rental_change.status == "signed":
        commercial.apply_signed(item, change)
    else:
        change.state = "pending_signatures"
        change.save()
    return access.changed(item, user, "company_continuation_resumed")
