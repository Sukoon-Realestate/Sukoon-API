"""Legacy preference history remains stored; inert switches are not editable rules."""

from django.db import transaction
from rest_framework.exceptions import ValidationError


def get_platform_settings():
    # Historical booleans have no runtime consumers. They cannot promise
    # verification, privacy or inventory behavior to an administrator.
    return {}


@transaction.atomic
def update_platform_settings(payload, actor=None):
    from core_apps.admin_api.permissions import require_staff_actor

    require_staff_actor(actor, {"system_owner"}, lock=True)
    if not isinstance(payload, dict) or payload:
        raise ValidationError(
            "These settings have no operational effect and are not editable. Use the relevant published workflow."
        )
    return get_platform_settings()
