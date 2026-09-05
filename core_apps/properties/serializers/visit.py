from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField
from core_apps.properties.serializers.property import PropertyListSerializer
from ..models import Property, PropertyVisit, PropertyVisitReview
from ..services import PropertyVisitService


# ? Arabic date/time labels for the tenant visit card UI
_ARABIC_WEEKDAYS = {
    0: "الإثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

_ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}

_ARABIC_VISIT_STATUS = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مؤكد",
    PropertyVisit.Status.CANCELED: "ملغي",
    PropertyVisit.Status.REJECTED: "مرفوض",
}

_ARABIC_REQUEST_STATUS = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مقبول",
    PropertyVisit.Status.CANCELED: "ملغي",
    PropertyVisit.Status.REJECTED: "مرفوض",
}

User = get_user_model()


class PropertyVisitSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_email = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "property",
            "tenant_name",
            "tenant_email",
            "visit_date",
            "visit_time",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_tenant_email(self, obj):
        request = self.context.get("request")
        if request and request.user:
            # Tenant can always see their own email
            if request.user == obj.tenant:
                return obj.tenant.email
            # Owner can only see the tenant's email if the visit is confirmed
            if (
                request.user == obj.property.owner
                and obj.status == PropertyVisit.Status.CONFIRMED
            ):
                return obj.tenant.email
        return ""


class TenantVisitListSerializer(serializers.ModelSerializer):
    """
    Card-style serializer for a tenant's own visit requests.

    Returns a compact Arabic-formatted payload matching the visit card UI:
    property title + district, visit day, time and status label.
    """

    title = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = ["id", "title", "day", "time", "status"]
        read_only_fields = fields

    def get_title(self, obj: PropertyVisit) -> str:
        return f"{obj.property.title} - {obj.property.district}"

    def get_day(self, obj: PropertyVisit) -> str:
        weekday = _ARABIC_WEEKDAYS[obj.visit_date.weekday()]
        month = _ARABIC_MONTHS[obj.visit_date.month]
        return f"{weekday} {obj.visit_date.day} {month}"

    def get_time(self, obj: PropertyVisit) -> str:
        hour = obj.visit_time.hour
        minute = obj.visit_time.minute
        period = "ص" if hour < 12 else "م"
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"

    def get_status(self, obj: PropertyVisit) -> str:
        return _ARABIC_VISIT_STATUS.get(obj.status, obj.status)


class VisitTenantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    # ? DRF returns None here if the tenant has no profile/avatar
    avatar = CloudinarySerializerField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ["name", "avatar", "is_verified"]
        read_only_fields = fields


class PropertyVisitDetailSerializer(serializers.ModelSerializer):
    tenant = VisitTenantSerializer(read_only=True)

    class Meta:
        model = PropertyVisit
        fields = ["id", "tenant", "visit_date", "status"]
        read_only_fields = fields


class PropertyVisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["id", "visit_date", "visit_time", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_visit_date(self, value):
        from django.utils import timezone

        if value < timezone.localdate():
            raise serializers.ValidationError(_("Visit date cannot be in the past."))
        return value

    def create(self, validated_data):
        tenant = validated_data.pop("tenant")
        property_obj = validated_data.pop("property_obj")
        return PropertyVisitService.create_visit(
            tenant=tenant, property_obj=property_obj, validated_data=validated_data
        )


class PropertyVisitUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["status"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        status = validated_data.get("status")
        return PropertyVisitService.update_visit_status(
            user=user, visit_obj=instance, status=status
        )


class AvailableDatesQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


class OwnerAvailabilityWeekQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)


class OwnerAvailabilitySlotInputSerializer(serializers.Serializer):
    time = serializers.TimeField()
    is_enabled = serializers.BooleanField(default=True)


class OwnerAvailabilityDayUpdateSerializer(serializers.Serializer):
    availability_date = serializers.DateField()
    slots = OwnerAvailabilitySlotInputSerializer(many=True)

    def validate(self, attrs):
        availability_date = attrs["availability_date"]
        now = timezone.localtime()
        slot_times = set()

        for slot in attrs["slots"]:
            slot_time = slot["time"]
            if slot_time in slot_times:
                raise serializers.ValidationError(
                    _("Each time can be submitted only once.")
                )
            if datetime.combine(availability_date, slot_time, now.tzinfo) <= now:
                raise serializers.ValidationError(
                    _("Availability slots must be in the future.")
                )
            slot_times.add(slot_time)
        return attrs


class OwnerVisitCalendarQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    day = serializers.CharField(required=False, allow_blank=True)
    date = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        year = attrs["year"]
        month = attrs["month"]
        day_raw = attrs.get("day")
        date_raw = attrs.get("date")

        selected_date = None

        # Parse date parameter if provided and not empty
        if date_raw is not None and str(date_raw).strip() != "":
            date_str = str(date_raw).strip()
            if date_str.isdigit():
                day_from_date = int(date_str)
                try:
                    selected_date = date(year, month, day_from_date)
                except ValueError:
                    raise serializers.ValidationError(
                        {"date": _("Invalid day for the specified month and year.")}
                    )
            else:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    raise serializers.ValidationError(
                        {"date": _("Date must be a day number (1-31) or in YYYY-MM-DD format.")}
                    )
                if parsed_date.year != year or parsed_date.month != month:
                    raise serializers.ValidationError(
                        {"date": _("The selected date must belong to the requested month.")}
                    )
                selected_date = parsed_date

        # Parse day parameter if provided and not empty
        if day_raw is not None and str(day_raw).strip() != "":
            day_str = str(day_raw).strip()
            if not day_str.isdigit():
                raise serializers.ValidationError(
                    {"day": _("Day must be an integer between 1 and 31.")}
                )
            day_num = int(day_str)
            try:
                date_from_day = date(year, month, day_num)
            except ValueError:
                raise serializers.ValidationError(
                    {"day": _("Invalid day for the specified month and year.")}
                )
            if selected_date is not None and selected_date != date_from_day:
                raise serializers.ValidationError(
                    _("Conflicting 'date' and 'day' parameters provided.")
                )
            selected_date = date_from_day

        attrs["date"] = selected_date
        return attrs


class VisitPropertySummarySerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "location",
            "price",
        ]
        read_only_fields = fields

    def get_location(self, obj):
        return f"{obj.district}, {obj.city.name}"


class VisitOwnerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    phone_number = serializers.SerializerMethodField()
    masked_phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "is_verified", "phone_number", "masked_phone_number"]
        read_only_fields = fields

    def _phone_number(self, obj):
        profile = getattr(obj, "profile", None)
        return str(profile.phone_number) if profile and profile.phone_number else ""

    def get_phone_number(self, obj):
        visit = self.context.get("visit")
        if visit and visit.status == PropertyVisit.Status.CONFIRMED:
            return self._phone_number(obj)
        return ""

    def get_masked_phone_number(self, obj):
        number = self.get_phone_number(obj)
        if len(number) <= 6:
            return number
        return f"{number[:3]}{'*' * (len(number) - 6)}{number[-3:]}"


class PropertyVisitReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisitReview
        fields = [
            "id",
            "overall_rating",
            "cleanliness_rating",
            "listing_accuracy_rating",
            "owner_interaction_rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TenantVisitRequestSerializer(serializers.ModelSerializer):
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
        return {
            "id": str(obj.property.owner.id),
            "name": obj.property.owner.get_full_name,
        }

    def get_day_label(self, obj):
        return TenantVisitListSerializer().get_day(obj)

    def get_time_label(self, obj):
        return TenantVisitListSerializer().get_time(obj)

    def get_status_label(self, obj):
        return _ARABIC_REQUEST_STATUS.get(obj.status, obj.status)

    def get_actions(self, obj):
        scheduled_at = datetime.combine(
            obj.visit_date, obj.visit_time, timezone.get_current_timezone()
        )
        was_reviewed = hasattr(obj, "review")
        return {
            "can_cancel": obj.status
            in (PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED),
            "can_chat": obj.status == PropertyVisit.Status.CONFIRMED,
            "can_review": (
                obj.status == PropertyVisit.Status.CONFIRMED
                and scheduled_at <= timezone.localtime()
                and not was_reviewed
            ),
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
            context={"visit": obj},
        ).data


# ? Helper functions for formatting dates and times for the owner screens

def _format_time_ar_compact(time_val):
    hour = time_val.hour
    minute = time_val.minute
    period = "ص" if hour < 12 else "م"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    if minute == 0:
        return f"{hour_12}{period}"
    return f"{hour_12}:{minute:02d}{period}"


def _format_time_ar_clock(time_val):
    hour = time_val.hour
    minute = time_val.minute
    period = "ص" if hour < 12 else "م"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    return f"{hour_12}:{minute:02d} {period}"


def _format_owner_schedule_label(visit_date, visit_time):
    today = timezone.localdate()
    time_str = _format_time_ar_compact(visit_time)
    if visit_date == today:
        return f"النهارده {time_str}"
    if visit_date == today + timezone.timedelta(days=1):
        return f"غداً {time_str}"
    weekday = _ARABIC_WEEKDAYS[visit_date.weekday()]
    return f"{weekday} {time_str}"


def _format_full_date_ar(visit_date):
    weekday = _ARABIC_WEEKDAYS[visit_date.weekday()]
    month = _ARABIC_MONTHS[visit_date.month]
    return f"{weekday} {visit_date.day} {month} {visit_date.year}"


def _mask_phone_number(raw_number):
    if not raw_number:
        return ""
    digits = str(raw_number).strip()
    clean = digits.replace("+2", "").strip() if digits.startswith("+2") else digits
    if len(clean) >= 7:
        return f"{clean[:3]}****{clean[-3:]}"
    return clean


_OWNER_CARD_STATUS_LABEL = {
    PropertyVisit.Status.PENDING: "جديد",
    PropertyVisit.Status.CONFIRMED: "مقبول",
    PropertyVisit.Status.REJECTED: "مرفوض",
    PropertyVisit.Status.CANCELED: "ملغي",
}

_OWNER_DETAIL_STATUS_LABEL = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مقبول",
    PropertyVisit.Status.REJECTED: "مرفوض",
    PropertyVisit.Status.CANCELED: "ملغي",
}


class OwnerVisitTenantCardSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    avatar = CloudinarySerializerField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "avatar", "is_verified"]
        read_only_fields = fields


class OwnerVisitRequestCardSerializer(serializers.ModelSerializer):
    """
    Card serializer for the Owner Visit Requests list screen (Screen 1).
    """

    tenant = OwnerVisitTenantCardSerializer(read_only=True)
    property = serializers.SerializerMethodField()
    schedule_label = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    is_verified_tenant = serializers.BooleanField(
        source="tenant.is_verified", read_only=True
    )
    verification_warning = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "tenant",
            "property",
            "schedule_label",
            "subtitle",
            "status",
            "status_label",
            "actions",
            "is_verified_tenant",
            "verification_warning",
            "created_at",
        ]
        read_only_fields = fields

    def get_property(self, obj: PropertyVisit):
        return {
            "id": str(obj.property.id),
            "title": obj.property.title,
            "district": obj.property.district,
        }

    def get_schedule_label(self, obj: PropertyVisit) -> str:
        return _format_owner_schedule_label(obj.visit_date, obj.visit_time)

    def get_subtitle(self, obj: PropertyVisit) -> str:
        schedule = _format_owner_schedule_label(obj.visit_date, obj.visit_time)
        return f"{obj.property.title} · {schedule}"

    def get_status_label(self, obj: PropertyVisit) -> str:
        if obj.status == PropertyVisit.Status.PENDING:
            return "جديد" if obj.tenant.is_verified else "انتظار"
        return _OWNER_CARD_STATUS_LABEL.get(obj.status, obj.status)

    def get_actions(self, obj: PropertyVisit):
        is_pending = obj.status == PropertyVisit.Status.PENDING
        is_confirmed = obj.status == PropertyVisit.Status.CONFIRMED
        return {
            "can_accept": is_pending,
            "can_reject": is_pending,
            "can_chat": is_pending or is_confirmed,
        }

    def get_verification_warning(self, obj: PropertyVisit) -> str:
        if not obj.tenant.is_verified:
            return "هذا المستأجر لم يوثق هويته بعد"
        return ""


class OwnerVisitRequestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the Owner Visit Request Details screen (Screen 2).
    """

    tenant = serializers.SerializerMethodField()
    property = serializers.SerializerMethodField()
    day_label = serializers.SerializerMethodField()
    time_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "tenant",
            "property",
            "visit_date",
            "visit_time",
            "day_label",
            "time_label",
            "note",
            "status",
            "status_label",
            "actions",
            "created_at",
        ]
        read_only_fields = fields

    def get_tenant(self, obj: PropertyVisit):
        tenant = obj.tenant
        profile = getattr(tenant, "profile", None)
        avatar_url = (
            profile.avatar.url
            if profile and getattr(profile, "avatar", None)
            else None
        )
        raw_phone = (
            str(profile.phone_number)
            if profile and getattr(profile, "phone_number", None)
            else ""
        )
        masked_phone = _mask_phone_number(raw_phone)
        is_confirmed = obj.status == PropertyVisit.Status.CONFIRMED
        member_year = tenant.date_joined.year if tenant.date_joined else 2024

        verification_prefix = "مستأجر موثّق · " if tenant.is_verified else ""
        membership_label = f"{verification_prefix}عضو منذ {member_year}"

        phone_notice = (
            ""
            if is_confirmed
            else f"رقم المستأجر {masked_phone} – يظهر بعد القبول فقط"
            if masked_phone
            else "رقم المستأجر – يظهر بعد القبول فقط"
        )

        return {
            "id": str(tenant.id),
            "name": tenant.get_full_name,
            "avatar": avatar_url,
            "is_verified": tenant.is_verified,
            "member_since_year": member_year,
            "membership_label": membership_label,
            "phone_number": raw_phone if is_confirmed else "",
            "masked_phone_number": masked_phone,
            "is_phone_revealed": is_confirmed,
            "phone_notice": phone_notice,
        }

    def get_property(self, obj: PropertyVisit):
        return {
            "id": str(obj.property.id),
            "title": obj.property.title,
            "district": obj.property.district,
            "display_name": f"{obj.property.title} – {obj.property.district}",
        }

    def get_day_label(self, obj: PropertyVisit) -> str:
        return _format_full_date_ar(obj.visit_date)

    def get_time_label(self, obj: PropertyVisit) -> str:
        return _format_time_ar_clock(obj.visit_time)

    def get_status_label(self, obj: PropertyVisit) -> str:
        return _OWNER_DETAIL_STATUS_LABEL.get(obj.status, obj.status)

    def get_actions(self, obj: PropertyVisit):
        is_pending = obj.status == PropertyVisit.Status.PENDING
        is_confirmed = obj.status == PropertyVisit.Status.CONFIRMED
        return {
            "can_accept": is_pending,
            "can_reject": is_pending,
            "can_chat": is_confirmed,
        }


class OwnerVisitRejectSerializer(serializers.Serializer):
    """
    Serializer for rejecting a visit request (Screen 3 modal).
    """

    REJECTION_REASONS = [
        ("timing_not_suitable", _("الموعد غير مناسب")),
        ("property_currently_rented", _("العقار مؤجر حالياً")),
        ("tenant_not_eligible", _("المستأجر لا يستوفي الشروط")),
        ("other", _("سبب آخر")),
    ]

    reason = serializers.ChoiceField(
        choices=REJECTION_REASONS, default="timing_not_suitable"
    )
    custom_reason = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

