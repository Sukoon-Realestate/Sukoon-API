"""Company case authority for the canonical chat transport, separate from groups."""

import uuid
from dataclasses import dataclass
from django.db import transaction
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.features.company_models import (
    Company,
    CompanyHousingRequest,
    CompanyMembership,
)
from core_apps.features.services.rental_lifecycle.common import require_actor
from core_apps.users.models import User
from core_apps.chat.models import Conversation, ConversationParticipant


@dataclass(frozen=True)
class CompanyConversationGrant:
    id: object
    role: str = "member"


def case_members(request):
    from core_apps.common.recovery import require_scope

    require_scope("company_authority")
    return (
        CompanyMembership.objects.filter(
            company=request.company,
            is_active=True,
            user__is_active=True,
            user__is_verified=True,
        )
        .filter(
            Q(is_coordinator=True, user_id=request.coordinator_id)
            | Q(is_approver=True, assigned_packages__request=request)
        )
        .distinct()
    )


def lock_root(conversation):
    initial = CompanyHousingRequest.objects.get(pk=conversation.company_request_id)
    Company.objects.select_for_update().get(pk=initial.company_id)
    return CompanyHousingRequest.objects.select_for_update().get(pk=initial.pk)


def authorize(conversation, user, *, action="read_chat", lock=False):
    from .group_access import actions

    require_actor(User.objects.get(pk=user.pk))
    request = (
        lock_root(conversation)
        if lock
        else get_object_or_404(
            CompanyHousingRequest, pk=conversation.company_request_id
        )
    )
    member = case_members(request).filter(user=user).first()
    if conversation.kind != "company_request" or not member:
        raise PermissionDenied(
            "Company discussion access is no longer available.",
            code="chat_access_revoked",
        )
    query = Conversation.objects.select_for_update() if lock else Conversation.objects
    conversation = query.get(pk=conversation.pk)
    participant = ConversationParticipant.objects.filter(
        conversation=conversation,
        user=user,
        company_membership=member,
        membership_revision=member.revision,
    ).first()
    if not participant or not participant.membership_period:
        raise PermissionDenied(
            "Company discussion access is no longer available.",
            code="chat_access_revoked",
        )
    grant = CompanyConversationGrant(member.id)
    if action not in actions(grant):
        raise PermissionDenied("This chat action is unavailable.")
    conversation.company_request = request
    return conversation, participant, grant


def eligible_participants(conversation):
    members = case_members(conversation.company_request)
    return conversation.participant_set.filter(
        company_membership__in=members,
        membership_revision=F("company_membership__revision"),
        user__is_active=True,
        user__is_verified=True,
    )


@transaction.atomic
def provision(request, actor):
    """Only domain commands alter participation; business history belongs to the case."""
    from .group_events import record_event

    Company.objects.select_for_update().get(pk=request.company_id)
    request = CompanyHousingRequest.objects.select_for_update().get(pk=request.pk)
    conversation, _ = Conversation.objects.get_or_create(
        company_request=request, defaults={"kind": "company_request"}
    )
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    members = list(case_members(request))
    current_ids = {m.pk for m in members}
    for participant in conversation.participant_set.exclude(
        company_membership_id__in=current_ids
    ):
        record_event(
            conversation,
            "conversation.access_revoked",
            actor=actor,
            data={"user_id": str(participant.user.id)},
        )
    for member in members:
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=member.user,
            defaults={
                "company_membership": member,
                "membership_revision": member.revision,
                "membership_period": uuid.uuid4(),
                "visible_from_sequence": 1,
            },
        )
        if not created and participant.membership_revision != member.revision:
            # A stale socket/journal cannot reuse an earlier authority epoch.
            record_event(
                conversation,
                "conversation.access_revoked",
                actor=actor,
                data={"user_id": str(member.user.id)},
            )
            participant.company_membership = member
            participant.membership_revision = member.revision
            participant.membership_period = uuid.uuid4()
            participant.save()
    record_event(conversation, "conversation.updated", actor=actor)
    return conversation


def refresh_company(company, actor):
    for request in company.housing_requests.filter(discussion__isnull=False).order_by(
        "pk"
    ):
        provision(request, actor)


@transaction.atomic
def approval_card(item, actor, event):
    from core_apps.chat.models import Message
    from .group_events import record_event

    conversation = provision(item.request, actor)
    identity = uuid.uuid5(
        uuid.NAMESPACE_URL, f"sokoun:company-package:{item.id}:{item.revision}:{event}"
    )
    if Message.objects.filter(
        conversation=conversation, client_message_id=identity
    ).exists():
        return
    conversation.last_sequence += 1
    conversation.save(update_fields=["last_sequence", "updated_at"])
    message = Message.objects.create(
        conversation=conversation,
        sender=actor,
        kind="system",
        content="",
        sequence=conversation.last_sequence,
        client_message_id=identity,
        system_data={
            "event": event,
            "company_id": str(item.request.company.id),
            "request_id": str(item.request.id),
            "item_id": str(item.id),
            "revision": item.revision,
        },
    )
    record_event(conversation, "message.new", message=message, actor=actor)
