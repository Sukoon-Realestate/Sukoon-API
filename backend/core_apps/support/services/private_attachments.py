"""Private, decoded image previews. Never expose a storage URL to the client."""

import io
import uuid
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError


def clean_image(stream):
    try:
        stream.seek(0)
        with Image.open(stream) as source:
            if (
                source.format not in {"JPEG", "PNG", "WEBP"}
                or getattr(source, "n_frames", 1) != 1
            ):
                raise ValueError()
            if source.width * source.height > 20_000_000:
                raise ValueError()
            source.verify()
        stream.seek(0)
        with Image.open(stream) as source:
            clean = ImageOps.exif_transpose(source).convert("RGB")
            clean.thumbnail((4096, 4096))
            output = io.BytesIO()
            clean.save(output, "JPEG", quality=90)
            if len(output.getvalue()) > 5 * 1024 * 1024:
                raise ValueError()
            return output.getvalue()
    except (
        ValueError,
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as error:
        raise ValidationError(
            {"attachments": "Supply a valid non-animated JPEG, PNG or WebP image."}
        ) from error


def store_image(message, upload):
    from core_apps.support.models import TicketAttachment

    clean_image(upload)
    upload.seek(0)
    content = upload.read()
    extension = upload.name.rsplit(".", 1)[-1].lower()
    return TicketAttachment.objects.create(
        message=message,
        name=upload.name,
        private_file=ContentFile(content, name=f"{uuid.uuid4().hex}.{extension}"),
    )
