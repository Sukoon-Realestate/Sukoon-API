"""Missing/corrupt historical advertising bytes require explicit original recovery."""

import hashlib
from io import StringIO
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from core_apps.advertising.models import AdvertisementMedia
from core_apps.advertising.services_parts.ensure_media_persisted import (
    media_is_available,
)
from core_apps.advertising.tests.test_sprint04_performance import ads

pytestmark = [pytest.mark.django_db, pytest.mark.mvp_deferred]


def test_missing_historical_media_probe_never_writes_or_fabricates(user):
    ad = ads(user, 1)[0]
    ad.pk = ad.id = "85295dd1-f8bd-4c82-a903-9bdc3d90af98"
    media = AdvertisementMedia.objects.first()
    ad.media = media
    with patch.object(media.banner.storage, "exists", return_value=False), patch.object(
        media.banner.storage, "save"
    ) as save, patch.object(media.banner.storage, "delete") as delete:
        assert not media_is_available(ad)
    save.assert_not_called()
    delete.assert_not_called()


def test_missing_artwork_gets_leave_storage_and_metadata_untouched(user, auth_client):
    ad = ads(user, 1)[0]
    media = ad.media
    before = AdvertisementMedia.objects.filter(pk=media.pk).values().get()
    with patch.object(media.banner.storage, "exists", return_value=False), patch.object(
        media.banner.storage, "save", side_effect=AssertionError("GET wrote artwork")
    ), patch.object(
        media.banner.storage, "delete", side_effect=AssertionError("GET deleted artwork")
    ), patch.object(
        AdvertisementMedia, "save", side_effect=AssertionError("GET repaired metadata")
    ):
        assert auth_client.get(reverse("advertising:advertisement-media", args=[ad.id])).status_code == 404
        assert auth_client.get(reverse("advertising:owner-advertisement-detail", args=[ad.id])).status_code == 200
        assert auth_client.get(reverse("advertising:tenant-home")).status_code == 200
    assert AdvertisementMedia.objects.filter(pk=media.pk).values().get() == before


def test_explicit_restore_requires_exact_original_bytes_and_apply(user, tmp_path, caplog):
    ad = ads(user, 1)[0]
    media = ad.media
    content = b"original verified upload bytes"
    media.banner.name = f"test/{uuid4()}.png"
    media.size_bytes = len(content)
    media.sha256 = hashlib.sha256(content).hexdigest()
    media.save()
    source = tmp_path / "original.png"
    source.write_bytes(content)
    caplog.set_level("INFO", logger="core_apps.advertising.management.commands.restore_advertising_media")
    with patch.object(media.banner.storage, "exists", return_value=False), patch.object(
        media.banner.storage, "save", return_value=media.banner.name
    ) as save:
        call_command(
            "restore_advertising_media", str(ad.id), str(source), stdout=StringIO()
        )
        save.assert_not_called()
        call_command(
            "restore_advertising_media",
            str(ad.id),
            str(source),
            apply=True,
            stdout=StringIO(),
        )
        save.assert_called_once()
        assert save.call_args.args[1].read() == content
    audit = [record.getMessage() for record in caplog.records if "advertising_media_repair" in record.getMessage()]
    assert len(audit) == 2
    assert "applied=False" in audit[0]
    assert "applied=True" in audit[1]
    assert all(str(ad.id) in entry and media.sha256 in entry for entry in audit)
    assert all(str(source) not in entry and content.decode() not in entry for entry in audit)
    source.write_bytes(b"x" * len(content))
    with pytest.raises(CommandError, match="digest"):
        call_command("restore_advertising_media", str(ad.id), str(source), apply=True)
