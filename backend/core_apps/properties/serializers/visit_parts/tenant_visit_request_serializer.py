from core_apps.features.services.reputation.eligibility import can_review_visit

"""Visit: tenant visit request serializer."""

from datetime import datetime
from django.utils import timezone
from rest_framework import serializers
from ...phone_disclosure import counterpart_phone_payload
from ...models import PropertyVisit
from .property_visit_serializer import (
    _ARABIC_WEEKDAYS,
    _ENGLISH_WEEKDAYS,
    _ARABIC_MONTHS,
    _ENGLISH_MONTHS,
    _ARABIC_REQUEST_STATUS,
    _ENGLISH_REQUEST_STATUS,
    get_visit_language,
    PostVisitContextMixin,
)
from .tenant_visit_list_serializer import TenantVisitListSerializer
from .visit_owner_serializer import (
    VisitPropertySummarySerializer,
    VisitOwnerSerializer,
    PropertyVisitReviewSerializer,
)


class TenantVisitRequestSerializer(PostVisitContextMixin, serializers.ModelSerializer):
    """Payload used by the tenant visit-request cards shown in the mobile app."""

    property = VisitPropertySummarySerializer(read_only=True)
    owner = serializers.SerializerMethodField()
    day_label = serializers.SerializerMethodField()
    time_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    alternative_search_filters = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "property",
            "owner",
            "day_label",
            "time_label",
            "status_label",
            "actions",
            "alternative_search_filters",
        ]
        read_only_fields = fields

    def get_owner(self, obj):
        contact = counterpart_phone_payload(
            viewer=getattr(self.context.get("request"), "user", None),
            counterpart=obj.property.owner,
            request=self.context.get("request"),
            visit=obj,
        )
        return {
            "id": str(obj.property.owner.id),
            "name": obj.property.owner.get_full_name,
            **contact,
        }

    def _lang(self) -> str:
        return get_visit_language(self.context)

    def get_day_label(self, obj):
        return TenantVisitListSerializer(context=self.context).get_day(obj)

    def get_time_label(self, obj):
        return TenantVisitListSerializer(context=self.context).get_time(obj)

    def get_status_label(self, obj):
        lang = self._lang()
        table = _ENGLISH_REQUEST_STATUS if lang == "en" else _ARABIC_REQUEST_STATUS
        return table.get(obj.status, obj.status)

    def get_actions(self, obj):
        scheduled_at = datetime.combine(
            obj.visit_date, obj.visit_time, timezone.get_current_timezone()
        )
        from ...services.viewing_access import participant

        current_attendee = participant(obj, self.context["request"].user)
        was_reviewed = hasattr(obj, "review")
        return {
            "can_cancel": obj.status
            in (PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED)
            and current_attendee
            and obj.tenant_id == self.context["request"].user.pk
            and not obj.participant_decisions.exists(),
            "can_chat": obj.status == PropertyVisit.Status.CONFIRMED,
            "can_review": can_review_visit(obj),
            "can_find_alternative": obj.status == PropertyVisit.Status.REJECTED,
        }

    def get_alternative_search_filters(self, obj):
        if obj.status != PropertyVisit.Status.REJECTED:
            return None
        return {
            "property_type": obj.property.property_type.slug,
            "governorate": str(obj.property.governorate_id),
            "city": str(obj.property.city_id),
        }


class TenantVisitRequestDetailSerializer(TenantVisitRequestSerializer):
    owner = serializers.SerializerMethodField()
    note = serializers.CharField(read_only=True)
    review = PropertyVisitReviewSerializer(read_only=True)

    class Meta(TenantVisitRequestSerializer.Meta):
        fields = TenantVisitRequestSerializer.Meta.fields + [
            "visit_date",
            "visit_time",
            "status",
            "note",
            "review",
        ]

    def get_owner(self, obj):
        return VisitOwnerSerializer(
            obj.property.owner,
            context={"visit": obj, "request": self.context.get("request")},
        ).data


def _format_time_compact(time_val, lang="ar"):
    hour = time_val.hour
    minute = time_val.minute
    if lang == "en":
        period = "AM" if hour < 12 else "PM"
    else:
        period = "ص" if hour < 12 else "م"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    if minute == 0:
        return f"{hour_12}{period}"
    return f"{hour_12}:{minute:02d}{period}"


def _format_time_clock(time_val, lang="ar"):
    hour = time_val.hour
    minute = time_val.minute
    if lang == "en":
        period = "AM" if hour < 12 else "PM"
    else:
        period = "ص" if hour < 12 else "م"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    return f"{hour_12}:{minute:02d} {period}"


def _format_owner_schedule_label(visit_date, visit_time, lang="ar"):
    today = timezone.localdate()
    time_str = _format_time_compact(visit_time, lang=lang)
    if visit_date == today:
        return f"Today {time_str}" if lang == "en" else f"النهارده {time_str}"
    if visit_date == today + timezone.timedelta(days=1):
        return f"Tomorrow {time_str}" if lang == "en" else f"غداً {time_str}"
    if lang == "en":
        weekday = _ENGLISH_WEEKDAYS[visit_date.weekday()]
    else:
        weekday = _ARABIC_WEEKDAYS[visit_date.weekday()]
    return f"{weekday} {time_str}"


def _format_full_date(visit_date, lang="ar"):
    if lang == "en":
        weekday = _ENGLISH_WEEKDAYS[visit_date.weekday()]
        month = _ENGLISH_MONTHS[visit_date.month]
    else:
        weekday = _ARABIC_WEEKDAYS[visit_date.weekday()]
        month = _ARABIC_MONTHS[visit_date.month]
    return f"{weekday} {visit_date.day} {month} {visit_date.year}"


_format_time_ar_compact = lambda t: _format_time_compact(t, lang="ar")


_format_time_ar_clock = lambda t: _format_time_clock(t, lang="ar")


_format_full_date_ar = lambda d: _format_full_date(d, lang="ar")
