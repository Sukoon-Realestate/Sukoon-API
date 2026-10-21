import pytest
from core_apps.properties.models import (
    City,
    Governorate,
    PropertyType,
    Property,
    PropertyImage,
)


@pytest.fixture(autouse=True)
def tour_settings(settings, tmp_path):
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path / "tours")
    settings.VIRTUAL_TOUR_S3_BUCKET = ""
    settings.VIRTUAL_TOUR_STORAGE_PROVIDER = "s3"
    settings.VIRTUAL_TOUR_VIEWER_URL = "https://viewer.sokoun.test/tours/"
    settings.VIRTUAL_TOUR_KINDS = {
        k: {"read": True, "write": True} for k in ("panorama_360", "model_3d")
    }


@pytest.fixture
def property_obj(user):
    gov = Governorate.objects.create(name="Tour governorate", slug="tour-gov")
    city = City.objects.create(name="Tour city", slug="tour-city", governorate=gov)
    kind = PropertyType.objects.create(name="Tour apartment", slug="tour-apartment")
    prop = Property.objects.create(
        owner=user,
        title="Synthetic tour test listing",
        property_type=kind,
        governorate=gov,
        city=city,
        district="Test",
        status="verified",
        main_image="cover.jpg",
        video="video.mp4",
        video_duration=15,
    )
    for i in range(9):
        PropertyImage.objects.create(property=prop, image=f"photo-{i}.jpg")
    return prop
