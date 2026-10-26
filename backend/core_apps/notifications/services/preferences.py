"""Workspace Push is separate from durable in-app receipts and account events."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.profiles.models import UserSettings
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import NotificationScopePreference

CATEGORY_FIELDS = (
    "visit_notifications",
    "new_properties_in_area",
    "owner_messages",
    "property_updates",
    "security_alerts",
    "promotions_and_updates",
)
LABELS = {
    "push_enabled": ("تنبيهات Push لهذه المساحة", "Push for this workspace"),
    "visit_notifications": ("طلبات الزيارات", "Viewing updates"),
    "new_properties_in_area": ("عقارات جديدة", "New properties"),
    "owner_messages": ("الرسائل الجديدة", "New messages"),
    "property_updates": ("تحديثات العقارات", "Property updates"),
    "security_alerts": ("تنبيهات الحساب الأمنية", "Account security alerts"),
    "promotions_and_updates": ("العروض والتحديثات", "Promotions and updates"),
}


def fields(scope):
    return (
        ("push_enabled", "security_alerts")
        if scope == "account"
        else (
            "push_enabled",
            "visit_notifications",
            "new_properties_in_area",
            "owner_messages",
            "property_updates",
            "promotions_and_updates",
        )
    )


def get(user, scope):
    existing = NotificationScopePreference.objects.filter(
        user=user, scope=scope
    ).first()
    if existing:
        return existing
    original = UserSettings.objects.filter(user=user).first()
    # Preserve existing opt-outs when introducing workspace preferences.
    defaults = (
        {key: getattr(original, key) for key in CATEGORY_FIELDS} if original else {}
    )
    return NotificationScopePreference.objects.get_or_create(
        user=user, scope=scope, defaults=defaults
    )[0]


def touch(user, scope):
    item = get(user, scope)
    NotificationScopePreference.objects.filter(pk=item.pk).update(
        last_used_at=timezone.now()
    )


def projection(item, language="ar"):
    selected = fields(item.scope)
    values = {key: getattr(item, key) for key in selected}
    english = language.startswith("en")
    items = []
    for key in selected:
        title = LABELS[key][int(english)]
        if key == "push_enabled" and item.scope == "account":
            title = "Account Push" if english else "تنبيهات Push الخاصة بالحساب"
        items.append(
            {"key": key, "title": title, "value": values[key], "enabled": True}
        )
    return {
        "id": str(item.id),
        "scope": item.scope,
        "revision": item.revision,
        **values,
        "sections": {
            "notifications": {
                "items": items,
                "footer_note": (
                    "In-app history remains available when Push is off."
                    if english
                    else "يبقى سجل الإشعارات داخل التطبيق متاحًا عند إيقاف Push."
                ),
            }
        },
    }


@transaction.atomic
def update(request, scope):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(user, request.auth or {})
    data = request.data
    if not isinstance(data, dict) or not data or set(data) - set(fields(scope)):
        raise ValidationError("Supply supported preferences for this scope.")
    if any(type(value) is not bool for value in data.values()):
        raise ValidationError("Preference values must be booleans.")
    item = get(user, scope)
    for key, value in data.items():
        setattr(item, key, value)
    item.revision += 1
    item.save(update_fields=[*data, "revision", "updated_at"])
    return item
