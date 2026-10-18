import io
import uuid
from PIL import Image
import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import RentalAuditEvent
from core_apps.support.models import Ticket, TicketAttachment
from core_apps.support.services import create_ticket

pytestmark = pytest.mark.django_db


def upload():
    stream = io.BytesIO()
    Image.new("RGB", (8, 4), color="red").save(stream, "PNG")
    return SimpleUploadedFile("private.png", stream.getvalue(), "image/png")


def ticket_with_image(user):
    return create_ticket(
        user,
        "tenant",
        "other",
        "Private inquiry",
        "Sensitive issue for support.",
        [upload()],
    )


def test_private_image_requires_owner_workspace_or_current_audited_operator(
    auth_client, user, another_user, api_client
):
    ticket = ticket_with_image(user)
    attachment = TicketAttachment.objects.get(message__ticket=ticket)
    assert attachment.private_file and not attachment.file
    with pytest.raises(NotImplementedError):
        _ = attachment.private_file.url
    url = reverse("support-attachment", kwargs={"id": attachment.id})
    from rest_framework.test import APIClient

    assert APIClient().get(url).status_code == 401
    assert auth_client.get(url, {"workspace": "owner"}).status_code == 404
    response = auth_client.get(url, {"workspace": "tenant"})
    assert response.status_code == 200
    assert response["Content-Type"] == "image/jpeg"
    assert response["Cache-Control"] == "private, no-store"
    image = Image.open(io.BytesIO(b"".join(response.streaming_content)))
    assert image.size == (8, 4)
    api_client.force_authenticate(another_user)
    assert api_client.get(url, {"workspace": "tenant"}).status_code == 404
    another_user.is_staff = True
    another_user.save()
    staff = StaffProfile.objects.create(user=another_user, role_name="support")
    response = api_client.get(url)
    assert response.status_code == 200
    assert b"".join(response.streaming_content)
    assert (
        RentalAuditEvent.objects.filter(
            action="support.attachment_read", subject_id=attachment.id
        ).count()
        == 1
    )
    staff.is_active = False
    staff.save()
    another_user.refresh_from_db()
    assert api_client.get(url).status_code == 404


def test_invalid_image_and_replayed_upload_do_not_create_duplicate_files(
    auth_client, tmp_path, settings
):
    url = reverse("support-ticket-list-create")
    body = {
        "workspace": "tenant",
        "category": "other",
        "subject": "A private issue",
        "description": "Please review the evidence.",
    }
    bad = auth_client.post(
        url,
        {
            **body,
            "attachments": [
                SimpleUploadedFile("fake.png", b"not-an-image", "image/png")
            ],
        },
        format="multipart",
    )
    assert bad.status_code == 400
    assert not Ticket.objects.exists()
    key = str(uuid.uuid4())
    for _ in range(2):
        response = auth_client.post(
            url,
            {**body, "attachments": [upload()]},
            format="multipart",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        assert response.status_code == 201, response.data
    assert Ticket.objects.count() == TicketAttachment.objects.count() == 1
    files = [
        p
        for p in __import__("pathlib")
        .Path(settings.SUPPORT_PRIVATE_MEDIA_ROOT)
        .rglob("*")
        if p.is_file()
    ]
    assert len(files) == 1
    assert (
        "/support/attachments/" in response.data["messages"][0]["attachments"][0]["url"]
    )
    assert "/media/" not in response.data["messages"][0]["attachments"][0]["url"]


def test_legacy_migration_is_dry_run_and_verifies_original_before_removal(
    user, settings, tmp_path, django_capture_on_commit_callbacks
):
    settings.MEDIA_ROOT = tmp_path / "public"
    ticket = create_ticket(
        user, "tenant", "other", "Legacy evidence", "Preserve its original bytes."
    )
    original = upload().read()
    item = TicketAttachment.objects.create(
        message=ticket.messages.first(),
        name="legacy.png",
        file=ContentFile(original, name="legacy.png"),
    )
    legacy_name, storage = item.file.name, item.file.storage
    call_command("privatize_support_attachments", stdout=io.StringIO())
    item.refresh_from_db()
    assert not item.private_file and storage.exists(legacy_name)
    call_command("privatize_support_attachments", apply=True, stdout=io.StringIO())
    item.refresh_from_db()
    with item.private_file.open("rb") as copied:
        assert copied.read() == original
    assert storage.exists(legacy_name)
    with django_capture_on_commit_callbacks(execute=True):
        call_command(
            "privatize_support_attachments",
            apply=True,
            remove_public=True,
            stdout=io.StringIO(),
        )
    item.refresh_from_db()
    assert not item.file and item.private_file
    assert not storage.exists(legacy_name)


def test_legacy_removal_recovers_interruption_after_public_delete(
    user, settings, tmp_path, django_capture_on_commit_callbacks
):
    settings.MEDIA_ROOT = tmp_path / "public"
    ticket = create_ticket(
        user, "tenant", "other", "Legacy recovery", "Preserve original evidence."
    )
    original = upload().read()
    item = TicketAttachment.objects.create(
        message=ticket.messages.first(),
        name="legacy.png",
        file=ContentFile(original, name="interrupted.png"),
    )
    call_command("privatize_support_attachments", apply=True, stdout=io.StringIO())
    item.refresh_from_db()
    # Simulate storage deletion succeeding but the DB field clear not committing.
    item.file.storage.delete(item.file.name)
    assert item.file and item.private_file
    with django_capture_on_commit_callbacks(execute=True):
        call_command(
            "privatize_support_attachments",
            apply=True,
            remove_public=True,
            stdout=io.StringIO(),
        )
    item.refresh_from_db()
    assert not item.file
    with item.private_file.open("rb") as recovered:
        assert recovered.read() == original


def test_missing_legacy_and_private_evidence_is_not_silently_cleared(
    user, settings, tmp_path
):
    from django.core.management.base import CommandError

    settings.MEDIA_ROOT = tmp_path / "public"
    ticket = create_ticket(
        user, "tenant", "other", "Missing evidence", "Storage review is required."
    )
    item = TicketAttachment.objects.create(
        message=ticket.messages.first(), name="missing.png", file="support/missing.png"
    )
    with pytest.raises(CommandError, match="missing"):
        call_command(
            "privatize_support_attachments",
            apply=True,
            remove_public=True,
            stdout=io.StringIO(),
        )
    item.refresh_from_db()
    assert item.file and not item.private_file
