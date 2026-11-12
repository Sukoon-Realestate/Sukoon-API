"""Password mutation and recovery use one account lock and revocation boundary.

Djoser's serializers retain their validation/error contracts. Revalidation happens
inside the lock so concurrent recovery links cannot both authorize a password.
"""
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.utils.timezone import now
from djoser import utils
from djoser.compat import get_user_email
from djoser.conf import settings

from ..models import User
from .sessions import revoke_all, validate_session


def apply_password(user, new_password, *, recovered=False):
    """Caller holds the account lock; mutation and revocation commit together."""
    user.set_password(new_password)
    if recovered and hasattr(user, "last_login"):
        user.last_login = now()
    user.save()
    revoke_all(user, action="password.reset" if recovered else "password.change")


def notify_password_changed(request, user):
    if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
        settings.EMAIL.password_changed_confirmation(request, {"user": user}).send(
            [get_user_email(user)]
        )


@transaction.atomic
def change_inherited_password(request, serializer_factory):
    current = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(current, request.auth or {"security_epoch": request.user.security_epoch})
    request.user = current
    serializer = serializer_factory(data=request.data)
    serializer.is_valid(raise_exception=True)
    apply_password(request.user, serializer.data["new_password"])
    notify_password_changed(request, request.user)
    if settings.LOGOUT_ON_PASSWORD_CHANGE:
        utils.logout_user(request)
    elif settings.CREATE_SESSION_ON_LOGIN:
        update_session_auth_hash(request, request.user)


@transaction.atomic
def reset_inherited_password(request, serializer_factory):
    serializer = serializer_factory(data=request.data)
    serializer.is_valid(raise_exception=True)
    User.objects.select_for_update().get(pk=serializer.user.pk)
    # Re-read and revalidate the epoch-bound link after acquiring the account lock.
    serializer = serializer_factory(data=request.data)
    serializer.is_valid(raise_exception=True)
    apply_password(serializer.user, serializer.data["new_password"], recovered=True)
    notify_password_changed(request, serializer.user)
