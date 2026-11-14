"""Compact support replies/recovery have a bounded cost at large histories."""

from uuid import uuid4
import pytest
from django.urls import reverse
from core_apps.support.models import Ticket, TicketMessage
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("size", [1, 100, 1000])
def test_compact_reply_and_recovery_preserve_paged_history(size, auth_client, user):
    ticket = Ticket.objects.create(
        user=user, category="other", workspace="tenant", subject="Synthetic inquiry"
    )
    TicketMessage.objects.bulk_create(
        [
            TicketMessage(ticket=ticket, sender_user=user, body=f"Old message {i}")
            for i in range(size)
        ]
    )
    key = str(uuid4())
    reply_url = reverse("support-ticket-reply", kwargs={"id": ticket.id})

    def reply():
        result = auth_client.post(
            reply_url + "?receipt=compact",
            {"body": "Current reply"},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        assert result.status_code == 200, result.data
        result.render()
        return result

    result, report = measured("sprint09-compact-support-reply", size, reply)
    assert "messages" not in result.data and result.data["id"] == str(ticket.id)
    assert report["queries"] <= 35 and report["payload_bytes"] < 1000
    replay = reply()
    assert replay.data == result.data and ticket.messages.count() == size + 1
    receipt_url = (
        reverse("support-reply-receipt", kwargs={"id": ticket.id}) + "?receipt=compact"
    )
    recovered, recovery_report = measured(
        "sprint09-compact-support-recovery",
        size,
        lambda: auth_client.get(receipt_url, HTTP_IDEMPOTENCY_KEY=key),
    )
    assert recovered.status_code == 200, recovered.data
    assert recovered.data["outcome"] == "acknowledged"
    assert recovered.data["ticket"] == result.data
    assert recovery_report["queries"] <= 12 and recovery_report["payload_bytes"] < 1000
    detail = auth_client.get(
        reverse("support-ticket-detail", kwargs={"id": ticket.id}),
        {"bounded": "true", "messages_page_size": "1"},
    )
    assert detail.status_code == 200 and len(detail.data["messages"]) == 1
    assert detail.data["pages"]["messages"]["count"] == size + 1
    # Full receipts remain the compatible legacy representation; a retained
    # identity cannot be reinterpreted as a different response command.
    assert (
        auth_client.post(
            reply_url,
            {"body": "Current reply"},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        ).status_code
        == 409
    )
