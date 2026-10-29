"""Explicit bilateral notice reductions for personal fixed-term agreements."""

from copy import deepcopy
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from ..models import RentalConsentRecord
from .rental_phase2 import RentalConflict, fingerprint

VERSION = "contract_notice_bilateral_v1"
CAIRO = ZoneInfo("Africa/Cairo")
TERMINAL = {"accepted", "applied", "rejected"}
MESSAGES = {
    "termination_notice_unavailable": "The current contract notice could not be verified. Review the agreement before requesting an early end.",
    "termination_notice_basis_changed": "The agreement or notice date changed. Refresh and review a new termination proposal.",
    "termination_mode_mismatch": "Choose the termination mode that matches this exact date and the contract notice.",
    "termination_short_notice_ack_required": "Explicit agreement to shorten notice for this date is required. Financial obligations and possession return remain separate.",
    "termination_notice_review_required": "This termination needs a new notice review. Reject it and create a new proposal; earlier approval is not a notice waiver.",
    "termination_effective_date_elapsed": "The proposed end date has passed. Reject this proposal and review a new current or future date.",
    "termination_proposal_pending": "Resolve the existing termination or renewal before proposing another end.",
}


def fail(code):
    raise RentalConflict(MESSAGES[code], code=code)


def today():
    return timezone.localdate(timezone=CAIRO)


def material(lease):
    amendment = (
        lease.rental_changes.filter(
            kind="amendment", status="applied", terms=lease.terms
        )
        .order_by("-applied_at", "-created_at", "-pk")
        .first()
    )
    return {
        "lease_id": str(lease.id),
        "owner_id": str(lease.owner.id),
        "tenant_id": str(lease.tenant.id),
        "starts_on": str(lease.start_date),
        "natural_end_on": str(lease.end_date),
        "terms_digest": fingerprint(lease.terms),
        "document_id": str(lease.document_id) if lease.document_id else None,
        "document_hash": lease.document_hash,
        "applied_amendment": (
            {
                "id": str(amendment.id),
                "content_revision": amendment.content_revision,
                "document_id": (
                    str(amendment.document_id) if amendment.document_id else None
                ),
                "document_hash": amendment.document_hash,
            }
            if amendment
            else None
        ),
    }


def policy(lease):
    from core_apps.common.translation import translate_message

    terms = lease.terms if isinstance(lease.terms, dict) else {}
    clause = terms.get("termination_policy")
    days = clause.get("notice_days") if isinstance(clause, dict) else None
    valid_days = type(days) is int and days >= 0
    supported = (
        not lease.renter_company_id
        and not lease.legacy_read_only
        and terms.get("timezone") == "Africa/Cairo"
        and lease.start_date < lease.end_date
    )
    day = today()
    available = supported and valid_days
    try:
        earliest = (
            max(lease.start_date, day + timedelta(days=days)) if available else None
        )
    except OverflowError:
        available, valid_days, earliest = False, False, None
    return {
        "version": VERSION,
        "available": available,
        "policy_date": str(day),
        "timezone": "Africa/Cairo",
        "lease_revision": lease.revision,
        "notice_days": days if valid_days else None,
        "minimum_effective_on": str(max(lease.start_date, day)),
        "earliest_effective_on": str(earliest) if earliest else None,
        "natural_end_on": str(lease.end_date),
        "basis_digest": fingerprint(
            {
                "version": VERSION,
                "policy_date": str(day),
                "lease_revision": lease.revision,
                "material": material(lease),
            }
        ),
        "blocking_reasons": (
            []
            if available
            else [translate_message(MESSAGES["termination_notice_unavailable"])]
        ),
    }


def prepare(lease, effective_on, data):
    from ..rental_serializers_parts.termination_notice_serializer import (
        TerminationNoticeCreateSerializer,
    )

    serializer = TerminationNoticeCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    current = policy(lease)
    if values["notice_basis_digest"] != current["basis_digest"]:
        fail("termination_notice_basis_changed")
    if lease.status != "active" or lease.legacy_read_only or lease.renter_company_id:
        fail("termination_notice_review_required")
    if (
        not effective_on
        or not max(lease.start_date, today()) <= effective_on <= lease.end_date
    ):
        raise ValidationError(
            {"effective_on": "Choose a current or future date within this lease term."}
        )
    if competing_proposal(lease):
        fail("termination_proposal_pending")
    mode = values["termination_mode"]
    natural = effective_on == lease.end_date
    if natural:
        expected_mode = "natural_expiry"
    else:
        if not current["available"]:
            fail("termination_notice_unavailable")
        expected_mode = (
            "mutual_short_notice"
            if effective_on < date.fromisoformat(current["earliest_effective_on"])
            else "contract_notice"
        )
    if mode != expected_mode:
        fail("termination_mode_mismatch")
    short = mode == "mutual_short_notice"
    if short and values.get("short_notice_acknowledged") is not True:
        fail("termination_short_notice_ack_required")
    snapshot = {
        **{
            key: current[key]
            for key in (
                "version",
                "policy_date",
                "timezone",
                "lease_revision",
                "notice_days",
                "minimum_effective_on",
                "earliest_effective_on",
                "natural_end_on",
                "basis_digest",
            )
        },
        "created_at": timezone.now().isoformat(),
        "material": material(lease),
        "termination_policy": (
            deepcopy(lease.terms.get("termination_policy"))
            if isinstance(lease.terms, dict)
            else None
        ),
        "effective_on": str(effective_on),
        "mode": mode,
        "content_revision": 1,
        "requires_short_notice_acknowledgement": short,
        "financial_obligations_preserved": True,
    }
    snapshot["digest"] = fingerprint(snapshot)
    return snapshot, values


