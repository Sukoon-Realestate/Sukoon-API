import json

from rest_framework.renderers import JSONRenderer

from core_apps.common.renderers import _extract_message, _extract_message_and_payload


class FeatureJsonRenderer(JSONRenderer):
    """Renderer for the mobile feature-v1 success contract."""

    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        request = renderer_context.get("request")
        if response is None:
            raise ValueError("Response not found in renderer context.")
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        if response.status_code == 204:
            return b""
        if response.status_code >= 400:
            error = {
                "message": _extract_message(
                    data, getattr(request, "LANGUAGE_CODE", None)
                )
            }
            if isinstance(data, dict):
                for key in (
                    "code",
                    "subject_id",
                    "next_action",
                    "payment_attempt_id",
                    "correlation_id",
                ):
                    if key in data:
                        error[key] = data[key]
                detail = data.get("detail")
                detail_code = getattr(detail, "code", None)
                if detail_code and "code" not in error:
                    error["code"] = detail_code
            return json.dumps(
                error,
                ensure_ascii=False,
            ).encode(self.charset)
        message, payload = _extract_message_and_payload(data)
        return json.dumps(
            {"key": "success", "msg": message or "", "data": payload},
            ensure_ascii=False,
        ).encode(self.charset)
