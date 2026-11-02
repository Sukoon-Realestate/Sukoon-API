"""Owner metadata follows the mobile locale; account/reputation data stay literal."""

import copy
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils.translation import override

from core_apps.features.services.reputation import visibility
from core_apps.properties.models import Property, PropertyVisit, PropertyVisitReview
from core_apps.properties.services import OwnerDashboardService
from .test_owner_profile_screen import create_test_property


URL = reverse("owner-profile")
MONTHS = (
    ("January", "يناير"), ("February", "فبراير"), ("March", "مارس"),
    ("April", "أبريل"), ("May", "مايو"), ("June", "يونيو"),
    ("July", "يوليو"), ("August", "أغسطس"), ("September", "سبتمبر"),
    ("October", "أكتوبر"), ("November", "نوفمبر"), ("December", "ديسمبر"),
)


def read(client, language=None, query=None):
    headers = {"HTTP_ACCEPT_LANGUAGE": language} if language else {}
    response = client.get(URL, query or {}, **headers)
    assert response.status_code == 200
    assert set(response.json()) == {"message", "data"}
    assert "Accept-Language" in response["Vary"]
    return response, response.json()["data"]


@pytest.mark.django_db
@pytest.mark.parametrize("header,query,expected", [
    (None, {}, "en"), ("en", {}, "en"), ("ar", {}, "ar"),
    ("ar-EG", {}, "ar"), ("en-GB", {}, "en"),
    ("ar;q=0.3,en;q=0.9", {}, "en"), ("fr", {}, "en"),
    ("en", {"lang": "ar"}, "ar"), ("ar", {"language": "en"}, "en"),
])
def test_request_language_controls_owner_copy(auth_client, header, query, expected):
    response, data = read(auth_client, header, query)
    assert response["Content-Language"] == expected
    arabic = expected == "ar"
    assert data["owner"]["role_badge"] == ("مالك" if arabic else "Owner")
    assert data["stats"] == {
        "properties_count": 0, "properties_label": "عقارات" if arabic else "Properties",
        "reviews_count": 0, "reviews_label": "تقييم" if arabic else "Reviews",
        "acceptance_rate": 100, "acceptance_label": "قبول" if arabic else "Acceptance",
        "formatted_acceptance_rate": "100%",
    }
    assert data["privacy_notice"] == {"icon": "lock", "text": (
        "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة" if arabic else
        "Your number is hidden from tenants and is shown only after a visit is accepted"
    )}


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("verified", [False, True])
def test_owner_verification_and_user_text_are_distinct(auth_client, user, language, verified):
    user.first_name, user.last_name = "مالك", "عقارات"
    user.is_verified = verified
    user.date_joined = datetime(2024, 4, 5, tzinfo=timezone.utc)
    user.save()
    user.profile.phone_number = "+201012345432"
    user.profile.save()
    _, data = read(auth_client, language)
    assert data["owner"]["id"] == str(user.id)
    assert data["owner"]["is_verified"] is verified
    assert data["owner"]["full_name"] == "مالك عقارات"
    assert data["owner"]["role_badge"] == (
        ("مالك موثّق" if verified else "مالك") if language == "ar" else
        ("Verified owner" if verified else "Owner")
    )
    assert data["owner"]["member_since_label"] == (
        "عضو منذ أبريل 2024" if language == "ar" else "Member since April 2024"
    )
    assert data["account_details"] == {"name": "مالك عقارات", "email": user.email,
        "phone_number": "+201012345432", "masked_phone_number": "010****432"}


@pytest.mark.django_db
@pytest.mark.parametrize("month,names", enumerate(MONTHS, start=1))
@pytest.mark.parametrize("language,index,prefix", [("en", 0, "Member since"), ("ar", 1, "عضو منذ")])
def test_owner_membership_keeps_calendar_month(user, month, names, language, index, prefix):
    # Direct service accepts date and datetime; localization must not shift zones.
    user.date_joined = datetime(2024, month, 1, tzinfo=timezone(timedelta(hours=3)))
    with override(language):
        data = OwnerDashboardService.get_owner_profile(user)
    assert data["owner"]["member_since_label"] == f"{prefix} {names[index]} 2024"


@pytest.mark.django_db
@pytest.mark.parametrize("language,expected", [
    ("ar", "عضو منذ يناير 2025"), ("en", "Member since January 2025"),
])
def test_owner_missing_date_retains_2025_fallback(auth_client, user, language, expected):
    user.date_joined = None  # In-memory fallback only; DB column is non-null.
    _, data = read(auth_client, language)
    assert data["owner"]["member_since_label"] == expected


def business(payload):
    result = copy.deepcopy(payload)
    for key in ("role_badge", "member_since_label"):
        result["owner"].pop(key)
    for key in ("properties_label", "reviews_label", "acceptance_label"):
        result["stats"].pop(key)
    result["privacy_notice"].pop("text")
    return result


@pytest.mark.django_db
def test_switch_keeps_counts_owner_scope_phones_and_database(auth_client, user, another_user):
    prop = create_test_property(user, title="عقارات")
    create_test_property(another_user, title="مالك")
    for index, status in enumerate(["confirmed", "confirmed", "rejected"]):
        PropertyVisit.objects.create(property=prop, tenant=another_user,
            visit_date=date(2026, 7, 20), visit_time=time(14, index), status=status)
    tables = (Property, PropertyVisit, PropertyVisitReview)
    before = [list(model.objects.order_by("pk").values()) for model in tables]
    _, ar = read(auth_client, "ar")
    _, en = read(auth_client, "en")
    _, ar_again = read(auth_client, "ar")
    assert ar_again == ar
    assert business(ar) == business(en)
    assert en["stats"]["properties_count"] == 1  # Other owner's property excluded.
    assert en["stats"]["acceptance_rate"] == 67
    assert en["stats"]["formatted_acceptance_rate"] == "67%"
    assert en["owner"]["rating_label"] == "— (0)"
    assert before == [list(model.objects.order_by("pk").values()) for model in tables]


@pytest.mark.django_db
def test_projected_public_review_content_is_never_translated(auth_client, user, monkeypatch):
    review = SimpleNamespace(id=uuid4(), overall_score=4, public_comment="مالك موثّق عقارات قبول",
        created_at=datetime(2026, 4, 25, 14, 30, tzinfo=timezone.utc))
    calls = []
    def rows(kind, subject_id, *, aggregate):
        calls.append((kind, subject_id, aggregate))
        return [review]
    monkeypatch.setattr(visibility, "subject_rows", rows)
    monkeypatch.setattr(visibility, "summary", lambda *args: {"review_count": 1, "average": 4})
    _, ar = read(auth_client, "ar")
    _, en = read(auth_client, "en")
    assert business(ar) == business(en)
    assert ar["recent_reviews"][0]["comment"] == review.public_comment
    assert ar["recent_reviews"][0]["reviewer_name"] == ""
    assert en["owner"]["rating_label"] == "4 (1)"
    assert calls == [("person_landlord", user.id, True)] * 2


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["ar", "en"])
def test_localization_never_grants_anonymous_profile_access(api_client, language):
    response = api_client.get(URL, HTTP_ACCEPT_LANGUAGE=language)
    assert response.status_code == 401
    assert response["Content-Language"] == language
    assert "owner" not in (response.json().get("data") or {})
