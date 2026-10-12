from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from .planning_models import LifestyleProfile, RoommateConnection
from .services.planning import (
    check_revision,
    display_name,
    mutate,
    page,
    planning_api,
    text_field,
)
from .services.rental_phase2 import RentalConflict


DIMENSIONS = {
    "sleep": {"early", "late", "flexible"},
    "quiet": {"low", "moderate", "high"},
    "cleaning": {"low", "moderate", "high"},
    **{
        key: {"yes", "no", "sometimes"}
        for key in ("workFromHome", "smoking", "guests", "pets")
    },
}


def lifestyle_payload(item):
    return {
        "id": str(item.id) if item else "",
        "revision": item.revision if item else 0,
        "discoverable": item.discoverable if item else False,
        "habits": item.habits if item else {},
        "preferences": item.preferences if item else {},
        "disclosed": item.disclosed if item else [],
    }


def profile_values(data):
    if type(data.get("discoverable")) is not bool:
        raise ValidationError({"discoverable": "Use a boolean."})
    result = {"discoverable": data["discoverable"]}
    for category in ("habits", "preferences"):
        raw = data.get(category, {})
        if not isinstance(raw, dict) or set(raw) - set(DIMENSIONS):
            raise ValidationError({category: "Unknown lifestyle dimension."})
        for key, value in raw.items():
            if not isinstance(value, str) or value not in DIMENSIONS[key] | {
                "unspecified",
                "preferNotToAnswer",
            } | ({"noPreference"} if category == "preferences" else set()):
                raise ValidationError(
                    {category: "Unsupported answer for this dimension."}
                )
        result[category] = raw
    disclosed = data.get("disclosed", [])
    if (
        not isinstance(disclosed, list)
        or any(key not in DIMENSIONS for key in disclosed)
        or len(set(disclosed)) != len(disclosed)
    ):
        raise ValidationError({"disclosed": "Select supported distinct dimensions."})
    result["disclosed"] = [
        key
        for key in disclosed
        if result["habits"].get(key, "unspecified")
        not in {"unspecified", "preferNotToAnswer"}
    ]
    return result


@planning_api(["GET", "POST"], "lifestyle")
def lifestyle_profile(request):
    if request.method == "GET":
        return Response(
            lifestyle_payload(
                LifestyleProfile.objects.filter(user=request.user).first()
            )
        )

    def apply(item, revision):
        check_revision(item.revision if item else 0, revision)
        values = profile_values(request.data)
        if item is None:
            return LifestyleProfile.objects.create(user=request.user, **values)
        for key, value in values.items():
            setattr(item, key, value)
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        "lifestyle.save",
        lambda: LifestyleProfile.objects.select_for_update()
        .filter(user=request.user)
        .first(),
        apply,
        lifestyle_payload,
    )


def connections(user):
    return RoommateConnection.objects.filter(Q(first=user) | Q(second=user))


def roommate_actions(user, item):
    if item.status == "blocked":
        return []
    result = ["block"]
    if item.status == "pending":
        result += (
            ["withdraw"] if item.requester_id == user.pk else ["accept", "decline"]
        )
    elif item.status == "accepted":
        result += ["withdraw"]
    return result


def disclosures(profile):
    return [
        f"{key}: {profile.habits[key]}"
        for key in profile.disclosed
        if key in profile.habits
        and profile.habits[key] not in {"unspecified", "preferNotToAnswer"}
    ]


def candidate_payload(item):
    return {
        "id": str(item.id),
        "user_id": str(item.user.id),
        "display_name": display_name(item.user),
        "status": "candidate",
        "revision": item.revision,
        "explanations": [],
        "disclosures": disclosures(item),
        "chat_granted": False,
        "allowed_actions": ["request", "block"],
        "blocking_reasons": [],
    }


def connection_payload(item, user):
    other = item.second if item.first_id == user.pk else item.first
    profile = LifestyleProfile.objects.filter(user=other).first()
    return {
        "id": str(item.id),
        "user_id": str(other.id),
        "display_name": display_name(other),
        "status": item.status,
        "revision": item.revision,
        "explanations": [],
        "disclosures": (
            disclosures(profile) if profile and item.status == "accepted" else []
        ),
        "chat_granted": item.status == "accepted"
        and user.is_active
        and other.is_active,
        "allowed_actions": roommate_actions(user, item),
        "blocking_reasons": [],
    }


@planning_api(["GET"], "roommates")
def roommate_candidates(request):
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
    return page(request, queryset, candidate_payload)


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


@planning_api(["POST"], "roommates")
def roommate_connection_action(request, connection_id, action):
    def apply(item, revision):
        if action not in roommate_actions(request.user, item):
            raise PermissionDenied("This connection action is not available to you.")
        if request.data.get("decision") != action:
            raise ValidationError({"decision": "Must match the route."})
        item.status = {
            "accept": "accepted",
            "decline": "declined",
            "withdraw": "withdrawn",
            "block": "blocked",
        }[action]
        if action == "block":
            item.blocked_by = [str(request.user.id)]
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"roommate.connection.{action}.{connection_id}",
        lambda: get_object_or_404(
            connections(request.user).select_for_update(), id=connection_id
        ),
        apply,
        lambda x: connection_payload(x, request.user),
    )
