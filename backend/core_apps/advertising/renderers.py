from django.utils.cache import patch_vary_headers
from core_apps.common.renderers import GenericJsonRenderer


class AdvertisingJsonRenderer(GenericJsonRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        from .views import language

        context = renderer_context or {}
        request, response = context.get("request"), context.get("response")
        effective_language = language(request)
        if request is not None:
            request.LANGUAGE_CODE = effective_language
        if response is not None:
            response["Content-Language"] = effective_language
            patch_vary_headers(response, ["Accept-Language"])
        return super().render(data, accepted_media_type, context)
