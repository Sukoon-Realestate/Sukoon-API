"""Request-local list projections; never reused for inventory authorization."""

from rest_framework import serializers


class PropertyCollectionSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        from core_apps.features.services.reputation.visibility import (
            sections,
            visible,
            summarize_rows,
        )
        from core_apps.features.models import HabitabilityRestriction

        rows = list(data.all() if hasattr(data, "all") else data)
        if not rows:
            return []
        from core_apps.chat.models import AccountRestriction
        from core_apps.chat.moderation.policy import ACTIVE_RESTRICTIONS
        blocked = set(AccountRestriction.objects.filter(user_id__in={r.owner_id for r in rows}, state__in=ACTIVE_RESTRICTIONS).values_list('user_id', flat=True))
        for row in rows:
            row._policy_owner_restricted = row.owner_id in blocked
        grouped = {str(row.id): [] for row in rows}
        for section in (
            sections()
            .filter(
                subject_kind="property_stay",
                subject_id__in=grouped,
                content_state="approved",
            )
            .exclude(verification_basis="legacy_unverified")
        ):
            if visible(section, public_only=True):
                grouped[str(section.subject_id)].append(section)
        restrictions = {row.pk: set() for row in rows if row.rental_inventory}
        if restrictions:
            for prop_id, key in HabitabilityRestriction.objects.filter(
                unit__property_id__in=restrictions, cleared_at__isnull=True
            ).values_list("unit__property_id", "unit__physical_key"):
                restrictions[prop_id].add(key)
        for row in rows:
            row._listing_stay_rating = summarize_rows(
                "property_stay", grouped[str(row.id)]
            )["average"]
            row._listing_restricted_keys = restrictions.get(row.pk, set())
        return super().to_representation(rows)


def stay_rating(obj):
    if hasattr(obj, "_listing_stay_rating"):
        return obj._listing_stay_rating
    from core_apps.features.services.reputation.visibility import summary

    return summary("property_stay", obj.id)["average"]
