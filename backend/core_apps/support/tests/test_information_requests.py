import json
import os
from pathlib import Path
from uuid import uuid4
import pytest
from django.urls import reverse
from core_apps.admin_api.models import StaffProfile
from core_apps.support.models import TicketInformationRequest, TicketInformationEvent, TicketMessage
from core_apps.support.services import create_ticket
from core_apps.features.planning_models import PlanningEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def inquiry(user, another_user):
    another_user.is_staff = True
    another_user.save(update_fields=["is_staff"])
    StaffProfile.objects.create(user=another_user, role_name="support")
    return create_ticket(user, "tenant", "other", "Private MVP inquiry", "Please help with a property viewing."), another_user


def command(api, ticket, actor, action="request_information", **extra):
    api.force_authenticate(actor)
    ticket.refresh_from_db()
    body = {"action": action, "expected_revision": ticket.revision,
        "reason": "Please review this information request.", **extra}
    if action == "request_information": body.setdefault("prompt", "Which entrance did you use?")
    return api.post(reverse("admin-support-detail", args=[ticket.id]), body, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))


def answer(api, ticket, actor, row, key=None, **extra):
    api.force_authenticate(actor)
    return api.post(reverse("support-ticket-reply", args=[ticket.id]), {
        "body": "I used the north entrance.", "information_request_id": str(row.id),
        "information_revision": row.revision, **extra}, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


def test_answer_sent_is_not_staff_acceptance_and_unknown_ack_does_not_duplicate(api_client, user, inquiry):
    ticket, staff = inquiry
    created = command(api_client, ticket, staff)
    assert created.status_code == 200, created.data
    row = TicketInformationRequest.objects.get()
    key = str(uuid4())
    first = answer(api_client, ticket, user, row, key)
    assert first.status_code == 200, first.data
    assert first.data["information_requests"][0]["status"] == "answer_sent"
    assert answer(api_client, ticket, user, row, key).data == first.data
    assert TicketMessage.objects.filter(sender="user").count() == 2  # Initial message and one answer.
    receipt = api_client.get(reverse("support-reply-receipt", args=[ticket.id]), HTTP_IDEMPOTENCY_KEY=key)
    assert receipt.data["outcome"] == "acknowledged"
    row.refresh_from_db(); ticket.refresh_from_db()
    assert ticket.status == "in_progress" and row.status == "answer_sent"
    assert command(api_client, ticket, staff, "resolve", body="Inquiry reviewed.", acknowledge_resolution=True).status_code == 409
    accepted = command(api_client, ticket, staff, "accept_information", information_request_id=str(row.id), information_revision=row.revision)
    assert accepted.status_code == 200, accepted.data
    row.refresh_from_db(); ticket.refresh_from_db()
    assert row.status == "accepted" and ticket.status == "in_progress"
    assert list(row.history.order_by("revision").values_list("action", flat=True)) == ["request_information", "answer_sent", "accept_information"]
    api_client.force_authenticate(user)
    detail = api_client.get(reverse("support-ticket-detail", args=[ticket.id]))
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "support_information_ticket.json").write_text(json.dumps(detail.data, default=str), encoding="utf8")
    assert "north entrance" not in json.dumps(list(PlanningEvent.objects.values_list("destination", flat=True)))


def test_withdrawal_stops_answers_and_account_isolation(api_client, user, superuser, inquiry):
    ticket, staff = inquiry
    assert command(api_client, ticket, staff).status_code == 200
    row = TicketInformationRequest.objects.get()
    assert answer(api_client, ticket, superuser, row).status_code == 404
    assert command(api_client, ticket, staff, "withdraw_information", information_request_id=str(row.id), information_revision=row.revision).status_code == 200
    assert answer(api_client, ticket, user, row).status_code == 409
    api_client.force_authenticate(user)
    item = api_client.get(reverse("support-ticket-detail", args=[ticket.id])).data["information_requests"][0]
    assert item["status"] == "withdrawn" and item["can_answer"] is False


