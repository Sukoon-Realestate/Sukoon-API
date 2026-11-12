"""Locked Djoser mutations preserve current authority and closed-account erasure."""
from django.db import transaction
from djoser import signals
from djoser.compat import get_user_email
from djoser.conf import settings
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from ..models import User
from .sessions import validate_session


@transaction.atomic
def update_account(request, serializer, *, sender, check_permissions):
    identities = {request.user.pk, serializer.instance.pk}
    locked = {user.pk: user for user in User.objects.select_for_update().filter(
        pk__in=identities,
    ).order_by("pk")}
    actor, target = locked.get(request.user.pk), locked.get(serializer.instance.pk)
    if actor is None:
        raise AuthenticationFailed("Account unavailable.")
    if target is None:
        raise NotFound()
    validate_session(actor, request.auth or {"security_epoch": request.user.security_epoch})
    request.user = actor
    check_permissions(request, target)
    if target.closed_at:
        raise PermissionDenied("Closed account data cannot be restored.")
    serializer.instance = target
    user = serializer.save()
    signals.user_updated.send(sender=sender, user=user, request=request)
    if settings.SEND_ACTIVATION_EMAIL and not user.is_active:
        settings.EMAIL.activation(request, {"user": user}).send([get_user_email(user)])


def activate_account(request, serializer_factory, *, sender):
    serializer = serializer_factory(data=request.data)
    serializer.is_valid(raise_exception=True)
    return _activate_locked(request, serializer.user.pk, serializer_factory, sender=sender)


@transaction.atomic
def _activate_locked(request, user_pk, serializer_factory, *, sender):
    current = User.objects.select_for_update().get(pk=user_pk)
    if current.closed_at:
        raise PermissionDenied("Closed accounts cannot be reactivated.")
    serializer = serializer_factory(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.user
    user.is_active = True
    user.save()
    signals.user_activated.send(sender=sender, user=user, request=request)
    if settings.SEND_CONFIRMATION_EMAIL:
        settings.EMAIL.confirmation(request, {"user": user}).send([get_user_email(user)])
