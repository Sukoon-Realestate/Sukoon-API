"""Compatibility response for clients that used scheduled home reminders."""
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def home_visit_reminder(request):
    response = Response({'banner': None})
    response['Cache-Control'] = 'private, no-store'
    return response
