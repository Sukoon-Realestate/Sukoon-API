from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import ReputationAccessGrant
from .policy import ReviewError, require_enabled, keys, revision, text_value
from .submission import command, audit
from .visibility import summary


def payload(item):
    return {
        "id": str(item.id),
        "subject_kind": item.subject_kind,
        "recipient_id": str(item.recipient.id),
        "purpose": item.purpose,
        "expires_at": item.expires_at.isoformat(),
        "revoked": bool(item.revoked_at),
        "revision": item.revision,
    }


def create(user, body):
    def action():
        require_enabled()
        keys(
            body,
            ["request_key", "subject_kind", "recipient_id", "purpose", "days"],
            ["request_key", "subject_kind", "recipient_id", "purpose"],
        )
        days = body.get("days", 7)
        if (
            body["subject_kind"] not in {"person_tenant", "person_housemate"}
            or type(days) is not int
            or not 1 <= days <= 30
        ):
            raise ReviewError("invalid_review_target", 400)
        recipient = (
            get_user_model()
            .objects.filter(id=body["recipient_id"], is_active=True)
            .first()
        )
        if not recipient or recipient.pk == user.pk:
            raise NotFound()
        if not text_value(body["purpose"], 200):
            raise ReviewError("invalid_review_text", 400)
        item = ReputationAccessGrant.objects.create(
            owner=user,
            recipient=recipient,
            subject_kind=body["subject_kind"],
            purpose=text_value(body["purpose"], 200),
            expires_at=timezone.now() + timedelta(days=days),
        )
        audit(item, user, "summary_shared")
        return payload(item)

    return command(user, "review.grant_create", body, action)


def revoke(user, identity, body):
    item = ReputationAccessGrant.objects.filter(id=identity, owner=user).first()
    if not item:
        raise NotFound()

    def action():
        locked = ReputationAccessGrant.objects.select_for_update().get(pk=item.pk)
        revision(locked, body.get("expected_revision"))
        locked.revoked_at = timezone.now()
        locked.revision += 1
        locked.save(update_fields=["revoked_at", "revision", "updated_at"])
        audit(locked, user, "summary_revoked")
        return payload(locked)

    return command(user, f"review.grant_revoke.{identity}", body, action, item.id)


def read(user, identity):
    item = (
        ReputationAccessGrant.objects.select_related("owner")
        .filter(id=identity, recipient=user)
        .first()
    )
    if not item:
        raise NotFound()
    if item.revoked_at:
        raise ReviewError("grant_revoked")
    if timezone.now() >= item.expires_at:
        raise ReviewError("grant_expired")
    audit(item, user, "summary_read")
    return summary(item.subject_kind, item.owner.id, item.owner)
