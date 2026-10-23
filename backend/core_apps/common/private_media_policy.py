"""Shared inspection, never shared resource authorization."""

import hashlib
import io
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

IMAGE_MAX = 5 * 1024 * 1024
PDF_MAX = 25 * 1024 * 1024
VIDEO_MAX = 50 * 1024 * 1024
VIDEO_DURATION_MS = 300000
MIME_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "application/pdf": "pdf",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}


def policy(student=False):
    return {
        "schema_version": 2,
        "types": ["image", "pdf"] if student else ["image", "pdf", "video"],
        "image_max_bytes": IMAGE_MAX,
        "pdf_max_bytes": PDF_MAX,
        "video_max_bytes": VIDEO_MAX,
        "video_max_duration_ms": VIDEO_DURATION_MS,
        "pdf_max_pages": 500,
    }


def maximum(mime):
    if isinstance(mime, str) and mime.startswith("image/"):
        return IMAGE_MAX
    return PDF_MAX if mime == "application/pdf" else VIDEO_MAX


def inspect(content, mime, *, student=False, digest=None, deep=True):
    if mime not in MIME_EXTENSIONS or not 0 < len(content) <= maximum(mime):
        raise ValidationError(
            {"file": "Choose a supported file within its size limit."}
        )
    actual = hashlib.sha256(content).hexdigest()
    if digest is not None and actual != digest:
        raise ValidationError({"sha256": "Digest does not match the uploaded bytes."})
    meta = {"sha256": actual, "mime_type": mime, "size_bytes": len(content)}
    if student and mime.startswith("video/"):
        raise ValidationError({"file": "Student evidence accepts images and PDF only."})
    if not deep and not mime.startswith("image/"):
        if mime == "application/pdf" and not content.startswith(b"%PDF-"):
            raise ValidationError({"file": "Invalid PDF file."})
        if mime.startswith("video/") and content[4:8] != b"ftyp":
            raise ValidationError({"file": "Invalid video container."})
        return {**meta, "kind": "pdf" if mime == "application/pdf" else "video"}
    try:
        if mime.startswith("image/"):
            with Image.open(io.BytesIO(content)) as source:
                expected = {
                    "image/png": "PNG",
                    "image/jpeg": "JPEG",
                    "image/webp": "WEBP",
                }[mime]
                if (
                    source.format != expected
                    or getattr(source, "n_frames", 1) != 1
                    or source.width * source.height > 20_000_000
                ):
                    raise ValueError()
                source.verify()
            with Image.open(io.BytesIO(content)) as source:
                source.load()
                meta.update(kind="image", width=source.width, height=source.height)
        elif mime == "application/pdf":
            process = subprocess.run(
                [sys.executable, "-m", "core_apps.common.pdf_inspection"],
                input=content,
                capture_output=True,
                timeout=12,
                check=True,
            )
            meta.update(kind="pdf", **json.loads(process.stdout))
        else:
            if student:
                raise ValidationError(
                    {"file": "Student evidence accepts images and PDF only."}
                )
            from core_apps.chat.services.rich_media import _run

            with tempfile.TemporaryDirectory(prefix="sokoun-evidence-") as folder:
                path = Path(folder) / ("source." + MIME_EXTENSIONS[mime])
                path.write_bytes(content)
                info = json.loads(
                    _run(
                        "ffprobe",
                        ["-show_streams", "-show_format", "-of", "json", str(path)],
                    )
                )
                video = [
                    s for s in info.get("streams", []) if s.get("codec_type") == "video"
                ]
                duration = float(info["format"]["duration"]) * 1000
                if (
                    len(video) != 1
                    or not math.isfinite(duration)
                    or not 0 < duration <= VIDEO_DURATION_MS
                ):
                    raise ValueError()
                stream = video[0]
                if (
                    stream.get("codec_name") not in {"h264", "hevc", "mpeg4"}
                    or not 0 < stream["width"] * stream["height"] <= 20_000_000
                ):
                    raise ValueError()
                if not any(
                    x in info["format"].get("format_name", "").split(",")
                    for x in ("mp4", "mov")
                ):
                    raise ValueError()
                _run(
                    "ffmpeg",
                    ["-i", str(path), "-map", "0:v:0", "-f", "null", "-"],
                    timeout=90,
                )
                meta.update(
                    kind="video",
                    duration_ms=round(duration),
                    width=stream["width"],
                    height=stream["height"],
                )
    except (
        ValueError,
        KeyError,
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        subprocess.SubprocessError,
    ) as error:
        raise ValidationError(
            {
                "file": "The file is invalid, encrypted, or exceeds the processing limits."
            }
        ) from error
    return meta
