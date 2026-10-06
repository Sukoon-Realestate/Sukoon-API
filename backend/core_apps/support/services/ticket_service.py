import logging
import uuid
from typing import Any, List, Optional
from django.db import transaction
from django.utils import timezone
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
) -> Ticket:
    """
    Creates a new support ticket with initial user message and attachments.
    """
    normalized_workspace = "owner" if workspace.lower() == "owner" else "tenant"
    subject = subject.strip()
    description = description.strip()

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
    )

    initial_message = TicketMessage.objects.create(
        ticket=ticket,
        sender=TicketMessage.SenderType.USER,
        sender_user=user,
        body=description,
    )

    for att in attachments:
        TicketAttachment.objects.create(
            message=initial_message,
            name=att.name,
            file=att,
        )

    logger.info(
        "Created support ticket %s (%s) for user %s in workspace %s",
        ticket.id,
        ticket.reference,
        user.id,
        normalized_workspace,
    )
    return ticket


def get_ticket_detail(
    user: Any, ticket_id: str, workspace: Optional[str] = None
) -> Ticket:
    """
    Retrieves full ticket detail ensuring account ownership and workspace scoping.
    Raises Ticket.DoesNotExist on ownership/workspace mismatch.
    """
    qs = (
        Ticket.objects.select_related("user")
        .prefetch_related("messages", "messages__attachments")
        .filter(user=user)
    )

    # Allow querying by UUID id or reference
    try:
        uuid_val = uuid.UUID(ticket_id)
        ticket = qs.filter(id=uuid_val).first()
    except (ValueError, AttributeError):
        ticket = qs.filter(reference=ticket_id).first()

    if not ticket:
        raise Ticket.DoesNotExist("Ticket not found or access denied.")

    if workspace:
        normalized_workspace = "owner" if workspace.lower() == "owner" else "tenant"
        if ticket.workspace != normalized_workspace:
            raise Ticket.DoesNotExist("Ticket does not belong to requested workspace.")

    return ticket


@transaction.atomic
def add_ticket_reply(
    user: Any, ticket_id: str, body: str, workspace: Optional[str] = None
) -> Ticket:
    """
    Adds a reply to an active ticket and returns the complete updated ticket.
    Rejects replies to resolved/closed tickets with TicketClosedConflict.
    """
    ticket = get_ticket_detail(user, ticket_id, workspace=workspace)

    if ticket.status in [Ticket.Status.RESOLVED, Ticket.Status.CLOSED]:
        raise TicketClosedConflict("لا يمكن الرد على تذكرة دعم تم حلها أو إغلاقها.")

    clean_body = body.strip()
    if len(clean_body) < 1 or len(clean_body) > 4000:
        raise ValidationError({"body": "يجب أن يتراوح طول نص الرد بين 1 و4000 حرف."})

    TicketMessage.objects.create(
        ticket=ticket,
        sender=TicketMessage.SenderType.USER,
        sender_user=user,
        body=clean_body,
    )

    ticket.updated_at = timezone.now()
    ticket.save(update_fields=["updated_at"])

    logger.info("Added reply to ticket %s by user %s", ticket.reference, user.id)
    return get_ticket_detail(user, ticket_id, workspace=workspace)
