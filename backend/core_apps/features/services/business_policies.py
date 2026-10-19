"""Policy publication over the existing decision registry, with a locked head."""

import re
import uuid
from copy import deepcopy
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.users.models import User
from ..models import PolicyDecision, PolicyDecisionHead
from .business_policy_catalog import CATALOG, SOURCES, definition, validate_rules
from .rental_phase2 import (
    RentalConflict,
    fingerprint,
    remember_mutation,
    replay_operation,
)
from .rental_lifecycle.common import audit, require_keys


def administrator(user):
    if not (
        user
        and user.is_authenticated
        and user.is_active
        and user.is_staff
        and not user.sensitive_actions_frozen
        and (user.is_superuser or user.has_perm("features.change_policydecision"))
    ):
        raise PermissionDenied("An active policy administrator is required.")


def current(code):
    candidates = PolicyDecision.objects.filter(
        code=code,
        status="approved",
        effective_at__lte=timezone.now(),
        presentation__contract="public-business-policy-v1",
    ).order_by("-effective_at", "-pkid")
    spec = CATALOG.get(code, {})
    # Expanded prospective scopes do not hide immutable older publications.
    # A new consumer must require its own explicit scope before using a policy.
    required = set(spec.get("legacy_scope", spec.get("scope", [])))
    return next((item for item in candidates if required.issubset(item.scope)), None)


def snapshot(item):
    result = {
        "id": str(item.id),
        "code": item.code,
        "version": item.version,
        "effective_at": item.effective_at.isoformat(),
        "rules": deepcopy(item.rules),
        "disclosure": item.disclosure,
        "presentation": deepcopy(item.presentation),
        "historical_treatment": item.historical_treatment,
    }
    result["digest"] = fingerprint(result)
    return result


def freeze(codes):
    return {code: snapshot(item) for code in codes if (item := current(code))}


def bound(terms, code):
    """Absent historical policy is unknown, never today's default retroactively."""
    return (terms.get("business_policies") or {}).get(code)


def public(item, language="en"):
    data = snapshot(item) if isinstance(item, PolicyDecision) else item
    code = data["code"]
    spec = CATALOG.get(code, {})
    index = 1 if language == "ar" else 0
    locale = data.get("presentation", {}).get(language, {})
    return {
        "code": code,
        "version": data["version"],
        "digest": data["digest"],
        "effective_at": data["effective_at"],
        "title": locale.get("title") or spec.get("title", [code, code])[index],
        "description": locale.get("description") or data.get("disclosure", ""),
        "values": [
            {"name": key, "label": labels[index], "value": str(data["rules"][key])}
            for key, labels in spec.get("labels", {}).items()
            if key in data["rules"]
        ],
        "historical_application": "existing_accepted_terms_preserved",
    }


def public_bound(terms, language="en"):
    return [
        public(item, language)
        for item in (terms.get("business_policies") or {}).values()
    ]


def templates():
    heads = {
        head.code: head for head in PolicyDecisionHead.objects.select_related("current")
    }
    return [
        {
            "code": code,
            **deepcopy(spec),
            "source": SOURCES[code],
            "head_revision": heads[code].revision if code in heads else 0,
            "current_version": (item.version if (item := current(code)) else None),
        }
        for code, spec in CATALOG.items()
    ]


@transaction.atomic
def publish(user, data):
    administrator(user)
    user = User.objects.select_for_update(no_key=True).get(pk=user.pk)
    administrator(user)
    keys = {
        "code",
        "version",
        "expected_head_revision",
        "rules",
        "reason",
        "evidence_reference",
        "request_key",
    }
    require_keys(data, keys, keys)
    try:
        request_key = str(uuid.UUID(str(data["request_key"])))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({"request_key": "Use a UUID operation identity."})
    replay = replay_operation(user, "business_policy.publish", request_key, data)
    if replay:
        return replay
    spec = definition(data["code"])
    validate_rules(data["code"], data["rules"])
    if not isinstance(data["version"], str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", data["version"]
    ):
        raise ValidationError(
            {
                "version": "Use a new stable version, up to 80 letters, digits, dots, underscores or hyphens."
            }
        )
    for key, maximum in [("reason", 4000), ("evidence_reference", 500)]:
        if not isinstance(data[key], str) or not 1 <= len(data[key].strip()) <= maximum:
            raise ValidationError(
                {
                    key: f"Provide a reviewable reference or reason, up to {maximum} characters."
                }
            )
    PolicyDecisionHead.objects.get_or_create(code=data["code"])
    head = PolicyDecisionHead.objects.select_for_update().get(code=data["code"])
    if (
        type(data["expected_head_revision"]) is not int
        or data["expected_head_revision"] != head.revision
    ):
        raise RentalConflict(
            "Another policy version was published. Review it before publishing.",
            code="stale_revision",
        )
    if PolicyDecision.objects.filter(
        code=data["code"], version=data["version"]
    ).exists():
        raise RentalConflict(
            "This policy version already exists. Publish a new version.",
            code="policy_version_exists",
        )
    item = PolicyDecision.objects.create(
        code=data["code"],
        version=data["version"],
        status="approved",
        owner="Product policy administration",
        approver=user,
        source=SOURCES[data["code"]],
        evidence_reference=data["evidence_reference"].strip(),
        scope=spec["scope"],
        effective_at=timezone.now(),
        rules=data["rules"],
        evidence_requirements={
            "source": "Original canonical record, current independent authority and actual outcome evidence"
        },
        actions_and_consequences={
            "consumer": spec["consumer"],
            "automatic_consent": False,
            "retroactive_financial_changes": False,
        },
        historical_treatment="Prospective only. Accepted terms, original operation identities and existing case/hold policy snapshots remain unchanged.",
        audit_reason=data["reason"].strip(),
        disclosure=spec["description"][0],
        presentation={
            "contract": "public-business-policy-v1",
            **{
                lang: {"title": spec["title"][i], "description": spec["description"][i]}
                for i, lang in enumerate(["en", "ar"])
            },
        },
    )
    head.current = item
    head.revision += 1
    head.save()
    audit(
        item,
        user,
        "policy.published",
        data["reason"],
        {"head_revision": head.revision, "digest": snapshot(item)["digest"]},
    )
    result = remember_mutation(
        user=user,
        operation="business_policy.publish",
        request_key=request_key,
        payload=data,
        request_subject_id=uuid.uuid5(uuid.NAMESPACE_URL, "sokoun-policy:" + item.code),
        result_subject_id=item.id,
        result_revision=item.revision,
        resource={**public(item), "head_revision": head.revision},
        response_status=201,
    )
    return result, 201
