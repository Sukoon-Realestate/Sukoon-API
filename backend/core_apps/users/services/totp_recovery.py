"""R18: independent human review, exact-action proof and self-owned enrollment."""

from datetime import timedelta
from urllib.parse import quote, urlencode
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from core_apps.admin_api.models import StaffProfile
from core_apps.features.services.rental_phase2 import RentalConflict
from ..models import (
    User,
    AuthSession,
    SensitiveAuthorization,
    SecurityEvent,
    StaffSecurityIdentity,
    TotpFactor,
    TotpRecoveryRequest,
    TotpEnrollment,
    TotpRecoveryDecision,
    SecurityNotice,
)
from .sessions import validate_session
from . import totp


def _actor(request):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(user, request.auth or {})
    session = AuthSession.objects.filter(
        user=user,
        id=(request.auth or {}).get("session_id"),
        revoked_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).first()
    profile = StaffProfile.objects.filter(user=user).first()
    if (
        not session
        or (profile and not profile.is_active)
        or (not user.is_superuser and not profile)
    ):
        raise PermissionDenied("A current staff session is required.")
    return user, session, profile


def _identity(user):
    identity = StaffSecurityIdentity.objects.filter(user=user).first()
    if not identity or not all(
        (
            identity.person_reference,
            identity.evidence_reference,
            identity.known_channel_reference,
        )
    ):
        raise PermissionDenied(
            "Independent staff identity verification must be recorded first."
        )
    return identity


def _is_owner(user, profile=None):
    if profile and profile.role_name == "security_recovery_reviewer":
        return False
    return user.is_superuser or (
        profile.role_name == "system_owner"
        if profile
        else StaffProfile.objects.filter(
            user=user, role_name="system_owner", is_active=True
        ).exists()
    )


def _invalidate(user):
    SensitiveAuthorization.objects.filter(user=user, consumed_at__isnull=True).update(
        consumed_at=timezone.now()
    )
    TotpEnrollment.objects.filter(user=user, consumed_at__isnull=True).update(
        expires_at=timezone.now()
    )


def _event(item, actor, action):
    event = SecurityEvent.objects.create(
        user=item.user,
        actor=actor,
        action=f"account.totp.{action}",
        security_epoch=item.user.security_epoch,
        subject_id=item.id,
        decision=item.status,
    )
    SecurityNotice.objects.create(event=event, email_to=item.user.email)


def projection(item, *, review=False):
    value = {
        "id": str(item.id),
        "status": item.status,
        "revision": item.revision,
        "reason": item.reason,
        "review_available": _review_available(item),
        "decision_reason": item.decision_reason,
        "created_at": item.created_at.isoformat(),
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "decisions": [
            {
                "decision": row.decision,
                "reason": row.reason,
                "revision": row.revision,
                "created_at": row.created_at.isoformat(),
            }
            for row in item.decisions.order_by("created_at")
        ],
    }
    if review:
        value.update(
            user_id=str(item.user.id),
            email=item.user.email,
            identity_reference=item.identity.evidence_reference,
            known_channel_reference=item.identity.known_channel_reference,
            owner_request=item.owner_request,
        )
    return value


def _review_available(item):
    identities = (
        StaffSecurityIdentity.objects.select_related("user")
        .filter(user__is_active=True)
        .exclude(evidence_reference="")
        .exclude(known_channel_reference="")
        .exclude(person_reference="")
    )
    for identity in identities:
        user = identity.user
        if (
            user.pk == item.user_id
            or identity.person_reference == item.person_reference
        ):
            continue
        profile = StaffProfile.objects.filter(user=user).first()
        if profile and not profile.is_active:
            continue
        if not _is_owner(user, profile) and not (
            item.owner_request
            and profile
            and profile.role_name == "security_recovery_reviewer"
            and identity.designated_owner_reviewer
            and str(identity.id) in item.designated_reviewer_ids
        ):
            continue
        if user.sensitive_actions_frozen or totp.pending_recovery(user):
            continue
        if (
            TotpFactor.objects.filter(user=user, confirmed_at__isnull=False)
            .exclude(secret_ciphertext="")
            .exists()
        ):
            return True
    return False


@transaction.atomic
def status(request):
    from .staff_setup import initial_status

    user, _, profile = _actor(request)
    factor = TotpFactor.objects.filter(user=user).first()
    recovery = (
        TotpRecoveryRequest.objects.filter(user=user).order_by("-created_at").first()
    )
    return {
        "configured": bool(factor and factor.confirmed_at and factor.secret_ciphertext),
        "restricted": user.sensitive_actions_frozen
        or bool(recovery and recovery.active),
        "recovery": projection(recovery) if recovery else None,
        "initial_setup": initial_status(user),
        "can_document_staff_identity": _is_owner(user, profile),
    }


