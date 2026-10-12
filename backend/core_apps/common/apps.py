from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core_apps.common"
    verbose_name = _("Common")

    def ready(self):
        # Register worker evidence signals; importing does not connect to Redis.
        from config import runtime  # noqa: F401
