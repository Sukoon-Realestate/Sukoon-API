from core_apps.common.contract_testing import api_json
import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timedelta, timezone as datetime_timezone
from urllib.parse import urlsplit

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from core_apps.advertising.models import (
    Advertisement,
    AdvertisementOperation,
    AdvertisingPlan,
    MockAdvertisementPayment,
)
from core_apps.advertising.services import calendar_expiry, resolve_cairo_local
from core_apps.properties.models import City, Governorate, Property, PropertyType


def banner_file(name="banner.png", image_format="PNG"):
    stream = io.BytesIO()
    Image.new("RGB", (30, 10), color=(30, 120, 180)).save(stream, image_format)
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


def create_payload(operation_id=None, **overrides):
    payload = {
        "operation_id": operation_id or str(uuid.uuid4()),
        "plan_id": "weekly",
        "plan_revision": "1",
        "title": "Maadi rooms",
        "description": "Available now",
        "banner": banner_file(),
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def isolated_media(tmp_path):
    # Database IDs are reused between tests; throttle history must not leak
    # from these round trips into unrelated API tests using the same IDs.
    with override_settings(
        MEDIA_ROOT=tmp_path,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": str(tmp_path),
            }
        },
    ):
        yield


@pytest.fixture
def eligible_property(user):
    governorate = Governorate.objects.create(name="Cairo advertising")
    city = City.objects.create(name="Maadi advertising", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="Advertising apartment", slug="advertising-apartment"
    )
    return Property.objects.create(
        owner=user,
        title="Eligible property",
        price=10000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="Maadi",
        status=Property.Status.VERIFIED,
        is_verified=True,
        rental_inventory={
            "schema_version": 1,
            "offers": [
                {
                    "id": "offer-room-2",
                    "availability": "available",
                    "archived": False,
                }
            ],
        },
    )


