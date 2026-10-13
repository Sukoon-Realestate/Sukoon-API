"""Shared HTTP JSON contract. Protocol-specific endpoints opt out explicitly."""

import logging
import uuid

from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from .response_messages import _extract_message, _extract_message_and_payload
from .response_policy import envelope, error_metadata

logger = logging.getLogger(__name__)


class GenericJsonRenderer(JSONRenderer):
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        context = renderer_context or {}
        response = context.get("response")
        if response is None:
            raise ValueError("Response not found in renderer context!")
        request = context.get("request")
        if (
            response.status_code in (204, 304)
            or getattr(request, "method", None) == "HEAD"
        ):
            return b""
        return super().render(
            envelope(data, response, request), accepted_media_type, context
        )


def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)
    if response is None:
        correlation = str(uuid.uuid4())
        logger.error(
            "api_request_failed correlation=%s error_type=%s",
            correlation,
            type(exc).__name__,
        )
        response = Response({"message": "An error occurred.", "data": None}, status=500)
        response["X-Correlation-ID"] = correlation
    else:
        error_metadata(response, response.data, exc)
        language = getattr((context or {}).get("request"), "LANGUAGE_CODE", None)
        response.data = {
            "message": _extract_message(response.data, language),
            "data": None,
        }
    return response
