from datetime import date
import pytest
from django.contrib.auth import get_user_model

from core_apps.profiles.models import Profile
from core_apps.profiles.services.profile_service import (
    ProfileService,
    format_arabic_count,
    format_arabic_date,
    format_arabic_month_year,
    mask_phone_number,
)

User = get_user_model()


@pytest.mark.django_db
class TestProfileServiceHelpers:
    def test_mask_phone_number(self):
        assert mask_phone_number("+201012345432") == "010****432"
        assert mask_phone_number("01012345432") == "010****432"
        assert mask_phone_number("") == ""
        assert mask_phone_number(None) == ""

    def test_format_arabic_month_year(self):
        d = date(2026, 1, 15)
        assert format_arabic_month_year(d, prefix="عضو منذ") == "عضو منذ يناير 2026"
        assert format_arabic_month_year(d, prefix="منذ") == "منذ يناير 2026"

    def test_format_arabic_date(self):
        d = date(1995, 3, 15)
        assert format_arabic_date(d) == "15 مارس 1995"
        assert format_arabic_date(None) == ""

    def test_format_arabic_count(self):
        assert format_arabic_count(4, "طلب", "طلبات") == "4 طلبات"
        assert format_arabic_count(1, "طلب", "طلبات") == "1 طلب"
        assert format_arabic_count(12, "عقار", "عقارات") == "12 عقار"


@pytest.mark.django_db
class TestProfileService:
    def test_calculate_profile_completion_initial_user(self, user):
        # User only has first_name, last_name, email, default male gender
        score = ProfileService.calculate_profile_completion(user)
        # first_name + last_name = 15, email = 15, gender (default male) = 10 -> 40
        assert score >= 30

    def test_calculate_profile_completion_full_except_avatar(self, user):
        user.is_verified = True
        user.save()
        user.profile.phone_number = "+201012345432"
        user.profile.birth_date = date(1995, 3, 15)
        user.profile.gender = Profile.Gender.MALE
        user.profile.save()

        score = ProfileService.calculate_profile_completion(user)
        # 15 (name) + 15 (email) + 15 (phone) + 15 (birth_date) + 10 (gender) + 10 (verified) = 80
        assert score == 80

    def test_get_my_account_data(self, user):
        data = ProfileService.get_my_account_data(user)
        assert "user" in data
        assert "stats" in data
        assert "menu_items" in data
        assert "account_details" in data
        assert data["user"]["full_name"] == user.get_full_name
        assert data["stats"]["saved_count"] == 0

    def test_get_account_summary_data(self, user):
        data = ProfileService.get_account_summary_data(user)
        assert "user" in data
        assert "identity_verification" in data
        assert "stats" in data
        assert "shortcuts" in data
        assert data["user"]["initial"] == user.first_name[0]

    def test_update_user_profile_atomic(self, user):
        update_data = {
            "full_name": "محمد أحمد",
            "phone_number": "+201012345432",
            "birth_date": date(1995, 3, 15),
            "gender": Profile.Gender.MALE,
        }
        profile = ProfileService.update_user_profile(user, update_data)
        user.refresh_from_db()
        assert user.first_name == "محمد"
        assert user.last_name == "أحمد"
        assert str(profile.phone_number) == "+201012345432"
        assert profile.birth_date == date(1995, 3, 15)
