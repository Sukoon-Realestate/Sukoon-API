import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from core_apps.support.models import Ticket
from core_apps.support.services import (
    TicketClosedConflict,
    add_ticket_reply,
    create_ticket,
    get_help_center_content,
    get_ticket_detail,
    list_user_tickets,
)


@pytest.mark.django_db
class TestHelpCenterService:
    def test_tenant_arabic_help_center(self):
        data = get_help_center_content(workspace="tenant", lang="ar")
        assert "phone" in data
        assert "faqs" in data
        assert len(data["faqs"]) > 0
        assert data["faqs"][0]["id"] == "visit-booking"

    def test_owner_english_help_center(self):
        data = get_help_center_content(workspace="owner", lang="en")
        assert "listing-property" in [f["id"] for f in data["faqs"]]
        assert "Daily" in data["hours"]


@pytest.mark.django_db
class TestTicketService:
    def test_create_ticket_validates_subject_length(self, user):
        with pytest.raises(ValidationError):
            create_ticket(
                user=user,
                workspace="tenant",
                category="visit",
                subject="hi",  # < 3
                description="Valid description with more than 10 characters",
            )

    def test_create_ticket_validates_description_length(self, user):
        with pytest.raises(ValidationError):
            create_ticket(
                user=user,
                workspace="tenant",
                category="visit",
                subject="Valid subject",
                description="short",  # < 10
            )

    def test_tenant_cannot_use_report_tenant_category(self, user):
        with pytest.raises(ValidationError):
            create_ticket(
                user=user,
                workspace="tenant",
                category="report_tenant",
                subject="موضوع البلاغ",
                description="تفاصيل البلاغ بأكثر من عشرة أحرف",
            )

    def test_owner_cannot_use_report_owner_category(self, user):
        with pytest.raises(ValidationError):
            create_ticket(
                user=user,
                workspace="owner",
                category="report_owner",
                subject="موضوع البلاغ",
                description="تفاصيل البلاغ بأكثر من عشرة أحرف",
            )

    def test_attachments_count_limit(self, user):
        fake_files = [
            SimpleUploadedFile(f"file{i}.png", b"content", content_type="image/png")
            for i in range(4)
        ]
        with pytest.raises(ValidationError):
            create_ticket(
                user=user,
                workspace="tenant",
                category="visit",
                subject="مشكلة معينة",
                description="وصف المشكلة بالتفصيل الكافي",
                attachments=fake_files,
            )

    def test_invalid_attachment_extension(self, user):
        fake_file = SimpleUploadedFile(
            "script.sh", b"bash script", content_type="text/plain"
        )
        with pytest.raises(ValidationError):
            create_ticket(
                user=user,
                workspace="tenant",
                category="visit",
                subject="مشكلة معينة",
                description="وصف المشكلة بالتفصيل الكافي",
                attachments=[fake_file],
            )

    def test_create_and_list_user_tickets(self, user, another_user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="visit",
            subject="مشكلة حجز موعد",
            description="لا أستطيع تأكيد موعد الزيارة المحدد",
        )
        assert ticket.reference.startswith("SUP-")
        assert ticket.messages.count() == 1
        assert ticket.messages.first().body == "لا أستطيع تأكيد موعد الزيارة المحدد"

        # List should return ticket for tenant workspace
        user_tickets = list_user_tickets(user=user, workspace="tenant")
        assert user_tickets.count() == 1
        assert user_tickets.first() == ticket

        # Another user cannot see this ticket
        other_tickets = list_user_tickets(user=another_user, workspace="tenant")
        assert other_tickets.count() == 0

    def test_get_ticket_detail_access_control(self, user, another_user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="visit",
            subject="مشكلة حجز",
            description="تفاصيل المشكلة المذكورة",
        )

        # Owner user can access
        detail = get_ticket_detail(
            user=user, ticket_id=str(ticket.id), workspace="tenant"
        )
        assert detail.id == ticket.id

        # Wrong user cannot access
        with pytest.raises(Ticket.DoesNotExist):
            get_ticket_detail(user=another_user, ticket_id=str(ticket.id))

        # Wrong workspace cannot access
        with pytest.raises(Ticket.DoesNotExist):
            get_ticket_detail(user=user, ticket_id=str(ticket.id), workspace="owner")

    def test_add_reply_to_ticket(self, user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="property",
            subject="استفسار عن العقار",
            description="نص المشكلة الأساسية بالتفصيل",
        )

        updated = add_ticket_reply(
            user=user,
            ticket_id=str(ticket.id),
            body="شكراً، هذا رد إضافي للتوضيح",
            workspace="tenant",
        )
        assert updated.messages.count() == 2
        assert updated.messages.last().body == "شكراً، هذا رد إضافي للتوضيح"

    def test_reply_to_resolved_or_closed_ticket_raises_conflict(self, user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="visit",
            subject="مشكلة في الزيارة",
            description="وصف المشكلة الكامل بالتفصيل",
        )
        ticket.status = Ticket.Status.RESOLVED
        ticket.save()

        with pytest.raises(TicketClosedConflict):
            add_ticket_reply(
                user=user,
                ticket_id=str(ticket.id),
                body="محاولة رد على تذكرة محلولة",
                workspace="tenant",
            )
