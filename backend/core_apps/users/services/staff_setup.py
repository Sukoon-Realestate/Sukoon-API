"""Initial staff enrollment using independently documented, existing authority.

This cannot replace a factor or provision the exceptional owner-recovery role.
Operational bootstrap identities remain a separate, independently verified input.
"""

from datetime import timedelta
from urllib.parse import quote, urlencode

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from core_apps.admin_api.models import StaffProfile
from core_apps.features.services.rental_phase2 import RentalConflict, fingerprint
from ..models import (
    User,
    StaffSecurityIdentity,
    TotpFactor,
    TotpEnrollment,
    TotpRecoveryRequest,
    SensitiveAuthorization,
    SecurityEvent,
    SecurityNotice,
)
from . import totp, totp_recovery


def identity_projection(user, identity=None):
    identity = identity or StaffSecurityIdentity.objects.filter(user=user).first()
    factor = TotpFactor.objects.filter(user=user).first()
    return {
        "user_id": str(user.id),
        "email": user.email,
        "name": user.get_full_name,
        "documented": bool(identity),
        "configured": bool(factor and factor.confirmed_at and factor.secret_ciphertext),
        "recovery_pending": totp.pending_recovery(user),
        "identity_reference": identity.evidence_reference if identity else "",
        "known_channel_reference": identity.known_channel_reference if identity else "",
    }


def _notice(user, actor, subject, action):
    event = SecurityEvent.objects.create(
        user=user,
        actor=actor,
        action=action,
        subject_id=subject,
        security_epoch=user.security_epoch,
        decision="recorded",
    )
    SecurityNotice.objects.create(event=event, email_to=user.email)


def initial_status(user):
    identity = StaffSecurityIdentity.objects.filter(user=user).first()
    factor = TotpFactor.objects.filter(user=user).first()
    documented = bool(
        identity
        and identity.person_reference
        and identity.evidence_reference
        and identity.known_channel_reference
    )
    previously_bound = bool(
        (factor and (factor.confirmed_at or factor.revision > 1))
        or TotpEnrollment.objects.filter(user=user, consumed_at__isnull=False).exists()
        or TotpRecoveryRequest.objects.filter(user=user).exists()
    )
    restricted = user.sensitive_actions_frozen or totp.pending_recovery(user)
    return {
        "identity_documented": documented,
        "available": documented and not previously_bound and not restricted,
        "requires_recovery": previously_bound,
    }


@transaction.atomic
def identities(request):
    user, _, profile = totp_recovery._actor(request)
    if not totp_recovery._is_owner(user, profile):
        raise PermissionDenied("System-owner authority is required.")
    staff = (
        User.objects.filter(is_active=True)
        .filter(Q(staff_profile__is_active=True) | Q(is_superuser=True))
        .exclude(pk=user.pk)
        .order_by("email")
        .distinct()
    )
    return {"results": [identity_projection(target) for target in staff]}


@transaction.atomic
def document_identity(request, user_id, data):
    target = User.objects.filter(id=user_id, is_active=True).first()
    if not target:
        raise NotFound()
    list(
        User.objects.select_for_update()
        .filter(pk__in=[request.user.pk, target.pk])
        .order_by("pk")
    )
    actor, _, profile = totp_recovery._actor(request)
    if not totp_recovery._is_owner(actor, profile):
        raise PermissionDenied("System-owner authority is required.")
    reviewer_identity = totp_recovery._identity(actor)
    totp.require_sensitive_access(actor)
    totp.current_factor(actor)
    target.refresh_from_db()
    target_profile = StaffProfile.objects.filter(user=target).first()
    if (
        not target.is_active
        or (target_profile and not target_profile.is_active)
        or (not target.is_superuser and not target_profile)
    ):
        raise PermissionDenied("A current active staff account is required.")
    if (
        actor.pk == target.pk
        or data["person_reference"] == reviewer_identity.person_reference
    ):
        raise PermissionDenied(
            "The applicant cannot verify their own identity, including through another account."
        )
    if totp.pending_recovery(target):
        raise PermissionDenied(
            "Identity and reviewer designation cannot change during recovery."
        )
    identity = StaffSecurityIdentity.objects.filter(user=target).first()
    digest = fingerprint(data)
    if identity:
        if (
            identity.verified_by_id == actor.pk
            and identity.verification_digest == digest
        ):
            return identity_projection(target, identity)
        raise RentalConflict(
            "This staff identity is already documented. Refresh its current status.",
            code="identity_already_documented",
        )
    if data["identity_matched"] is not True:
        raise ValidationError(
            "Record a successful independent human identity check first."
        )
    from .sensitive_actions import consume

    consume(
        request,
        action="account.mfa.manage",
        resource_id=target.id,
        revision=0,
        payload=data,
    )
    identity = StaffSecurityIdentity.objects.create(
        user=target,
        person_reference=data["person_reference"],
        evidence_reference=data["evidence_reference"],
        known_channel_reference=data["known_channel_reference"],
        verification_method=data["verification_method"],
        verified_by=actor,
        verification_digest=digest,
    )
    totp_recovery._invalidate(target)
    _notice(target, actor, identity.id, "account.totp.identity_documented")
    return identity_projection(target, identity)


@transaction.atomic
def enroll(request):
    user, session, _ = totp_recovery._actor(request)
    if not initial_status(user)["available"]:
        raise PermissionDenied(
            "Initial binding requires an independently documented identity and no previous factor or recovery. Review account security."
        )
    identity = totp_recovery._identity(user)
    factor, _ = TotpFactor.objects.get_or_create(user=user)
    previous = (
        TotpEnrollment.objects.filter(
            user=user,
            recovery__isnull=True,
            consumed_at__isnull=True,
            expires_at__gt=timezone.now(),
            security_epoch=user.security_epoch,
        )
        .order_by("-created_at")
        .first()
    )
    if previous:
        if previous.session_id != session.pk:
            raise RentalConflict(
                "An initial binding is open in another session. Complete it there or wait for its five-minute expiry.",
                code="binding_in_progress",
            )
        enrollment = previous
    else:
        enrollment = TotpEnrollment.objects.create(
            user=user,
            session=session,
            initial_identity=identity,
            security_epoch=user.security_epoch,
            factor_revision=factor.revision,
            secret_ciphertext=totp.seal(totp.new_secret()),
            expires_at=timezone.now() + timedelta(minutes=5),
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


def confirm_locked(request, user, enrollment, code):
    factor = TotpFactor.objects.select_for_update().filter(user=user).first()
    if enrollment.consumed_at:
        # Recover the original receipt without rotating a factor or replaying a command.
        return totp_recovery.status(request)
    identity = totp_recovery._identity(user)
    if (
        not initial_status(user)["available"]
        or enrollment.initial_identity_id != identity.pk
        or enrollment.expires_at <= timezone.now()
        or not factor
        or factor.revision != enrollment.factor_revision
    ):
        raise PermissionDenied(
            "The initial binding expired or its authorization changed. Refresh account security."
        )
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
    SensitiveAuthorization.objects.filter(user=user, consumed_at__isnull=True).update(
        consumed_at=timezone.now()
    )
    TotpEnrollment.objects.filter(user=user, consumed_at__isnull=True).update(
        expires_at=timezone.now()
    )
    _notice(user, user, enrollment.id, "account.totp.initial_completed")
    return totp_recovery.status(request)
