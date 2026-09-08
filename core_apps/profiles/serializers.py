import base64
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import Profile, UserSettings
from .services.profile_service import (
    ARABIC_MONTHS,
    format_arabic_date,
    mask_phone_number,
)


class CloudinarySerializerField(serializers.ImageField):
    def to_internal_value(self, data):
        # ? Handle base64 encoded data URI strings
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                header, base64_data = data.split(";base64,")
                ext = header.split("/")[-1].split("+")[0]
                content_type = header.split(";")[0].replace("data:", "")
                file_name = f"{uuid.uuid4().hex[:10]}.{ext}"
                data = SimpleUploadedFile(
                    name=file_name,
                    content=base64.b64decode(base64_data),
                    content_type=content_type,
                )
            except Exception:
                raise serializers.ValidationError("Invalid base64 image data.")
        elif isinstance(data, str):
            # ? Allow direct URLs / Cloudinary public IDs without re-uploading
            return data

        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        if hasattr(value, "url"):
            return value.url
        return str(value)


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    full_name = serializers.ReadOnlyField(source="user.get_full_name")
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)
    phone_number = PhoneNumberField(read_only=True)
    avatar = CloudinarySerializerField(read_only=True)
    id_face = CloudinarySerializerField(read_only=True)
    id_back = CloudinarySerializerField(read_only=True)
    confirmation_selfi = CloudinarySerializerField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "birth_date",
            "phone_number",
            "avatar",
            "id_face",
            "id_back",
            "confirmation_selfi",
            "national_id",
            "date_joined",
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    avatar = CloudinarySerializerField(required=False, allow_null=True)
    id_face = CloudinarySerializerField(required=False, allow_null=True)
    id_back = CloudinarySerializerField(required=False, allow_null=True)
    confirmation_selfi = CloudinarySerializerField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "gender",
            "birth_date",
            "phone_number",
            "avatar",
            "id_face",
            "id_back",
            "confirmation_selfi",
            "national_id",
        ]


# * =========================================================================
# * Mobile Screens Serializers (Screens 1, 2, and 3)
# * =========================================================================


class MyAccountUserSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True, allow_blank=True)
    last_name = serializers.CharField(read_only=True, allow_blank=True)
    avatar = serializers.CharField(read_only=True, allow_null=True)
    is_verified = serializers.BooleanField(read_only=True)
    verification_badge = serializers.CharField(read_only=True)
    role_label = serializers.CharField(read_only=True)
    member_since_label = serializers.CharField(read_only=True)
    member_since_year = serializers.IntegerField(read_only=True)
    member_since_month = serializers.CharField(read_only=True)


class MyAccountStatsSerializer(serializers.Serializer):
    saved_count = serializers.IntegerField(read_only=True)
    visits_count = serializers.IntegerField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)


class MyAccountDetailsSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class MyAccountScreenSerializer(serializers.Serializer):
    """Serializer for Screen 1: 'حسابي' (My Account)."""

    user = MyAccountUserSerializer(read_only=True)
    stats = MyAccountStatsSerializer(read_only=True)
    menu_items = serializers.DictField(read_only=True)
    account_details = MyAccountDetailsSerializer(read_only=True)


class AccountSummaryUserSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    avatar = serializers.CharField(read_only=True, allow_null=True)
    initial = serializers.CharField(read_only=True)
    role_label = serializers.CharField(read_only=True)
    member_since_label = serializers.CharField(read_only=True)
    profile_completion_percentage = serializers.IntegerField(read_only=True)
    profile_completion_label = serializers.CharField(read_only=True)


class IdentityVerificationSerializer(serializers.Serializer):
    is_verified = serializers.BooleanField(read_only=True)
    title = serializers.CharField(read_only=True)
    subtitle = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)


class AccountSummaryStatsSerializer(serializers.Serializer):
    saved_properties_count = serializers.IntegerField(read_only=True)
    completed_visits_count = serializers.IntegerField(read_only=True)
    active_chats_count = serializers.IntegerField(read_only=True)


class AccountSummaryScreenSerializer(serializers.Serializer):
    """Serializer for Screen 2: 'ملخص الحساب' (Account Summary)."""

    user = AccountSummaryUserSerializer(read_only=True)
    identity_verification = IdentityVerificationSerializer(read_only=True)
    stats = AccountSummaryStatsSerializer(read_only=True)
    shortcuts = serializers.DictField(read_only=True)


