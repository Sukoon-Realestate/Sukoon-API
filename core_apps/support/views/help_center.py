import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJsonRenderer
from core_apps.support.serializers import HelpCenterSerializer
from core_apps.support.services import get_help_center_content

logger = logging.getLogger(__name__)


class HelpCenterAPIView(APIView):
    """
    GET support/help-center/?workspace=tenant&lang=ar
    Returns contacts and FAQs scoped to workspace (tenant/owner) and language (ar/en).
    """

    permission_classes = [permissions.AllowAny]
    renderer_classes = [GenericJsonRenderer]
    serializer_class = HelpCenterSerializer

    def get(self, request, *args, **kwargs) -> Response:
        workspace = request.query_params.get("workspace", "tenant")
        lang = request.query_params.get("lang", "ar")

        content = get_help_center_content(workspace=workspace, lang=lang)
        serializer = self.serializer_class(content)
        return Response(serializer.data, status=status.HTTP_200_OK)
