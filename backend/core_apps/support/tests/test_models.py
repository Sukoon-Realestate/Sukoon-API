import pytest
from core_apps.support.models import Ticket, TicketMessage


@pytest.mark.django_db
class TestSupportModels:
    def test_ticket_creation_and_str(self, user):
        ticket = Ticket.objects.create(
            user=user,
            workspace=Ticket.Workspace.TENANT,
            category=Ticket.Category.VISIT,
            subject="مشكلة في المعاينة",
            reference="SUP-12345",
        )
        assert ticket.reference == "SUP-12345"
        assert ticket.status == Ticket.Status.OPEN
        assert "SUP-12345" in str(ticket)

    def test_message_creation_and_str(self, user):
        ticket = Ticket.objects.create(
            user=user,
            workspace=Ticket.Workspace.TENANT,
            category=Ticket.Category.PAYMENT,
            subject="استفسار دفع",
            reference="SUP-99999",
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=TicketMessage.SenderType.USER,
            sender_user=user,
            body="تفاصيل الاستفسار...",
        )
        assert message.ticket == ticket
        assert "SUP-99999" in str(message)
