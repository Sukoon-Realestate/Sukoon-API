from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Lease, RentalInterest
from .planning_models import TenancyTransition
from .planning_condition_views import participant_lease
from .services.planning import (
    check_revision,
    civil_date,
    display_name,
    mutate,
    page,
    planning_api,
    require_planning,
    selection_payload,
    text_field,
)
from .services.rental_phase2 import RentalConflict


TERMINAL = {"withdrawn", "declined", "cancelled", "expired", "effective"}


def transition_actions(user, item):
    if item.status in TERMINAL or item.lease.legacy_read_only:
        return []
    if item.kind == "moveOutNotice":
        return (
            ["withdraw"]
            if user.pk == item.author_id
            else (["acknowledge"] if item.status == "submitted" else [])
        )
    if user.pk == item.lease.owner_id:
        actions = ["nominate", "decline", "cancel"]
        if not item.availability_approved:
            actions.append("approve_availability")
        if item.candidate_consented and not item.candidate_approved:
            actions.append("approve_candidate")
        return actions
    return ["withdraw"] if user.pk == item.author_id else []


def transition_projection(item):
    released = (
        item.lease.status == "ended" and item.lease.occupancy_status == "returned"
    )
    incoming = None
    if item.candidate_id:
        incoming = (
            Lease.objects.filter(
                property=item.lease.property,
                owner=item.lease.owner,
                tenant=item.candidate.tenant,
                offer_id=item.lease.offer_id,
                tenancy_invitation__interest=item.candidate,
                start_date__gte=item.requested_on,
                legacy_read_only=False,
            )
            .exclude(pk=item.lease_id)
            .exclude(status__in=["cancelled", "expired"])
            .order_by("-created_at")
            .first()
        )
    return {
        "outgoing_release_status": "released" if released else "pending",
        "incoming_agreement_status": incoming.status if incoming else "not_started",
        "future_availability_status": (
            "approved"
            if released and item.availability_approved
            else (
                "awaiting_possession_return"
                if item.availability_approved
                else "pending_approval"
            )
        ),
        "incoming_lease_id": str(incoming.id) if incoming else "",
    }


def transition_payload(item, user):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "kind": item.kind,
        "status": item.status,
        "revision": item.revision,
        "requested_on": str(item.requested_on),
        "received_at": item.created_at.isoformat(),
        "effective_on": str(item.effective_on) if item.effective_on else "",
        "reason": item.reason,
        "candidate_id": str(item.candidate.id) if item.candidate_id else "",
        "candidate_revision": item.candidate_revision,
        "candidate_consented": item.candidate_consented,
        **transition_projection(item),
        "history": item.history,
        "allowed_actions": transition_actions(user, item),
        "blocking_reasons": [],
    }


def transition_for(user, identifier, kind, *, lock=False):
    item = get_object_or_404(TenancyTransition, id=identifier, kind=kind)
    participant_lease(user, item.lease.id, lock=lock)
    return get_object_or_404(
        (
            TenancyTransition.objects.select_for_update()
            if lock
            else TenancyTransition.objects.all()
        ),
        pk=item.pk,
    )


def _candidates(lease):
    return (
        RentalInterest.objects.filter(
            property=lease.property,
            offer_id=lease.offer_id,
            tenant__is_active=True,
            tenant__is_verified=True,
            status__in=["submitted", "under_review", "proposed", "invited"],
        )
        .exclude(tenant_id__in=[lease.owner_id, lease.tenant_id])
        .order_by("-created_at", "pkid")
    )


def _nominate(request, item):
    if request.user.pk != item.lease.owner_id:
        raise PermissionDenied(
            "Only the owner can nominate a candidate from their authorized rental interests."
        )
    candidate = get_object_or_404(
        _candidates(item.lease), id=request.data.get("candidate_id")
    )
    check_revision(candidate.revision, request.data.get("candidate_revision"))
    item.candidate = candidate
    item.candidate_revision = candidate.revision
    item.candidate_consented = False
    item.candidate_approved = False
    item.status = "candidate_pending"


