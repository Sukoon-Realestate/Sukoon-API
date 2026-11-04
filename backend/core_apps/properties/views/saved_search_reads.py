from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from ..services.saved_search_reads import acknowledge


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def acknowledge_saved_search(request, read_id):
    return Response(
        acknowledge(request.user, read_id, request.auth),
        headers={"Cache-Control": "private, no-store"},
    )