@pytest.mark.django_db
class TestAdvertisingAPI:
    def test_public_plan_list_is_ordered_localized_and_enveloped(self, api_client):
        response = api_client.get(
            reverse("advertising:plan-list"), HTTP_ACCEPT_LANGUAGE="ar"
        )

        assert response.status_code == 200
        body = api_json(response)
        assert set(body) == {"message", "data"} and body["message"]
        assert [item["id"] for item in body["data"]["results"]] == [
            "weekly",
            "monthly",
            "yearly",
        ]
        assert body["data"]["results"][0]["title"] == "أسبوعية"
        assert response["Content-Language"] == "ar"

    def test_create_replay_conflict_recovery_and_owner_isolation(
        self, auth_client, another_user
    ):
        operation_id = str(uuid.uuid4())
        url = reverse("advertising:owner-advertisement-list")

        created = auth_client.post(
            url, create_payload(operation_id), format="multipart"
        )
        replay = auth_client.post(url, create_payload(operation_id), format="multipart")
        conflict = auth_client.post(
            url,
            create_payload(operation_id, title="Changed title"),
            format="multipart",
        )

        assert created.status_code == 201
        assert replay.status_code == 200
        assert replay.json()["data"]["id"] == created.json()["data"]["id"]
        assert conflict.status_code == 409
        assert conflict["X-App-Error-Code"] == "idempotency_conflict"
        assert Advertisement.objects.count() == 1
        assert AdvertisementOperation.objects.count() == 1

        lookup = auth_client.get(
            reverse("advertising:operation-detail", args=[operation_id])
        )
        assert lookup.json()["data"]["state"] == "found"
        assert (
            lookup.json()["data"]["advertisement"]["id"] == created.json()["data"]["id"]
        )

        other_client = APIClient()
        other_client.force_authenticate(another_user)
        hidden = other_client.get(
            reverse(
                "advertising:owner-advertisement-detail",
                args=[created.json()["data"]["id"]],
            )
        )
        assert hidden.status_code == 404

    def test_rejects_fake_image_and_enforces_destination_ownership(
        self, auth_client, another_user, eligible_property
    ):
        invalid_operation_id = str(uuid.uuid4())
        invalid_image = auth_client.post(
            reverse("advertising:owner-advertisement-list"),
            create_payload(
                invalid_operation_id,
                banner=SimpleUploadedFile(
                    "fake.png", b"not an image", content_type="image/png"
                ),
            ),
            format="multipart",
        )
        assert invalid_image.status_code == 415
        assert invalid_image["X-App-Error-Code"] == "invalid_image"
        rejected = auth_client.get(
            reverse("advertising:operation-detail", args=[invalid_operation_id])
        )
        assert rejected.json()["data"]["state"] == "rejected"
        assert rejected.json()["data"]["retry_allowed"] is True

        other_client = APIClient()
        other_client.force_authenticate(another_user)
        foreign = other_client.post(
            reverse("advertising:owner-advertisement-list"),
            create_payload(property_id=eligible_property.id),
            format="multipart",
        )
        assert foreign.status_code == 400
        assert foreign["X-App-Error-Code"] == "not_eligible"

    def test_property_offer_activation_payment_replay_and_public_feed(
        self, auth_client, eligible_property, another_user
    ):
        operation_id = str(uuid.uuid4())
        created = auth_client.post(
            reverse("advertising:owner-advertisement-list"),
            create_payload(
                operation_id,
                property_id=eligible_property.id,
                offer_id="offer-room-2",
            ),
            format="multipart",
        )
        advertisement_id = created.json()["data"]["id"]
        media_path = urlsplit(created.json()["data"]["banner_url"]).path
        assert APIClient().get(media_path).status_code == 404
        assert auth_client.get(media_path).status_code == 200
        payment_body = {
            "operation_id": f"{operation_id}-payment",
            "payment_mode": "mock",
        }
        payment_url = reverse("advertising:mock-payment", args=[advertisement_id])

        first = pay_invoice(auth_client, advertisement_id)
        replay = auth_client.post(payment_url, payment_body, format="json")

        assert first.status_code == 200
        assert first.json()["data"]["status"] == "active"
        assert first.json()["data"]["property_id"] == str(eligible_property.id)
        assert first.json()["data"]["payment"]["advertisement_id"] == advertisement_id
        assert first.json()["data"]["starts_at"] == replay.json()["data"]["starts_at"]
        assert first.json()["data"]["ends_at"] == replay.json()["data"]["ends_at"]
        assert MockAdvertisementPayment.objects.count() == 1
        assert APIClient().get(media_path).status_code == 200

        guest_feed = APIClient().get(reverse("advertising:tenant-home"))
        result = guest_feed.json()["data"]["results"][0]
        assert result["id"] == advertisement_id
        assert result["offer_id"] == "offer-room-2"
        assert "operation_id" not in result
        assert "plan_snapshot" not in result
        assert "payment" not in result

        eligible_property.status = Property.Status.HIDDEN
        eligible_property.save(update_fields=["status", "updated_at"])
        assert (
            APIClient()
            .get(reverse("advertising:tenant-home"))
            .json()["data"]["results"]
            == []
        )

    def test_expired_rows_are_hidden_without_waiting_for_worker(self, auth_client):
        operation_id = str(uuid.uuid4())
        created = auth_client.post(
            reverse("advertising:owner-advertisement-list"),
            create_payload(operation_id),
            format="multipart",
        )
        advertisement_id = created.json()["data"]["id"]
        assert pay_invoice(auth_client, advertisement_id).status_code == 200
        Advertisement.objects.filter(id=advertisement_id).update(
            ends_at=timezone.now() - timedelta(seconds=1),
            status=Advertisement.Status.ACTIVE,
        )

        assert (
            APIClient()
            .get(reverse("advertising:tenant-home"))
            .json()["data"]["results"]
            == []
        )
        detail = auth_client.get(
            reverse("advertising:owner-advertisement-detail", args=[advertisement_id])
        )
        assert detail.json()["data"]["status"] == "expired"

    def test_unknown_operation_is_safe_to_retry(self, auth_client):
        operation_id = str(uuid.uuid4())
        response = auth_client.get(
            reverse("advertising:operation-detail", args=[operation_id])
        )
        assert response.status_code == 200
        assert response.json()["data"] == {
            "operation_id": operation_id,
            "state": "not_found",
            "retry_allowed": True,
            "advertisement": None,
        }


