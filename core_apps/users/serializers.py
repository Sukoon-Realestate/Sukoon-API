from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer, UserSerializer
from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField

User = get_user_model()


class CreateUserSerializer(UserCreatePasswordRetypeSerializer):
    birth_date = serializers.DateField(write_only=True, required=False)
    phone_number = serializers.CharField(write_only=True, required=False)

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


class CustomUserSerializer(UserSerializer):
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


class UserDeleteSerializer(serializers.Serializer):
    """
    ? Serializer for user account deletion.
    ? Allows optional confirmation password (if user has a usable password)
    ? and optional reason feedback.
    """

    password = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=True,
        help_text="Optional account password for verification if account has a password.",
    )
    reason = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=True,
        max_length=500,
        help_text="Optional reason for deleting account.",
    )

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        password = attrs.get("password")

        # * If user has a usable password and password was submitted, verify it
        if password and user and user.is_authenticated and user.has_usable_password():
            if not user.check_password(password):
                raise serializers.ValidationError(
                    {"password": "Password is incorrect."}
                )

        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    """
    ? Serializer for verifying a user's email with an OTP code.
    """

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Enter a valid email address.",
        },
    )
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        error_messages={
            "required": "Verification code is required.",
            "max_length": "Verification code must be 6 digits.",
            "min_length": "Verification code must be 6 digits.",
        },
    )

    def validate_otp(self, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError(
                "Verification code must contain digits only."
            )
        return value

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class ResendOtpSerializer(serializers.Serializer):
    """
    ? Serializer for requesting a new OTP verification code.
    """

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Enter a valid email address.",
        },
    )

    def validate_email(self, value: str) -> str:
        return value.strip().lower()
