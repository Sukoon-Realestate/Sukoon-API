"""Action-bound proofs. Only a configured, approved assurance provider verifies identity."""

import hashlib
import secrets
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.common.idempotency import fingerprint
from core_apps.features.services.policy_registry import approved_policy
from core_apps.features.services.rental_phase2 import RentalConflict
from ..models import User, AuthSession, SensitiveAuthorization, SecurityEvent
from .sessions import validate_session

ACTIONS = {
    "beneficiary.onboarding",
    "payout.execute",
    "refund.execute",
    "company.member.update",
    "account.contact.change",
    "private.export",
    "account.mfa.manage",
    "account.totp.recovery.review",
    "account.closure.request",
    "account.closure.review",
}


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _adapter(policy):
    name = getattr(settings, "SECURITY_ASSURANCE_PROVIDER", "") or (
        "core_apps.users.services.assurance.AccountAssuranceProvider"
    )
    if name != policy.rules.get("provider"):
        raise RentalConflict(
            "Approved identity verification is unavailable.",
            code="assurance_unavailable",
        )
    provider = import_string(name)()
    if getattr(provider, "test_only", False) and not settings.DEBUG:
        raise RentalConflict(
            "Test assurance is disabled.", code="assurance_unavailable"
        )
    return provider


def _actor(request):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(user, request.auth or {})
    from .totp import require_sensitive_access

    require_sensitive_access(user)
    session = AuthSession.objects.filter(
        user=user, id=(request.auth or {}).get("session_id"), revoked_at__isnull=True
    ).first()
    if session is None:
        raise PermissionDenied("Sign in again before this sensitive action.")
    return user, session


def _binding(item):
    return {
        "challenge_id": str(item.id),
        "user_id": str(item.user.id),
        "session_id": str(item.session.id),
        "action": item.action,
        "resource_id": str(item.resource_id),
        "resource_revision": item.resource_revision,
        "payload_digest": item.payload_digest,
        "policy_version": item.policy.version,
        "security_epoch": item.security_epoch,
        "expires_at": item.expires_at.isoformat(),
    }


@transaction.atomic
def begin(request, data):
    user, session = _actor(request)
    if data["action"] not in ACTIONS:
        raise ValidationError({"action": "Unsupported sensitive action."})
    policy = approved_policy("D26", data["action"])
    provider = _adapter(policy)
    ttl = policy.rules.get("proof_lifetime_seconds")
    if type(ttl) is not int or ttl <= 0 or not policy.rules.get("assurance"):
        raise RentalConflict(
            "The assurance policy is incomplete.", code="awaiting_policy"
        )
    item = SensitiveAuthorization.objects.create(
        user=user,
        session=session,
        security_epoch=user.security_epoch,
        action=data["action"],
        resource_id=data["resource_id"],
        resource_revision=data["resource_revision"],
        payload_digest=fingerprint(data["payload"]),
        policy=policy,
        expires_at=timezone.now() + timedelta(seconds=min(ttl, 300)),
    )
    result = provider.begin(_binding(item))
    item.provider_challenge = result["reference"]
    item.save(update_fields=["provider_challenge", "updated_at"])
    return {
        "id": str(item.id),
        "expires_at": item.expires_at.isoformat(),
        "verification": result["public_challenge"],
    }


def verify(request, identity, assertion):
    # Invalid-code counters must commit; raising inside atomic would reset them.
    with transaction.atomic():
        result = _verify_locked(request, identity, assertion)
    if result is None:
        raise PermissionDenied("Identity verification was not confirmed.")
    return result


def _verify_locked(request, identity, assertion):
    user, session = _actor(request)
    item = (
        SensitiveAuthorization.objects.select_for_update()
        .select_related("policy")
        .filter(id=identity, user=user, session=session)
        .first()
    )
    if (
        not item
        or item.expires_at <= timezone.now()
        or item.consumed_at
        or item.verified_at
        or item.security_epoch != user.security_epoch
    ):
        raise PermissionDenied("Verification challenge expired or is unavailable.")
    current = approved_policy("D26", item.action)
    if current.pk != item.policy_id:
        raise PermissionDenied("Review the current verification policy.")
    result = _adapter(current).verify(
        item.provider_challenge, assertion, _binding(item)
    )
    if (
        result.get("binding") != _binding(item)
        or result.get("assurance") != current.rules["assurance"]
        or result.get("verified") is not True
    ):
        return None
    proof = secrets.token_urlsafe(32)
    item.proof_digest, item.verified_at = _digest(proof), timezone.now()
    item.assurance = result["assurance"]
    item.save(update_fields=["proof_digest", "verified_at", "assurance", "updated_at"])
    return {"proof": proof, "expires_at": item.expires_at.isoformat()}


def consume(request, *, action, resource_id, revision, payload=None):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Consume the authorization inside the command transaction.")
    from .totp import require_sensitive_access

    # Explicit isolated test setting only; never enabled by production defaults.
    if getattr(
        settings, "RENTAL_RUNTIME_ENVIRONMENT", "production"
    ) == "test" and getattr(settings, "SECURITY_TEST_BYPASS", False):
        from core_apps.features.providers import fake_provider_available

        if fake_provider_available():
            require_sensitive_access(
                User.objects.select_for_update().get(pk=request.user.pk)
            )
            return
    user, session = _actor(request)
    policy = approved_policy("D26", action)
    token = request.headers.get("X-Sokoun-Authorization", "")
    item = (
        SensitiveAuthorization.objects.select_for_update()
        .filter(
            user=user,
            session=session,
            proof_digest=_digest(token),
            action=action,
            resource_id=resource_id,
            resource_revision=revision,
            policy=policy,
            payload_digest=fingerprint(
                payload if payload is not None else request.data
            ),
            security_epoch=user.security_epoch,
            verified_at__isnull=False,
            consumed_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
        if token
        else None
    )
    if item is None:
        raise PermissionDenied(
            "Fresh verification for these exact action details is required."
        )
    if item.assurance == "email_otp_or_totp":
        from .totp import is_staff_account, current_factor

        if is_staff_account(user):
            if current_factor(user).revision != item.factor_revision:
                raise PermissionDenied(
                    "The staff verification factor changed. Verify this action again."
                )
        elif item.factor_revision is not None:
            raise PermissionDenied(
                "The account verification context changed. Verify this action again."
            )
    item.consumed_at = timezone.now()
    item.save(update_fields=["consumed_at", "updated_at"])
    SecurityEvent.objects.create(
        user=user,
        actor=user,
        action=action,
        security_epoch=user.security_epoch,
        subject_id=resource_id,
        policy_version=policy.version,
        decision="authorized",
    )
