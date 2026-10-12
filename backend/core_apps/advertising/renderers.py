import json

from rest_framework.renderers import JSONRenderer

from core_apps.common.translation import translate_message


class AdvertisingJsonRenderer(JSONRenderer):
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        request = (renderer_context or {}).get("request")
        
        # Resolve effective language from view/middleware/headers
        from .views import language as get_effective_lang
        request_language = get_effective_lang(request) if request else "en"
        
        if response is not None:
            response["Content-Language"] = request_language
            response["Vary"] = "Accept-Language"
            if response.status_code >= 400:
                response["Cache-Control"] = "no-store"
        if response is not None and response.status_code == 204:
            return b""
        if not isinstance(data, dict) or data.get("key") not in {"success", "error"}:
            is_error = bool(response and response.status_code >= 400)
            message = "Request failed." if is_error else "Request completed."
            if isinstance(data, dict):
                message = str(data.get("detail") or data.get("message") or message)
            message = translate_message(message, request_language)
            data = {
                "key": "error" if is_error else "success",
                "message": message,
                "data": None if is_error else data,
            }
            if is_error:
                data["errors"] = None
        return json.dumps(data, ensure_ascii=False).encode(self.charset)
