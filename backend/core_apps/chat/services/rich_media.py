"""Bounded private file/video inspection and persistent voice/location metadata."""

import array
import json
import math
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from django.conf import settings
from rest_framework.exceptions import ValidationError
from .group_limits import ChatUnavailable, limits
from .group_media_process import codec_environment


def original_name(value):
    name = str(value or "attachment").replace("\\", "/").split("/")[-1]
    name = "".join(c for c in name if not unicodedata.category(c).startswith("C"))
    return name.strip(" .")[:255] or "attachment"


def validate_waveform(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 96:
        raise ValidationError({"waveform": "Supply between 1 and 96 audio levels."})
    if any(
        type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
        for v in value
    ):
        raise ValidationError(
            {"waveform": "Audio levels must be finite values between zero and one."}
        )
    return [round(float(v), 4) for v in value]


def validate_location(value):
    if not isinstance(value, dict) or set(value) - {
        "latitude",
        "longitude",
        "accuracy_m",
    }:
        raise ValidationError({"location": "Supply a current coordinate pair."})
    result = {}
    for key, low, high in (("latitude", -90, 90), ("longitude", -180, 180)):
        coordinate = value.get(key)
        if (
            type(coordinate) not in (int, float)
            or not math.isfinite(coordinate)
            or not low <= coordinate <= high
        ):
            raise ValidationError({"location": "Invalid coordinates."})
        result[key] = round(float(coordinate), 7)
    accuracy = value.get("accuracy_m")
    if accuracy is not None:
        if (
            type(accuracy) not in (int, float)
            or not math.isfinite(accuracy)
            or not 0 <= accuracy <= 100000
        ):
            raise ValidationError({"location": "Invalid location accuracy."})
        result["accuracy_m"] = round(float(accuracy), 1)
    return result


def _run(program, arguments, *, timeout=30):
    binary = getattr(settings, "CHAT_" + program.upper(), program)
    try:
        return subprocess.run(
            [binary, "-v", "error", "-protocol_whitelist", "file,pipe", *arguments],
            check=True,
            capture_output=True,
            timeout=timeout,
            env=codec_environment(binary),
        ).stdout
    except FileNotFoundError as exc:
        raise ChatUnavailable("Media verification is unavailable.") from exc
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 127:
            raise ChatUnavailable("Media verification is unavailable.") from exc
        raise ValidationError({"file": "This media cannot be decoded."}) from exc
    except subprocess.TimeoutExpired as exc:
        raise ValidationError({"file": "Media processing exceeded the limit."}) from exc


def voice_waveform(path):
    raw = _run(
        "ffmpeg",
        [
            "-i",
            str(path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "8000",
            "-t",
            "121",
            "-f",
            "s16le",
            "pipe:1",
        ],
    )
    values = array.array("h", raw)
    if sys.byteorder != "little":
        values.byteswap()
    count = min(96, len(values))
    if not count:
        return [0.0]
    result = []
    for i in range(count):
        window = values[i * len(values) // count : (i + 1) * len(values) // count]
        peak = max(abs(v) for v in window) / 32768
        result.append(
            round(max(0, min(1, (20 * math.log10(peak) + 60) / 60)) if peak else 0.0, 4)
        )
    return result


def inspect_file(path):
    # Arbitrary files are opaque downloads. They are never executed or served inline.
    return (
        Path(path).read_bytes(),
        None,
        {
            "mime_type": "application/octet-stream",
            "width": None,
            "height": None,
            "duration_ms": None,
        },
    )


def inspect_video(path):
    try:
        info = json.loads(
            _run("ffprobe", ["-show_streams", "-show_format", "-of", "json", str(path)])
        )
        streams = info["streams"]
        video = [s for s in streams if s.get("codec_type") == "video"]
        if len(video) != 1 or video[0].get("codec_name") not in {
            "h264",
            "hevc",
            "mpeg4",
        }:
            raise ValueError()
        if any(s.get("codec_type") not in {"audio", "video", "data"} for s in streams):
            raise ValueError()
        if any(
            s.get("codec_name") != "aac"
            for s in streams
            if s.get("codec_type") == "audio"
        ):
            raise ValueError()
        seconds = float(info["format"]["duration"])
        width, height = int(video[0]["width"]), int(video[0]["height"])
        if (
            not math.isfinite(seconds)
            or not 0 < seconds * 1000 <= limits()["video_max_duration_ms"]
        ):
            raise ValueError()
        if not 0 < width * height <= limits()["image_max_pixels"]:
            raise ValueError()
        _run("ffmpeg", ["-xerror", "-i", str(path), "-f", "null", "-"], timeout=60)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "video.mp4"
            _run(
                "ffmpeg",
                [
                    "-i",
                    str(path),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0?",
                    "-c",
                    "copy",
                    "-map_metadata",
                    "-1",
                    "-movflags",
                    "+faststart",
                    str(output),
                ],
                timeout=60,
            )
            thumbnail = _run(
                "ffmpeg",
                [
                    "-i",
                    str(output),
                    "-frames:v",
                    "1",
                    "-vf",
                    "scale=480:480:force_original_aspect_ratio=decrease",
                    "-f",
                    "image2pipe",
                    "-vcodec",
                    "mjpeg",
                    "pipe:1",
                ],
            )
            return (
                output.read_bytes(),
                thumbnail,
                {
                    "mime_type": "video/mp4",
                    "width": width,
                    "height": height,
                    "duration_ms": round(seconds * 1000),
                },
            )
    except (ValueError, KeyError, TypeError) as exc:
        raise ValidationError(
            {
                "file": "Supply a supported MP4/MOV video within the size and duration limits."
            }
        ) from exc
