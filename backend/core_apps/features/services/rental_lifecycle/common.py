"""Command identity, policy, audit and actor checks shared by lifecycle extensions."""

import uuid
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.users.models import User
from ...models import RentalAuditEvent, RentalCommercialPolicy
from ..rental_phase2 import (
    RentalConflict,
    fingerprint,
    remember_mutation,
    replay_operation,
)


def require_actor(user):
    if (
        not user
        or not user.is_authenticated
        or not user.is_active
        or not user.is_verified
    ):
        raise PermissionDenied("A verified active account is required.")


def require_revision(item, value):
    if isinstance(value, bool) or not isinstance(value, int) or value != item.revision:
        raise RentalConflict(
            "Review the current revision before continuing.", code="stale_revision"
        )


def require_keys(data, allowed, required=()):
    if (
        not isinstance(data, dict)
        or set(data) - set(allowed)
        or set(required) - set(data)
    ):
        raise ValidationError(
            {"request": "The request contains missing or unsupported fields."}
        )


def audit(item, actor, action, reason="", metadata=None):
    return RentalAuditEvent.objects.create(
        actor=actor,
        subject_kind=item._meta.model_name,
        subject_id=item.id,
        subject_revision=getattr(item, "revision", 1),
        action=action,
        reason=reason,
        metadata=metadata or {},
    )


def lifecycle_policy(capability=None):
    version = getattr(settings, "RENTAL_LIFECYCLE_POLICY_VERSION", "")
    policy = (
        RentalCommercialPolicy.objects.filter(version=version, is_active=True).first()
        if version
        else None
    )
    rules = dict(policy.lifecycle_rules) if policy else {}
    validate_lifecycle_rules(rules)
    from ..business_policies import current, snapshot

    hold_policy = current("D17")
    if hold_policy:
        from ..business_policy_catalog import validate_rules

        validate_rules("D17", hold_policy.rules)
        rules.update(hold_policy.rules)
        rules["business_policies"] = {"D17": snapshot(hold_policy)}
    if capability and rules.get(capability) is not True:
        raise RentalConflict(
            "This rental capability is not enabled.", code="capability_unavailable"
        )
    return policy, rules


def validate_lifecycle_rules(rules):
    """Validate one policy independently of runtime settings or database writes."""
    if not isinstance(rules, dict) or rules.get("approved") is not True:
        raise RentalConflict(
            "The rental policy has not been configured.", code="policy_not_configured"
        )
    bounds = {
        "hold_minutes": (1, 1440),
        "max_extensions": (0, 3),
        "max_active_holds": (1, 10),
        "availability_hours": (1, 168),
        "turnover_days": (0, 7),
        "reconciliation_minutes": (1, 1440),
        "max_booking_days": (1, 1096),
        "share_days": (1, 90),
        "case_hours": (1, 168),
    }
    for key, (minimum, maximum) in bounds.items():
        value = rules.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not minimum <= value <= maximum
        ):
            raise RentalConflict(
                "The rental policy is incomplete.", code="policy_not_configured"
            )


def policy_available(capability):
    try:
        lifecycle_policy(capability)
        return True
    except RentalConflict:
        return False


def staff_role(user, roles):
    profile = getattr(user, "staff_profile", None)
    if profile and profile.role_name == "security_recovery_reviewer":
        return False
    return bool(
        user
        and user.is_active
        and (
            user.is_superuser
            or (profile and profile.is_active and profile.role_name in roles)
        )
    )


def require_staff(user, roles):
    if not staff_role(user, roles):
        raise PermissionDenied("This operation requires an assigned staff role.")


def command(*, user, operation, data, authorize, execute, account_parties=None):
    """Lock actor before domain roots; serialize same-actor retries across resources.

    authorize runs before receipt replay as well as before new execution. A receipt
    is the original result, never a substitute for a fresh resource projection.
    """
    require_actor(user)
    try:
        key = str(uuid.UUID(str(data.get("request_key", ""))))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({"request_key": "A UUID request key is required."})
    with transaction.atomic():
        parties = set(account_parties()) | {user.pk} if account_parties else {user.pk}
        # Multi-party commands must acquire all accounts before their domain
        # root. Taking the actor first can deadlock a second actor's command.
        if account_parties:
            list(
                User.objects.select_for_update(no_key=True)
                .filter(pk__in=parties)
                .order_by("pk")
            )
        current_actor = User.objects.select_for_update(no_key=True).get(pk=user.pk)
        require_actor(current_actor)
        subject = authorize()
        if account_parties and (set(account_parties()) | {user.pk}) != parties:
            raise RentalConflict(
                "The participants changed. Refresh before continuing.",
                code="participants_changed",
            )
        replay = replay_operation(user, operation, key, data)
        if replay:
            return replay
        item, payload, status = execute(subject)
        result = remember_mutation(
            user=user,
            operation=operation,
            request_key=key,
            payload=data,
            request_subject_id=subject.id,
            result_subject_id=item.id,
            result_revision=getattr(item, "revision", 1),
            resource=payload,
            response_status=status,
        )
        return result, status


def consent_snapshot(item, snapshot):
    return fingerprint(
        {"subject_id": str(item.id), "revision": item.revision, "snapshot": snapshot}
    )
