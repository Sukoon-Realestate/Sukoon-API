from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from core_apps.users.models import User
from .models import Profile
from .identity_media import IDENTITY_FIELDS, identity_bytes, version


@method_decorator(never_cache, name="dispatch")
class IdentityMediaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, field):
        if field not in IDENTITY_FIELDS:
            raise NotFound()
        user = get_object_or_404(User, pk=request.user.pk, is_active=True)
        profile = get_object_or_404(Profile, user=user)
        asset = getattr(profile, field)
        if not asset or request.query_params.get("version") != version(asset):
            raise NotFound()
        return identity_bytes(asset)
