from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer, UserSerializer
from rest_framework import serializers

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
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]


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