@transaction.atomic
def create_request(request, reason):
    user, _, profile = _actor(request)
    identity = _identity(user)
    item = TotpRecoveryRequest.objects.filter(user=user, active=True).first()
    if item:
        return projection(item)
    item = TotpRecoveryRequest.objects.create(
        user=user,
        identity=identity,
        person_reference=identity.person_reference,
        reason=reason,
        owner_request=_is_owner(user, profile),
        designated_reviewer_ids=[
            str(value)
            for value in StaffSecurityIdentity.objects.filter(
                designated_owner_reviewer=True,
                created_at__lt=timezone.now(),
                user__staff_profile__role_name="security_recovery_reviewer",
                user__staff_profile__is_active=True,
                user__totpfactor__confirmed_at__isnull=False,
            )
            .exclude(person_reference=identity.person_reference)
            .values_list("id", flat=True)
        ],
    )
    _invalidate(user)
    _event(item, user, "recovery_requested")
    return projection(item)


@transaction.atomic
def respond(request, identity, data):
    user, _, _ = _actor(request)
    item = (
        TotpRecoveryRequest.objects.select_for_update()
        .filter(id=identity, user=user, active=True)
        .first()
    )
    if not item:
        raise NotFound()
    if item.revision != data["expected_revision"] or item.status not in {
        "rejected",
        "information_requested",
    }:
        raise RentalConflict(
            "Refresh the current recovery request before responding.",
            code="revision_conflict",
        )
    item.reason = data["reason"]
    item.status = "pending"
    item.revision += 1
    item.save()
    TotpRecoveryDecision.objects.create(
        recovery=item,
        actor=user,
        revision=item.revision,
        decision="information_provided",
        reason=data["reason"],
    )
    _event(item, user, "recovery_updated")
    return projection(item)


def _can_review(user, profile, item):
    identity = _identity(user)
    if user.pk == item.user_id or identity.person_reference == item.person_reference:
        raise PermissionDenied(
            "Independent review cannot be performed by the applicant."
        )
    totp.require_sensitive_access(user)
    totp.current_factor(user)
    if _is_owner(user, profile):
        return
    if not (
        item.owner_request
        and profile
        and profile.role_name == "security_recovery_reviewer"
        and identity.designated_owner_reviewer
        and str(identity.id) in item.designated_reviewer_ids
        and identity.created_at < item.created_at
    ):
        raise PermissionDenied(
            "Only an independent authorized reviewer can decide this request."
        )
    # The designated authority is an exceptional fallback, not an alternate owner.
    owners = (
        User.objects.filter(is_active=True)
        .filter(
            Q(is_superuser=True)
            | Q(staff_profile__role_name="system_owner", staff_profile__is_active=True)
        )
        .exclude(pk=item.user_id)
        .distinct()
    )
    for owner in owners:
        owner_profile = StaffProfile.objects.filter(user=owner).first()
        if (owner_profile and not owner_profile.is_active) or not _is_owner(
            owner, owner_profile
        ):
            continue
        owner_identity = StaffSecurityIdentity.objects.filter(user=owner).first()
        if (
            owner_identity
            and owner_identity.evidence_reference
            and owner_identity.known_channel_reference
            and owner_identity.person_reference != item.person_reference
            and not owner.sensitive_actions_frozen
            and not totp.pending_recovery(owner)
            and TotpFactor.objects.filter(user=owner, confirmed_at__isnull=False)
            .exclude(secret_ciphertext="")
            .exists()
        ):
            raise PermissionDenied(
                "An available independent system owner must review this request."
            )


@transaction.atomic
def review_queue(request):
    user, _, profile = _actor(request)
    if not _is_owner(user, profile) and (
        not profile or profile.role_name != "security_recovery_reviewer"
    ):
        raise PermissionDenied("Recovery review authority is required.")
    result = []
    for item in TotpRecoveryRequest.objects.filter(active=True).select_related(
        "user", "identity"
    ):
        try:
            _can_review(user, profile, item)
        except PermissionDenied:
            continue
        result.append(projection(item, review=True))
    return result


