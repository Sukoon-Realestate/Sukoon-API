from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .identity_media import identity_bytes
from .selectors import owned_identity_asset


@method_decorator(never_cache, name="dispatch")
class IdentityMediaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, field):
        asset = owned_identity_asset(request.user, field, request.query_params.get("version"))
        return identity_bytes(asset)
