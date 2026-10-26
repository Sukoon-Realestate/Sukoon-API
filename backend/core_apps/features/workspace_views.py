"""Additive presentation summary. A workspace selection is never an authority."""

from rest_framework.response import Response
from rest_framework.exceptions import APIException
from .company_views import company_api
from core_apps.chat.services.workspace_inbox import scoped, visible
from core_apps.chat.services.group_access import authorize, unread_count
from core_apps.chat.models import ConversationWorkspace
from core_apps.profiles.services import ProfileService


@company_api(["GET"])
def summary(request):
    user = request.user
    from core_apps.notifications.services.inbox_scope import request_scope
    from core_apps.notifications.services.preferences import touch
    scope = request_scope(request)
    if request.query_params.get("active_workspace") == "true":
        touch(user, scope)
    data = ProfileService.get_tenant_unread_counts(user, scope=scope)
    counts = {
        key: 0
        for key in ("individual", "student", "owner", "company", "general", "all")
    }
    company_counts = {}
    contexts = {}
    for cid, workspace in ConversationWorkspace.objects.filter(user=user).values_list(
        "conversation_id", "workspace"
    ):
        contexts.setdefault(cid, set()).add(workspace)
    for conversation in visible(user).select_related("company_request"):
        if conversation.kind == "direct":
            participant = conversation.participant_set.get(user=user)
            count = participant.unread_count
            spaces = contexts.get(conversation.pk, {"general"})
        else:
            try:
                _, participant, _ = authorize(conversation, user)
                count = unread_count(conversation, participant)
            except APIException:
                continue
            if conversation.kind == "company_request":
                spaces = {"company"}
                cid = str(conversation.company_request.company.id)
                company_counts[cid] = company_counts.get(cid, 0) + count
            else:
                spaces = {"student"}
        counts["all"] += count
        for space in spaces:
            counts[space] += count
    data.update(
        workspace_chat_counts=counts,
        company_chat_counts=company_counts,
        unread_chat_messages_count=counts["all"],
    )
    response = Response(data)
    response["Cache-Control"] = "private, no-store"
    return response
