"""Serializers: create user serializer."""

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer, UserSerializer
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from core_apps.profiles.serializers import CloudinarySerializerField
from ..journey import PrivateJourneySerializerMixin


User = get_user_model()


class CreateUserSerializer(UserCreatePasswordRetypeSerializer):
    birth_date = serializers.DateField(write_only=True, required=False)
    phone_number = PhoneNumberField(write_only=True, required=False, allow_blank=True)

    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "birth_date",
            "phone_number",
        ]

    def validate_first_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name cannot be blank.")
        if len(value) > 50:
            raise serializers.ValidationError("First name cannot exceed 50 characters.")
        return value

    def validate_last_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Last name cannot be blank.")
        if len(value) > 50:
            raise serializers.ValidationError("Last name cannot exceed 50 characters.")
        return value

    def validate_password(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Password cannot be blank or whitespace only."
            )
        return (
            super().validate(value) if hasattr(super(), "validate_password") else value
        )

    def validate(self, attrs):
        birth_date = attrs.pop("birth_date", None)
        phone_number = attrs.pop("phone_number", None)
        attrs = super().validate(attrs)
        if birth_date is not None:
            attrs["birth_date"] = birth_date
        if phone_number is not None:
            attrs["phone_number"] = phone_number
        return attrs

    def create(self, validated_data):
        birth_date = validated_data.pop("birth_date", None)
        phone_number = validated_data.pop("phone_number", None)
        user = super().create(validated_data)
        update_fields = []
        if birth_date:
            user.profile.birth_date = birth_date
            update_fields.append("birth_date")
        if phone_number:
            user.profile.phone_number = phone_number
            update_fields.append("phone_number")
        if update_fields:
            user.profile.save(update_fields=update_fields)
        return user


class CustomUserSerializer(PrivateJourneySerializerMixin, UserSerializer):
    full_name = serializers.ReadOnlyField(source="get_full_name")
    gender = serializers.ReadOnlyField(source="profile.gender")
    birth_date = serializers.ReadOnlyField(source="profile.birth_date")
    type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "birth_date",
            "is_verified",
            "type",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined", "is_verified", "type"]

    def get_type(self, obj):
        return "user"


class CompleteRegisterSerializer(serializers.Serializer):
    """
    Serializer for uploading missing KYC documents and national ID.
    """

    national_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=14,
        min_length=14,
        error_messages={
            "max_length": "National ID must be exactly 14 digits.",
            "min_length": "National ID must be exactly 14 digits.",
        },
    )
    front_id_image = CloudinarySerializerField(required=False, allow_null=True)
    back_id_image = CloudinarySerializerField(required=False, allow_null=True)
    selfie_image = CloudinarySerializerField(required=False, allow_null=True)

    def validate_national_id(self, value: str) -> str:
        value = value.strip()
        if value and not value.isdigit():
            raise serializers.ValidationError("National ID must contain digits only.")
        return value


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField(
        error_messages={
            "required": "Google ID token is required.",
            "blank": "Google ID token cannot be blank.",
        }
    )


class AppleAuthSerializer(serializers.Serializer):
    token = serializers.CharField(
        error_messages={
            "required": "Apple identity token is required.",
            "blank": "Apple identity token cannot be blank.",
        }
    )
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")


class FacebookAuthSerializer(serializers.Serializer):
    token = serializers.CharField(
        error_messages={
            "required": "Facebook access token is required.",
            "blank": "Facebook access token cannot be blank.",
        }
    )
