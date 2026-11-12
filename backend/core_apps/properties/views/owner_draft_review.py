"""Fresh owner reads for local draft review, without public-interest events."""

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property
from ..serializers import PropertyDetailSerializer


class OwnerDraftReviewAPIView(APIView):
    http_method_names = ["get", "options"]
    name = "Owner Draft Review"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, property_id):
        actor = User.objects.get(pk=request.user.pk)
        if not actor.is_active or actor.closed_at:
            raise PermissionDenied()
        if request.auth:
            validate_session(actor, request.auth)
        prop = get_object_or_404(
            Property, id=property_id, owner=actor, retired_at__isnull=True
        )
        return Response(
            PropertyDetailSerializer(prop, context={"request": request}).data,
            headers={"Cache-Control": "private, no-store"},
        )
