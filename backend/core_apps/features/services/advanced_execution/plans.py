"""Immutable reviewed plan; appending decisions never signs for another person."""

import json
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ...advanced_execution_models import (
    AdvancedExecution,
    AdvancedExecutionLeg,
    AdvancedExecutionConsent,
    AdvancedExecutionStep,
)
from ..rental_phase2 import fingerprint, RentalConflict
from .registry import adapter, CAPABILITIES

POLICY = "advanced-partial-preserve-v1"
MODES = {"independent_participants", "conditional_package"}


def record_step(
    plan,
    leg,
    kind,
    state,
    canonical_kind="",
    canonical_id=None,
    metadata=None,
    actor=None,
):
    return AdvancedExecutionStep.objects.create(
        execution=plan,
        leg=leg,
        kind=kind,
        state=state,
        canonical_kind=canonical_kind,
        canonical_id=canonical_id or None,
        metadata=metadata or {},
        actor=actor,
    )


def create_plan(
    actor,
    *,
    source_kind,
    source_id,
    source_revision,
    source_digest,
    mode,
    legs,
    context=None
):
    from config.advanced_housing import require_mock_mode

    require_mock_mode()
    from ..planning import require_planning

    require_planning(actor, CAPABILITIES[source_kind])
    if mode == "conditional_package":
        require_planning(actor, "conditional_group_execution")
    adapter(source_kind).authorize(actor, source_id)
    if mode not in MODES or not isinstance(legs, list) or not 1 <= len(legs) <= 24:
        raise ValidationError(
            "Provide a supported execution mode and 1 to 24 exact legs."
        )
    clean = json.loads(json.dumps(legs, default=str))
    keys, required = set(), set()
    for item in clean:
        if not item.get("key") or item["key"] in keys:
            raise ValidationError("Every execution leg needs a unique stable key.")
        keys.add(item["key"])
        if item.get("canonical_kind", "individual") == "company":
            people = item.get("terms", {}).get("actor_ids", [])
        else:
            people = [
                item.get("owner_id"),
                item.get("tenant_id"),
                *item.get("metadata", {}).get("required_occupant_ids", []),
            ]
            if (
                not item.get("owner_id")
                or not item.get("tenant_id")
                or item["owner_id"] == item["tenant_id"]
            ):
                raise ValidationError(
                    "Execution requires distinct named owner and tenant accounts."
                )
        if not people or any(not value for value in people):
            raise ValidationError("Every execution leg requires named consent actors.")
        item["actor_ids"] = sorted(set(people))
        required.update(people)
    from core_apps.users.models import User

    if User.objects.filter(
        id__in=required, is_active=True, is_verified=True
    ).count() != len(required):
        raise ValidationError(
            "Every required participant must have a current verified account."
        )
    digest = fingerprint(
        {
            "source": str(source_id),
            "revision": source_revision,
            "source_digest": source_digest,
            "mode": mode,
            "policy": POLICY,
            "legs": clean,
        }
    )
    existing = AdvancedExecution.objects.filter(
        source_kind=source_kind, source_id=source_id, digest=digest
    ).first()
    if existing:
        get_plan(actor, existing.id)
        return existing
    plan = AdvancedExecution.objects.create(
        source_kind=source_kind,
        source_id=source_id,
        source_revision=source_revision,
        source_digest=source_digest,
        digest=digest,
        mode=mode,
        policy_version=POLICY,
        created_by=actor,
        required_actor_ids=sorted(required),
        context=context or {},
    )
    # Durable inbox membership is separate from the immutable consent snapshot.
    plan.actors.set(User.objects.filter(id__in=required | {str(actor.id)}))
    for item in clean:
        AdvancedExecutionLeg.objects.create(
            execution=plan,
            key=item["key"],
            canonical_kind=item.get("canonical_kind", "individual"),
            canonical_id=item.get("canonical_id"),
            actor_ids=item["actor_ids"],
            specification=item,
        )
    record_step(
        plan,
        None,
        "plan_created",
        "confirmed",
        actor=actor,
        metadata={"provider_mode": "mock", "policy_version": POLICY},
    )
    return plan


def get_plan(user, identifier, *, lock=False):
    query = AdvancedExecution.objects.all()
    if lock:
        query = query.select_for_update(of=("self",))
    plan = get_object_or_404(query, id=identifier)
    source = adapter(plan.source_kind)
    if str(user.id) in plan.required_actor_ids:
        authorize_participant = getattr(source, "authorize_participant", None)
        if authorize_participant:
            try:
                authorize_participant(plan, user)
            except (NotFound, PermissionDenied, Http404):
                raise NotFound()
    else:
        try:
            source.authorize(user, plan.source_id)
        except (PermissionDenied, NotFound, Http404):
            raise NotFound()
    return plan


def subject(user, identifier):
    if AdvancedExecution.objects.filter(id=identifier).exists():
        return get_plan(user, identifier)
    return None


def decisions(plan):
    result = {}
    for row in plan.consents.order_by("-pkid"):
        if row.digest == plan.digest:
            result.setdefault(str(row.actor.id), row.decision)
    return result


def require_accepted(plan):
    latest = decisions(plan)
    if any(latest.get(actor) != "accept" for actor in plan.required_actor_ids):
        raise RentalConflict(
            "Every required actor must accept this exact execution plan.",
            code="participant_consent_required",
        )


def consent(plan, actor, data):
    if str(actor.id) not in plan.required_actor_ids or "participant_id" in data:
        raise PermissionDenied(
            "Execution consent must be supplied by the required actor personally."
        )
    if (
        data.get("digest") != plan.digest
        or data.get("policy_version") != POLICY
        or data.get("decision") not in {"accept", "decline"}
    ):
        raise RentalConflict(
            "Review the exact execution snapshot and partial-resolution policy.",
            code="document_changed",
        )
    if plan.state not in {"awaiting_consents", "ready"}:
        raise RentalConflict(
            "Prepared execution terms cannot be silently reconsented.",
            code="invalid_state",
        )
    adapter(plan.source_kind).revalidate(plan, action="consents")
    AdvancedExecutionConsent.objects.create(
        execution=plan,
        actor=actor,
        digest=plan.digest,
        decision=data["decision"],
        execution_revision=plan.revision,
    )
    latest = decisions(plan)
    plan.state = (
        "ready"
        if all(latest.get(x) == "accept" for x in plan.required_actor_ids)
        else "awaiting_consents"
    )
    record_step(plan, None, "consent", data["decision"], actor=actor)
    return plan


def enabled(plan):
    from config.advanced_housing import mock_mode_available
    from ..planning import enabled_services

    services = enabled_services()
    return (
        mock_mode_available()
        and CAPABILITIES[plan.source_kind] in services
        and (
            plan.mode != "conditional_package"
            or "conditional_group_execution" in services
        )
    )


def actions(user, capability, subject_id=""):
    if not subject_id:
        return []
    try:
        plan = get_plan(user, subject_id)
    except (NotFound, ValueError, Http404):
        return []
    if capability != CAPABILITIES[plan.source_kind]:
        return []
    result = ["read"]
    if not enabled(plan):
        return result
    own = str(user.id) in plan.required_actor_ids
    if own and plan.state in {"awaiting_consents", "ready"}:
        result.append("consents")
    if plan.state == "ready":
        result.append("prepare")
    if plan.state in {
        "prepared",
        "executing",
        "partial",
        "manual_resolution",
        "unknown",
        "awaiting_handover",
    }:
        result += ["reconcile"]
        if own:
            result += ["advance", "withdraw"]
    if own and plan.state in {"partial", "manual_resolution"}:
        result.append("resolve")
    return result
