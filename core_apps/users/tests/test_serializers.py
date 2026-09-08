import pytest
from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from core_apps.users.serializers import UserDeleteSerializer


@pytest.mark.django_db
class TestUserDeleteSerializer:
    def test_serializer_valid_empty_payload(self, user):
        factory = RequestFactory()
        request = factory.delete("/")
        request.user = user

        serializer = UserDeleteSerializer(data={}, context={"request": request})
        assert serializer.is_valid()

    def test_serializer_valid_with_reason(self, user):
        factory = RequestFactory()
        request = factory.delete("/")
        request.user = user

        serializer = UserDeleteSerializer(
            data={"reason": "Moving away"}, context={"request": request}
        )
        assert serializer.is_valid()
        assert serializer.validated_data["reason"] == "Moving away"

    def test_serializer_valid_with_correct_password(self, user):
        factory = RequestFactory()
        request = factory.delete("/")
        request.user = user

        serializer = UserDeleteSerializer(
            data={"password": "Testpass123!"}, context={"request": request}
        )
        assert serializer.is_valid()

    def test_serializer_invalid_with_wrong_password(self, user):
        factory = RequestFactory()
        request = factory.delete("/")
        request.user = user

        serializer = UserDeleteSerializer(
            data={"password": "WrongPassword!"}, context={"request": request}
        )
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_serializer_valid_for_unusable_password_user(self, user):
        # Social login user with unusable password
        user.set_unusable_password()
        user.save()

        factory = RequestFactory()
        request = factory.delete("/")
        request.user = user

        serializer = UserDeleteSerializer(data={}, context={"request": request})
        assert serializer.is_valid()
