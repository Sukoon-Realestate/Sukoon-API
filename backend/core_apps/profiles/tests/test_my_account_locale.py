"""Account labels follow the request locale without translating account data."""

import copy
import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
from django.urls import reverse
from django.utils.translation import override

from core_apps.features.models import Lease, RentalChange
from core_apps.profiles.models import Contract
from core_apps.profiles.services import contract_projection
from core_apps.profiles.services.profile_service_parts.account_metadata import (
    format_account_count,
    membership_labels,
)
from core_apps.properties.models import PropertyVisit, PropertyVisitReview, SavedProperty
from .test_screen_views import create_test_property


URL = reverse("my-account")
MONTHS = (
    ("January", "يناير"), ("February", "فبراير"), ("March", "مارس"),
    ("April", "أبريل"), ("May", "مايو"), ("June", "يونيو"),
    ("July", "يوليو"), ("August", "أغسطس"), ("September", "سبتمبر"),
    ("October", "أكتوبر"), ("November", "نوفمبر"), ("December", "ديسمبر"),
)


def account(client, language=None, query=None):
    headers = {"HTTP_ACCEPT_LANGUAGE": language} if language else {}
    response = client.get(URL, query or {}, **headers)
    assert response.status_code == 200
    # Exercise the actual wire envelope, not a response normalizer.
    assert set(response.json()) == {"message", "data"}
    assert "Accept-Language" in response["Vary"]
    return response, response.json()["data"]


@pytest.mark.parametrize("month,names", enumerate(MONTHS, start=1))
@pytest.mark.parametrize("language,index,prefix", [("en", 0, "Member since"), ("ar", 1, "عضو منذ")])
def test_all_membership_months_preserve_stored_calendar(month, names, language, index, prefix):
    # An offset must not shift the displayed month through timezone conversion.
    joined = datetime(2024, month, 1, tzinfo=timezone(timedelta(hours=3)))
    with override(language):
        assert membership_labels(joined) == (2024, names[index], f"{prefix} {names[index]} 2024")


@pytest.mark.parametrize("count,english,arabic", [
    (0, "0 requests", "0 طلب"), (1, "1 request", "1 طلب"),
    (2, "2 requests", "2 طلب"), (3, "3 requests", "3 طلبات"),
    (10, "10 requests", "10 طلبات"), (11, "11 requests", "11 طلب"),
])
def test_count_grammar_keeps_existing_arabic(count, english, arabic):
    for language, expected in [("en", english), ("ar", arabic)]:
        with override(language):
            assert format_account_count(count, "request", "requests", "طلب", "طلبات") == expected
    for singular, plural, arabic_noun in [
        ("active contract", "active contracts", "عقد نشط"),
        ("review", "reviews", "تقييم"),
    ]:
        with override("en"):
            assert format_account_count(count, singular, plural, arabic_noun, arabic_noun) == (
                f"{count} {singular if count == 1 else plural}"
            )
        with override("ar"):
            assert format_account_count(count, singular, plural, arabic_noun, arabic_noun) == f"{count} {arabic_noun}"


