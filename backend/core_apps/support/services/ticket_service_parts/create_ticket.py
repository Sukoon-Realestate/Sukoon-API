"""Ticket service: create ticket."""

import logging
import uuid
from typing import Any, List, Optional
from django.db import transaction
from rest_framework.exceptions import ValidationError
from core_apps.support.models import Ticket, TicketAttachment, TicketMessage


logger = logging.getLogger(__name__)


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


MAX_ATTACHMENTS_COUNT = 3


class TicketClosedConflict(Exception):
    """Raised when an action is attempted on a resolved or closed ticket."""

    pass


def list_user_tickets(user: Any, workspace: str = "tenant"):
    """
    Returns ordered queryset of support tickets belonging to the authenticated user and workspace.
    """
    normalized_workspace = "owner" if workspace.lower() == "owner" else "tenant"
    return Ticket.objects.filter(user=user, workspace=normalized_workspace).order_by(
        "-updated_at", "-id"
    )


def generate_ticket_reference() -> str:
    """Generate human-readable unique reference like SUP-00142."""
    short_code = uuid.uuid4().hex[:5].upper()
    return f"SUP-{short_code}"


@transaction.atomic
def create_ticket(
    user: Any,
    workspace: str,
    category: str,
    subject: str,
    description: str,
    attachments: Optional[List[Any]] = None,
    rental_context: Optional[dict] = None,
) -> Ticket:
    """
    Creates a new support ticket with initial user message and attachments.
    """
    normalized_workspace = "owner" if workspace.lower() == "owner" else "tenant"
    subject = subject.strip()
    description = description.strip()
    rental_context = rental_context or {}
    if not isinstance(rental_context, dict):
        raise ValidationError({"rental_context": "Must be an object."})
    allowed_context = {
        "lease_id",
        "invoice_id",
        "payment_attempt_id",
        "subject_kind",
        "subject_id",
    }
    if set(rental_context) - allowed_context:
        raise ValidationError({"rental_context": "Contains unsupported fields."})
    if rental_context:
        from core_apps.features.models import Lease, PaymentAttempt, RentInvoice
        from core_apps.features.services.rental_foundation import (
            get_authorized_rental_subject,
        )

        resolved = {}
        for key in ("lease_id", "invoice_id", "payment_attempt_id", "subject_id"):
            if rental_context.get(key):
                resolved[key] = get_authorized_rental_subject(user, rental_context[key])
        lease_ids = set()
        for value in resolved.values():
            if isinstance(value, Lease):
                lease_ids.add(value.pk)
            elif isinstance(value, RentInvoice):
                lease_ids.add(value.lease_id)
            elif isinstance(value, PaymentAttempt):
                lease_ids.add(value.invoice.lease_id)
        if len(lease_ids) > 1:
            raise ValidationError(
                {"rental_context": "All rental IDs must belong to one lease."}
            )

    if len(subject) < 3 or len(subject) > 160:
        raise ValidationError(
            {"subject": "يجب أن يتراوح طول عنوان التذكرة بين 3 و160 حرفاً."}
        )

    if len(description) < 10 or len(description) > 4000:
        raise ValidationError(
            {"description": "يجب أن يتراوح طول وصف المشكلة بين 10 و4000 حرف."}
        )

    # Validate category constraints by workspace
    if normalized_workspace == "tenant" and category == "report_tenant":
        raise ValidationError(
            {"category": "تصنيف 'إبلاغ عن مستأجر' غير متاح لحساب المستأجر."}
        )

    if normalized_workspace == "owner" and category == "report_owner":
        raise ValidationError(
            {"category": "تصنيف 'إبلاغ عن مالك' غير متاح لحساب المالك."}
        )

    # Validate attachments
    attachments = attachments or []
    if len(attachments) > MAX_ATTACHMENTS_COUNT:
        raise ValidationError(
            {"attachments": f"الحد الأقصى للمرفقات هو {MAX_ATTACHMENTS_COUNT} صور."}
        )

    for att in attachments:
        ext = att.name.split(".")[-1].lower() if "." in att.name else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                {
                    "attachments": f"صيغة الملف '{att.name}' غير مدعومة. الصيغ المسموحة: JPG, PNG, WebP."
                }
            )
        if att.size > MAX_ATTACHMENT_SIZE_BYTES:
            raise ValidationError(
                {
                    "attachments": f"حجم الملف '{att.name}' يتجاوز الحد الأقصى 5 ميجابايت."
                }
            )
        from core_apps.support.services.private_attachments import clean_image
        clean_image(att)

    reference = generate_ticket_reference()
    while Ticket.objects.filter(reference=reference).exists():
        reference = generate_ticket_reference()

    ticket = Ticket.objects.create(
        user=user,
        workspace=normalized_workspace,
        category=category,
        subject=subject,
        reference=reference,
        status=Ticket.Status.OPEN,
        rental_context=rental_context,
    )

    initial_message = TicketMessage.objects.create(
        ticket=ticket,
        sender=TicketMessage.SenderType.USER,
        sender_user=user,
        body=description,
    )

    stored = []
    try:
        for att in attachments:
            from core_apps.support.services.private_attachments import store_image
            stored.append(store_image(initial_message, att))
    except Exception:
        for attachment in stored:
            attachment.private_file.delete(save=False)
        raise

    logger.info(
        "Created support ticket %s (%s) for user %s in workspace %s",
        ticket.id,
        ticket.reference,
        user.id,
        normalized_workspace,
    )
    return ticket
