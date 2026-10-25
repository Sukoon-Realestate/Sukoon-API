from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import ChatQuickReply
from core_apps.users.models import User
from core_apps.features.services.rental_lifecycle.common import require_actor
from .group_limits import ChatConflict


class QuickReplyBody(serializers.Serializer):
    title = serializers.CharField(max_length=60)
    content = serializers.CharField(max_length=2000)
    expected_revision = serializers.IntegerField(min_value=0)


def payload(reply):
    return {"id": str(reply.id), "title": reply.title, "content": reply.content, "revision": reply.revision}


def listing(user):
    require_actor(user)
    return [
        payload(r) for r in ChatQuickReply.objects.filter(user=user, deleted_at__isnull=True).order_by("title", "pk")
    ]


@transaction.atomic
def save(user, identity, data=None):
    require_actor(User.objects.select_for_update().get(pk=user.pk))
    existing = ChatQuickReply.objects.filter(id=identity).first()
    if existing and existing.user_id != user.pk:
        raise PermissionDenied("This saved reply is unavailable.")
    if data is None:
        if existing is None:
            ChatQuickReply.objects.create(id=identity, user=user, title="", content="", deleted_at=timezone.now())
        elif not existing.deleted_at:
            existing.deleted_at = timezone.now()
            existing.save(update_fields=["deleted_at"])
        return {"id": str(identity)}
    body = QuickReplyBody(data=data)
    body.is_valid(raise_exception=True)
    values = body.validated_data
    if existing:
        if existing.deleted_at:
            raise ChatConflict("This saved reply was deleted. Create a new reply.")
        if existing.title == values["title"] and existing.content == values["content"]:
            return payload(existing)
        if existing.revision != values["expected_revision"]:
            raise ChatConflict("This saved reply changed. Reload it before editing.")
        existing.title, existing.content = values["title"], values["content"]
        existing.revision += 1
        existing.save()
    else:
        if values["expected_revision"] != 0:
            raise ChatConflict("This saved reply is unavailable.")
        if ChatQuickReply.objects.filter(user=user, deleted_at__isnull=True).count() >= 50:
            raise ValidationError("You can save up to 50 quick replies.")
        existing = ChatQuickReply.objects.create(
            id=identity, user=user, title=values["title"], content=values["content"]
        )
    return payload(existing)