@pytest.mark.django_db
class TestAdvertisingCalendarExpiry:
    def test_month_clamps_january_31(self):
        starts_at = datetime(2027, 1, 31, 10, 30, tzinfo=datetime_timezone.utc)
        result = calendar_expiry(starts_at, "calendar_month", 1)
        assert result.astimezone(datetime_timezone.utc) == datetime(
            2027, 2, 28, 10, 30, tzinfo=datetime_timezone.utc
        )

    def test_year_clamps_leap_day_and_week_is_elapsed_time(self):
        leap_day = datetime(2028, 2, 29, 8, 0, tzinfo=datetime_timezone.utc)
        yearly = calendar_expiry(leap_day, "calendar_year", 1)
        assert yearly.astimezone(datetime_timezone.utc) == datetime(
            2029, 2, 28, 8, 0, tzinfo=datetime_timezone.utc
        )
        assert calendar_expiry(leap_day, "week", 1) == leap_day + timedelta(days=7)

    def test_cairo_dst_gap_moves_forward_by_the_gap_and_overlap_uses_later_fold(self):
        gap = resolve_cairo_local(datetime(2026, 4, 24, 0, 30))
        overlap = resolve_cairo_local(datetime(2026, 10, 29, 23, 30))

        assert (gap.hour, gap.minute, gap.utcoffset()) == (
            1,
            30,
            timedelta(hours=3),
        )
        assert overlap.fold == 1
        assert overlap.utcoffset() == timedelta(hours=2)


def pay_invoice(client, ad_id):
    """Explicit local purchase path; return the authoritative private ad on success."""
    root = "/api/v1/features/v1/billing/invoices/"
    identity = str(ad_id)
    issued = client.post(
        root,
        {
            "purpose": "advertising",
            "workspace": "owner",
            "advertisement_id": identity,
            "request_key": str(uuid.uuid5(uuid.NAMESPACE_URL, "issue:" + identity)),
        },
        format="json",
    )
    if issued.status_code not in (200, 201):
        return issued
    invoice = issued.json()["data"]
    quote = client.post(
        root + invoice["id"] + "/quote/",
        {
            "expected_revision": invoice["revision"],
            "request_key": str(uuid.uuid5(uuid.NAMESPACE_URL, "quote:" + identity)),
        },
        format="json",
    )
    if quote.status_code not in (200, 201):
        return quote
    paid = client.post(
        root + invoice["id"] + "/checkout/",
        {
            "quote_id": quote.json()["data"]["id"],
            "expected_revision": invoice["revision"],
            "request_key": str(uuid.uuid5(uuid.NAMESPACE_URL, "pay:" + identity)),
        },
        format="json",
    )
    return (
        client.get(reverse("advertising:owner-advertisement-detail", args=[ad_id]))
        if paid.status_code == 200
        else paid
    )


def pending_ad(client, **overrides):
    response = client.post(
        reverse("advertising:owner-advertisement-list"),
        create_payload(**overrides),
        format="multipart",
    )
    assert response.status_code == 201, response.data
    data = response.json()["data"]
    return (
        Advertisement.objects.get(id=data["id"]),
        reverse("advertising:mock-payment", args=[data["id"]]),
        {"operation_id": data["operation_id"] + "-payment", "payment_mode": "mock"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "ar"])
