import hashlib
import io
import shutil
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from core_apps.common.private_storage import PrivateStorageUnavailable
from core_apps.support.models import TicketAttachment
from core_apps.support.storage import SupportPrivateStorage
from core_apps.virtual_tours.errors import TourError
from .test_private_attachments import ticket_with_image

pytestmark = pytest.mark.django_db


@pytest.fixture
def durable(settings, tmp_path, monkeypatch):
    settings.SUPPORT_PRIVATE_STORAGE_PROVIDER = "cloudinary"
    settings.SUPPORT_PRIVATE_MEDIA_ROOT = tmp_path / "cache"
    objects = {}

    def persist(key, source, *, prefix):
        objects[(prefix, key)] = source.read_bytes()

    def materialize(key, target, *, prefix, maximum):
        if (prefix, key) not in objects:
            raise TourError("resource_missing", "missing", 404)
        content = objects[(prefix, key)]
        assert len(content) <= maximum
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    from core_apps.virtual_tours import cloudinary_storage

    monkeypatch.setattr(cloudinary_storage, "persist", persist)
    monkeypatch.setattr(cloudinary_storage, "materialize", materialize)
    monkeypatch.setattr(cloudinary_storage, "remove", lambda key, *, prefix: objects.pop((prefix, key), None))
    return objects


def test_private_original_survives_cache_loss_and_read_still_requires_permission(durable, user, auth_client, settings):
    item = TicketAttachment.objects.get(message__ticket=ticket_with_image(user))
    original = item.private_file.read()
    item.private_file.close()
    shutil.rmtree(settings.SUPPORT_PRIVATE_MEDIA_ROOT)
    response = auth_client.get(item.file_url, {"workspace": "owner"})
    assert response.status_code == 404
    assert not Path(settings.SUPPORT_PRIVATE_MEDIA_ROOT).exists()
    response = auth_client.get(item.file_url, {"workspace": "tenant"})
    assert response.status_code == 200
    assert b"".join(response.streaming_content).startswith(b"\xff\xd8")
    assert Path(item.private_file.path).read_bytes() == original
    assert list(durable)[0][0] == "sokoun-support-private"


def test_backup_failure_is_not_a_successful_ticket(durable, user, monkeypatch):
    from core_apps.virtual_tours import cloudinary_storage

    def fail(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(cloudinary_storage, "persist", fail)
    with pytest.raises(PrivateStorageUnavailable):
        ticket_with_image(user)
    assert not TicketAttachment.objects.exists()


def test_backfill_is_non_destructive_resumable_and_detects_corruption(durable, user, settings):
    settings.SUPPORT_PRIVATE_STORAGE_PROVIDER = "local"
    item = TicketAttachment.objects.get(message__ticket=ticket_with_image(user))
    original = Path(item.private_file.path).read_bytes()
    settings.SUPPORT_PRIVATE_STORAGE_PROVIDER = "cloudinary"
    call_command("backfill_support_private_storage", stdout=io.StringIO())
    assert not durable
    for _ in range(2):
        output = io.StringIO()
        call_command("backfill_support_private_storage", apply=True, stdout=output)
        assert hashlib.sha256(original).hexdigest() in output.getvalue()
    assert len(durable) == 1
    durable[next(iter(durable))] = b"damaged"
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("backfill_support_private_storage", apply=True, stdout=io.StringIO())
    assert Path(item.private_file.path).read_bytes() == original


def test_private_storage_never_returns_public_url_or_accepts_path_traversal(durable):
    storage = SupportPrivateStorage()
    with pytest.raises(NotImplementedError):
        storage.url("a.png")
    from django.core.exceptions import SuspiciousFileOperation

    with pytest.raises(SuspiciousFileOperation):
        storage.open("../outside")
    name = storage.save("original.png", ContentFile(b"original bytes"))
    with pytest.raises(ValueError):
        storage.open(name, "wb")


def test_corrupt_local_cache_is_not_delivered(durable, user, auth_client):
    item = TicketAttachment.objects.get(message__ticket=ticket_with_image(user))
    assert item.content_sha256
    Path(item.private_file.path).write_bytes(b"damaged")
    response = auth_client.get(item.file_url, {"workspace": "tenant"})
    assert response.status_code == 503


def test_backfill_preserves_missing_legacy_record(durable, user, auth_client):
    from django.core.management.base import CommandError
    from core_apps.support.services import create_ticket

    ticket = create_ticket(user, "tenant", "other", "Legacy QA", "Missing original")
    item = TicketAttachment.objects.create(
        message=ticket.messages.first(), name="missing.png",
        file="support/missing-original.png",
    )
    with pytest.raises(CommandError):
        call_command("backfill_support_private_storage", apply=True, stdout=io.StringIO())
    item.refresh_from_db()
    assert item.file.name == "support/missing-original.png"
    assert not item.private_file and not item.content_sha256
    assert not durable
    assert auth_client.get(item.file_url, {"workspace": "tenant"}).status_code == 404


def test_backfill_does_not_bind_bytes_from_a_replaced_legacy_reference(
    durable, user, monkeypatch, settings, tmp_path
):
    from django.core.management.base import CommandError
    from core_apps.support.services import create_ticket
    from .test_private_attachments import upload

    settings.MEDIA_ROOT = tmp_path / "legacy"
    ticket = create_ticket(user, "tenant", "other", "Legacy QA", "Concurrent repair")
    original = upload().read()
    item = TicketAttachment.objects.create(
        message=ticket.messages.first(), name="original.png",
        file=ContentFile(original, name="original.png"),
    )
    old_name = item.file.name
    verify = SupportPrivateStorage.ensure_remote

    def replace_during_backup(storage, name):
        digest = verify(storage, name)
        TicketAttachment.objects.filter(pk=item.pk).update(file="support/repaired.png")
        return digest

    monkeypatch.setattr(SupportPrivateStorage, "ensure_remote", replace_during_backup)
    with pytest.raises(CommandError):
        call_command("backfill_support_private_storage", apply=True, stdout=io.StringIO())
    item.refresh_from_db()
    assert item.file.name == "support/repaired.png"
    assert not item.private_file and not item.content_sha256
    assert item.file.storage.open(old_name, "rb").read() == original
