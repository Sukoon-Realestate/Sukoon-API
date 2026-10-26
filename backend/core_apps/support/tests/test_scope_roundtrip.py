"""Support keeps account and all four workspaces through commands and files."""

import pytest
from django.urls import reverse

from core_apps.common.contract_testing import api_json
from core_apps.support.models import Ticket, TicketAttachment
from .test_private_attachments import upload

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("scope", ["tenant", "owner", "student", "company", "account"])
def test_scope_roundtrip_and_foreign_context_rejection(
    auth_client, api_client, another_user, scope
):
    collection = reverse("support-ticket-list-create")
    body = {
        "workspace": scope,
        "category": "other",
        "subject": "Scoped support inquiry",
        "description": "Follow up this original support request.",
        "attachments": [upload()],
    }
    created = auth_client.post(
        collection, body, format="multipart", HTTP_IDEMPOTENCY_KEY="original-ticket"
    )
    assert created.status_code == 201, created.data
    ticket_id = created.json()["data"]["id"]
    ticket = Ticket.objects.get(id=ticket_id)
    assert ticket.workspace == scope
    detail = reverse("support-ticket-detail", kwargs={"id": ticket_id})
    reply = reverse("support-ticket-reply", kwargs={"id": ticket_id})
    file_url = reverse(
        "support-attachment",
        kwargs={"id": TicketAttachment.objects.get(message__ticket=ticket).id},
    )
    rows = api_json(auth_client.get(collection, {"workspace": scope}))["data"][
        "results"
    ]
    assert [row["id"] for row in rows] == [ticket_id]
    assert auth_client.get(detail, {"workspace": scope}).status_code == 200
    image = auth_client.get(file_url, {"workspace": scope})
    assert image.status_code == 200
    assert b"".join(image.streaming_content)
    response = auth_client.post(
        f"{reply}?workspace={scope}",
        {"body": "Follow up my original inquiry"},
        format="json",
        HTTP_IDEMPOTENCY_KEY="original-reply",
    )
    assert response.status_code == 200, response.data
    recovered = auth_client.post(
        reverse("support-ticket-creation-receipt"),
        {"workspace": scope},
        format="json",
        HTTP_IDEMPOTENCY_KEY="original-ticket",
    )
    assert recovered.json()["data"]["ticket"]["id"] == ticket_id
    receipt = reverse("support-reply-receipt", kwargs={"id": ticket_id})
    recovered_reply = auth_client.post(
        f"{receipt}?workspace={scope}",
        {},
        format="json",
        HTTP_IDEMPOTENCY_KEY="original-reply",
    )
    assert recovered_reply.json()["data"]["outcome"] == "acknowledged"
    for other in set(Ticket.Workspace.values) - {scope}:
        assert (
            api_json(auth_client.get(collection, {"workspace": other}))["data"][
                "results"
            ]
            == []
        )
        assert auth_client.get(detail, {"workspace": other}).status_code == 404
        assert auth_client.get(file_url, {"workspace": other}).status_code == 404
        assert (
            auth_client.post(
                f"{reply}?workspace={other}",
                {"body": "Must not reach a different context"},
                format="json",
                HTTP_IDEMPOTENCY_KEY=f"wrong-{other}",
            ).status_code
            == 404
        )
    api_client.force_authenticate(another_user)
    assert api_client.get(detail, {"workspace": scope}).status_code == 404
    assert Ticket.objects.count() == 1
    assert ticket.messages.count() == 2
