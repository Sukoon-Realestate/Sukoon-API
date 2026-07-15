import pytest
from core_apps.profiles.models import Profile


@pytest.mark.django_db
class TestProfileModel:
    def test_profile_auto_created_via_signal(self, user):
        assert Profile.objects.filter(user=user).exists()

    def test_profile_str_representation(self, user):
        assert str(user.profile) == f"{user.email} profile"

    def test_profile_default_gender_is_male(self, user):
        assert user.profile.gender == Profile.Gender.MALE

    def test_profile_birth_date_is_nullable(self, user):
        assert user.profile.birth_date is None

    def test_profile_has_uuid_id(self, user):
        import uuid

        assert isinstance(user.profile.id, uuid.UUID)

    def test_one_profile_per_user(self, user):
        assert Profile.objects.filter(user=user).count() == 1