@transaction.atomic
def decide(request, identity, data):
    target = TotpRecoveryRequest.objects.filter(id=identity).first()
    if not target:
        raise NotFound()
    # Shared lock order for cross-owner decisions, requests and enrollment.
    list(
        User.objects.select_for_update()
        .filter(pk__in=[request.user.pk, target.user_id])
        .order_by("pk")
    )
    user, _, profile = _actor(request)
    item = (
        TotpRecoveryRequest.objects.select_for_update()
        .select_related("user", "identity")
        .get(pk=target.pk)
    )
    _can_review(user, profile, item)
    if not item.active or item.revision != data["expected_revision"]:
        raise RentalConflict(
            "The recovery request changed. Refresh before deciding.",
            code="revision_conflict",
        )
    decision = data["decision"]
    if item.status == "approved" and decision != "renew_enrollment":
        raise RentalConflict("This request has already been approved.")
    if decision == "renew_enrollment" and item.status != "approved":
        raise ValidationError("Approve the independent review first.")
    approving = decision in {"approve", "renew_enrollment"}
    if approving and (
        data.get("verification_method") not in {"in_person", "known_channel_video"}
        or not data.get("verification_reference")
        or data.get("identity_matched") is not True
    ):
        raise ValidationError(
            "Record a successful independent identity check through the known channel."
        )
    from .sensitive_actions import consume

    consume(
        request,
        action="account.totp.recovery.review",
        resource_id=item.id,
        revision=item.revision,
        payload=data,
    )
    _invalidate(item.user)
    if approving:
        factor, _ = TotpFactor.objects.get_or_create(user=item.user)
        factor.secret_ciphertext = ""
        factor.confirmed_at = None
        factor.revision += 1
        factor.last_counter = -1
        factor.failed_attempts = 0
        factor.locked_until = None
        factor.save()
        item.approved_at = timezone.now()
        item.verified_at = timezone.now()
        item.verification_method = data["verification_method"]
        item.verification_reference = data["verification_reference"]
        item.status = "approved"
    else:
        item.status = "rejected" if decision == "reject" else "information_requested"
    item.reviewer = user
    item.decision_reason = data["reason"]
    item.revision += 1
    item.save()
    TotpRecoveryDecision.objects.create(
        recovery=item,
        actor=user,
        revision=item.revision,
        decision=decision,
        reason=data["reason"],
        verification_method=data.get("verification_method", ""),
        verification_reference=data.get("verification_reference", ""),
    )
    _event(item, user, "recovery_decided")
    return projection(item, review=True)


@transaction.atomic
def enroll(request, recovery_id):
    user, session, _ = _actor(request)
    item = (
        TotpRecoveryRequest.objects.select_for_update()
        .filter(id=recovery_id, user=user, active=True)
        .first()
    )
    if not item or item.status != "approved" or not item.approved_at:
        raise PermissionDenied(
            "Independent approval is required before binding a new factor."
        )
    # Approval is not a renewable bearer credential. A fresh review renews this window.
    deadline = item.approved_at + timedelta(minutes=5)
    if deadline <= timezone.now():
        raise PermissionDenied(
            "The binding authorization expired. Request a fresh review."
        )
    previous = TotpEnrollment.objects.filter(
        recovery=item, recovery_revision=item.revision
    ).first()
    if previous:
        if previous.session_id != session.pk or previous.expires_at <= timezone.now():
            raise PermissionDenied(
                "This binding belongs to another session or has expired. Request a fresh review."
            )
        enrollment = previous
    else:
        factor = TotpFactor.objects.select_for_update().get(user=user)
        enrollment = TotpEnrollment.objects.create(
            user=user,
            session=session,
            recovery=item,
            recovery_revision=item.revision,
            security_epoch=user.security_epoch,
            factor_revision=factor.revision,
            secret_ciphertext=totp.seal(totp.new_secret()),
            expires_at=deadline,
        )
    secret = totp.unseal(enrollment.secret_ciphertext)
    return {
        "id": str(enrollment.id),
        "expires_at": enrollment.expires_at.isoformat(),
        "secret": secret,
        "uri": "otpauth://totp/"
        + quote("Sokoun:" + user.email, safe="")
        + "?"
        + urlencode({"secret": secret, "issuer": "Sokoun", "digits": 6, "period": 30}),
    }


def confirm(request, identity, code):
    with transaction.atomic():
        result = _confirm_locked(request, identity, code)
    if result is None:
        raise ValidationError(
            {"code": "Invalid authenticator code. Try again within the binding window."}
        )
    return result


def _confirm_locked(request, identity, code):
    user, session, _ = _actor(request)
    enrollment = (
        TotpEnrollment.objects.select_for_update()
        .filter(id=identity, user=user, session=session)
        .first()
    )
    if not enrollment or enrollment.security_epoch != user.security_epoch:
        raise PermissionDenied("This binding authorization is unavailable.")
    if enrollment.recovery_id is None:
        from .staff_setup import confirm_locked

        return confirm_locked(request, user, enrollment, code)
    item = TotpRecoveryRequest.objects.select_for_update().get(
        pk=enrollment.recovery_id
    )
    if enrollment.consumed_at and item.status == "completed":
        return projection(
            item
        )  # Lost response: recover the original receipt, never rebind.
    if (
        enrollment.expires_at <= timezone.now()
        or not item.active
        or item.status != "approved"
        or item.revision != enrollment.recovery_revision
    ):
        raise PermissionDenied("This binding authorization expired or changed.")
    factor = TotpFactor.objects.select_for_update().get(user=user)
    if factor.revision != enrollment.factor_revision:
        raise PermissionDenied("The factor changed. Refresh the recovery request.")
    if not totp.check_code(
        factor, code, secret=totp.unseal(enrollment.secret_ciphertext)
    ):
        return None
    factor.secret_ciphertext = enrollment.secret_ciphertext
    factor.confirmed_at = timezone.now()
    factor.save()
    enrollment.consumed_at = timezone.now()
    enrollment.secret_ciphertext = ""
    enrollment.save()
    item.status, item.active, item.completed_at = "completed", False, timezone.now()
    item.revision += 1
    item.save()
    _event(item, user, "recovery_completed")
    # No role, account restriction, payment or provider instruction is changed.
    return projection(item)