class ProfileEditSerializer(serializers.ModelSerializer):
    """
    Serializer for Screen 3: 'تعديل الملف' (Edit Profile).
    Supports GET (prefilled fields with labels & masking) and PUT/PATCH (saving changes).
    """

    full_name = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    email = serializers.EmailField(
        source="user.email", required=False, allow_blank=True
    )
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    masked_phone_number = serializers.SerializerMethodField(read_only=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    birth_date_label = serializers.SerializerMethodField(read_only=True)
    gender = serializers.ChoiceField(choices=Profile.Gender.choices, required=False)
    gender_label = serializers.SerializerMethodField(read_only=True)
    avatar = CloudinarySerializerField(required=False, allow_null=True)
    profile_image = CloudinarySerializerField(
        required=False, allow_null=True, write_only=True
    )
    image = CloudinarySerializerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "masked_phone_number",
            "birth_date",
            "birth_date_label",
            "gender",
            "gender_label",
            "avatar",
            "profile_image",
            "image",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # * Support profile_image and image as aliases for avatar
        img = attrs.pop("profile_image", None) or attrs.pop("image", None)
        if img is not None and "avatar" not in attrs:
            attrs["avatar"] = img
        return attrs

    def get_masked_phone_number(self, obj: Profile) -> str:
        return mask_phone_number(obj.phone_number)

    def get_birth_date_label(self, obj: Profile) -> str:
        return format_arabic_date(obj.birth_date)

    def get_gender_label(self, obj: Profile) -> str:
        if obj.gender == Profile.Gender.MALE:
            return "ذكر"
        elif obj.gender == Profile.Gender.FEMALE:
            return "أنثى"
        return ""

    def to_representation(self, instance: Profile):
        data = super().to_representation(instance)
        data["full_name"] = (
            instance.user.get_full_name
            or instance.user.first_name
            or instance.user.email
        )
        data["profile_image"] = data.get("avatar")
        return data


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Screen: 'الإعدادات والخصوصية' (Settings and Privacy).
    Supports GET (view settings) and PUT/PATCH (save changes).
    """

    always_hide_mobile_number = serializers.BooleanField(
        read_only=True,
        default=True,
        help_text="Always hide mobile number for privacy protection (cannot be changed)",
    )
    always_hide_mobile_number_locked = serializers.SerializerMethodField(read_only=True)
    sections = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserSettings
        fields = [
            "id",
            # Notifications
            "visit_notifications",
            "new_properties_in_area",
            "owner_messages",
            "promotions_and_updates",
            # Privacy
            "always_hide_mobile_number",
            "always_hide_mobile_number_locked",
            "share_location_for_search",
            "show_profile_in_search",
            # Grouped representation
            "sections",
        ]
        read_only_fields = [
            "id",
            "always_hide_mobile_number",
            "always_hide_mobile_number_locked",
            "sections",
        ]

    def get_always_hide_mobile_number_locked(self, obj: UserSettings) -> bool:
        return True

    def get_sections(self, obj: UserSettings) -> dict:
        return {
            "notifications": {
                "title": "الإشعارات",
                "items": [
                    {
                        "key": "visit_notifications",
                        "title": "إشعارات الزيارات",
                        "value": obj.visit_notifications,
                        "enabled": True,
                    },
                    {
                        "key": "new_properties_in_area",
                        "title": "عقارات جديدة في منطقتي",
                        "value": obj.new_properties_in_area,
                        "enabled": True,
                    },
                    {
                        "key": "owner_messages",
                        "title": "رسائل المالك",
                        "value": obj.owner_messages,
                        "enabled": True,
                    },
                    {
                        "key": "promotions_and_updates",
                        "title": "التحديثات والعروض",
                        "value": obj.promotions_and_updates,
                        "enabled": True,
                    },
                ],
            },
            "privacy": {
                "title": "الخصوصية",
                "items": [
                    {
                        "key": "always_hide_mobile_number",
                        "title": "إخفاء رقم الموبايل دائماً",
                        "subtitle": "لا يمكن تغييره – لحماية خصوصيتك",
                        "value": obj.always_hide_mobile_number,
                        "enabled": False,
                        "locked": True,
                    },
                    {
                        "key": "share_location_for_search",
                        "title": "مشاركة موقعي للبحث",
                        "subtitle": "",
                        "value": obj.share_location_for_search,
                        "enabled": True,
                        "locked": False,
                    },
                    {
                        "key": "show_profile_in_search",
                        "title": "ظهور حسابي في البحث",
                        "subtitle": "",
                        "value": obj.show_profile_in_search,
                        "enabled": True,
                        "locked": False,
                    },
                ],
            },
        }

    def to_internal_value(self, data):
        # ? Support both flat and nested payloads ({ "notifications": {...}, "privacy": {...} })
        mutable_data = data.copy() if hasattr(data, "copy") else dict(data)
        if "notifications" in mutable_data and isinstance(
            mutable_data["notifications"], dict
        ):
            for k, v in mutable_data.pop("notifications").items():
                mutable_data.setdefault(k, v)
        if "privacy" in mutable_data and isinstance(mutable_data["privacy"], dict):
            for k, v in mutable_data.pop("privacy").items():
                mutable_data.setdefault(k, v)
        return super().to_internal_value(mutable_data)
