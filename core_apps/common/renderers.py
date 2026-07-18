import json
from typing import Optional, Any, Union
from django.utils.translation import gettext_lazy as _
from rest_framework.renderers import JSONRenderer


class GenericJsonRenderer(JSONRenderer):
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

        if data is None:
            return b""

        if isinstance(data, list):
            errors = None
        else:
            errors = data.get("errors", None)

        if errors is not None:
            return super(GenericJsonRenderer, self).render(data)

        return json.dumps({"status_code": status_code, "data": data}).encode(
            self.charset
        )