def test_informational_payment_snapshot_recovery_and_expired_retry(
    auth_client, another_user, monkeypatch, language
):
    auth_client.defaults["HTTP_ACCEPT_LANGUAGE"] = language
    ad, url, body = pending_ad(auth_client)
    snapshot = ad.plan_snapshot
    start = timezone.now()
    monkeypatch.setattr("core_apps.advertising.services.timezone.now", lambda: start)
    response = pay_invoice(auth_client, ad.id)
    AdvertisingPlan.objects.filter(id="weekly").update(
        amount_minor=123,
        duration_count=3,
        revision="2",
        active=False,
    )
    assert response.status_code == 200
    paid = response.json()["data"]
    assert set(response.json()) == {"message", "data"} and response.json()["message"]
    assert paid["property_id"] is paid["offer_id"] is None
    assert paid["plan_snapshot"] == snapshot
    assert paid["payment"]["advertisement_id"] == str(ad.id)
    assert paid["payment"]["operation_id"] == body["operation_id"]
    assert paid["payment"]["status"] == "mock_succeeded"
    assert paid["payment"]["payment_mode"] == "mock"
    ad.refresh_from_db()
    assert ad.starts_at == start
    assert (ad.ends_at - start).total_seconds() == 604800
    assert auth_client.post(url, body, format="json").json()["data"] == paid
    detail = reverse("advertising:owner-advertisement-detail", args=[ad.id])
    assert auth_client.get(detail).json()["data"] == paid
    assert auth_client.get(reverse("advertising:owner-advertisement-list")).json()[
        "data"
    ] == [paid]
    assert (
        auth_client.get(
            reverse("advertising:operation-detail", args=[ad.operation.operation_id])
        ).json()["data"]["advertisement"]
        == paid
    )
    other = APIClient()
    other.force_authenticate(another_user)
    assert other.get(detail).status_code == 404
    assert other.post(url, body, format="json").status_code == 404
    assert APIClient().post(url, body, format="json").status_code == 401
    for viewer in (APIClient(), other):
        feed = viewer.get(
            reverse("advertising:tenant-home"), HTTP_ACCEPT_LANGUAGE=language
        )
        public = feed.json()["data"]["results"][0]
        assert public["id"] == str(ad.id)
        assert (
            not {"owner_id", "operation_id", "plan_snapshot", "payment", "price"}
            & public.keys()
        )
        media = viewer.get(urlsplit(paid["banner_url"]).path)
        assert media.status_code == 200
        assert b"".join(media.streaming_content)
    invalid = auth_client.post(url, {**body, "operation_id": "wrong"}, format="json")
    assert invalid.status_code == 400
    assert set(invalid.json()) == {"message", "data"} and invalid.json()["data"] is None
    assert invalid["X-App-Error-Code"] == "invalid_payment_operation"
    assert ("معرف" if language == "ar" else "operation ID") in invalid.json()["message"]
    monkeypatch.setattr(
        "core_apps.advertising.services.timezone.now", lambda: ad.ends_at
    )
    expired = auth_client.post(url, body, format="json").json()["data"]
    assert expired == {**paid, "status": "expired"}
    assert MockAdvertisementPayment.objects.count() == 1
    assert (
        APIClient().get(reverse("advertising:tenant-home")).json()["data"]["results"]
        == []
    )
    assert APIClient().get(urlsplit(paid["banner_url"]).path).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    "failure", ["missing_media", "transferred", "hidden", "archived"]
)
def test_payment_revalidates_media_and_destination(
    auth_client, eligible_property, another_user, failure
):
    ad, url, body = pending_ad(
        auth_client, property_id=eligible_property.id, offer_id="offer-room-2"
    )
    if failure == "missing_media":
        ad.media.banner.storage.delete(ad.media.banner.name)
    elif failure == "transferred":
        eligible_property.owner = another_user
    elif failure == "hidden":
        eligible_property.status = Property.Status.HIDDEN
    else:
        eligible_property.rental_inventory["offers"][0]["archived"] = True
    eligible_property.save()
    response = pay_invoice(auth_client, ad.id)
    assert response.status_code == 409
    assert (
        set(response.json()) == {"message", "data"} and response.json()["data"] is None
    )
    ad.refresh_from_db()
    assert ad.status == "pending_payment"
    assert ad.starts_at is ad.ends_at is None
    assert not MockAdvertisementPayment.objects.exists()


