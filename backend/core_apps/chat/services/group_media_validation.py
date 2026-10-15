"""Inspect bytes, not extensions or caller-supplied MIME/duration."""

import io
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from django.conf import settings
from rest_framework.exceptions import ValidationError
from .group_limits import ChatUnavailable, limits


def inspect_image(path):
    policy = limits()
    try:
        with Image.open(path) as source:
            if (
                source.format not in {"JPEG", "PNG", "WEBP"}
                or getattr(source, "n_frames", 1) != 1
            ):
                raise ValueError("Unsupported image format")
            if source.width * source.height > policy["image_max_pixels"]:
                raise ValueError("Image dimensions exceed the limit")
            source.verify()
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((policy["image_max_edge"], policy["image_max_edge"]))
            clean = Image.new("RGB", image.size)
            clean.paste(image)
            content, thumbnail = io.BytesIO(), io.BytesIO()
            clean.save(content, "JPEG", quality=88)
            width, height = clean.size
            clean.thumbnail((480, 480))
            clean.save(thumbnail, "JPEG", quality=80)
            return (
                content.getvalue(),
                thumbnail.getvalue(),
                {
                    "mime_type": "image/jpeg",
                    "width": width,
                    "height": height,
                    "duration_ms": None,
                },
            )
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValidationError(
            {
                "file": "Supply a valid, non-animated JPEG, PNG or WebP within the image limits."
            }
        ) from exc


def inspect_voice(path):
    try:
        command = [
            getattr(settings, "CHAT_FFPROBE", "ffprobe"),
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, timeout=15, check=True)
        data = json.loads(result.stdout)
        streams = data["streams"]
        audio = [s for s in streams if s.get("codec_type") == "audio"]
        if len(streams) != 1 or len(audio) != 1 or audio[0].get("codec_name") != "aac":
            raise ValueError()
        if "mp4" not in data["format"].get("format_name", "").split(","):
            raise ValueError()
        seconds = float(audio[0].get("duration", data["format"].get("duration")))
        if not math.isfinite(seconds):
            raise ValueError()
        duration = round(seconds * 1000)
        if (
            not limits()["voice_min_duration_ms"]
            <= duration
            <= limits()["voice_max_duration_ms"]
        ):
            raise ValueError()
        # A successful demux alone is insufficient: require the audio to decode.
        subprocess.run(
            [
                getattr(settings, "CHAT_FFMPEG", "ffmpeg"),
                "-v",
                "error",
                "-xerror",
                "-protocol_whitelist",
                "file,pipe",
                "-i",
                str(path),
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            timeout=20,
            check=True,
        )
        return (
            Path(path).read_bytes(),
            None,
            {
                "mime_type": "audio/mp4",
                "duration_ms": duration,
                "width": None,
                "height": None,
            },
        )
    except FileNotFoundError:
        raise ChatUnavailable("Voice verification is unavailable.")
    except (ValueError, KeyError, TypeError, subprocess.SubprocessError):
        raise ValidationError(
            {"file": "Supply a valid AAC/M4A voice note within the duration limit."}
        )
