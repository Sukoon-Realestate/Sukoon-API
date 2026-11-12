from .http import IdentityAPIView as APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from .services import email_change


class EmailChangeThrottle(UserRateThrottle):
    scope = "email_change"
    rate = "60/hour"


class EmailChangeStartAPIView(APIView):
    name = "Start"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]
    throttle_classes = [EmailChangeThrottle]

    def post(self, request):
        return Response(email_change.start(request), status=201)


class EmailChangeAPIView(APIView):
    name = "Change"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'post', 'delete', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]
    throttle_classes = [EmailChangeThrottle]

    def get(self, request, identity, action=None):
        data, code = email_change.command(request, identity, "status")
        return Response(data, status=code)

    def post(self, request, identity, action=None):
        data, code = email_change.command(request, identity, action)
        return Response(data, status=code)

    def delete(self, request, identity, action=None):
        data, code = email_change.command(request, identity, "cancel")
        return Response(data, status=code)
