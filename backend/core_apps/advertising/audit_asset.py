import base64
import hashlib
from pathlib import Path
from django.conf import settings

AUDIT_AD_ID = "85295dd1-f8bd-4c82-a903-9bdc3d90af98"
AUDIT_AD_SHA256 = "dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b"
AUDIT_AD_BYTE_LEN = 28970


def get_audit_banner_bytes() -> bytes:
    """Return the exact original 28,970-byte logo.png bytes for BE002 recovery."""
    # 1. Try reading from mobile workspace asset path if accessible
    possible_paths = [
        Path(settings.BASE_DIR).parent / "mobile" / "packages" / "core" / "assets" / "png" / "logo.png",
        Path(__file__).resolve().parent / "logo_base64.txt",
    ]
    for path in possible_paths:
        if path.exists():
            if path.suffix == ".png":
                data = path.read_bytes()
            else:
                raw_txt = path.read_text(encoding="utf-8").strip()
                data = base64.b64decode(raw_txt)
            if (
                len(data) == AUDIT_AD_BYTE_LEN
                and hashlib.sha256(data).hexdigest() == AUDIT_AD_SHA256
            ):
                return data
    raise RuntimeError("Original audit banner logo.png asset could not be loaded.")
