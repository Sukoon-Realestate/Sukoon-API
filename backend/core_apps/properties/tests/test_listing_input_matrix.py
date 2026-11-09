"""Sprint 02 listing input/upload matrix (A2-04, A2-05, A2-06).

Malformed inventory/metadata/media inputs return field-level 400s before any
mutation, reservation or provider call; valid multipart/base64/native images
and measured videos still work; cover and gallery share one 25-image cap
including pending reservations, also under concurrency (PostgreSQL).
"""

import base64
import io
import threading
import uuid
from copy import deepcopy
from unittest.mock import patch

import pytest
from django.db import connection
from django.urls import reverse
from PIL import Image
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from core_apps.features.models import IdempotencyRecord
from core_apps.properties.models import Property, PropertyImage
from core_apps.properties.rental_inventory import normalize_inventory

from .media_samples import real_image, real_mp4
from .test_discovery_fixes import listing  # noqa: F401  (fixture)
from .test_rental_inventory import _room_offer_payload

pytestmark = pytest.mark.django_db


def provider_resource(file, **kwargs):
    return {
        "public_id": kwargs.get("public_id", "mocked/listing"),
        "url": "https://res.cloudinary.com/mocked/listing",
        "secure_url": "https://res.cloudinary.com/mocked/listing",
        "format": "jpg",
        "resource_type": kwargs.get("resource_type", "image"),
        "version": 1,
        "type": "upload",
    }


@pytest.fixture
def provider():
    with patch("cloudinary.uploader.upload", side_effect=provider_resource) as upload:
        yield upload


# ---------------------------------------------------------------- inventory


def _mutate(path, value):
    def apply(payload):
        target = payload
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return payload

    return apply


INVENTORY_INVALID = {
    "revision string": _mutate(["expected_revision"], "oops"),
    "revision bool": _mutate(["expected_revision"], True),
    "revision list": _mutate(["expected_revision"], []),
    "revision float": _mutate(["expected_revision"], 0.5),
    "schema bool": _mutate(["schema_version"], True),
    "rooms object": _mutate(["rooms"], {"a": 1}),
    "room null": _mutate(["rooms"], [None]),
    "room name list": _mutate(["rooms", 0, "name"], []),
    "room capacity bool": _mutate(["rooms", 0, "capacity"], True),
    "beds string": _mutate(["rooms", 0, "beds"], "bed"),
    "bed null": _mutate(["rooms", 0, "beds"], [None]),
    "shared_defaults list": _mutate(["shared_defaults"], [1]),
    "shared rules numbers": _mutate(["shared_defaults", "rules"], [1, 2]),
    "smoking string": _mutate(["shared_defaults", "smoking_allowed"], "yes"),
    "rental_period text": _mutate(["shared_defaults", "rental_period"], "three"),
    "offers object": _mutate(["offers"], {"a": 1}),
    "offer null": _mutate(["offers"], [None]),
    "price infinity": _mutate(["offers", 0, "term_overrides", "price"], "Infinity"),
    "price nan": _mutate(["offers", 0, "term_overrides", "price"], "NaN"),
    "price overflow": _mutate(["offers", 0, "term_overrides", "price"], "1e400"),
    "price too many digits": _mutate(["offers", 0, "term_overrides", "price"], "12345678901.00"),
    "price too precise": _mutate(["offers", 0, "term_overrides", "price"], "1.234"),
    "price negative": _mutate(["offers", 0, "term_overrides", "price"], "-1"),
    "price bool": _mutate(["offers", 0, "term_overrides", "price"], True),
    "price object": _mutate(["offers", 0, "term_overrides", "price"], {"amount": 1}),
    "terms list": _mutate(["offers", 0, "term_overrides"], [1]),
    "archived string": _mutate(["offers", 0, "archived"], "no"),
    "room_ids string": _mutate(["offers", 0, "room_ids"], "room-a"),
    "room_ids numbers": _mutate(["offers", 0, "room_ids"], [1]),
    "inherited string": _mutate(["offers", 0, "inherited_fields"], "deposit"),
    "scope list": _mutate(["offers", 0, "rental_scope"], ["room"]),
    "too many rooms": _mutate(
        ["rooms"], [{"client_key": f"r{i}", "name": "R"} for i in range(51)]
    ),
    "too deep": _mutate(["rooms", 0, "media_ids"], [[[[[[[["deep"]]]]]]]]),
    "too large": _mutate(["rooms", 0, "description"], "x" * 5000),
}


@pytest.mark.parametrize("mutation", INVENTORY_INVALID.values(), ids=INVENTORY_INVALID.keys())
def test_inventory_rejects_malformed_shapes_with_validation_errors(mutation):
    payload = mutation(deepcopy(_room_offer_payload()))
    with pytest.raises(ValidationError):
        normalize_inventory(payload)


