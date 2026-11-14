"""Missing/corrupt historical advertising bytes require explicit original recovery."""

import hashlib
from io import StringIO
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

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


def test_explicit_restore_requires_exact_original_bytes_and_apply(user, tmp_path):
    ad = ads(user, 1)[0]
    media = ad.media
    content = b"original verified upload bytes"
    media.banner.name = f"test/{uuid4()}.png"
    media.size_bytes = len(content)
    media.sha256 = hashlib.sha256(content).hexdigest()
    media.save()
    source = tmp_path / "original.png"
    source.write_bytes(content)
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
    source.write_bytes(b"x" * len(content))
    with pytest.raises(CommandError, match="digest"):
        call_command("restore_advertising_media", str(ad.id), str(source), apply=True)
