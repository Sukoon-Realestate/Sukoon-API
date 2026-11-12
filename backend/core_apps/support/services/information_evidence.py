"""Ticket-owned evidence requirements, immutable versions and independent review."""

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.common.private_media_policy import policy
from core_apps.support.models import TicketAttachment, TicketEvidenceSubmission


def requirement(ticket):
    rules = policy()
    return {
        "schema_version": 1,
        "policy_revision": rules["schema_version"],
        "case_type": f"support.{ticket.category}",
        "required_from_user_id": str(ticket.user.id),
        "min_attachments": 1,
        "max_attachments": 3,
        "types": rules["types"],
    }


def validate_answer(row, attachment_ids, user):
    rules = row.evidence_requirement
    if not rules:
        return
    if rules.get("required_from_user_id") != str(user.id):
        raise ValidationError(
            "Only the requested ticket owner may submit this evidence."
        )
    if not rules["min_attachments"] <= len(attachment_ids) <= rules["max_attachments"]:
        raise ValidationError(
            {"attachment_ids": "Attach the evidence required by this request."}
        )
    for identity in attachment_ids:
        item = (
            TicketAttachment.objects.select_for_update()
            .filter(id=identity, uploader=user, pending_ticket=row.ticket)
            .first()
        )
        if (
            item is None
            or item.status != "ready"
            or item.message_id
            or (item.media_metadata or {}).get("kind") not in rules["types"]
        ):
            raise ValidationError(
                {
                    "attachment_ids": "The evidence is not authorized, inspected, or compatible with this request."
                }
            )


def record_submission(row):
    if not row.evidence_requirement:
        return
    previous = row.evidence_versions.order_by("-version").first()
    files = [
        {
            "id": str(item.id),
            "sha256": item.content_sha256,
            "mime_type": item.media_metadata["mime_type"],
            "size_bytes": item.media_metadata["size_bytes"],
        }
        for item in row.answer.attachments.all()
    ]
    TicketEvidenceSubmission.objects.create(
        request=row,
        message=row.answer,
        version=previous.version + 1 if previous else 1,
        files=files,
    )


def files_current(submission):
    for version in submission.files:
        item = TicketAttachment.objects.filter(
            id=version["id"], message=submission.message, status="attached"
        ).first()
        if item is None or item.content_sha256 != version["sha256"]:
            return False
    return bool(submission.files)


def review(row, actor, action, reason):
    if not row.evidence_requirement:
        if action == "mark_evidence_conflicting":
            raise ValidationError(
                "Choose an evidence requirement to record a conflict."
            )
        return
    submission = (
        row.evidence_versions.select_for_update().filter(message=row.answer).first()
    )
    if submission is None:
        raise ValidationError("This request has no submitted evidence version.")
    if action == "accept_information" and not files_current(submission):
        raise ValidationError(
            "Evidence access changed. Review its current availability before accepting."
        )
    submission.review_status = {
        "accept_information": "accepted",
        "return_information": "correction",
        "mark_evidence_conflicting": "conflicting",
    }[action]
    submission.reviewed_by, submission.reviewed_at, submission.review_reason = (
        actor,
        timezone.now(),
        reason,
    )
    submission.save(
        update_fields=[
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "review_reason",
            "updated_at",
        ]
    )


def availability_for(submissions):
    """Resolve current file proof in one query, scoped to each version's message."""
    identities = {value["id"] for item in submissions for value in item.files}
    if not identities:
        return set()
    return {
        (identity, message_id, digest)
        for identity, message_id, digest in TicketAttachment.objects.filter(
            id__in=identities, status="attached"
        ).values_list("id", "message_id", "content_sha256")
    }


def projection(row, *, submissions=None, available=None):
    submissions = (
        list(row.evidence_versions.select_related("message").order_by("version"))
        if submissions is None
        else submissions
    )
    available = availability_for(submissions) if available is None else available
    return [
        {
            "id": str(item.id),
            "version": item.version,
            "message_id": str(item.message.id),
            "review_status": item.review_status,
            "review_reason": item.review_reason,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
            "files": [
                {
                    **value,
                    "available": (
                        TicketAttachment._meta.get_field("id").to_python(value["id"]),
                        item.message_id,
                        value["sha256"],
                    )
                    in available,
                }
                for value in item.files
            ],
        }
        for item in submissions
    ]
