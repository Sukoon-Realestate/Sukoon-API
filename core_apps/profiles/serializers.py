from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import Profile


class CloudinarySerializerField(serializers.ImageField):
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
