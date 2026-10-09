import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from core_apps.support.models import Ticket
from core_apps.support.services import create_ticket

HELP_CENTER_URL = reverse("support-help-center")
TICKETS_URL = reverse("support-ticket-list-create")


@pytest.mark.django_db
class TestHelpCenterView:
    def test_help_center_tenant_arabic(self, api_client):
        res = api_client.get(f"{HELP_CENTER_URL}?workspace=tenant&lang=ar")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert "phone" in data
        assert "email" in data
        assert "hours" in data
        assert len(data["faqs"]) > 0

    def test_help_center_owner_english(self, api_client):
        res = api_client.get(f"{HELP_CENTER_URL}?workspace=owner&lang=en")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert "Daily" in data["hours"]


@pytest.mark.django_db
class TestTicketListCreateAPIView:
    def test_unauthenticated_get_returns_401(self, api_client):
        res = api_client.get(TICKETS_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_post_returns_401(self, api_client):
        res = api_client.post(TICKETS_URL, {})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tickets_empty(self, auth_client, user):
        res = auth_client.get(f"{TICKETS_URL}?workspace=tenant&page=1&page_size=20")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["count"] == 0
        assert data["results"] == []

    def test_create_ticket_json_success(self, auth_client, user):
        payload = {
            "workspace": "owner",
            "category": "report_tenant",
            "subject": "موضوع المشكلة بالتفصيل",
            "description": "وصف المشكلة بالتفصيل مع المستأجر في العقار",
        }
        res = auth_client.post(TICKETS_URL, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()["data"]
        assert "id" in data
        assert data["reference"].startswith("SUP-")
        assert data["subject"] == "موضوع المشكلة بالتفصيل"
        assert len(data["messages"]) == 1
        assert (
            data["messages"][0]["body"] == "وصف المشكلة بالتفصيل مع المستأجر في العقار"
        )

    def test_create_ticket_idempotency_replays_original_ticket(self, auth_client):
        payload = {
            "workspace": "tenant",
            "category": "visit",
            "subject": "تعذر حجز الزيارة",
            "description": "تعذر حجز الزيارة وأحتاج إلى مساعدة من الدعم",
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "support-create-1"}

        first = auth_client.post(TICKETS_URL, payload, format="json", **headers)
        replay = auth_client.post(TICKETS_URL, payload, format="json", **headers)
        conflict = auth_client.post(
            TICKETS_URL,
            {**payload, "description": "وصف مختلف ولكنه طويل بما يكفي"},
            format="json",
            **headers,
        )

        assert first.status_code == status.HTTP_201_CREATED
        assert replay.status_code == status.HTTP_201_CREATED
        assert replay.headers["Idempotency-Replayed"] == "true"
        assert replay.json()["data"]["id"] == first.json()["data"]["id"]
        assert conflict.status_code == status.HTTP_409_CONFLICT
        assert Ticket.objects.count() == 1

    def test_create_ticket_with_multipart_attachment(self, auth_client, user):
        image = SimpleUploadedFile(
            "screenshot.png", b"fake_image_bytes", content_type="image/png"
        )
        payload = {
            "workspace": "tenant",
            "category": "visit",
            "subject": "تعذر حجز موعد",
            "description": "واجهت خطأ أثناء محاولة اختيار الوقت في التقويم",
            "attachments": [image],
        }
        res = auth_client.post(TICKETS_URL, payload, format="multipart")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()["data"]
        assert len(data["messages"][0]["attachments"]) == 1
        assert data["messages"][0]["attachments"][0]["name"] == "screenshot.png"

    def test_create_ticket_role_mismatch_returns_400(self, auth_client, user):
        # Tenant cannot report tenant
        payload = {
            "workspace": "tenant",
            "category": "report_tenant",
            "subject": "عنوان غير ملائم",
            "description": "تفاصيل كافية للوصف أكثر من عشرة أحرف",
        }
        res = auth_client.post(TICKETS_URL, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTicketDetailAndRepliesAPIView:
    def test_detail_unauthenticated_returns_401(self, api_client):
        url = reverse("support-ticket-detail", kwargs={"id": "nonexistent"})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_access_denied_for_other_user_ticket(
        self, auth_client, user, another_user
    ):
        ticket = create_ticket(
            user=another_user,
            workspace="tenant",
            category="visit",
            subject="مشكلة خاصة",
            description="تفاصيل المشكلة الخاصة بمستخدم آخر",
        )
        url = reverse("support-ticket-detail", kwargs={"id": str(ticket.id)})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_happy_path(self, auth_client, user):
        ticket = create_ticket(
            user=user,
            workspace="owner",
            category="payment",
            subject="استفسار عن الدفع",
            description="تفاصيل الاستفسار بالكامل",
        )
        url = reverse("support-ticket-detail", kwargs={"id": str(ticket.id)})
        res = auth_client.get(f"{url}?workspace=owner")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["id"] == str(ticket.id)
        assert data["status"] == "open"
        assert len(data["messages"]) == 1

    def test_reply_to_ticket_happy_path(self, auth_client, user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="verification",
            subject="توثيق الحساب",
            description="أواجه مشكلة في قبول صورة الهوية",
        )
        reply_url = reverse("support-ticket-reply", kwargs={"id": str(ticket.id)})
        payload = {"body": "قمت برفع صورة أوضح الآن"}
        res = auth_client.post(reply_url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert len(data["messages"]) == 2
        assert data["messages"][-1]["body"] == "قمت برفع صورة أوضح الآن"

    def test_reply_idempotency_replays_one_message(self, auth_client, user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="verification",
            subject="توثيق الحساب",
            description="أواجه مشكلة في قبول صورة الهوية",
        )
        url = reverse("support-ticket-reply", kwargs={"id": str(ticket.id)})
        payload = {"body": "قمت برفع صورة أوضح الآن"}
        headers = {"HTTP_IDEMPOTENCY_KEY": "support-reply-1"}

        first = auth_client.post(url, payload, format="json", **headers)
        replay = auth_client.post(url, payload, format="json", **headers)
        conflict = auth_client.post(
            url, {"body": "رد مختلف"}, format="json", **headers
        )

        assert first.status_code == status.HTTP_200_OK
        assert replay.status_code == status.HTTP_200_OK
        assert replay.headers["Idempotency-Replayed"] == "true"
        assert len(replay.json()["data"]["messages"]) == 2
        assert conflict.status_code == status.HTTP_409_CONFLICT
        ticket.refresh_from_db()
        assert ticket.messages.count() == 2

    def test_reply_to_resolved_ticket_returns_409(self, auth_client, user):
        ticket = create_ticket(
            user=user,
            workspace="tenant",
            category="other",
            subject="استفسار عام",
            description="تفاصيل كافية لأكثر من عشرة أحرف",
        )
        ticket.status = Ticket.Status.RESOLVED
        ticket.save()

        reply_url = reverse("support-ticket-reply", kwargs={"id": str(ticket.id)})
        payload = {"body": "محاولة إرسال رد بعد الحل"}
        res = auth_client.post(reply_url, payload, format="json")
        assert res.status_code == status.HTTP_409_CONFLICT
