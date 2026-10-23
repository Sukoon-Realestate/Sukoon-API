"""Quarantined uploads, bound to one message under the command transaction."""

from datetime import timedelta
from uuid import uuid4
import hashlib
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound
from core_apps.common.private_media_policy import inspect, MIME_EXTENSIONS
from core_apps.support.models import TicketAttachment


def payload(item):
    return {
        "id": str(item.id),
        "name": item.name,
        "status": item.status,
        "media_metadata": item.media_metadata or {},
        "expires_at": item.expires_at,
        "client_upload_id": str(item.client_upload_id),
    }


def bind(message, ids, *, user, creation_key=None):
    if len(ids) > 3 or len(set(map(str, ids))) != len(ids):
        raise ValidationError(
            {"attachment_ids": "Choose up to three different attachments."}
        )
    for identity in ids:
        item = (
            TicketAttachment.objects.select_for_update()
            .filter(id=identity, uploader=user)
            .first()
        )
        if not item or item.workspace != message.ticket.workspace:
            raise NotFound()
        context_matches = (
            item.pending_ticket_id == message.ticket.pk
            if item.pending_ticket_id
            else str(item.creation_request_key) == str(creation_key) and creation_key
        )
        if (
            not context_matches
            or item.status != "ready"
            or item.message_id
            or not item.expires_at
            or item.expires_at <= timezone.now()
        ):
            raise ValidationError(
                {
                    "attachment_ids": "An attachment is unavailable, still being checked, or belongs to another request."
                }
            )
        item.message, item.status, item.private_content = message, "attached", None
        item.save(update_fields=["message", "status", "private_content"])


def cleanup_expired():
    """Keep identity tombstones; never delete a bound or actively scanned file."""
    ids = (
        TicketAttachment.objects.filter(
            message__isnull=True, expires_at__lte=timezone.now()
        )
        .exclude(
            status__in=["expired", "failed", "unsafe"],
            private_file="",
            private_content__isnull=True,
        )
        .order_by("expires_at")
        .values_list("pk", flat=True)[:100]
    )
    for identity in list(ids):
        with transaction.atomic():
            item = TicketAttachment.objects.select_for_update().get(pk=identity)
            if (
                item.message_id
                or item.expires_at > timezone.now()
                or (item.scan_until and item.scan_until > timezone.now())
            ):
                continue
            try:
                if item.private_file:
                    item.private_file.delete(save=False)
            except Exception:
                # Retain the reference for the next cleanup attempt.
                continue
            if item.status not in {"failed", "unsafe"}:
                item.status = "expired"
            item.private_content = None
            item.scan_token = item.scan_until = None
            item.save(
                update_fields=[
                    "status",
                    "private_content",
                    "private_file",
                    "scan_token",
                    "scan_until",
                ]
            )


def scan_pending():
    from django.db.models import Q
    from core_apps.features.services.evidence_storage import available, scan

    cleanup_expired()
    if not available():
        return {"unavailable": True}
    scanned = 0
    ids = (
        TicketAttachment.objects.filter(status="pending", expires_at__gt=timezone.now())
        .filter(Q(scan_until__isnull=True) | Q(scan_until__lt=timezone.now()))
        .order_by("created_at")
        .values_list("pk", flat=True)[:2]
    )
    for identity in list(ids):
        token = uuid4()
        with transaction.atomic():
            item = TicketAttachment.objects.select_for_update().get(pk=identity)
            if (
                item.status != "pending"
                or item.expires_at <= timezone.now()
                or (item.scan_until and item.scan_until > timezone.now())
            ):
                continue
            item.scan_token, item.scan_until = token, timezone.now() + timedelta(
                minutes=5
            )
            # Persist the deterministic destination before external I/O. Lost
            # responses and cancellation retain the same cleanup identity.
            item.private_file.name = f"attachments/{item.id}.{MIME_EXTENSIONS[item.media_metadata['mime_type']]}"
            item.save(update_fields=["scan_token", "scan_until", "private_file"])
        content = bytes(item.private_content or b"")
        try:
            metadata = inspect(
                content, item.media_metadata["mime_type"], digest=item.content_sha256
            )
            result = scan(content)
            if result.sha256 != item.content_sha256:
                raise ValidationError("Integrity mismatch")
            state = "ready" if result.safe else "unsafe"
            if result.safe:
                if not TicketAttachment.objects.filter(
                    pk=identity,
                    scan_token=token,
                    status="pending",
                    scan_until__gt=timezone.now(),
                    expires_at__gt=timezone.now(),
                ).exists():
                    continue
                item.private_file.storage.save_immutable(
                    item.private_file.name, content, item.content_sha256
                )
        except ValidationError:
            state, metadata = "failed", item.media_metadata
        except Exception:
            TicketAttachment.objects.filter(
                pk=identity, scan_token=token, status="pending"
            ).update(scan_token=None, scan_until=timezone.now() + timedelta(minutes=1))
            continue
        with transaction.atomic():
            current = TicketAttachment.objects.select_for_update().get(pk=identity)
            if current.scan_token != token or current.status != "pending":
                # A later worker may own this exact immutable object. Never
                # delete its winning file from a stale completion.
                if current.scan_token == token and current.status == "expired":
                    current.scan_token = current.scan_until = None
                    current.save(update_fields=["scan_token", "scan_until"])
                continue
            current.status, current.media_metadata = state, metadata
            current.private_file = item.private_file
            current.scan_token = current.scan_until = None
            if state != "ready":
                current.private_content = None
                current.expires_at = timezone.now()
            current.save()
        scanned += 1
    cleanup_expired()
    return {"scanned": scanned}