def test_inventory_rejects_duplicate_persisted_ids_and_keeps_valid_ids_stable():
    payload = _room_offer_payload()
    payload["rooms"].append({"client_key": "room-b", "name": "Room B", "capacity": 1})
    current = normalize_inventory(payload)
    edit = deepcopy(current)
    edit["expected_revision"] = current["revision"]
    for offer in edit["offers"]:
        offer["term_overrides"] = {
            k: v for k, v in offer.pop("terms").items() if k not in offer["inherited_fields"]
        }
    stable = normalize_inventory(deepcopy(edit), current)
    assert [room["id"] for room in stable["rooms"]] == [room["id"] for room in current["rooms"]]
    duplicate = deepcopy(edit)
    duplicate["rooms"][1]["id"] = duplicate["rooms"][0]["id"]
    with pytest.raises(ValidationError, match="Duplicate room id"):
        normalize_inventory(duplicate, current)
    duplicate = deepcopy(edit)
    duplicate["offers"].append(deepcopy(duplicate["offers"][0]))
    with pytest.raises(ValidationError, match="Duplicate offer id"):
        normalize_inventory(duplicate, current)


def test_inventory_preserves_exact_money_and_client_extension_keys():
    payload = _room_offer_payload()
    payload["shared_media_ids"] = ["m1"]
    payload["rooms"][0]["media_ids"] = ["m2"]
    payload["offers"][0]["term_overrides"]["price"] = "5000.50"
    result = normalize_inventory(payload)
    assert result["offers"][0]["terms"]["price"] == "5000.50"
    assert result["shared_media_ids"] == ["m1"]
    assert result["rooms"][0]["media_ids"] == ["m2"]


# ------------------------------------------------------- property commands


def _verified_client(user):
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client = APIClient()
    client.force_authenticate(user)
    return client


def _create_body(apartment_type, cairo_governorate, cairo_city, **extra):
    return {
        "title": "Typed listing",
        "price": "12000.00",
        "price_period": "monthly",
        "property_type": apartment_type.slug,
        "governorate": str(cairo_governorate.id),
        "city": str(cairo_city.id),
        "district": "Nasr City",
        "bedrooms": 2,
        "bathrooms": 1,
        "area": 100,
        **extra,
    }


CREATE_INVALID = {
    "amenity object": {"amenities": [{"wifi": True}]},
    "amenity number": {"amenities": [1]},
    "deposit nan": {"deposit": "nan"},
    "deposit inf": {"deposit": "inf"},
    "price infinity": {"price": "Infinity"},
    "inventory bad revision": {
        "rental_inventory": {**_room_offer_payload(), "expected_revision": "oops"}
    },
    "inventory infinite price": {
        "rental_inventory": _mutate(["offers", 0, "term_overrides", "price"], "Infinity")(
            _room_offer_payload()
        )
    },
    "update-only main_image_id": {"main_image_id": str(uuid.uuid4())},
    "update-only retained": {"retained_image_ids": [str(uuid.uuid4())]},
    "update-only metadata": {"images_metadata": [{"id": str(uuid.uuid4()), "name": "x"}]},
    "main_image url": {"main_image": "https://res.cloudinary.com/other/image/upload/x.jpg"},
    "main_image public id": {"main_image": "properties/images/someone-else"},
}


@pytest.mark.parametrize("extra", CREATE_INVALID.values(), ids=CREATE_INVALID.keys())
def test_property_create_rejects_malformed_inputs_without_writes(
    user, apartment_type, cairo_governorate, cairo_city, provider, extra
):
    client = _verified_client(user)
    response = client.post(
        reverse("property-create"),
        _create_body(apartment_type, cairo_governorate, cairo_city, **extra),
        format="json",
    )
    assert response.status_code == 400, response.content
    assert not Property.objects.exists() and not PropertyImage.objects.exists()
    assert provider.call_count == 0


def test_property_create_ignores_empty_update_only_keys(
    user, apartment_type, cairo_governorate, cairo_city, provider
):
    client = _verified_client(user)
    response = client.post(
        reverse("property-create"),
        _create_body(
            apartment_type,
            cairo_governorate,
            cairo_city,
            main_image_id="",
            retained_image_ids=[],
            images_metadata=[],
        ),
        format="json",
    )
    assert response.status_code == 201, response.content


