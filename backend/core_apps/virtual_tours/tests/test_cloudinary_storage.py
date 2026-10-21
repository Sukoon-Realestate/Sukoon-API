import io
import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from core_apps.virtual_tours import cloudinary_storage as cloud, storage
from core_apps.virtual_tours.errors import TourError


@pytest.fixture
def private_cloud(settings):
    settings.VIRTUAL_TOUR_STORAGE_PROVIDER = "cloudinary"
    settings.VIRTUAL_TOUR_CLOUDINARY_PREFIX = "tour-test"
    objects, calls = {}, []

    def upload(content, **options):
        assert options["type"] == "authenticated"
        assert options["resource_type"] == "raw"
        assert options["overwrite"] is False
        value = content.read()
        identity = options["public_id"]
        objects.setdefault(identity, value)
        calls.append(identity)
        return {
            "public_id": identity,
            "bytes": len(objects[identity]),
            "type": "authenticated",
        }

    def download(identity, maximum):
        value = objects[identity]
        assert len(value) <= maximum
        return value

    with patch.object(
        cloud.cloudinary.uploader, "upload", side_effect=upload
    ), patch.object(cloud, "download", side_effect=download):
        yield objects, calls


def test_large_source_survives_cache_loss_and_commits_manifest_last(private_cloud):
    objects, calls = private_cloud
    content = b"a" * (cloud.CHUNK_BYTES + 179)
    key, size, digest = storage.write_blob([content], len(content))
    assert size == len(content)
    assert len(objects) == 3
    assert calls[-1].endswith("/manifest")
    assert max(map(len, objects.values())) <= cloud.CHUNK_BYTES
    storage.path(key).unlink()
    assert storage.read_path(key).read_bytes() == content
    assert storage.path(key).stat().st_mode & 0o777 == 0o600


def test_tile_survives_cache_loss_without_public_media_url(private_cloud):
    objects, _ = private_cloud
    key = "a" * 32
    directory = storage.path(key)
    directory.mkdir()
    tile = directory / "f_0_0_0.jpg"
    tile.write_bytes(b"private tile")
    storage.persist_tiles(key)
    tile.unlink()
    assert storage.read_path(key, tile.name).read_bytes() == b"private tile"
    assert list(objects) == ["tour-test/" + key + "/f_0_0_0.jpg"]


def test_corruption_never_becomes_a_cached_asset(private_cloud):
    objects, _ = private_cloud
    key, _, _ = storage.write_blob([b"original"], 10)
    storage.path(key).unlink()
    part = next(k for k in objects if "/part-" in k)
    objects[part] = b"modified"
    with pytest.raises(TourError, match="integrity"):
        storage.read_path(key)
    assert not storage.path(key).exists()
    assert not list(storage.root().glob("*.pending"))


def test_partial_upload_has_no_committed_manifest_or_local_success(settings):
    settings.VIRTUAL_TOUR_STORAGE_PROVIDER = "cloudinary"
    with patch.object(
        cloud, "upload", side_effect=RuntimeError("provider secret details")
    ):
        with pytest.raises(TourError, match="Private storage is unavailable") as error:
            storage.write_blob([b"source"], 10)
    assert "secret" not in str(error.value)
    assert not list(storage.root().iterdir())


def test_manifest_cannot_supply_a_download_url_or_cross_namespace(private_cloud):
    objects, _ = private_cloud
    key, _, _ = storage.write_blob([b"source"], 10)
    storage.path(key).unlink()
    manifest = cloud.object_id(key, "manifest")
    objects[manifest] = json.dumps(
        {
            "version": 1,
            "bytes": 6,
            "parts": [{"bytes": 6, "sha256": "https://untrusted.invalid/private"}],
        }
    ).encode()
    with pytest.raises(TourError, match="manifest"):
        storage.read_path(key)


def test_cleanup_only_removes_old_unreferenced_tour_assets(settings):
    settings.VIRTUAL_TOUR_CLOUDINARY_PREFIX = "tour-test"
    keep, orphan, recent = "a" * 32, "b" * 32, "c" * 32
    resources = [
        {"public_id": f"tour-test/{key}/manifest", "created_at": created}
        for key, created in [
            (keep, "2020-01-01T00:00:00Z"),
            (orphan, "2020-01-01T00:00:00Z"),
            (recent, "2026-10-21T00:00:00Z"),
            ("unrelated", "2020-01-01T00:00:00Z"),
        ]
    ]
    threshold = datetime(2026, 10, 20, tzinfo=timezone.utc).timestamp()
    with patch.object(
        cloud.cloudinary.api, "resources", return_value={"resources": resources}
    ), patch.object(cloud.cloudinary.uploader, "destroy") as destroy:
        assert cloud.sweep({keep}, threshold) == 1
    destroy.assert_called_once_with(
        f"tour-test/{orphan}/manifest", resource_type="raw", type="authenticated"
    )


def test_download_is_signed_short_lived_and_bounded():
    response = type(
        "Response",
        (),
        {
            "status_code": 200,
            "__enter__": lambda s: s,
            "__exit__": lambda *a: None,
            "raise_for_status": lambda s: None,
            "iter_content": lambda s, size: iter([b"abc", b"def"]),
        },
    )()
    with patch.object(
        cloud.cloudinary.utils,
        "private_download_url",
        return_value="https://api.cloudinary.com/private",
    ) as signed, patch.object(cloud.requests, "get", return_value=response):
        with pytest.raises(TourError, match="exceeds"):
            cloud.download("tour-test/server-owned/manifest", 5)
    options = signed.call_args.kwargs
    assert options["type"] == "authenticated"
    assert options["resource_type"] == "raw"
    assert 0 <= options["expires_at"] - cloud.time.time() <= 60
