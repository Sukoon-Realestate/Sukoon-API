from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.services.reputation.public_summary import public_summary
from ..services.public_access import public_properties
from .property_parts.property_list_apiview import PropertyListAPIView


class PublicOwnerProfileView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, identity):
        owner = get_object_or_404(get_user_model(), id=identity, is_active=True)
        from core_apps.features.models import Lease
        from ..models import Property

        # Switching workspaces does not make a tenant account a public owner.
        if not Property.objects.filter(owner=owner).exists() and not Lease.objects.filter(owner=owner).exists():
            raise NotFound()
        profile = getattr(owner, "profile", None)
        image = getattr(profile, "avatar", None)
        from core_apps.features.services.owner_achievements import summary

        progress = summary(owner)
        progress.pop("pending_event", None)
        response = Response(
            {
                "achievements": progress,
                "id": str(owner.id),
                "name": owner.get_full_name or owner.first_name,
                "avatar": request.build_absolute_uri(image.url) if image else "",
                "is_verified": owner.is_verified,
                "member_since": owner.date_joined.date().isoformat(),
                "listing_count": public_properties().filter(owner=owner).count(),
                "reputation": public_summary("person_landlord", owner.id),
            }
        )
        response["Cache-Control"] = "no-store"
        return response


class PublicOwnerListingsView(PropertyListAPIView):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(owner__id=self.kwargs["identity"], owner__is_active=True)
        )
