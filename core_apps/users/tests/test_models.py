import uuid
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_user_created_with_email_as_identifier(self, user):
        assert user.email == "user@example.com"
        assert User.USERNAME_FIELD == "email"

    def test_get_full_name_property(self, user):
        assert user.get_full_name == "Test User"

    def test_user_id_is_uuid(self, user):
        assert isinstance(user.id, uuid.UUID)

    def test_user_pkid_is_integer(self, user):
        assert isinstance(user.pkid, int)

    def test_create_user_without_email_raises(self, db):
        with pytest.raises(ValidationError):
            User.objects.create_user(email="", password="pass123")

    def test_create_user_with_invalid_email_raises(self, db):
        with pytest.raises(ValidationError):
            User.objects.create_user(email="not-an-email", password="pass123")

    def test_create_superuser_sets_is_staff_and_is_superuser(self, superuser):
        assert superuser.is_staff
        assert superuser.is_superuser

    def test_create_superuser_with_is_staff_false_raises(self, db):
        with pytest.raises(ValidationError):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                is_staff=False,
            )

    def test_profile_auto_created_on_user_creation(self, user):
        assert hasattr(user, "profile")
        assert user.profile is not None
