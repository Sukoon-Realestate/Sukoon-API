"""Filter before pagination; display scope never replaces chat authorization."""

from uuid import UUID
from django.db.models import Q, F, Exists, OuterRef
from rest_framework.exceptions import ValidationError, APIException
from core_apps.chat.models import Conversation, ConversationParticipant
from core_apps.features.services.planning import require_planning
from core_apps.features.services.company.access import company_for


def visible(user):
    participant = ConversationParticipant.objects.filter(conversation_id=OuterRef("pk"), user=user).filter(
        Q(hidden_through_sequence__isnull=True) | Q(hidden_through_sequence__lt=F("conversation__last_sequence"))
    )
    base = Conversation.objects.annotate(viewer_visible=Exists(participant)).filter(viewer_visible=True)
    allowed = Q(kind="direct")
    try:
        require_planning(user, "housing_groups")
    except APIException:
        pass
    else:
        allowed |= Q(
            kind="housing_group",
            housing_group__status="active",
            participant_set__user=user,
            participant_set__membership__status="active",
            participant_set__membership_revision=F(
                "participant_set__membership__joined_revision"
            ),
        )
    company = ConversationParticipant.objects.filter(
        conversation_id=OuterRef("pk"),
        user=user,
        user__is_active=True,
        user__is_verified=True,
        company_membership__is_active=True,
        company_membership__company_id=F("conversation__company_request__company_id"),
        membership_revision=F("company_membership__revision"),
        membership_period__isnull=False,
    ).filter(
        Q(
            company_membership__is_coordinator=True,
            conversation__company_request__coordinator_id=user.pk,
        )
        | Q(
            company_membership__is_approver=True,
            company_membership__assigned_packages__request_id=F(
                "conversation__company_request_id"
            ),
        )
    )
    return (
        base.annotate(company_chat_allowed=Exists(company))
        .filter(allowed | Q(kind="company_request", company_chat_allowed=True))
        .distinct()
    )


def scoped(user, scope, company_id=""):
    if scope not in {"all", "general", "individual", "student", "owner", "company"}:
        raise ValidationError({"workspace": "Unknown message workspace."})
    qs = visible(user)
    if scope == "all":
        raise ValidationError({"workspace": "Choose one workspace to view messages."})
    if scope == "company":
        try:
            UUID(str(company_id))
        except (ValueError, TypeError):
            raise ValidationError({"company_id": "Choose a company."})
        company_for(user, company_id)
        return qs.filter(
            kind="company_request", company_request__company__id=company_id
        )
    classified = Q(workspace_contexts__user=user)
    if scope == "general":
        return qs.filter(kind="direct").exclude(classified)
    query = Q(
        kind="direct",
        workspace_contexts__user=user,
        workspace_contexts__workspace=scope,
    )
    if scope == "student":
        # Group membership grants access; a stale workspace hint cannot move it.
        query |= Q(kind="housing_group")
    return qs.filter(query).distinct()
