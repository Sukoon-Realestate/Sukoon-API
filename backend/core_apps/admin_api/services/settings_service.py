from django.db import transaction
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.models.platform_preferences import (
    PlatformPreferences,
    PlatformPreferenceAudit,
    default_platform_preferences,
)


def get_platform_settings():
    current, _ = PlatformPreferences.objects.get_or_create(pk=1)
    return dict(current.values)


@transaction.atomic
def update_platform_settings(payload, actor=None):
    if (
        not isinstance(payload, dict)
        or set(payload) - set(default_platform_preferences())
        or any(type(value) is not bool for value in payload.values())
    ):
        raise ValidationError(
            {"detail": "Supply supported boolean platform preferences."}
        )
    PlatformPreferences.objects.get_or_create(pk=1)
    current = PlatformPreferences.objects.select_for_update().get(pk=1)
    before = dict(current.values)
    current.values = {**before, **payload}
    if current.values != before:
        current.revision += 1
        current.full_clean()
        current.save(update_fields=["values", "revision", "updated_at"])
        PlatformPreferenceAudit.objects.create(
            actor=actor, revision=current.revision, before=before, after=current.values
        )
    return dict(current.values)
