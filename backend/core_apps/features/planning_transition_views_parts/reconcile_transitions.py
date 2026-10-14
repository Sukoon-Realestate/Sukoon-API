"""Planning transition views: reconcile transitions."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..models import Lease, RentalInterest
from ..planning_models import TenancyTransition
from ..planning_condition_views import participant_lease
from ..services.planning import (
    check_revision,
    display_name,
    mutate,
    page,
    planning_api,
    selection_payload,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .transition_projection import TERMINAL, transition_projection, _candidates


@planning_api(["GET"], "replacements")
def replacement_candidates(request, lease_id):
    lease = participant_lease(request.user, lease_id)
    candidates = _candidates(lease)
    if request.user.pk != lease.owner_id:
        candidates = candidates.filter(
            pk__in=lease.planning_transitions.filter(candidate_consented=True).values(
                "candidate_id"
            )
        )
    consented = set(
        lease.planning_transitions.filter(candidate_consented=True).values_list(
            "candidate_id", flat=True
        )
    )
    return page(
        request,
        candidates,
        lambda x: {
            "id": str(x.id),
            "display_name": display_name(x.tenant),
            "source": "rental_interest",
            "revision": x.revision,
            "consented": x.pk in consented,
        },
    )


def candidate_invitation_payload(item):
    return {
        "id": str(item.id),
        "revision": item.revision,
        "kind": item.kind,
        "status": item.status,
        "candidate_id": str(item.candidate.id),
        "candidate_revision": item.candidate_revision,
        "property_id": str(item.lease.property.id),
        "selection": selection_payload(item.lease.offer_snapshot),
        "requested_on": str(item.requested_on),
        "allowed_actions": (
            ["accept", "decline"] if item.status == "candidate_pending" else []
        ),
        "blocking_reasons": [],
    }


@planning_api(["GET"], "replacements")
def replacement_invitations(request):
    return page(
        request,
        TenancyTransition.objects.filter(
            candidate__tenant=request.user, kind="replacement"
        )
        .exclude(status__in=TERMINAL)
        .order_by("-created_at", "pkid"),
        candidate_invitation_payload,
    )


@planning_api(["POST"], "replacements")
def replacement_candidate_consent(request, transition_id):
    def load():
        item = get_object_or_404(
            TenancyTransition,
            id=transition_id,
            kind="replacement",
            candidate__tenant=request.user,
        )
        Lease.objects.select_for_update().get(pk=item.lease_id)
        return TenancyTransition.objects.select_for_update().get(pk=item.pk)

    def apply(item, revision):
        if item.status != "candidate_pending":
            raise RentalConflict("This candidate invitation is not pending.")
        check_revision(item.candidate.revision, item.candidate_revision)
        action = request.data.get("decision")
        if action not in {"accept", "decline"}:
            raise ValidationError({"decision": "Use accept or decline."})
        item.candidate_consented = action == "accept"
        item.status = "candidate_consented" if item.candidate_consented else "declined"
        item.revision += 1
        item.history.append(f"Candidate {action} at revision {item.revision}.")
        note = text_field(request.data, "note", limit=2000)
        if note:
            item.history.append(note)
        item.save()
        return item

    return mutate(
        request,
        f"replacement.candidate-consent.{transition_id}",
        load,
        apply,
        candidate_invitation_payload,
    )


def reconcile_transitions():
    changed = 0
    for candidate in TenancyTransition.objects.exclude(status__in=TERMINAL).order_by(
        "pkid"
    ):
        with transaction.atomic():
            lease = Lease.objects.select_for_update().get(pk=candidate.lease_id)
            item = TenancyTransition.objects.select_for_update().get(pk=candidate.pk)
            if item.status in TERMINAL:
                continue
            item.lease = lease
            projection = transition_projection(item)
            released = projection["outgoing_release_status"] == "released"
            effective_on = max(lease.end_date, item.requested_on)
            if projection["incoming_lease_id"]:
                incoming = Lease.objects.get(id=projection["incoming_lease_id"])
                effective_on = max(effective_on, incoming.start_date)
            ready = released and timezone.localdate() >= effective_on
            if item.kind == "replacement":
                ready = (
                    ready
                    and item.candidate_consented
                    and item.candidate_approved
                    and item.availability_approved
                    # Agreement progression advances the interest revision. Its
                    # immutable invitation link binds the signed/captured lease
                    # to the approved nominee; withdrawn/rejected interests do
                    # not qualify even when another lease exists.
                    and item.candidate.status == RentalInterest.Status.INVITED
                    and projection["incoming_agreement_status"] == "active"
                )
            else:
                ready = ready and item.status == "acknowledged"
            if ready:
                item.status = "effective"
                item.effective_on = effective_on
                item.revision += 1
                item.history.append(
                    "Effective state confirmed from legal, possession and agreement records."
                )
                item.save()
                changed += 1
    return changed