@pytest.mark.parametrize(
    "extra",
    [
        {"images_metadata": [{"id": "{image}", "name": []}]},
        {"images_metadata": [{"id": "{image}", "description": 5}]},
        {"images_metadata": [{"id": "not-a-uuid"}]},
        {"images_metadata": [{"id": "{image}"}, {"id": "{image}"}]},
        {"retained_image_ids": ["not-a-uuid"]},
        {"retained_image_ids": ["{image}", "{image}"]},
        {"retained_image_ids": [{"id": 1}]},
        {"main_image_id": "not-a-uuid"},
        {"main_image_name": ["x"]},
        {"amenities": [{"wifi": True}]},
    ],
    ids=repr,
)
def test_property_patch_rejects_malformed_metadata_without_writes(
    listing, user, provider, extra  # noqa: F811
):
    image = PropertyImage.objects.create(property=listing, image="properties/images/a", name="Kept")
    client = _verified_client(user)
    body = {
        key: (
            [
                {k: (str(image.id) if v == "{image}" else v) for k, v in item.items()}
                if isinstance(item, dict)
                else (str(image.id) if item == "{image}" else item)
                for item in value
            ]
            if isinstance(value, list)
            else value
        )
        for key, value in extra.items()
    }
    revision = Property.objects.get(pk=listing.pk).review_revision
    response = client.patch(reverse("property-detail", kwargs={"id": listing.id}), body, format="json")
    assert response.status_code == 400, response.content
    image.refresh_from_db()
    assert image.name == "Kept"
    assert Property.objects.get(pk=listing.pk).review_revision == revision


# ------------------------------------------------------------ image uploads


def _upload(client, listing, image, **extra):  # noqa: F811
    return client.post(
        reverse("property-image-upload", kwargs={"property_id": listing.id}),
        {"image": image, **extra},
        format="multipart",
    )


def _png_bytes(size=(16, 16), mode="RGB"):
    buffer = io.BytesIO()
    Image.new(mode, size).save(buffer, format="PNG")
    return buffer.getvalue()


INVALID_IMAGES = {
    "url string": lambda: "https://res.cloudinary.com/other/image/upload/x.jpg",
    "public id string": lambda: "properties/images/borrowed",
    "unsupported data uri": lambda: "data:text/html;base64," + base64.b64encode(b"<b>").decode(),
    "bad base64": lambda: "data:image/png;base64,@@@@",
    "not an image": lambda: _file(b"definitely not an image", "photo.jpg"),
    "html as jpg": lambda: _file(b"<!doctype html><script>x</script>", "photo.jpg"),
    "empty": lambda: _file(b"", "photo.jpg"),
    "truncated jpeg": lambda: _file(real_image("JPEG", (64, 64)).read()[:200], "photo.jpg"),
    "bmp format": lambda: real_image("BMP"),
    "pixel bomb": lambda: _file(_png_bytes((8000, 8000), "1"), "bomb.png"),
}


def _file(content, name):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content, content_type="image/jpeg")


@pytest.mark.parametrize("factory", INVALID_IMAGES.values(), ids=INVALID_IMAGES.keys())
def test_invalid_listing_images_fail_before_reservation_or_provider(
    listing, user, provider, factory  # noqa: F811
):
    client = _verified_client(user)
    image = factory()
    response = client.post(
        reverse("property-image-upload", kwargs={"property_id": listing.id}),
        {"image": image},
        format="multipart" if not isinstance(image, str) else "json",
    )
    assert response.status_code == 400, response.content
    assert not IdempotencyRecord.objects.exists()
    assert not listing.images.exists()
    assert provider.call_count == 0


@pytest.mark.parametrize(
    "factory",
    [
        lambda: real_image("JPEG"),
        lambda: real_image("PNG"),
        lambda: real_image("WEBP"),
        lambda: "data:image/png;base64," + base64.b64encode(_png_bytes()).decode(),
    ],
    ids=["jpeg", "png", "webp", "base64-png"],
)
def test_valid_listing_images_still_upload(listing, user, provider, factory):  # noqa: F811
    client = _verified_client(user)
    image = factory()
    response = client.post(
        reverse("property-image-upload", kwargs={"property_id": listing.id}),
        {"image": image, "name": "Room"},
        format="multipart" if not isinstance(image, str) else "json",
    )
    assert response.status_code == 201, response.content
    assert listing.images.count() == 1 and provider.call_count == 1


def test_native_heic_listing_image_still_uploads(listing, user, provider):  # noqa: F811
    from pillow_heif import from_pillow

    buffer = io.BytesIO()
    from_pillow(Image.new("RGB", (32, 24), (10, 20, 30))).save(buffer, format="HEIF")
    response = _upload(_verified_client(user), listing, _file(buffer.getvalue(), "IMG_0001.HEIC"))
    assert response.status_code == 201, response.content


# ------------------------------------------------------------------ video


