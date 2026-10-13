"""Serializers: set user password serializer."""

from rest_framework import serializers


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


class SetUserPasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password via POST auth/users/set_password/.
    Enforces minimum 8 chars, matching passwords, and no trimming.
    """

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        error_messages={
            "min_length": "يجب ألا تقل كلمة المرور الجديدة عن 8 أحرف.",
            "required": "كلمة المرور الجديدة مطلوبة.",
        },
    )
    re_new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        error_messages={
            "min_length": "يجب ألا تقل كلمة المرور الجديدة عن 8 أحرف.",
            "required": "تأكيد كلمة المرور مطلوب.",
        },
    )

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("re_new_password"):
            raise serializers.ValidationError(
                {"re_new_password": "كلمتا المرور غير متطابقتين."}
            )
        return attrs
