"""Information projection batches version/file availability without weakening proof."""

from uuid import uuid4

import pytest
from core_apps.admin_api.tests.test_sprint04_performance import measured
from core_apps.support.models import (
    Ticket,
    TicketMessage,
    TicketInformationRequest,
    TicketInformationEvent,
    TicketEvidenceSubmission,
)
from core_apps.support.services.information import projection

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("size", [1, 25, 100])
def test_information_relations_and_missing_file_proof(size, user):
    ticket = Ticket.objects.create(
        user=user, workspace="tenant", category="other", subject="Budget"
    )
    for i in range(size):
        message = TicketMessage.objects.create(
            ticket=ticket, sender="user", sender_user=user, body="Private"
        )
        row = TicketInformationRequest.objects.create(
            ticket=ticket,
            source_message=message,
            answer=message,
            created_by=user,
            prompt=f"Question {i}",
        )
        TicketInformationEvent.objects.create(
            request=row, actor=user, action="answer_sent", revision=1, answer=message
        )
        TicketEvidenceSubmission.objects.create(
            request=row,
            message=message,
            version=1,
            files=[{"id": str(uuid4()), "sha256": "missing"}],
        )
    result, report = measured("support-information", size, lambda: projection(ticket))
    assert len(result) == size
    assert all(
        not row["evidence_versions"][0]["files"][0]["available"] for row in result
    )
    assert report["queries"] <= 4


def test_evidence_uuid_normalization_message_digest_and_revocation(user):
    from core_apps.support.models import TicketAttachment

    ticket = Ticket.objects.create(
        user=user,
        reference="normalization",
        workspace="tenant",
        category="other",
        subject="Proof",
    )
    message = TicketMessage.objects.create(
        ticket=ticket, sender="user", sender_user=user, body="Proof"
    )
    other = TicketMessage.objects.create(
        ticket=ticket, sender="user", sender_user=user, body="Other"
    )
    row = TicketInformationRequest.objects.create(
        ticket=ticket,
        source_message=message,
        answer=message,
        created_by=user,
        prompt="Proof",
    )
    attachment = TicketAttachment.objects.create(
        message=message, name="Proof", status="attached", content_sha256="digest"
    )
    TicketEvidenceSubmission.objects.create(
        request=row,
        message=message,
        version=1,
        files=[{"id": str(attachment.id).upper(), "sha256": "digest"}],
    )
    assert projection(ticket)[0]["evidence_versions"][0]["files"][0]["available"]
    TicketAttachment.objects.filter(pk=attachment.pk).update(message=other)
    assert not projection(ticket)[0]["evidence_versions"][0]["files"][0]["available"]
    TicketAttachment.objects.filter(pk=attachment.pk).update(
        message=message, content_sha256="changed"
    )
    assert not projection(ticket)[0]["evidence_versions"][0]["files"][0]["available"]
    TicketAttachment.objects.filter(pk=attachment.pk).update(
        content_sha256="digest", status="unsafe"
    )
    assert not projection(ticket)[0]["evidence_versions"][0]["files"][0]["available"]
