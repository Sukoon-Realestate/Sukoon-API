"""Serializers: update profile serializer."""

import base64
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from ..models import Profile
from core_apps.users.journey import PrivateJourneySerializerMixin


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


class ProfileCitySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    revision = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):
        from core_apps.properties.catalog_labels import location_label, catalog_language

        data = super().to_representation(instance)
        data["name"] = location_label(instance, catalog_language(self.context))
        return data


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    full_name = serializers.ReadOnlyField(source="user.get_full_name")
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)
    phone_number = PhoneNumberField(read_only=True)
    city = ProfileCitySerializer(read_only=True)
    avatar = CloudinarySerializerField(read_only=True)
    id_face = serializers.SerializerMethodField()
    id_back = serializers.SerializerMethodField()
    confirmation_selfi = serializers.SerializerMethodField()

    def _identity_url(self, obj, field):
        from django.urls import reverse
        from ..identity_media import reference, version

        asset = getattr(obj, field)
        if not reference(asset).startswith("image/authenticated/"):
            return None
        url = (
            reverse("identity-media", kwargs={"field": field})
            + "?version="
            + version(asset)
        )
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_id_face(self, obj):
        return self._identity_url(obj, "id_face")

    def get_id_back(self, obj):
        return self._identity_url(obj, "id_back")

    def get_confirmation_selfi(self, obj):
        return self._identity_url(obj, "confirmation_selfi")

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
            "city",
            "avatar",
            "id_face",
            "id_back",
            "confirmation_selfi",
            "national_id",
            "date_joined",
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(read_only=True)
    birth_date = serializers.DateField(read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    city = ProfileCitySerializer(read_only=True)
    city_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    avatar = CloudinarySerializerField(required=False, allow_null=True)
    id_face = CloudinarySerializerField(required=False, allow_null=True)
    id_back = CloudinarySerializerField(required=False, allow_null=True)
    confirmation_selfi = CloudinarySerializerField(required=False, allow_null=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in ("id_face", "id_back", "confirmation_selfi"):
            data[field] = ProfileSerializer._identity_url(self, instance, field)
        return data

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "gender",
            "birth_date",
            "phone_number",
            "city",
            "city_id",
            "avatar",
            "id_face",
            "id_back",
            "confirmation_selfi",
            "national_id",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
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


class MyAccountUserSerializer(PrivateJourneySerializerMixin, serializers.Serializer):
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


class AccountSummaryUserSerializer(
    PrivateJourneySerializerMixin, serializers.Serializer
):
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
