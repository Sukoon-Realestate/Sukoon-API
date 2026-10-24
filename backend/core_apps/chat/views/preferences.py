from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import Conversation, ChatList
from core_apps.chat.services.conversation_preferences import preferences_payload, update_preferences, WORKSPACES
from core_apps.chat.services.group_access import authorize


class ConversationPreferencesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        conversation, participant, _ = authorize(get_object_or_404(Conversation, id=id), request.user)
        return Response(preferences_payload(conversation, request.user, participant))

    def patch(self, request, id):
        from core_apps.chat.services.group_rate_limit import enforce_rate
        from core_apps.chat.services.group_projection import summary
        enforce_rate(request.user, "preferences")
        conversation = get_object_or_404(Conversation, id=id)
        update_preferences(conversation, request.user, request.data)
        conversation.refresh_from_db()
        return Response(summary(conversation, request.user))


def list_context(user, values):
    scope = values.get("workspace")
    if not isinstance(scope, str) or scope not in WORKSPACES | {"company"}:
        raise ValidationError({"workspace": "Choose a workspace."})
    organization = ""
    if scope == "company":
        from core_apps.features.services.company.access import company_for
        from uuid import UUID
        try:
            organization = str(UUID(str(values.get("company_id", ""))))
        except (ValueError, TypeError):
            raise ValidationError({"company_id": "Choose a company."})
        company_for(user, organization)
    return scope, organization


class ChatListsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scope, organization = list_context(request.user, request.query_params)
        return Response({"results": [{"id": str(x.id), "name": x.name} for x in ChatList.objects.filter(user=request.user, workspace=scope, organization=organization).order_by("name")]})

    def post(self, request):
        scope, organization = list_context(request.user, request.data)
        name = request.data.get("name")
        if scope not in WORKSPACES | {"company"} or not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValidationError("Choose a workspace and a list name of up to 80 characters.")
        item, _ = ChatList.objects.get_or_create(user=request.user, workspace=scope, organization=organization, name=name.strip())
        return Response({"id": str(item.id), "name": item.name})

    def delete(self, request):
        from rest_framework.serializers import UUIDField
        identity = UUIDField().run_validation(request.data.get("id"))
        get_object_or_404(ChatList, id=identity, user=request.user).delete()
        return Response(status=204)
