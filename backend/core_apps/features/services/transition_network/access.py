from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import Lease
from ...transition_network_models import (
    MoveIntent,
    TransitionCandidate,
    TransitionMatchRun,
)


def intent_for(user, identifier, *, lock=False):
    rows = MoveIntent.objects.select_related("lease__property", "source_transition")
    if lock:
        rows = rows.select_for_update(of=("self",))
    return get_object_or_404(rows, id=identifier, user=user)


def candidate_for(user, identifier, *, lock=False):
    rows = TransitionCandidate.objects.all()
    if lock:
        rows = rows.select_for_update()
    return get_object_or_404(rows, id=identifier, participants__user=user)


def subject(user, identifier):
    for model in (MoveIntent, TransitionMatchRun):
        item = model.objects.filter(id=identifier).first()
        if item:
            if item.user_id != user.pk:
                raise NotFound()
            return item
    item = TransitionCandidate.objects.filter(id=identifier).first()
    if item:
        if not item.participants.filter(user=user).exists():
            raise NotFound()
        return item
    return None


def intent_actions(item):
    if item.status in {"withdrawn", "expired"} or item.expires_at <= timezone.now():
        return []
    actions = ["withdraw"]
    if item.status in {"draft", "paused"}:
        actions += ["update", "publish"]
    if item.status == "matching":
        actions += ["pause", "match"]
    return actions


def actions(user, capability, subject_id=""):
    if capability not in {
        "housing_transition_planning",
        "housing_transition_execution",
    }:
        return []
    if not subject_id:
        return ["read", "create"]
    try:
        item = subject(user, subject_id)
        if isinstance(item, MoveIntent):
            return ["read", *intent_actions(item)]
        if isinstance(item, TransitionCandidate):
            from .projections import candidate_stale, candidate_actions

            available = candidate_actions(item, candidate_stale(item))
            return ["read"] + [
                action
                for action in available
                if (action == "create_execution")
                == (capability == "housing_transition_execution")
            ]
        if isinstance(item, TransitionMatchRun):
            return ["read"]
        if Lease.objects.filter(
            id=subject_id, tenant=user, legacy_read_only=False
        ).exists():
            return ["read", "create"]
    except (NotFound, ValueError):
        pass
    return []