def _transition_list(request, lease_id, kind):
    require_planning(
        request.user, "move_out_notices" if kind == "moveOutNotice" else "replacements"
    )
    lease = participant_lease(request.user, lease_id)
    if request.method == "GET":
        return page(
            request,
            lease.planning_transitions.filter(kind=kind).order_by(
                "-created_at", "pkid"
            ),
            lambda x: transition_payload(x, request.user),
        )

    def apply(lease, revision):
        if lease.legacy_read_only or lease.status not in {
            "active",
            "termination_pending",
        }:
            raise RentalConflict(
                "Only a current tenancy can submit a notice or replacement request."
            )
        if (
            request.data.get("kind") != kind
            or request.data.get("action") != "submit"
            or str(request.data.get("lease_id")) != str(lease.id)
        ):
            raise ValidationError("Kind, action and lease must match the route.")
        if (
            lease.planning_transitions.filter(kind=kind)
            .exclude(status__in=TERMINAL)
            .exists()
        ):
            raise RentalConflict(
                "Resolve the existing request before submitting another."
            )
        day = civil_date(request.data.get("requested_on"), "requested_on", future=True)
        if day < lease.start_date:
            raise ValidationError(
                {"requested_on": "The date cannot precede the lease."}
            )
        item = TenancyTransition(
            lease=lease,
            author=request.user,
            kind=kind,
            requested_on=day,
            reason=text_field(request.data, "reason", required=True),
            history=["Request received; the lease and possession remain unchanged."],
        )
        if request.data.get("candidate_id"):
            if kind != "replacement":
                raise ValidationError(
                    {"candidate_id": "Candidates belong to replacement requests."}
                )
            _nominate(request, item)
        item.save()
        return item

    return mutate(
        request,
        f"transition.{kind}.create.{lease_id}",
        lambda: participant_lease(request.user, lease_id, lock=True),
        apply,
        lambda x: transition_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET", "POST"], "move_out_notices")
def move_out_notices(request, lease_id):
    return _transition_list(request, lease_id, "moveOutNotice")


@planning_api(["GET", "POST"], "replacements")
def replacement_requests(request, lease_id):
    return _transition_list(request, lease_id, "replacement")


@planning_api(["GET", "POST"], None)
def transition_detail_action(request, transition_id, kind, action=None):
    # Notice and replacement switches remain independent of housing groups.
    require_planning(
        request.user, "move_out_notices" if kind == "moveOutNotice" else "replacements"
    )
    if request.method == "GET":
        if action:
            raise NotFound()
        return Response(
            transition_payload(
                transition_for(request.user, transition_id, kind), request.user
            )
        )

    def apply(item, revision):
        if action not in transition_actions(request.user, item):
            raise PermissionDenied("This transition action is not available to you.")
        if (
            request.data.get("action") != action
            or request.data.get("kind") != kind
            or str(request.data.get("lease_id")) != str(item.lease.id)
        ):
            raise ValidationError("Kind, action and lease must match the transition.")
        if action == "acknowledge":
            item.status = "acknowledged"
        elif action == "nominate":
            _nominate(request, item)
        elif action == "approve_availability":
            item.availability_approved = True
        elif action == "approve_candidate":
            candidate = get_object_or_404(_candidates(item.lease), pk=item.candidate_id)
            check_revision(candidate.revision, item.candidate_revision)
            if not item.candidate_consented:
                raise RentalConflict(
                    "The current candidate has not consented.", code="consent_required"
                )
            item.candidate_approved = True
            item.status = "signatures_pending"
        else:
            item.status = {
                "withdraw": "withdrawn",
                "decline": "declined",
                "cancel": "cancelled",
            }[action]
        item.history.append(
            f"{action} by {display_name(request.user)} at revision {item.revision + 1}."
        )
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"transition.{action}.{transition_id}",
        lambda: transition_for(request.user, transition_id, kind, lock=True),
        apply,
        lambda x: transition_payload(x, request.user),
    )


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