def snapshot_valid(item):
    value = item.termination_notice_snapshot
    return bool(
        isinstance(value, dict)
        and value.get("version") == VERSION
        and value.get("effective_on") == str(item.effective_on)
        and value.get("content_revision") == item.content_revision
        and value.get("digest")
        == fingerprint({key: val for key, val in value.items() if key != "digest"})
    )


def competing_proposal(lease, *, exclude=None):
    # Renewal may have been proposed after this termination was reviewed.
    return (
        lease.rental_changes.filter(
            Q(kind="renewal") & ~Q(status="rejected")
            | Q(kind="termination") & ~Q(status__in=["rejected", "applied"])
        )
        .exclude(pk=exclude)
        .exists()
    )


def blocker(item):
    if (
        item.kind != "termination"
        or item.lease.renter_company_id
        or item.status in TERMINAL
    ):
        return None
    if not snapshot_valid(item) or item.status != "proposed":
        return "termination_notice_review_required"
    if item.effective_on < today():
        return "termination_effective_date_elapsed"
    if item.lease.status != "active" or item.termination_notice_snapshot[
        "material"
    ] != material(item.lease):
        return "termination_notice_basis_changed"
    if competing_proposal(item.lease, exclude=item.pk):
        return "termination_proposal_pending"
    return None


def record_decision(item, actor, decision, acknowledged):
    # Separate evidence from ordinary approvals. Both remain inside the command transaction.
    snapshot = item.termination_notice_snapshot
    return RentalConsentRecord.objects.get_or_create(
        actor=actor,
        subject_kind="rentalchange",
        subject_id=item.id,
        subject_revision=item.revision,
        decision=f"termination_{decision}",
        defaults={
            "terms_digest": snapshot["digest"],
            "policy_version": VERSION,
            "snapshot": {
                "termination_notice": deepcopy(snapshot),
                "short_notice_acknowledged": acknowledged is True,
                "financial_obligations_preserved": True,
            },
        },
    )[0]


def reviewed_by(item, *, short_only=False):
    value = item.termination_notice_snapshot
    if not snapshot_valid(item):
        return []
    actors = []
    for consent in RentalConsentRecord.objects.filter(
        subject_kind="rentalchange",
        subject_id=item.id,
        decision__in=["termination_propose", "termination_accept"],
        terms_digest=value["digest"],
        policy_version=VERSION,
    ).select_related("actor"):
        if consent.snapshot.get("termination_notice") != value:
            continue
        if short_only and consent.snapshot.get("short_notice_acknowledged") is not True:
            continue
        actors.append(str(consent.actor.id))
    return sorted(set(actors))


def validate_accept(item, data):
    from ..rental_serializers_parts.termination_notice_serializer import (
        TerminationNoticeAcceptSerializer,
    )

    reason = blocker(item)
    if reason:
        fail(reason)
    serializer = TerminationNoticeAcceptSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    if (
        values["termination_notice_digest"]
        != item.termination_notice_snapshot["digest"]
    ):
        fail("termination_notice_basis_changed")
    if (
        item.termination_notice_snapshot["requires_short_notice_acknowledgement"]
        and values.get("short_notice_acknowledged") is not True
    ):
        fail("termination_short_notice_ack_required")
    return values


def require_application(item):
    if item.lease.renter_company_id:
        return
    if item.kind != "termination" or item.status != "accepted":
        fail("termination_notice_review_required")
    if not snapshot_valid(item):
        fail("termination_notice_review_required")
    if item.lease.status != "active":
        fail("termination_notice_basis_changed")
    if item.effective_on < today():
        fail("termination_effective_date_elapsed")
    if item.termination_notice_snapshot["material"] != material(item.lease):
        fail("termination_notice_basis_changed")
    if competing_proposal(item.lease, exclude=item.pk):
        fail("termination_proposal_pending")
    parties = {str(item.lease.owner.id), str(item.lease.tenant.id)}
    if not parties.issubset(set(item.approvals)) or not parties.issubset(
        set(reviewed_by(item))
    ):
        fail("termination_notice_review_required")
    if item.termination_notice_snapshot[
        "requires_short_notice_acknowledgement"
    ] and not parties.issubset(set(reviewed_by(item, short_only=True))):
        fail("termination_short_notice_ack_required")


def projection(item, user=None):
    from core_apps.common.translation import translate_message

    if item.kind != "termination" or item.lease.renter_company_id:
        return None
    value = deepcopy(item.termination_notice_snapshot)
    reason = blocker(item)
    acknowledged = reviewed_by(item, short_only=True)
    return {
        **value,
        "acknowledged_by": acknowledged,
        "current_user_acknowledged": bool(user and str(user.id) in acknowledged),
        "review_required": bool(reason),
        "blocking_reasons": [translate_message(MESSAGES[reason])] if reason else [],
    }
