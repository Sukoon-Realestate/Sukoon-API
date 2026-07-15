from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer, UserSerializer
from rest_framework import serializers

User = get_user_model()


class CreateUserSerializer(UserCreatePasswordRetypeSerializer):
    birth_date = serializers.DateField(write_only=True, required=False)

    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "birth_date",
        ]

    def validate(self, attrs):
        birth_date = attrs.pop("birth_date", None)
        attrs = super().validate(attrs)
        if birth_date is not None:
            attrs["birth_date"] = birth_date
        return attrs

    def create(self, validated_data):
        birth_date = validated_data.pop("birth_date", None)
        user = super().create(validated_data)
        if birth_date:
            user.profile.birth_date = birth_date
            user.profile.save(update_fields=["birth_date"])
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
