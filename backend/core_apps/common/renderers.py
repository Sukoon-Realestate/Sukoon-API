import json
from typing import Any, Optional, Union

from django.utils.translation import gettext as _
from rest_framework.renderers import JSONRenderer


from core_apps.common.translation import (
    translate_field_label,
    translate_message,
)


class GenericJsonRenderer(JSONRenderer):
    """
    Standardizes every API response into one of two shapes:

    * Success GET  -> {"data": <payload>}
    * Success else -> {"message": "...", "data": <payload>}
    * Error        -> {"message": "..."}
    """

    charset = "utf-8"

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Optional[dict] = None,
    ) -> Union[bytes, str]:
        if renderer_context is None:
            renderer_context = {}

        response = renderer_context.get("response")

        if not response:
            raise ValueError(_("Response not found in renderer context!"))

        status_code = response.status_code
        request = renderer_context.get("request")
        req_lang = getattr(request, "LANGUAGE_CODE", None)

        # * HTTP 204 No Content must never contain a message body (RFC 9110)
        # ? Proxies terminate connections with protocol_error if 204 has a body
        if status_code == 204:
            return b""

        # * DRF sometimes sets the data to the status code integer for empty bodies
        if data is None or data == "" or data == status_code:
            data = {}

        if status_code >= 400:
            return json.dumps(
                {"message": _extract_message(data, req_lang)}, ensure_ascii=False
            ).encode(self.charset)

        if request and request.method == "GET":
            return json.dumps({"data": data}, ensure_ascii=False).encode(self.charset)

        message, payload = _extract_message_and_payload(data)
        if not message:
            message = _default_success_message(
                request.method if request else None, status_code
            )

        if req_lang:
            message = translate_message(str(message), req_lang)

        return json.dumps(
            {"message": message, "data": payload}, ensure_ascii=False
        ).encode(self.charset)


def _extract_message(data: Any, language: Optional[str] = None) -> str:
    """
    Convert an error payload into a single human-readable message string.
    """
    if isinstance(data, str):
        return translate_message(data, language) if language else data

    if isinstance(data, list):
        return _stringify_value(data, language)

    if not isinstance(data, dict):
        msg = _("An error occurred.")
        return translate_message(str(msg), language) if language else str(msg)

    if "message" in data and isinstance(data["message"], str):
        return translate_message(data["message"], language) if language else data["message"]

    if "detail" in data:
        return _stringify_value(data["detail"], language)

    if "errors" in data:
        return _stringify_value(data["errors"], language)

    return _stringify_field_errors(data, language)


def _stringify_value(value: Any, language: Optional[str] = None) -> str:
    if isinstance(value, str):
        return translate_message(value, language) if language else value

    if isinstance(value, list):
        return " ".join(_stringify_value(item, language) for item in value if item)

    if isinstance(value, dict):
        return _stringify_field_errors(value, language)

    return str(value)


def _stringify_field_errors(errors: dict, language: Optional[str] = None) -> str:
    messages = []
    for field, value in errors.items():
        label = field.replace("_", " ").title()
        if language and language.startswith("ar"):
            label = translate_field_label(label, language)
        messages.append(f"{label}: {_stringify_value(value, language)}")

    default_err = _("An error occurred.")
    fallback = translate_message(str(default_err), language) if language else str(default_err)
    return " ".join(messages) if messages else fallback


def _extract_message_and_payload(data: Any) -> tuple[Optional[str], Any]:
    """
    Pull a top-level 'message' key out of a success payload and return the
    remaining data as the payload.
    """
    if not isinstance(data, dict) or "message" not in data:
        return None, data

    payload = data.copy()
    message = payload.pop("message", None)
    return message, payload


def _default_success_message(method: Optional[str], status_code: int) -> str:
    if status_code == 201:
        return _("Created successfully.")

    if method == "DELETE":
        return _("Deleted successfully.")

    if method in ("PUT", "PATCH"):
        return _("Updated successfully.")

    return _("Operation successful.")


def custom_exception_handler(exc: Any, context: Any) -> Any:
    """
    Standardize DRF exception responses to the app-wide error format.
    """
    # ? Lazy import avoids a circular import when DRF settings load this module
    from rest_framework.views import exception_handler as drf_exception_handler

    response = drf_exception_handler(exc, context)
    if response is not None:
        request = context.get("request") if context else None
        req_lang = getattr(request, "LANGUAGE_CODE", None)
        response.data = {"message": _extract_message(response.data, req_lang)}
    return response
