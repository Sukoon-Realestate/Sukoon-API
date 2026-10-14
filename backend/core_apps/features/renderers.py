from core_apps.common.renderers import GenericJsonRenderer


class FeatureJsonRenderer(GenericJsonRenderer):
    """Rental/planning projections are private and non-cacheable by HTTP."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response is not None:
            response["Cache-Control"] = "private, no-store"
            response["Pragma"] = "no-cache"
        return super().render(data, accepted_media_type, renderer_context)
