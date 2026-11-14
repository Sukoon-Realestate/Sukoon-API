from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_projection import summary


class DiscussionView(FeatureAPIView):
    name = "Discussion"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_chat_views",
            "discussion",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id, request_id):
        conversation = get_object_or_404(
            Conversation,
            kind="company_request",
            company_request__id=request_id,
            company_request__company__id=company_id,
        )
        return Response(
            summary(conversation, request.user),
            headers={"Cache-Control": "private, no-store"},
        )


# Stable callable import for integrations; URLs use the explicit class.
discussion = DiscussionView.as_view()
