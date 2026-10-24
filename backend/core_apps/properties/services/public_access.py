"""One publication predicate for every public property projection."""


def public_properties(queryset=None):
    from core_apps.properties.models import Property
    from core_apps.chat.moderation.policy import visible_properties

    if queryset is None:
        queryset = Property.objects.all()
    return visible_properties(
        queryset.filter(
            status=Property.Status.VERIFIED,
            retired_at__isnull=True,
        )
    )