@pytest.mark.django_db
def test_payment_failure_rolls_back_activation_and_same_operation_can_retry(
    auth_client, monkeypatch
):
    ad, url, body = pending_ad(auth_client)
    with monkeypatch.context() as patch:

        def fail(**kwargs):
            raise RuntimeError("Injected payment storage failure")

        patch.setattr(MockAdvertisementPayment.objects, "create", fail)
        response = pay_invoice(auth_client, ad.id)
        assert response.status_code == 500
        assert response.json()["data"] is None
        assert response["X-Correlation-ID"]
    ad.refresh_from_db()
    assert ad.status == "pending_payment"
    assert ad.starts_at is ad.ends_at is ad.activated_at is None
    assert not MockAdvertisementPayment.objects.exists()
    assert pay_invoice(auth_client, ad.id).status_code == 200
    assert MockAdvertisementPayment.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ineligible", ["future", "placement", "media", "owner", "payment"]
)
def test_public_media_and_feed_share_live_eligibility(auth_client, user, ineligible):
    ad, url, body = pending_ad(auth_client)
    assert pay_invoice(auth_client, ad.id).status_code == 200
    ad.refresh_from_db()
    if ineligible == "future":
        ad.starts_at = timezone.now() + timedelta(hours=1)
    elif ineligible == "placement":
        ad.placement = "other"
    elif ineligible == "media":
        ad.media.banner.storage.delete(ad.media.banner.name)
    elif ineligible == "owner":
        user.is_active = False
        user.save()
    else:
        ad.payment.delete()
    ad.save()
    guest = APIClient()
    assert guest.get(reverse("advertising:tenant-home")).json()["data"]["results"] == []
    assert (
        guest.get(reverse("advertising:advertisement-media", args=[ad.id])).status_code
        == 404
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_payment_retries_share_one_receipt(auth_client, user):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL")
    AdvertisingPlan.objects.get_or_create(
        id="weekly",
        defaults={
            "title_en": "Weekly",
            "title_ar": "أسبوعية",
            "duration_unit": "week",
            "duration_count": 1,
            "amount_minor": 100000,
            "revision": "1",
        },
    )
    ad, _, _ = pending_ad(auth_client)
    root = "/api/v1/features/v1/billing/invoices/"
    issued = auth_client.post(
        root,
        {
            "purpose": "advertising",
            "workspace": "owner",
            "advertisement_id": str(ad.id),
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert issued.status_code == 201
    invoice = issued.json()["data"]
    quote = auth_client.post(
        root + invoice["id"] + "/quote/",
        {"expected_revision": invoice["revision"], "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert quote.status_code == 201
    url = root + invoice["id"] + "/checkout/"
    body = {
        "quote_id": quote.json()["data"]["id"],
        "expected_revision": invoice["revision"],
        "request_key": str(uuid.uuid4()),
    }
    barrier = Barrier(2)

    def submit():
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            client = APIClient()
            client.force_authenticate(user)
            barrier.wait(timeout=10)
            response = client.post(url, body, format="json")
            return response.status_code, response.json()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert results[0][0] == results[1][0] == 200
    assert results[0][1] == results[1][1]
    assert MockAdvertisementPayment.objects.filter(advertisement=ad).count() == 1
    from core_apps.features.models import PaymentAttempt, PaymentReceipt

    assert PaymentAttempt.objects.filter(invoice__id=invoice["id"]).count() == 1
    assert (
        PaymentReceipt.objects.filter(
            payment_attempt__invoice__id=invoice["id"]
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_existing_audit_ad_media_recovery_and_mock_payment_activation(
    auth_client, user
):
    """
    BE002: Verify that existing audit ad 85295dd1-f8bd-4c82-a903-9bdc3d90af98
    recovers missing media across container restart, activates with mock payment,
    replays idempotently, serves media, and places banner in tenant home.
    """
    from core_apps.advertising.models import AdvertisementMedia

    op_id = "74682688-4428-413c-a1ae-c4b87222c687"
    payment_op_id = f"{op_id}-payment"
    ad_id = uuid.UUID("85295dd1-f8bd-4c82-a903-9bdc3d90af98")

    op = AdvertisementOperation.objects.create(
        owner=user,
        operation_id=op_id,
        state=AdvertisementOperation.State.FOUND,
    )
    plan = AdvertisingPlan.objects.get(id="weekly")
    ad = Advertisement.objects.create(
        id=ad_id,
        owner=user,
        operation=op,
        title="Sokoun live test 74682688",
        description="Integration test banner. Mock payment only; no money collected.",
        plan_snapshot={
            "id": plan.id,
            "title": plan.title_en,
            "duration_unit": plan.duration_unit,
            "duration_count": plan.duration_count,
            "amount_minor": plan.amount_minor,
            "revision": plan.revision,
        },
        status=Advertisement.Status.PENDING_PAYMENT,
    )
    media = AdvertisementMedia.objects.create(
        advertisement=ad,
        banner="advertising/banner_ads/2026/10/85295dd1-f8bd-4c82-a903-9bdc3d90af98.png",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        content_type="image/png",
        size_bytes=1024,
    )

    # 1. Simulate media file missing from ephemeral disk
    if media.banner.storage.exists(media.banner.name):
        media.banner.storage.delete(media.banner.name)

    # 2. Mock payment activation succeeds (does not fail with 400 errors.banner)
    pay_url = reverse("advertising:mock-payment", args=[ad.id])
    body = {"operation_id": payment_op_id, "payment_mode": "mock"}
    res = pay_invoice(auth_client, ad.id)
    assert res.status_code == 200
    assert set(res.json()) == {"message", "data"} and res.json()["message"]
    data = res.json()["data"]
    assert data["status"] == "active"
    assert data["payment"]["operation_id"] == payment_op_id

    # 3. Media is retrievable with exact 28,970 bytes and expected digest
    import hashlib

    media_url = reverse("advertising:advertisement-media", args=[ad.id])
    media_res = auth_client.get(media_url)
    assert media_res.status_code == 200
    media_bytes = (
        b"".join(media_res.streaming_content)
        if hasattr(media_res, "streaming_content")
        else media_res.content
    )
    assert len(media_bytes) == 28970
    assert (
        hashlib.sha256(media_bytes).hexdigest()
        == "dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b"
    )

    # 4. Tenant home placement returns the active ad
    guest_client = APIClient()
    home_res = guest_client.get(reverse("advertising:tenant-home"))
    assert home_res.status_code == 200
    results = home_res.json()["data"]["results"]
    assert any(item["id"] == str(ad.id) for item in results)

    # 5. Idempotent replay of same activation returns same payload with HTTP 200
    replay_res = auth_client.post(pay_url, body, format="json")
    assert replay_res.status_code == 200
    assert replay_res.json()["data"]["id"] == str(ad.id)

    # 6. Alternating Accept-Language headers return proper Content-Language and localized messages
    res_ar = guest_client.get(
        reverse("advertising:plan-list"), HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert res_ar.status_code == 200
    assert res_ar["Content-Language"] == "ar"
    assert res_ar.json()["message"] == "الخطط المتاحة."

    res_en = guest_client.get(
        reverse("advertising:plan-list"), HTTP_ACCEPT_LANGUAGE="en"
    )
    assert res_en.status_code == 200
    assert res_en["Content-Language"] == "en"
    assert res_en.json()["message"] == "Available plans."
