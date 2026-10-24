"""Shared terms validation and explicit answer-to-terms commands."""

import copy
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...models import ReservationHold, TenancyInvitation
from ..rental_phase2 import RentalConflict
from .common import require_revision, audit
from .consents import record_consent
from .notifications import record_rental_event


def money_minor_from_offer(snapshot):
    try:
        return int(
            (Decimal(str(snapshot["terms"]["price"])) * 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
    except (KeyError, TypeError, InvalidOperation):
        raise ValidationError({"offer_id": "The offer has no valid monthly price."})


def _json_safe(value):
    return json.loads(json.dumps(value, default=str))


def validate_terms_offer(terms, snapshot):
    if snapshot.get("terms", {}).get("price_period") != "monthly":
        raise ValidationError({"offer_id": "V1 supports monthly offers only."})
    if terms["monthly_rent"]["amount_minor"] != money_minor_from_offer(snapshot):
        raise RentalConflict(
            "The agreement rent does not match the selected offer.",
            code="document_changed",
        )


def release_proposal_holds(proposal):
    for hold in ReservationHold.objects.select_for_update().filter(
        proposal=proposal, lease__isnull=True, status="active"
    ):
        hold.day_locks.all().delete()
        hold.status, hold.released_at, hold.revision = (
            "released",
            timezone.now(),
            hold.revision + 1,
        )
        hold.save()


def propose_answer(item, actor, data):
    from ..shared_housing.access import guard_individual
    guard_individual(item.interest)
    require_revision(item, data["expected_revision"])
    if item.invitations.filter(lease__isnull=False).exists() or item.status in {
        "rejected",
        "superseded",
    }:
        raise RentalConflict(
            "Use the agreement change workflow for a committed agreement.",
            code="invalid_state",
        )
    source = None
    if data.get("source_message_id"):
        from core_apps.chat.models import Message

        source = get_object_or_404(
            Message.objects.filter(
                conversation__kind="direct",
                sender=actor,
                deleted_at__isnull=True,
                conversation__participants=actor,
            ).filter(conversation__participants=item.interest.tenant),
            id=data["source_message_id"],
        )
    if data["wording"] in item.terms.get(data["field"], []):
        raise ValidationError({"wording": "This reviewed term already exists."})
    item.previous_terms = [*item.previous_terms, copy.deepcopy(item.terms)]
    item.terms = {
        **item.terms,
        data["field"]: [*item.terms.get(data["field"], []), data["wording"]],
    }
    item.revision += 1
    item.accepted_by = [str(actor.id)]
    item.status = "proposed"
    item.save()
    record_consent(item, actor, "propose_answer")
    audit(
        item,
        actor,
        "terms.answer_proposed",
        metadata={
            "source_message_id": str(source.id) if source else None,
            "field": data["field"],
        },
    )
    release_proposal_holds(item)
    TenancyInvitation.objects.filter(
        terms_proposal=item, lease__isnull=True, status__in=["pending", "accepted"]
    ).update(status="revoked", revoked_at=timezone.now(), revision=F("revision") + 1)
    record_rental_event(
        item, {item.interest.tenant}, "terms.answer_proposed", "open_rental_terms"
    )
    return item
