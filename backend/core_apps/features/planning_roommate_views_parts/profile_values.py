"""Planning roommate views: profile values."""

from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..planning_models import LifestyleProfile, RoommateConnection
from ..services.planning import (
    check_revision,
    display_name,
    mutate,
    planning_api,
    criteria_payload,
)
from ..services.lifestyle_matching import profile_extensions


DIMENSIONS = {
    "sleep": {"early", "late", "flexible"},
    "quiet": {"low", "moderate", "high"},
    "cleaning": {"low", "moderate", "high"},
    **{
        key: {"yes", "no", "sometimes"}
        for key in ("workFromHome", "smoking", "guests", "pets")
    },
    "workFromHome": {
        "yes",
        "no",
        "sometimes",
        "never",
        "someDays",
        "mostDays",
        "variable",
    },
    "smoking": {"yes", "no", "sometimes", "outdoors", "indoors"},
}


def lifestyle_payload(item):
    return {
        "id": str(item.id) if item else "",
        "revision": item.revision if item else 0,
        "discoverable": item.discoverable if item else False,
        "habits": item.habits if item else {},
        "preferences": item.preferences if item else {},
        "disclosed": item.disclosed if item else [],
        "importance": item.importance if item else {},
        "details": item.details if item else {},
        "search_context": (
            criteria_payload(item.search_context)
            if item and item.search_context
            else {}
        ),
        "reason_categories": item.reason_categories if item else [],
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
    result.update(profile_extensions(data, set(DIMENSIONS)))
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


def disclosures(profile, fields=None):
    return [
        f"{key}: {profile.habits[key]}"
        for key in (profile.disclosed if fields is None else fields)
        if key in profile.habits
        and profile.habits[key] not in {"unspecified", "preferNotToAnswer"}
    ]


def candidate_payload(item, facts=(), viewer_revision=0):
    from ..services.student_housing.profiles import roommate_disclosures

    return {
        "id": str(item.id),
        "user_id": str(item.user.id),
        "display_name": display_name(item.user),
        "status": "candidate",
        "revision": item.revision,
        "explanations": [],
        "match_facts": list(facts),
        "matching_rule_version": "declared-v2",
        "student_disclosures": roommate_disclosures(item.user),
        "profile_revisions": {"candidate": item.revision, "viewer": viewer_revision},
        "disclosures": disclosures(item),
        "chat_granted": False,
        "allowed_actions": ["request", "block"],
        "blocking_reasons": [],
    }
