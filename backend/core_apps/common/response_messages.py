"""Localized response text; stable codes never depend on these messages."""

from typing import Any, Optional
from django.utils.translation import gettext as _
from .translation import translate_field_label, translate_message


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
        return (
            translate_message(data["message"], language)
            if language
            else data["message"]
        )

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
    fallback = (
        translate_message(str(default_err), language) if language else str(default_err)
    )
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
