import json
from typing import Any, Optional, Union

from django.utils.translation import gettext as _
from rest_framework.renderers import JSONRenderer


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

        # * DRF sometimes sets the data to the status code integer for empty bodies
        if data is None or data == "" or data == status_code:
            data = {}

        if status_code >= 400:
            return json.dumps(
                {"message": _extract_message(data)}, ensure_ascii=False
            ).encode(self.charset)

        if request and request.method == "GET":
            return json.dumps({"data": data}, ensure_ascii=False).encode(self.charset)

        message, payload = _extract_message_and_payload(data)
        if not message:
            message = _default_success_message(
                request.method if request else None, status_code
            )

        return json.dumps(
            {"message": message, "data": payload}, ensure_ascii=False
        ).encode(self.charset)


def _extract_message(data: Any) -> str:
    """
    Convert an error payload into a single human-readable message string.
    """
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        return _stringify_value(data)

    if not isinstance(data, dict):
        return _("An error occurred.")

    if "message" in data and isinstance(data["message"], str):
        return data["message"]

    if "detail" in data:
        return _stringify_value(data["detail"])

    if "errors" in data:
        return _stringify_value(data["errors"])

    return _stringify_field_errors(data)


def _stringify_value(value: Any) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(_stringify_value(item) for item in value if item)

    if isinstance(value, dict):
        return _stringify_field_errors(value)

    return str(value)


def _stringify_field_errors(errors: dict) -> str:
    messages = []
    for field, value in errors.items():
        label = field.replace("_", " ").title()
        messages.append(f"{label}: {_stringify_value(value)}")

    return " ".join(messages) if messages else _("An error occurred.")


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
        response.data = {"message": _extract_message(response.data)}
    return response
