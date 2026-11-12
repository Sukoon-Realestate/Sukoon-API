from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.idempotency import request_key, response_headers
from . import identity_expiry


class IdentityExpiryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(identity_expiry.current_expiry(request.user), headers={"Cache-Control": "private, no-store"})

    def post(self, request):
        result, code, replayed = identity_expiry.save_expiry(
            request.user, request_key(request), request.data
        )
        return Response(
            result, status=code,
            headers={**response_headers(replayed), "Cache-Control": "private, no-store"},
        )