def test_returned_answer_keeps_history_and_current_staff_authority_is_required(api_client, user, inquiry):
    ticket, staff = inquiry
    assert command(api_client, ticket, staff).status_code == 200
    row = TicketInformationRequest.objects.get()
    assert answer(api_client, ticket, user, row).status_code == 200
    row.refresh_from_db(); old_answer = row.answer_id
    assert command(api_client, ticket, staff, "return_information", information_request_id=str(row.id), information_revision=row.revision,
        reason="Please name the street too.").status_code == 200
    row.refresh_from_db(); assert row.status == "requested"
    assert answer(api_client, ticket, user, row, body="North entrance on Fixture Street.").status_code == 200
    row.refresh_from_db(); assert row.answer_id != old_answer and TicketMessage.objects.filter(pk=old_answer).exists()
    StaffProfile.objects.filter(user=staff).update(is_active=False)
    assert command(api_client, ticket, staff, "accept_information", information_request_id=str(row.id), information_revision=row.revision).status_code == 403
    assert TicketInformationEvent.objects.count() == 4


def test_new_controls_do_not_enable_payment_or_company_cases(api_client, user, inquiry):
    ticket, staff = inquiry
    ticket.category = "payment"; ticket.save()
    assert command(api_client, ticket, staff).status_code == 403
    ticket.category = "other"; ticket.workspace = "company"; ticket.save()
    assert command(api_client, ticket, staff).status_code == 403
    assert not TicketInformationRequest.objects.exists()


def test_attachment_answer_does_not_close_or_accept_and_ticket_controls_access(api_client, user, superuser, inquiry, settings, tmp_path):
    import hashlib
    from django.core.files.uploadedfile import SimpleUploadedFile
    from .test_staged_media import pdf
    from core_apps.support.services.staged_attachments import scan_pending
    from core_apps.support.models import TicketAttachment
    settings.SUPPORT_PRIVATE_STORAGE_PROVIDER = "local"
    settings.SUPPORT_PRIVATE_MEDIA_ROOT = tmp_path / "private-support"
    settings.EVIDENCE_SCANNER_BACKEND = "fake"
    settings.EVIDENCE_STORAGE_PROVIDER = "database"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = True
    ticket, staff = inquiry
    assert command(api_client, ticket, staff).status_code == 200
    row = TicketInformationRequest.objects.get()
    api_client.force_authenticate(user)
    content = pdf()
    upload = api_client.post(reverse("support-upload"), {"workspace": "tenant", "ticket_id": str(ticket.id),
        "client_upload_id": str(uuid4()), "file": SimpleUploadedFile("answer.pdf", content, content_type="application/pdf"),
        "sha256": hashlib.sha256(content).hexdigest()}, format="multipart")
    assert upload.status_code == 201, upload.data
    identity = upload.data["id"]
    assert scan_pending()["scanned"] == 1
    staged = TicketAttachment.objects.get(id=identity)
    assert staged.status == "ready", staged.media_metadata
    assert staged.pending_ticket_id == ticket.pk and staged.message_id is None
    response = answer(api_client, ticket, user, row, body="", attachment_ids=[str(identity)])
    assert response.status_code == 200, response.data
    ticket.refresh_from_db(); row.refresh_from_db()
    assert ticket.status == "in_progress" and row.status == "answer_sent"
    attachment_path = reverse("support-attachment", args=[identity]) + "?workspace=tenant"
    allowed = api_client.get(attachment_path)
    assert allowed.status_code == 200
    assert b"".join(allowed.streaming_content) == content
    from core_apps.users.models import User
    outsider = User.objects.create_user(email="support-outsider@example.invalid", password="local-test-only")
    api_client.force_authenticate(outsider)
    assert api_client.get(attachment_path).status_code == 404
    api_client.force_authenticate(superuser)
    # The user-facing answer endpoint never grants access to another ticket.
    assert answer(api_client, ticket, superuser, row).status_code == 404
    api_client.force_authenticate(user)
    TicketAttachment.objects.filter(id=identity).update(status="unsafe")
    assert api_client.get(attachment_path).status_code == 404
