import pytest
from unittest.mock import patch
from rest_framework.test import APIRequestFactory
from core_apps.properties.models import Property, PropertyImage, SavedProperty
from core_apps.properties.services.public_access import public_properties
from core_apps.properties.search import PropertySearchFilter
from core_apps.properties.services.search_document import normalize
from rest_framework.request import Request

pytestmark = pytest.mark.django_db


@pytest.fixture
def listing(user, apartment_type, cairo_governorate, cairo_city):
    return Property.objects.create(
        owner=user,
        title="Garden room",
        description="غرفة هادئة مفروشة",
        property_type=apartment_type,
        governorate=cairo_governorate,
        city=cairo_city,
        district="مدينة نصر",
        price=3000,
        is_furnished=True,
        has_wifi=True,
        status="verified",
        bedrooms=2,
        bathrooms=1,
        area=80,
    )


def test_publication_is_authoritative(listing, auth_client):
    assert public_properties().filter(pk=listing.pk).exists()
    for status in ["under_review", "needs_revision", "hidden"]:
        listing.status, listing.is_verified = status, True
        listing.save()
        assert not public_properties().filter(pk=listing.pk).exists()
        # The owner can preview the same identity.
        assert auth_client.get(f"/api/v1/properties/{listing.id}/").status_code == 200


def test_search_partial_typo_and_description(listing):
    factory = APIRequestFactory()
    for text in ["gard", "gardeen", "اوضة مفروشة فيها واي فاي"]:
        request = Request(factory.get("/", {"search": text}))
        found = PropertySearchFilter().filter_queryset(
            request, public_properties(), None
        )
        assert list(found.values_list("pk", flat=True)) == [listing.pk]
    request = Request(factory.get("/", {"search": "بدون واي فاي"}))
    assert (
        not PropertySearchFilter()
        .filter_queryset(request, public_properties(), None)
        .exists()
    )


def test_normalization_does_not_change_display(listing):
    assert normalize("أُوضة ــ") == "غرفه"
    listing.refresh_from_db()
    assert listing.description == "غرفة هادئة مفروشة"


def test_photo_order_survives_and_rejects_foreign_ids(listing, auth_client):
    images = [
        PropertyImage.objects.create(property=listing, image=f"sample-{i}", position=i)
        for i in range(5)
    ]
    listing.refresh_from_db()
    order = [str(images[-1].id), *[str(x.id) for x in images[:-1]]]
    response = auth_client.patch(
        f"/api/v1/properties/{listing.id}/images/order/",
        {
            "image_ids": order,
            "main_image_id": order[0],
            "expected_revision": listing.media_revision,
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    assert list(listing.images.order_by("position").values_list("id", flat=True)) == [
        images[-1].id,
        *[x.id for x in images[:-1]],
    ]
    listing.refresh_from_db()
    assert str(listing.main_image) == str(images[-1].image)
    invalid = auth_client.patch(
        f"/api/v1/properties/{listing.id}/images/order/",
        {
            "image_ids": order[:-1],
            "main_image_id": order[0],
            "expected_revision": listing.media_revision,
        },
        format="json",
    )
    assert invalid.status_code == 400


def test_hidden_listing_is_not_exposed_by_saved_or_image_endpoints(
    listing, auth_client
):
    from rest_framework.test import APIClient

    SavedProperty.objects.create(user=listing.owner, property=listing)
    image = PropertyImage.objects.create(property=listing, image="sample")
    visitor = APIClient()
    assert visitor.get(f"/api/v1/properties/images/{image.id}/").status_code == 200
    listing.status = "under_review"
    listing.save(update_fields=["status"])
    assert visitor.get(f"/api/v1/properties/{listing.id}/").status_code == 404
    assert visitor.get(f"/api/v1/properties/images/{image.id}/").status_code == 404
    response = auth_client.get("/api/v1/properties/saved/")
    assert response.status_code == 200
    payload = response.data
    if isinstance(payload, dict):
        payload = payload.get("data", payload)
    if isinstance(payload, dict):
        payload = payload.get("results", payload)
    assert payload == []
    assert auth_client.get(f"/api/v1/properties/images/{image.id}/").status_code == 200


def test_deleted_image_cannot_return_through_stale_photo_order(listing, auth_client):
    images = [
        PropertyImage.objects.create(property=listing, image=f"sample-{i}", position=i)
        for i in range(2)
    ]
    listing.refresh_from_db()
    old_revision = listing.media_revision
    response = auth_client.delete(f"/api/v1/properties/images/{images[0].id}/")
    assert response.status_code == 204
    listing.refresh_from_db()
    assert listing.media_revision > old_revision
    stale = auth_client.patch(
        f"/api/v1/properties/{listing.id}/images/order/",
        {
            "image_ids": [str(image.id) for image in images],
            "main_image_id": str(images[0].id),
            "expected_revision": old_revision,
        },
        format="json",
    )
    assert stale.status_code == 400
    assert not listing.images.filter(pk=images[0].pk).exists()


def test_media_serializer_preserves_order_and_reuses_prefetched_images(
    listing, django_assert_num_queries
):
    from core_apps.properties.serializers import PropertyDetailSerializer

    for i in range(3):
        PropertyImage.objects.create(
            property=listing, image=f"sample-{i}", position=2 - i
        )
    listing = Property.objects.prefetch_related("images").get(pk=listing.pk)
    serializer = PropertyDetailSerializer()
    with django_assert_num_queries(0):
        assert serializer.get_main_image_id(listing) == str(
            max(listing.images.all(), key=lambda image: image.pk).id
        )
        assert len(serializer.get_images(listing)) == 3
        serializer.get_main_image_name(listing)
        serializer.get_main_image_description(listing)
