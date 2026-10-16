from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_projection import summary
from .company_views import company_api


@company_api(["GET"])
def discussion(request, company_id, request_id):
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
