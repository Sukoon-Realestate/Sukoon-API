"""Explicit tour transport policies, including the credential-only byte protocol."""

from rest_framework.views import APIView
from rest_framework.parsers import BaseParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from core_apps.features.renderers import FeatureJsonRenderer
from .errors import require
from .operations import mutate


class OwnerTourAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if (
            request.method in ("POST", "PATCH", "DELETE")
            and request.method.lower() in self.http_method_names
        ):
            require(
                isinstance(request.data, dict),
                "invalid_request",
                "A JSON object is required.",
                400,
            )

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if (
            not getattr(response, "exception", False)
            and request.method != "OPTIONS"
            and request.method.lower() in self.http_method_names
        ):
            response["Cache-Control"] = "private, no-store"
            response["Referrer-Policy"] = "no-referrer"
            response["X-Content-Type-Options"] = "nosniff"
        return response


class PublicTourAPIView(OwnerTourAPIView):
    permission_classes = [AllowAny]


class ReviewerTourAPIView(OwnerTourAPIView):
    """Reviewer authority is checked fresh by the review read/command service."""


class ViewerTourAPIView(PublicTourAPIView):
    authentication_classes = []


class RawPartParser(BaseParser):
    media_type = "application/octet-stream"

    def parse(self, stream, media_type=None, parser_context=None):
        # The upload service reads bounded chunks; never materialize request.body.
        return stream


def mutation(request, action, resource, execute):
    data, status, replayed = mutate(
        user=request.user,
        auth=request.auth,
        key=request.headers.get("Idempotency-Key", ""),
        body=request.data,
        etag=request.headers.get("If-Match", ""),
        action=action,
        resource=resource,
        execute=execute,
    )
    return Response(
        data, status=status, headers={"Idempotency-Replayed": str(replayed).lower()}
    )
