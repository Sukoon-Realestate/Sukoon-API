"""Real, tiny listing media for upload tests (generated, never stored)."""

import io
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

_VIDEO_CACHE = {}


def real_mp4(seconds=2, name="tour.mp4", *, codec="libx264"):
    """An H.264 MP4 of ``seconds`` length; skips when FFmpeg is unavailable."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("Real FFmpeg and FFprobe are required")
    key = (seconds, codec)
    if key not in _VIDEO_CACHE:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "clip.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-f", "lavfi",
                    "-i", "color=c=blue:s=64x48:r=5",
                    "-c:v", codec, "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-t", str(seconds), str(path),
                ],
                check=True,
                capture_output=True,
            )
            _VIDEO_CACHE[key] = path.read_bytes()
    return SimpleUploadedFile(name, _VIDEO_CACHE[key], content_type="video/mp4")


def real_image(fmt="JPEG", size=(32, 24), name=None):
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buffer, format=fmt)
    extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "BMP": "bmp"}[fmt]
    return SimpleUploadedFile(
        name or f"photo.{extension}",
        buffer.getvalue(),
        content_type=f"image/{extension if extension != 'jpg' else 'jpeg'}",
    )