def test_listing_video_is_decoded_and_measured(
    user, apartment_type, cairo_governorate, cairo_city, provider
):
    client = _verified_client(user)
    response = client.post(
        reverse("property-create"),
        _create_body(
            apartment_type, cairo_governorate, cairo_city, video=real_mp4(3), video_duration=40
        ),
        format="multipart",
    )
    assert response.status_code == 201, response.content
    # The decoded duration wins over the client's claim.
    assert response.json()["data"]["video_duration"] == 3


@pytest.mark.parametrize(
    "video",
    [
        lambda: _file(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64, "fake.mp4"),
        lambda: _file(b"RIFF....AVI LIST", "clip.mp4"),
        lambda: _file(b"", "empty.mp4"),
        lambda: real_mp4(65, "long.mp4"),
    ],
    ids=["ftyp-only garbage", "wrong signature", "empty", "over 60 seconds"],
)
def test_invalid_listing_videos_fail_before_provider(
    user, apartment_type, cairo_governorate, cairo_city, provider, video
):
    client = _verified_client(user)
    response = client.post(
        reverse("property-create"),
        _create_body(apartment_type, cairo_governorate, cairo_city, video=video()),
        format="multipart",
    )
    assert response.status_code == 400, response.content
    assert not Property.objects.exists() and provider.call_count == 0


def test_oversized_listing_video_rejected_by_declared_and_actual_bytes(
    user, apartment_type, cairo_governorate, cairo_city, provider
):
    with patch("core_apps.properties.listing_media.VIDEO_MAX_BYTES", 1024):
        response = _verified_client(user).post(
            reverse("property-create"),
            _create_body(apartment_type, cairo_governorate, cairo_city, video=real_mp4(2)),
            format="multipart",
        )
    assert response.status_code == 400, response.content
    assert not Property.objects.exists()


# --------------------------------------------------------------- capacity


def _fill(listing, count):  # noqa: F811
    PropertyImage.objects.bulk_create(
        [PropertyImage(property=listing, image=f"properties/images/{i}", position=i) for i in range(count)]
    )


def test_cover_replacement_at_capacity_is_a_controlled_validation(listing, user, provider):  # noqa: F811
    _fill(listing, 25)
    client = _verified_client(user)
    url = reverse("property-detail", kwargs={"id": listing.id})
    response = client.patch(url, {"main_image": real_image("JPEG")}, format="multipart")
    assert response.status_code == 400, response.content
    assert "main_image" in response.content.decode()
    assert listing.images.count() == 25
    # Replacing a defined record works: retain 24, add the new cover.
    keep = [str(i) for i in listing.images.order_by("position").values_list("id", flat=True)[:24]]
    response = client.patch(
        url,
        {"main_image": real_image("JPEG"), "retained_image_ids": __import__("json").dumps(keep)},
        format="multipart",
    )
    assert response.status_code == 200, response.content
    assert listing.images.count() == 25


def test_pending_reservations_hold_capacity_for_cover_and_gallery(listing, user, provider):  # noqa: F811
    _fill(listing, 24)
    IdempotencyRecord.objects.create(
        user=user,
        operation=f"property.image.upload:{listing.id}",
        request_key="pending-slot",
        fingerprint="0" * 64,
        request_subject_id=listing.id,
        recovery_status="pending",
        response_status=503,
        response_data={},
    )
    client = _verified_client(user)
    cover = client.patch(
        reverse("property-detail", kwargs={"id": listing.id}),
        {"main_image": real_image("JPEG")},
        format="multipart",
    )
    gallery = _upload(client, listing, real_image("PNG"))
    assert cover.status_code == 400 and gallery.status_code == 400
    assert listing.images.count() == 24 and provider.call_count == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_cover_and_gallery_never_exceed_cap(listing, user):  # noqa: F811
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock serialization is a PostgreSQL guarantee")
    _fill(listing, 23)
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    barrier = threading.Barrier(4)
    results = []

    def run(kind):
        from django.db import connections

        client = APIClient()
        client.force_authenticate(user)
        barrier.wait()
        try:
            if kind == "cover":
                response = client.patch(
                    reverse("property-detail", kwargs={"id": listing.id}),
                    {"main_image": real_image("JPEG")},
                    format="multipart",
                )
            else:
                response = _upload(client, listing, real_image("PNG"))
            results.append(response.status_code)
        finally:
            connections.close_all()

    with patch("cloudinary.uploader.upload", side_effect=provider_resource):
        threads = [threading.Thread(target=run, args=(k,)) for k in ("cover", "gallery", "cover", "gallery")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    assert listing.images.count() == 25
    # Exactly two writers fit; the losers get a controlled 400 (no 5xx).
    assert len(results) == 4 and results.count(400) == 2, results
