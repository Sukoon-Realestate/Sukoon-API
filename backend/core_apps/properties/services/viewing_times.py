"""Individual/owner appointment negotiation; no rental or attendance decisions."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.db import transaction
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.users.models import User
from ..models import Property, PropertyVisit, OwnerAvailabilitySlot, ViewingTimeProposal
from .availability_closures import slot_in_closure, closure_intervals
from .viewing_access import can_read


def authorize(visit, actor):
    if (
        not can_read(visit, actor)
        or visit.company_id
        or visit.academic_plan_id
        or visit.context_kind != "personal"
        or visit.renter_workspace != "individual"
    ):
        raise PermissionDenied(
            "Only the individual and owner can arrange this viewing."
        )
    if visit.property.retired_at:
        raise PermissionDenied("This property is no longer available.")


def instant(day, time):
    return datetime.combine(day, time).replace(tzinfo=ZoneInfo("Africa/Cairo"))


def availability(visit):
    now = timezone.now()
    first_day = timezone.localdate()
    last_day = first_day + timedelta(days=180)
    intervals = closure_intervals(
        visit.property,
        instant(first_day, datetime.min.time()),
        instant(last_day + timedelta(days=1), datetime.min.time()),
    )
    busy = set(
        PropertyVisit.objects.filter(
            visit_date__gte=first_day,
            visit_date__lte=last_day,
            status="confirmed",
            visit_date__isnull=False,
            visit_time__isnull=False,
        )
        .filter(
            Q(property__owner_id=visit.property.owner_id) | Q(tenant_id=visit.tenant_id)
        )
        .exclude(pk=visit.pk)
        .values_list("visit_date", "visit_time")
    )
    slots = []
    for slot in OwnerAvailabilitySlot.objects.filter(
        property=visit.property,
        owner_id=visit.property.owner_id,
        is_enabled=True,
        date__gte=first_day,
        date__lte=last_day,
    ).order_by("date", "time"):
        at = instant(slot.date, slot.time)
        if (
            at <= now
            or (slot.date, slot.time) in busy
            or slot_in_closure(
                visit.property, slot.date, slot.time, intervals=intervals
            )
        ):
            continue
        if visit.visit_date == slot.date and visit.visit_time == slot.time:
            continue
        slots.append(
            {
                "id": str(slot.id),
                "date": slot.date.isoformat(),
                "time": slot.time.strftime("%H:%M"),
                "starts_at": at.isoformat(),
            }
        )
    revision = fingerprint(
        {
            "property": str(visit.property.id),
            "slots": slots,
            "closures": list(
                visit.property.dated_closures.order_by("pk").values_list(
                    "id", "revision", "active"
                )
            ),
        }
    )
    return slots, revision


def proposal_projection(row):
    return {
        "id": str(row.id),
        "proposer_id": str(row.proposer.id),
        "revision": row.revision,
        "visit_revision": row.visit_revision,
        "choices": row.choices,
        "expires_at": row.expires_at.isoformat(),
        "state": (
            "expired"
            if row.state == "open" and row.expires_at <= timezone.now()
            else row.state
        ),
        "selected_slot": row.selected_slot,
    }


def snapshot(visit):
    slots, revision = availability(visit)
    return {
        "protocol": 1,
        "visit_id": str(visit.id),
        "visit_revision": visit.revision,
        "date": visit.visit_date.isoformat() if visit.visit_date else None,
        "time": visit.visit_time.strftime("%H:%M") if visit.visit_time else None,
        "timezone": "Africa/Cairo",
        "can_propose": visit.status == "confirmed"
        and not visit.participant_decisions.exists()
        and not visit.rental_invitations.exists()
        and (
            visit.visit_date is None
            or visit.visit_time is not None
            and instant(visit.visit_date, visit.visit_time) > timezone.now()
        ),
        "availability_revision": revision,
        "slots": slots,
        "proposals": [
            proposal_projection(row)
            for row in visit.time_proposals.select_related("proposer").order_by(
                "-created_at"
            )[:30]
        ],
    }


@transaction.atomic
def locked_visit(identity, actor):
    found = get_object_or_404(
        PropertyVisit.objects.select_related("property"), id=identity
    )
    people = list(
        User.objects.select_for_update()
        .filter(pk__in=[found.tenant_id, found.property.owner_id])
        .order_by("pk")
    )
    if len(people) != 2 or any(not p.is_active or p.closed_at for p in people):
        raise PermissionDenied("Both parties must have active accounts.")
    Property.objects.select_for_update().get(pk=found.property_id)
    visit = (
        PropertyVisit.objects.select_for_update(of=("self",))
        .select_related("property", "property__owner", "tenant")
        .get(pk=found.pk)
    )
    authorize(visit, actor)
    return visit


def command(visit, actor, body):
    action = body["action"]
    if (
        visit.status != "confirmed"
        or visit.participant_decisions.exists()
        or visit.rental_invitations.exists()
    ):
        raise IdempotencyConflict("This viewing cannot be rescheduled.")
    if visit.visit_date and (
        not visit.visit_time
        or instant(visit.visit_date, visit.visit_time) <= timezone.now()
    ):
        raise IdempotencyConflict("This appointment has already started.")
    if action == "propose":
        if visit.revision != body["expected_visit_revision"]:
            raise IdempotencyConflict("The viewing changed. Refresh and review again.")
        slots, revision = availability(visit)
        if revision != body["availability_revision"]:
            raise IdempotencyConflict("Availability changed. Refresh and review again.")
        ids = {str(identity) for identity in body["slot_ids"]}
        choices = [slot for slot in slots if slot["id"] in ids]
        if len(choices) != len(ids):
            raise IdempotencyConflict("A selected time is no longer available.")
        if (
            visit.time_proposals.filter(
                proposer=actor, state="open", expires_at__gt=timezone.now()
            ).count()
            >= 3
        ):
            raise ValidationError("Withdraw an open proposal before adding another.")
        expiry = timezone.now() + timedelta(hours=24)
        if visit.visit_date:
            expiry = min(expiry, instant(visit.visit_date, visit.visit_time))
        ViewingTimeProposal.objects.create(
            visit=visit,
            proposer=actor,
            visit_revision=visit.revision,
            availability_revision=revision,
            choices=choices,
            expires_at=expiry,
        )
    else:
        row = get_object_or_404(
            ViewingTimeProposal.objects.select_for_update(),
            visit=visit,
            id=body["proposal_id"],
        )
        if (
            row.revision != body["expected_proposal_revision"]
            or row.state != "open"
            or row.expires_at <= timezone.now()
        ):
            raise IdempotencyConflict("This proposal changed or expired.")
        if (action == "withdraw") != (row.proposer_id == actor.pk):
            raise PermissionDenied(
                "Only the other party may accept or reject a proposal."
            )
        if action == "accept":
            if visit.revision != row.visit_revision:
                raise IdempotencyConflict(
                    "The original appointment changed. Refresh before accepting."
                )
            slots, revision = availability(visit)
            selected = next(
                (
                    slot
                    for slot in slots
                    if slot["id"] == str(body["slot_id"]) and slot in row.choices
                ),
                None,
            )
            if not selected or revision != row.availability_revision:
                raise IdempotencyConflict(
                    "The proposed time is no longer available. The original appointment is retained."
                )
            from core_apps.features.services.rental_lifecycle.habitability import (
                assert_habitable,
            )

            assert_habitable(visit.property, visit.offer_snapshot or {})
            if visit.offer_id:
                offer = next(
                    (
                        o
                        for o in visit.property.rental_inventory.get("offers", [])
                        if str(o.get("id")) == visit.offer_id
                    ),
                    None,
                )
                if (
                    not offer
                    or offer.get("archived")
                    or offer.get("availability") != "available"
                ):
                    raise IdempotencyConflict(
                        "The accommodation is no longer available."
                    )
            visit.visit_date = datetime.fromisoformat(selected["starts_at"]).date()
            visit.visit_time = (
                datetime.fromisoformat(selected["starts_at"])
                .time()
                .replace(tzinfo=None)
            )
            visit.save(update_fields=["visit_date", "visit_time", "updated_at"])
            row.selected_slot = selected["id"]
            row.state = "accepted"
            visit.time_proposals.filter(state="open").exclude(pk=row.pk).update(
                state="superseded", revision=F("revision") + 1
            )
            from .viewing_commands import notify

            notify(visit, "time_changed")
        else:
            row.state = "withdrawn" if action == "withdraw" else "rejected"
        row.revision += 1
        row.save(update_fields=["revision", "state", "selected_slot", "updated_at"])
    return snapshot(visit)
