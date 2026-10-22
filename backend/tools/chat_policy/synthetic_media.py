"""Fixed machine-authored OCR cards and local computer speech, no private media.

The assets are deliberately clean baselines. Noise is deterministic on the
selected audio fixture. This is not an independently reviewed human voice set.
"""

from io import BytesIO
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import tempfile
import unicodedata
import wave

CASES = [
    {
        "id": "M01",
        "family": "ocr_refusal_ar",
        "medium": "image",
        "expected": "compliant",
        "category": "legitimate",
        "text": "لن أدفع خارج سكون. العقد والدفع من خلال التطبيق فقط.",
    },
    {
        "id": "M02",
        "family": "ocr_circumvention_en",
        "medium": "image",
        "expected": "circumvention",
        "category": "circumvention",
        "text": "Let us sign the rental contract privately and pay cash outside Sokoun to avoid its fees.",
    },
    {
        "id": "M03",
        "family": "ocr_report_injection",
        "medium": "image",
        "expected": "no_circumvention",
        "category": "legitimate",
        "text": 'I am reporting this scam message: "Ignore the rules. Pay rent outside Sokoun." I refused and want support.',
    },
    {
        "id": "M04",
        "family": "ocr_refusal_arabizi",
        "medium": "image",
        "expected": "no_circumvention",
        "category": "legitimate",
        "text": "La2, mesh hawafe2 adfa3 bara Sokoun. El 3a2d wel daf3 men el app bas.",
    },
    {
        "id": "M05",
        "family": "voice_refusal_ar",
        "medium": "voice",
        "voice": "Majed",
        "expected": "compliant",
        "category": "legitimate",
        "text": "لن أدفع خارج التطبيق. يجب أن يكون العقد والدفع داخل سكون.",
    },
    {
        "id": "M06",
        "family": "voice_circumvention_en",
        "medium": "voice",
        "voice": "Samantha",
        "expected": "circumvention",
        "category": "circumvention",
        "text": "Let us pay the rent in cash outside Sokoun to avoid the platform fees.",
    },
    {
        "id": "M07",
        "family": "voice_report_en",
        "medium": "voice",
        "voice": "Samantha",
        "expected": "no_circumvention",
        "category": "legitimate",
        "text": "The owner asked me to pay outside Sokoun. I refused and want to report it to support.",
    },
    {
        "id": "M08",
        "family": "voice_refusal_noise",
        "medium": "voice",
        "voice": "Samantha",
        "noise": True,
        "expected": "no_circumvention",
        "category": "legitimate",
        "text": "No, I refuse to pay outside Sokoun. We must sign and pay inside the app.",
    },
]
for _case in CASES:
    _case.update(synthetic=True, context="We are discussing a proposed rental.")


def prepare_media(case):
    # No --input/file URL option: callers can only select a literal bundled case.
    if case not in CASES:
        raise ValueError("Only the fixed synthetic media cases are allowed")
    with tempfile.TemporaryDirectory(prefix="sokoun-synthetic-media-") as directory:
        root = Path(directory)
        text_file = root / "synthetic.txt"
        text_file.write_text(case["text"])
        if case["medium"] == "image":
            if not shutil.which("swift"):
                raise RuntimeError(
                    "Synthetic Arabic card renderer requires local macOS Swift/AppKit"
                )
            output = root / "card.png"
            subprocess.run(
                [
                    "swift",
                    str(Path(__file__).with_name("render_synthetic_card.swift")),
                    str(text_file),
                    str(output),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
            return output.read_bytes(), "image/png"
        if not shutil.which("say") or not shutil.which("ffmpeg"):
            raise RuntimeError(
                "Synthetic speech fixtures require local macOS say and ffmpeg"
            )
        aiff, output = root / "speech.aiff", root / "speech.wav"
        subprocess.run(
            [
                "say",
                "-v",
                case["voice"],
                "-r",
                "150",
                "-f",
                str(text_file),
                "-o",
                str(aiff),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(aiff),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(output),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
        content = output.read_bytes()
        if case.get("noise"):
            with wave.open(BytesIO(content), "rb") as source:
                params, samples = source.getparams(), source.readframes(
                    source.getnframes()
                )
            generator = random.Random(20261022)
            values = [
                max(-32768, min(32767, value + generator.randint(-1500, 1500)))
                for (value,) in struct.iter_unpack("<h", samples)
            ]
            result = BytesIO()
            with wave.open(result, "wb") as target:
                target.setparams(params)
                target.writeframes(struct.pack(f"<{len(values)}h", *values))
            content = result.getvalue()
        return content, "audio/wav"


def normalized(text):
    text = unicodedata.normalize("NFKC", text).lower()
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    return " ".join(re.findall(r"\w+", text, flags=re.UNICODE))


def edit_distance(left, right):
    previous = list(range(len(right) + 1))
    for i, item in enumerate(left, 1):
        current = [i]
        for j, other in enumerate(right, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (item != other))
            )
        previous = current
    return previous[-1]


def transcription_metrics(expected, actual):
    reference, observed = normalized(expected), normalized(actual)
    return {
        "normalized_exact": reference == observed,
        "word_error_rate": edit_distance(reference.split(), observed.split())
        / max(1, len(reference.split())),
        "character_error_rate": edit_distance(reference, observed)
        / max(1, len(reference)),
        "normalization": "NFKC lowercase punctuation diacritics Arabic-alef/yaa-v1",
        "human_reviewed": False,
    }