@pytest.mark.django_db
@pytest.mark.parametrize("header,query,expected", [
    (None, {}, "en"), ("en", {}, "en"), ("ar", {}, "ar"),
    ("ar-EG", {}, "ar"), ("en-GB", {}, "en"),
    ("ar;q=0.3,en;q=0.9", {}, "en"), ("fr", {}, "en"),
    ("en", {"lang": "ar"}, "ar"), ("ar", {"language": "en"}, "en"),
])
def test_request_locale_controls_payload_and_headers(auth_client, header, query, expected):
    response, data = account(auth_client, header, query)
    assert response["Content-Language"] == expected
    arabic = expected == "ar"
    assert data["user"]["role_label"] == ("مستأجر" if arabic else "Tenant")
    assert data["user"]["verification_badge"] == ("غير موثّق" if arabic else "Unverified")
    assert data["menu_items"] == {
        "visit_requests": {
            "title": "طلبات الزيارة" if arabic else "Visit requests",
            "count": 0, "subtitle": "0 طلب" if arabic else "0 requests",
        },
        "contracts": {
            "title": "عقودي" if arabic else "My contracts", "count": 0,
            "subtitle": "0 عقد نشط" if arabic else "0 active contracts",
            "as_of": contract_projection.civil_day().isoformat(), "projection_version": 1,
        },
        "reviews": {
            "title": "تقييماتي" if arabic else "My reviews",
            "count": 0, "subtitle": "0 تقييم" if arabic else "0 reviews",
        },
        "verification": {
            "title": "التوثيق والخصوصية" if arabic else "Verification and privacy",
            "is_verified": False, "subtitle": "غير موثّق" if arabic else "Unverified",
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("verified", [False, True])
def test_verification_membership_and_user_content(auth_client, user, language, verified):
    # Deliberately collide with UI labels: account content must remain verbatim.
    user.first_name, user.last_name = "مستأجر", "عقودي"
    user.date_joined = datetime(2024, 4, 5, tzinfo=timezone.utc)
    user.is_verified = verified
    user.save()
    _, data = account(auth_client, language)
    badge = ("موثّق" if verified else "غير موثّق") if language == "ar" else (
        "Verified" if verified else "Unverified"
    )
    assert data["user"]["verification_badge"] == badge
    assert data["menu_items"]["verification"]["subtitle"] == (f"{badge} ✓" if verified else badge)
    assert data["user"]["is_verified"] is verified
    assert data["user"]["id"] == str(user.id)
    assert data["user"]["full_name"] == "مستأجر عقودي"
    assert data["user"]["first_name"] == "مستأجر" and data["user"]["last_name"] == "عقودي"
    assert data["user"]["member_since_year"] == 2024
    assert data["user"]["member_since_month"] == ("أبريل" if language == "ar" else "April")
    assert data["user"]["member_since_label"] == (
        "عضو منذ أبريل 2024" if language == "ar" else "Member since April 2024"
    )
    assert data["account_details"] == {"name": "مستأجر عقودي", "email": user.email}


@pytest.mark.django_db
@pytest.mark.parametrize("language,month,label", [
    ("ar", "يناير", "عضو منذ يناير 2026"),
    ("en", "January", "Member since January 2026"),
])
def test_missing_membership_date_keeps_existing_fallback(auth_client, user, language, month, label):
    # In-memory caller fallback only; do not persist a null in the non-null column.
    user.date_joined = None
    _, data = account(auth_client, language)
    assert data["user"]["member_since_year"] == 2026
    assert data["user"]["member_since_month"] == month
    assert data["user"]["member_since_label"] == label


def activity(user, owner, count):
    prop = create_test_property(owner)
    SavedProperty.objects.create(user=user, property=prop)
    for number in range(count):
        visit = PropertyVisit.objects.create(
            tenant=user, property=prop, visit_date=date(2026, 7, 20),
            visit_time=time(14, number), status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisitReview.objects.create(
            visit=visit, overall_rating=5, cleanliness_rating=5,
            listing_accuracy_rating=5, owner_interaction_rating=5, comment="مستأجر عقودي",
        )
    return prop


@pytest.mark.django_db
def test_singular_wire_labels_use_real_counts(auth_client, user, another_user):
    activity(user, another_user, 1)
    Contract.objects.create(
        tenant=user, property_title="منزل", status=Contract.Status.ACTIVE,
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
    )
    _, data = account(auth_client, "en")
    assert data["stats"] == {"saved_count": 1, "visits_count": 1, "reviews_count": 1}
    assert data["menu_items"]["visit_requests"]["subtitle"] == "1 request"
    assert data["menu_items"]["contracts"]["subtitle"] == "1 active contract"
    assert data["menu_items"]["reviews"]["subtitle"] == "1 review"


@pytest.mark.django_db
def test_language_switch_preserves_projection_counts_identities_and_business_data(auth_client, user, another_user):
    prop = activity(user, another_user, 3)
    day = contract_projection.civil_day()

    def lease(**changes):
        values = dict(
            tenant=user, owner=another_user, property=prop, template_id="eg-v1",
            template_version="1", legacy_read_only=False, offer_id=str(uuid.uuid4()),
            rent_amount_minor=1000, start_date=day - timedelta(days=1),
            end_date=day + timedelta(days=30), status=Lease.Status.ACTIVE,
        )
        values.update(changes)
        return Lease.objects.create(**values)

    old = lease()
    current = lease(offer_id=old.offer_id, tenancy_root_id=old.tenancy_root_id, revision=7)
    RentalChange.objects.create(
        lease=old, result_lease=current, requester=user, kind="renewal", status="applied",
    )
    lease(tenant=another_user, owner=user)  # another tenant never contributes
    lease(end_date=day)  # canonical exclusive end date never contributes
    legacy = Contract.objects.create(
        tenant=user, property_title="عقودي", status=Contract.Status.ACTIVE,
        start_date=date(2001, 1, 1), end_date=date(2002, 1, 1),
    )
    models = (Lease, RentalChange, Contract, PropertyVisit, PropertyVisitReview, SavedProperty)
    before = [list(model.objects.order_by("pk").values()) for model in models]
    _, arabic = account(auth_client, "ar")
    _, english = account(auth_client, "en")
    _, arabic_again = account(auth_client, "ar")
    assert arabic_again == arabic
    assert english["stats"] == arabic["stats"] == {"saved_count": 1, "visits_count": 3, "reviews_count": 3}
    assert english["menu_items"]["contracts"]["count"] == arabic["menu_items"]["contracts"]["count"] == 2
    assert english["menu_items"]["contracts"]["subtitle"] == "2 active contracts"
    assert arabic["menu_items"]["contracts"]["subtitle"] == "2 عقد نشط"
    assert english["menu_items"]["reviews"]["subtitle"] == "3 reviews"
    assert arabic["menu_items"]["reviews"]["subtitle"] == "3 تقييم"
    assert english["menu_items"]["visit_requests"]["subtitle"] == "3 requests"
    assert arabic["menu_items"]["visit_requests"]["subtitle"] == "3 طلبات"
    # Strip only the reviewed static presentation fields; all remaining bytes agree.
    def business(payload):
        result = copy.deepcopy(payload)
        for field in ("verification_badge", "role_label", "member_since_label", "member_since_month"):
            result["user"].pop(field)
        for item in result["menu_items"].values():
            item.pop("title")
            item.pop("subtitle")
        return result

    assert business(arabic) == business(english)
    pages = []
    for language in ("ar", "en"):
        response = auth_client.get(
            reverse("tenant-contracts-list"), {"bucket": "current"}, HTTP_ACCEPT_LANGUAGE=language,
        )
        assert response.status_code == 200 and int(response["X-Total-Count"]) == 2
        pages.append(response.json()["data"])
    assert pages[0] == pages[1]
    assert {row["id"] for row in pages[0]} == {f"lease:{current.id}", str(legacy.id)}
    assert before == [list(model.objects.order_by("pk").values()) for model in models]


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["ar", "en"])
def test_localization_does_not_allow_anonymous_account_read(api_client, language):
    response = api_client.get(URL, HTTP_ACCEPT_LANGUAGE=language)
    assert response.status_code == 401
    assert response["Content-Language"] == language
    assert "user" not in (response.json().get("data") or {})
