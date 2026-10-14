"""Owner/tenant-scoped tenancy invitation collection."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import Property
from ..models import TenancyInvitation
from ..serializers import TenancyInvitationSerializer
from ..services.tenancy_invitations import refresh_effective_status
from .rental_operation_lookup import _paginate


def list_invitations(request):
    workspace = request.query_params.get("workspace")
    if workspace == "owner":
        queryset = TenancyInvitation.objects.filter(owner=request.user)
    elif workspace == "tenant":
        queryset = TenancyInvitation.objects.filter(tenant=request.user)
    else:
        raise ValidationError({"workspace": "Must be owner or tenant."})
    property_id = request.query_params.get("property_id")
    if property_id:
        if workspace == "owner":
            get_object_or_404(Property, id=property_id, owner=request.user)
        queryset = queryset.filter(property__id=property_id)
    queryset = queryset.select_related(
        "property", "property__owner", "owner", "tenant", "lease"
    ).order_by("-created_at", "-id")
    for invitation in list(queryset):
        refresh_effective_status(invitation)
    return _paginate(request, queryset.all(), TenancyInvitationSerializer)
