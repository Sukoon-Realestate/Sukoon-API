from datetime import date, time
from unittest.mock import MagicMock, patch
import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from core_apps.common.models import ContentView
from core_apps.profiles.models import Profile, UserSettings
from core_apps.properties.models import (
    Property,
    PropertyFavorite,
    PropertyRating,
    PropertyType,
    PropertyVisit,
    SavedProperty,
)
from core_apps.users.models import SocialAccount
from core_apps.users.services.user_service import delete_user_account

User = get_user_model()


@pytest.fixture
def property_type(db):
    obj, _ = PropertyType.objects.get_or_create(name="Apartment")
    return obj



@pytest.mark.django_db
class TestUserService:
    def test_delete_user_account_removes_user(self, user):
        user_id = user.id
        delete_user_account(user)
        assert not User.objects.filter(id=user_id).exists()

    def test_delete_user_account_cascades_all_related_objects(
        self, user, another_user, property_type
    ):
        user_id = user.id

        # Profile is created via signals, ensure UserSettings exists
        profile = user.profile
        profile.avatar = "profile_documents/avatar/test_avatar"
        profile.save()

        user_settings, _ = UserSettings.objects.get_or_create(user=user)

        social_acc = SocialAccount.objects.create(
            user=user,
            provider=SocialAccount.PROVIDER_GOOGLE,
            provider_uid="google_12345",
            email=user.email,
        )

        from core_apps.properties.models import City, Governorate

        governorate = Governorate.objects.get_or_create(
            slug="cairo", defaults={"name": "Cairo"}
        )[0]
        city = City.objects.get_or_create(
            governorate=governorate, slug="nasr-city", defaults={"name": "Nasr City"}
        )[0]

        # Property owned by user
        property_obj = Property.objects.create(
            owner=user,
            title="Luxury Villa",
            price=5000,
            property_type=property_type,
            governorate=governorate,
            city=city,
        )

        # Saved property, favorite, rating
        saved = SavedProperty.objects.create(user=user, property=property_obj)
        favorite = PropertyFavorite.objects.create(user=user, property=property_obj)
        rating = PropertyRating.objects.create(
            user=user, property=property_obj, rating=5
        )

        # Visit by user on another user's property
        other_prop = Property.objects.create(
            owner=another_user,
            title="Other Condo",
            price=3000,
            property_type=property_type,
            governorate=governorate,
            city=city,
        )
        visit = PropertyVisit.objects.create(

            tenant=user,
            property=other_prop,
            visit_date=date(2026, 10, 1),
            visit_time=time(14, 0),
        )

        # ContentView by user
        prop_ct = ContentType.objects.get_for_model(Property)
        content_view = ContentView.objects.create(
            content_type=prop_ct,
            object_id=property_obj.pkid,
            user=user,
            viewer_ip="127.0.0.1",
            last_viewed=timezone.now(),
        )

        profile_id = profile.id
        user_settings_id = user_settings.id

        # Execute service
        with patch("cloudinary.uploader.destroy", return_value={"result": "ok"}):
            delete_user_account(user)

        # Assert User is gone
        assert not User.objects.filter(id=user_id).exists()

        # Assert cascaded objects are gone
        assert not Profile.objects.filter(id=profile_id).exists()
        assert not UserSettings.objects.filter(id=user_settings_id).exists()
        assert not SocialAccount.objects.filter(id=social_acc.id).exists()
        assert not Property.objects.filter(id=property_obj.id).exists()
        assert not SavedProperty.objects.filter(id=saved.id).exists()
        assert not PropertyFavorite.objects.filter(id=favorite.id).exists()
        assert not PropertyRating.objects.filter(id=rating.id).exists()
        assert not PropertyVisit.objects.filter(id=visit.id).exists()


        # Assert ContentView user was set to NULL (SET_NULL on_delete)
        content_view.refresh_from_db()
        assert content_view.user is None

    def test_delete_user_account_resilient_to_cloudinary_errors(self, user):
        user_id = user.id
        user.profile.avatar = "profile_documents/avatar/test_avatar"
        user.profile.save()

        # Cloudinary destroy raises an exception
        with patch(
            "cloudinary.uploader.destroy", side_effect=Exception("Cloudinary timeout")
        ):
            delete_user_account(user)

        # User is still deleted cleanly without throwing
        assert not User.objects.filter(id=user_id).exists()
