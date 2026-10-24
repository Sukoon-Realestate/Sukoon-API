from io import BytesIO
import pytest
from PIL import Image
from pillow_heif import register_heif_opener
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from core_apps.profiles.identity_media import IdentityImageField


@pytest.mark.parametrize(
    "fmt,extension",
    [
        ("JPEG", "jpg"),
        ("PNG", "png"),
        ("WEBP", "webp"),
        ("GIF", "gif"),
        ("BMP", "bmp"),
        ("TIFF", "tiff"),
        ("AVIF", "avif"),
        ("HEIF", "heic"),
    ],
)
def test_supported_image_is_normalized_without_metadata(fmt, extension):
    register_heif_opener()
    out = BytesIO()
    image = Image.new("RGB", (64, 40), "white")
    image.save(out, format=fmt)
    uploaded = SimpleUploadedFile(
        "identity." + extension, out.getvalue(), content_type="application/octet-stream"
    )
    normalized = IdentityImageField().run_validation(uploaded)
    result = Image.open(normalized)
    assert result.format == "JPEG"
    assert result.size == (64, 40)
    assert not result.getexif()
    assert normalized.content_type == "image/jpeg"


@pytest.mark.parametrize("payload", [b"%PDF-1.7 fake", b"<svg/>", b"not a JPEG"])
def test_non_images_are_rejected(payload):
    with pytest.raises(ValidationError):
        IdentityImageField().run_validation(
            SimpleUploadedFile("id.jpg", payload, content_type="image/jpeg")
        )


def test_animation_keeps_first_frame():
    out = BytesIO()
    Image.new("RGB", (20, 20), "red").save(
        out,
        format="GIF",
        save_all=True,
        append_images=[Image.new("RGB", (20, 20), "blue")],
        duration=50,
    )
    result = Image.open(
        IdentityImageField().run_validation(
            SimpleUploadedFile("id.gif", out.getvalue())
        )
    )
    assert getattr(result, "n_frames", 1) == 1
    assert result.getpixel((0, 0))[0] > 240
