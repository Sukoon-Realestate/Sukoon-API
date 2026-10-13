"""Planning roommate views: roommate candidate action."""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..planning_models import LifestyleProfile, RoommateConnection
from ..services.planning import (
    check_revision,
    display_name,
    mutate,
    page,
    planning_api,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from ..services.lifestyle_matching import match_facts, disclosure_scope
from .profile_values import (
    DIMENSIONS,
    connections,
    roommate_actions,
    disclosures,
    candidate_payload,
)


def connection_payload(item, user):
    other = item.second if item.first_id == user.pk else item.first
    profile = LifestyleProfile.objects.filter(user=other).first()
    grant = item.disclosure_grants.get(str(other.id), {})
    extra = (
        grant.get("fields", [])
        if isinstance(grant, dict)
        and profile
        and grant.get("revision") == profile.revision
        else []
    )
    return {
        "id": str(item.id),
        "user_id": str(other.id),
        "display_name": display_name(other),
        "status": item.status,
        "revision": item.revision,
        "explanations": [],
        "disclosures": (
            disclosures(
                profile,
                sorted(
                    set(profile.disclosed if profile.discoverable else []) | set(extra)
                ),
            )
            if profile and item.status == "accepted"
            else []
        ),
        "chat_granted": item.status == "accepted"
        and user.is_active
        and other.is_active,
        "allowed_actions": roommate_actions(user, item),
        "blocking_reasons": [],
    }


@planning_api(["GET"], "roommates")
def roommate_candidates(request):
    viewer = LifestyleProfile.objects.filter(
        user=request.user, discoverable=True
    ).first()
    if viewer is None:
        return page(request, [], candidate_payload)
    excluded = {request.user.pk}
    for relation in connections(request.user).filter(
        status__in=["pending", "accepted", "blocked"]
    ):
        excluded.update((relation.first_id, relation.second_id))
    queryset = (
        LifestyleProfile.objects.filter(
            discoverable=True, user__is_active=True, user__is_verified=True
        )
        .exclude(user_id__in=excluded)
        .select_related("user")
        .order_by("pkid")
    )
    ranked = []
    for item in queryset:
        conflict, agreements, differences, facts = match_facts(viewer, item, DIMENSIONS)
        if not conflict:
            ranked.append(((-agreements, differences, item.pk), item, facts))
    ranked.sort(key=lambda x: x[0])
    return page(
        request, ranked, lambda x: candidate_payload(x[1], x[2], viewer.revision)
    )


@planning_api(["GET"], "roommates")
def roommate_connections(request):
    return page(
        request,
        connections(request.user)
        .select_related("first", "second")
        .order_by("-updated_at", "pkid"),
        lambda x: connection_payload(x, request.user),
    )


@planning_api(["POST"], "roommates")
def roommate_candidate_action(request, candidate_id, action):
    def load():
        return get_object_or_404(
            LifestyleProfile.objects.select_for_update(of=("self",))
            .select_related("user")
            .filter(discoverable=True, user__is_active=True, user__is_verified=True)
            .exclude(user=request.user),
            id=candidate_id,
        )

    def apply(candidate, revision):
        if action not in {"request", "block"} or request.data.get("decision") != action:
            raise ValidationError(
                {"decision": "Use request or block matching the route."}
            )
        check_revision(candidate.revision, request.data.get("candidate_revision"))
        if (
            action == "request"
            and not LifestyleProfile.objects.filter(
                user=request.user, discoverable=True
            ).exists()
        ):
            raise PermissionDenied(
                "Enable roommate discovery before requesting a connection."
            )
        first, second = sorted((request.user.pk, candidate.user_id))
        item = (
            RoommateConnection.objects.select_for_update()
            .filter(first_id=first, second_id=second)
            .first()
        )
        if item and item.status in {"pending", "accepted", "blocked"}:
            raise RentalConflict(
                "A connection already exists; use its current revision."
            )
        values = {
            "requester": request.user,
            "status": "blocked" if action == "block" else "pending",
            "blocked_by": [str(request.user.id)] if action == "block" else [],
            "note": text_field(request.data, "note"),
            "disclosure_grants": {
                str(request.user.id): disclosure_scope(
                    request.user, request.data, DIMENSIONS
                )
            },
        }
        if not item:
            try:
                with transaction.atomic():
                    item = RoommateConnection.objects.create(
                        first_id=first, second_id=second, **values
                    )
            except IntegrityError:
                raise RentalConflict(
                    "Another connection request won the race; refresh the connection."
                )
        else:
            for key, value in values.items():
                setattr(item, key, value)
            item.revision += 1
            item.save()
        return item

    return mutate(
        request,
        f"roommate.candidate.{action}.{candidate_id}",
        load,
        apply,
        lambda x: connection_payload(x, request.user),
        creating=True,
    )
