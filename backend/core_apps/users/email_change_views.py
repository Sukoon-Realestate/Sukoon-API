from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    throttle_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from .services import email_change


class EmailChangeThrottle(UserRateThrottle):
    scope = "email_change"
    rate = "60/hour"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
@throttle_classes([EmailChangeThrottle])
def start(request):
    return Response(email_change.start(request), status=201)


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
@throttle_classes([EmailChangeThrottle])
def change(request, identity, action=None):
    if request.method == "GET":
        action = "status"
    elif request.method == "DELETE":
        action = "cancel"
    data, code = email_change.command(request, identity, action)
    return Response(data, status=code)
