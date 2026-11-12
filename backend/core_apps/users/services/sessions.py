"""Server-owned revocation; JWT signature validity does not restore authority."""

from datetime import datetime, timezone as dt_timezone
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import User, AuthSession, SecurityEvent


def validate_session(user, claims):

    if not user.is_active or claims.get("security_epoch", 0) != user.security_epoch:
        raise AuthenticationFailed(
            "Session revoked. Sign in again.", code="session_revoked"
        )
    sid = claims.get("session_id")
    if (
        sid
        and not AuthSession.objects.filter(
            id=sid,
            user=user,
            security_epoch=user.security_epoch,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).exists()
    ):
        raise AuthenticationFailed(
            "Session revoked. Sign in again.", code="session_revoked"
        )
    # Existing access tokens are compatible only before the first revocation.
    if not sid and (user.security_epoch or user.requires_bound_session):
        raise AuthenticationFailed("Sign in again.", code="session_revoked")
    return user


@transaction.atomic
def issue_refresh(user):
    current = User.objects.select_for_update().get(pk=user.pk)
    if current.security_epoch != user.security_epoch:
        raise AuthenticationFailed(
            "Session changed during sign-in. Try again.", code="session_revoked"
        )
    if not current.is_active:
        raise AuthenticationFailed("Account unavailable.")
    refresh = RefreshToken.for_user(current)
    session = AuthSession.objects.create(
        user=current,
        security_epoch=current.security_epoch,
        expires_at=datetime.fromtimestamp(refresh["exp"], tz=dt_timezone.utc),
    )

    refresh["security_epoch"] = current.security_epoch
    refresh["session_id"] = str(session.id)
    return refresh


@transaction.atomic
def revoke_all(user, *, actor=None, action="account.recovery", freeze=False):
    current = User.objects.select_for_update().get(pk=user.pk)
    current.security_epoch += 1
    if freeze:
        current.sensitive_actions_frozen = True
    current.save(update_fields=["security_epoch", "sensitive_actions_frozen"])
    AuthSession.objects.filter(user=current, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    from core_apps.notifications.models import DeviceToken

    DeviceToken.objects.filter(user=current, is_active=True).update(is_active=False)
    SecurityEvent.objects.create(
        user=current,
        actor=actor,
        action=action,
        security_epoch=current.security_epoch,
        decision="revoked",
    )
    return current


@transaction.atomic
def revoke_current(user, claims):
    sid = claims.get("session_id") if claims else None
    if not sid:
        return revoke_all(user, actor=user, action="session.legacy_logout")
    User.objects.select_for_update().get(pk=user.pk)
    AuthSession.objects.filter(id=sid, user=user, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    from core_apps.notifications.models import DeviceToken

    DeviceToken.objects.filter(user=user, auth_session__id=sid, is_active=True).update(
        is_active=False
    )
    # Unbound legacy devices cannot be attributed safely to a current session.
    DeviceToken.objects.filter(
        user=user, auth_session__isnull=True, is_active=True
    ).update(is_active=False)
    SecurityEvent.objects.create(
        user=user,
        actor=user,
        action="session.logout",
        security_epoch=user.security_epoch,
        subject_id=sid,
        decision="revoked",
    )


def issue_token_pair(user):
    refresh = issue_refresh(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@transaction.atomic
def refresh_bound_session(attrs, token_class=RefreshToken):
    """Rotate only a current bound session, updating its server-owned lifetime."""
    from rest_framework_simplejwt.serializers import TokenRefreshSerializer

    token = token_class(attrs["refresh"])
    user = User.objects.select_for_update().filter(id=token.get("user_id")).first()
    if user is None:
        raise AuthenticationFailed("Session unavailable.")
    validate_session(user, token)
    result = TokenRefreshSerializer().validate(attrs)
    rotated = token_class(result.get("refresh", attrs["refresh"]))
    if rotated.get("session_id"):
        AuthSession.objects.filter(
            id=rotated["session_id"], user=user, revoked_at__isnull=True
        ).update(expires_at=datetime.fromtimestamp(rotated["exp"], tz=dt_timezone.utc))
    return result
