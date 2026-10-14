"""Stable public imports for ticket service.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
import uuid
from typing import Any, List, Optional
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.support.models import Ticket, TicketAttachment, TicketMessage

from .ticket_service_parts.create_ticket import (
    logger,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_ATTACHMENT_SIZE_BYTES,
    MAX_ATTACHMENTS_COUNT,
    TicketClosedConflict,
    list_user_tickets,
    generate_ticket_reference,
    create_ticket,
)
from .ticket_service_parts.get_ticket_detail import (
    get_ticket_detail,
    add_ticket_reply,
)
