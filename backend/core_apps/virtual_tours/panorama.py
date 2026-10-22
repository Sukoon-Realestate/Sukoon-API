"""Tiled cubemaps with bounded per-tile memory and metadata-free JPEG output."""

import math
import os
import uuid
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from django.conf import settings
from .errors import TourError, require
from .storage import path, read_path, persist_tiles

FACES = ("f", "b", "l", "r", "u", "d")
LEVELS = (512, 1024, 2048)


def cube_direction(face, u, v):
    one = np.ones_like(u)
    return {
        "f": (u, -v, -one),
        "b": (-u, -v, one),
        "l": (-one, -v, -u),
        "r": (one, -v, u),
        "u": (u, one, v),
        "d": (u, -one, -v),
    }[face]


def tile_pixels(pixels, face, size, tile_x, tile_y):
    # Bilinear interpolation creates several floating-point intermediates.
    # Bound those to 64 rows while preserving the exact projection and output.
    result = np.empty((512, 512, 3), dtype=np.uint8)
    for start in range(0, 512, 64):
        result[start : start + 64] = _tile_rows(
            pixels, face, size, tile_x, tile_y, start
        )
    return result


def _tile_rows(pixels, face, size, tile_x, tile_y, start):
    height, width, _ = pixels.shape
    u, v = np.meshgrid(
        (np.arange(512, dtype=np.float32) + tile_x * 512 + 0.5) / size * 2 - 1,
        (np.arange(start, start + 64, dtype=np.float32) + tile_y * 512 + 0.5)
        / size * 2 - 1,
    )
    x, y, z = cube_direction(face, u, v)
    sx = (np.arctan2(x, -z) / (2 * math.pi) + 0.5) * width - 0.5
    sy = (0.5 - np.arctan2(y, np.sqrt(x * x + z * z)) / math.pi) * height - 0.5
    sy = np.clip(sy, 0, height - 1)
    x0, y0 = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    a, b = pixels[y0, x0 % width], pixels[y0, (x0 + 1) % width]
    c, d = (
        pixels[np.minimum(y0 + 1, height - 1), x0 % width],
        pixels[np.minimum(y0 + 1, height - 1), (x0 + 1) % width],
    )
    return ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy).astype(
        np.uint8
    )


def process_panorama(asset, *, heartbeat=lambda: None):
    try:
        heartbeat()
        with Image.open(read_path(asset.blob)) as original:
            width, height = original.size
            require(
                original.format in ("JPEG", "PNG")
                and 4096 <= width <= 8192
                and width == 2 * height
                and width * height <= 35_000_000,
                "invalid_panorama",
                "Use a complete 2:1 JPEG/PNG sphere, 4096–8192 pixels wide.",
            )
            require(
                getattr(original, "n_frames", 1) == 1,
                "invalid_panorama",
                "Animated panoramas are not supported.",
            )
            require(
                original.getexif().get(274, 1) not in (5, 6, 7, 8),
                "invalid_panorama_orientation",
                "Normalize rotated panorama orientation before uploading.",
            )
            # JPEG draft decodes at the selected size; PNG is reduced before
            # creating RGB/NumPy copies. Small shared servers can select 4096.
            processing_width = max(
                4096, min(settings.VIRTUAL_TOUR_PROCESSING_WIDTH, 8192)
            )
            original.draft("RGB", (processing_width, processing_width // 2))
            original.thumbnail(
                (processing_width, processing_width // 2), Image.Resampling.LANCZOS
            )
            ImageOps.exif_transpose(original, in_place=True)
            image = original.convert("RGB")
            pixels = np.asarray(image)
            original.close()
            image.close()
            key = uuid.uuid4().hex
            directory = path(key)
            directory.mkdir(mode=0o700)
            for level, size in enumerate(LEVELS):
                for face in FACES:
                    for tile_y in range(size // 512):
                        for tile_x in range(size // 512):
                            heartbeat()
                            target = directory / f"{face}_{level}_{tile_x}_{tile_y}.jpg"
                            Image.fromarray(
                                tile_pixels(pixels, face, size, tile_x, tile_y)
                            ).save(target, "JPEG", quality=85)
                            os.chmod(target, 0o600)
            del pixels
            persist_tiles(key, progress=heartbeat)
            return {
                "blob": key,
                "type": "tiles",
                "media_type": "image/jpeg",
                "faces": list(FACES),
                "levels": list(LEVELS),
            }
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise TourError("invalid_panorama", "Panorama decoding failed.") from exc
