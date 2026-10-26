"""Serializers: profile edit serializer."""

from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from ..models import Profile
from ..services.profile_service import format_arabic_date, mask_phone_number
from .update_profile_serializer import (
    CloudinarySerializerField,
    ProfileCitySerializer,
    AccountSummaryUserSerializer,
    IdentityVerificationSerializer,
    AccountSummaryStatsSerializer,
)


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
    birth_date = serializers.DateField(read_only=True)
    birth_date_label = serializers.SerializerMethodField(read_only=True)
    gender = serializers.ChoiceField(choices=Profile.Gender.choices, read_only=True)
    gender_label = serializers.SerializerMethodField(read_only=True)
    city = ProfileCitySerializer(read_only=True)
    city_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
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
            "city",
            "city_id",
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

        if "city_id" in attrs:
            city_id = attrs.pop("city_id")
            if city_id:
                from core_apps.properties.models import City

                try:
                    attrs["city"] = City.objects.get(id=city_id)
                    from core_apps.properties.catalog_access import require_current_selection

                    require_current_selection(attrs["city"], previous=getattr(self.instance, "city", None), field="city_id")
                except City.DoesNotExist:
                    raise serializers.ValidationError({"city_id": "Invalid city ID."})
            else:
                attrs["city"] = None
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
