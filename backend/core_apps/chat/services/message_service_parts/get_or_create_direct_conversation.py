"""Message service: get or create direct conversation."""

import logging
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from core_apps.chat.models import Conversation


logger = logging.getLogger(__name__)



class ChatMessageConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "client_message_id was already used for different content."
    default_code = "client_message_conflict"


def direct_message_blocked(first_user, second_user, *, lock=False):
    from core_apps.features.planning_models import RoommateConnection
    from core_apps.chat.models import ChatBlock
    from django.db.models import Q
    if ChatBlock.objects.filter(Q(user=first_user, blocked_user=second_user) | Q(user=second_user, blocked_user=first_user)).exists():
        return True

    first, second = sorted([first_user.pk, second_user.pk])
    query = RoommateConnection.objects.filter(first_id=first, second_id=second)
    if lock:
        query = query.select_for_update()
    item = query.first()
    return item is not None and item.status != "accepted"


@transaction.atomic
def get_or_create_direct_conversation(*, user, other_user, workspace=None, rental_context=None, expected_visit_revision=None) -> Conversation:
    """
    Return the canonical 1:1 conversation between two users, creating it if absent.

    Raises ValidationError if user tries to create a conversation with themselves.
    """
    if user.pk == other_user.pk:
        raise ValidationError(
            {"user_id": "You cannot start a conversation with yourself."}
        )

    from django.contrib.auth import get_user_model

    people = list(
        get_user_model()
        .objects.select_for_update()
        .filter(pk__in=[user.pk, other_user.pk])
        .order_by("pk")
    )
    if len(people) != 2 or not all(person.is_active and not person.closed_at for person in people):
        raise PermissionDenied("Both conversation participants must be active.")
    visit_id=rental_context.get('visit_id') if isinstance(rental_context,dict) else None
    if expected_visit_revision is not None and not visit_id:
        raise ValidationError('A viewing revision requires its viewing identity.')
    if visit_id:
        from core_apps.properties.models import Property,PropertyVisit
        from core_apps.properties.services.viewing_access import can_read
        from core_apps.common.idempotency import IdempotencyConflict
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            found=PropertyVisit.objects.select_related('property').filter(id=visit_id).first()
        except (ValueError,TypeError,DjangoValidationError):
            raise ValidationError('Supply a valid viewing identity.')
        if not found:
            raise PermissionDenied('The viewing is not available to these participants.')
        Property.objects.select_for_update().get(pk=found.property_id)
        visit=PropertyVisit.objects.select_for_update(of=('self',)).select_related('property').get(pk=found.pk)
        if (str(visit.property.id)!=str(rental_context.get('property_id')) or
                not can_read(visit,user) or not can_read(visit,other_user)):
            raise PermissionDenied('The viewing does not belong to this conversation.')
        if expected_visit_revision is not None:
            if (visit.revision!=expected_visit_revision or visit.status!='confirmed' or visit.visit_date is None or visit.visit_time is None):
                raise IdempotencyConflict('The appointment changed. Review it before preparing this message.')
            if visit.context_kind!='personal' or visit.renter_workspace!='individual' or visit.company_id or visit.academic_plan_id:
                raise PermissionDenied('This draft is available for individual viewings only.')
    from core_apps.chat.services.conversation_preferences import contextual_conversation

    if workspace is None:
        # Calls without an explicit workspace are ordinary individual chats.
        # The app always supplies its current workspace; rental context still
        # identifies the owner when an internal caller only supplies a property.
        workspace = "individual"
        if isinstance(rental_context, dict) and rental_context.get("property_id"):
            from core_apps.properties.models import Property
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                if Property.objects.filter(id=rental_context["property_id"], owner=user).exists():
                    workspace = "owner"
            except (ValueError, TypeError, DjangoValidationError):
                raise ValidationError({"rental_context": "Invalid property identity."})
    return contextual_conversation(user, other_user, workspace, rental_context)
