"""Fresh owner reads for local draft review, without public-interest events."""
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property
from ..serializers import PropertyDetailSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def owner_draft_review(request, property_id):
    actor = User.objects.get(pk=request.user.pk)
    if not actor.is_active or actor.closed_at:
        raise PermissionDenied()
    if request.auth:
        validate_session(actor, request.auth)
    prop = get_object_or_404(Property, id=property_id, owner=actor, retired_at__isnull=True)
    return Response(PropertyDetailSerializer(prop, context={"request": request}).data,
        headers={"Cache-Control": "private, no-store"})
