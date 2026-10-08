from datetime import time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    send_message,
)
from core_apps.notifications.models import Notification
from core_apps.properties.models import Property, PropertyVisit


def make_property(owner, apartment_type, cairo_city, cairo_governorate, title="Phone home"):
    return Property.objects.create(
        owner=owner,
        title=title,
        price=5000,
        property_type=apartment_type,
        governorate=cairo_governorate,
        city=cairo_city,
        district="Nasr City",
    )


def make_visit(property_obj, tenant, status=PropertyVisit.Status.PENDING):
    return PropertyVisit.objects.create(
        property=property_obj,
        tenant=tenant,
        visit_date=timezone.localdate() + timedelta(days=1),
        visit_time=time(13),
        status=status,
    )


def set_phones(owner, tenant):
    owner.profile.phone_number = "+201001234567"
    owner.profile.save(update_fields=["phone_number"])
    tenant.profile.phone_number = "+201112345678"
    tenant.profile.save(update_fields=["phone_number"])


@pytest.mark.django_db
def test_pending_visit_hides_numbers_across_visit_property_and_chat_reads(
    api_client,
    user,
    another_user,
    superuser,
    apartment_type,
    cairo_city,
    cairo_governorate,
):
    tenant, owner = user, another_user
    set_phones(owner, tenant)
    property_obj = make_property(
        owner, apartment_type, cairo_city, cairo_governorate
    )
    visit = make_visit(property_obj, tenant)
    conversation = get_or_create_direct_conversation(user=tenant, other_user=owner)

    api_client.force_authenticate(tenant)
    tenant_detail = api_client.get(
        reverse("tenant-visit-request-detail", kwargs={"id": visit.id}),
        HTTP_ACCEPT_LANGUAGE="en",
    ).json()["data"]
    assert tenant_detail["owner"]["phone_number"] == ""
    assert tenant_detail["owner"]["is_phone_revealed"] is False
    assert "after the owner accepts" in tenant_detail["owner"]["phone_notice"]

    property_data = api_client.get(
        reverse("property-detail", kwargs={"id": property_obj.id}),
        HTTP_ACCEPT_LANGUAGE="en",
    ).json()["data"]
    assert property_data["owner"]["phone_number"] == ""
    assert property_data["owner"]["is_phone_revealed"] is False

    conversation_data = api_client.get(
        reverse("conversation-detail", kwargs={"id": conversation.id}),
        HTTP_ACCEPT_LANGUAGE="en",
    ).json()["data"]
    assert conversation_data["other_participant"]["phone_number"] == ""
    assert conversation_data["other_participant"]["is_phone_revealed"] is False
    created_conversation = api_client.post(
        reverse("conversation-create"), {"user_id": str(owner.id)}, format="json"
    ).json()["data"]
    assert created_conversation["other_participant"]["is_phone_revealed"] is False

    send_message(conversation=conversation, sender=owner, content="Hello")
    messages = api_client.get(
        reverse("message-list", kwargs={"id": conversation.id})
    ).json()["data"]["results"]
    assert "phone_number" not in messages[0]["sender"]

    api_client.force_authenticate(owner)
    owner_detail = api_client.get(
        reverse("owner-visit-request-detail", kwargs={"id": visit.id})
    ).json()["data"]
    assert owner_detail["tenant"]["phone_number"] == ""
    assert owner_detail["tenant"]["is_phone_revealed"] is False

    api_client.force_authenticate(superuser)
    unrelated_property = api_client.get(
        reverse("property-detail", kwargs={"id": property_obj.id})
    ).json()["data"]
    assert unrelated_property["owner"]["phone_number"] == ""


@pytest.mark.django_db
def test_acceptance_discloses_both_numbers_is_idempotent_and_survives_cancel(
    api_client,
    user,
    another_user,
    apartment_type,
    cairo_city,
    cairo_governorate,
):
    tenant, owner = user, another_user
    set_phones(owner, tenant)
    property_obj = make_property(
        owner, apartment_type, cairo_city, cairo_governorate
    )
    visit = make_visit(property_obj, tenant)
    conversation = get_or_create_direct_conversation(user=tenant, other_user=owner)

    api_client.force_authenticate(owner)
    accept_url = reverse("owner-visit-request-accept", kwargs={"id": visit.id})
    accepted = api_client.post(accept_url, {}, format="json")
    repeated = api_client.post(accept_url, {}, format="json")
    assert accepted.status_code == repeated.status_code == 200
    visit.refresh_from_db()
    assert visit.accepted_at is not None
    assert Notification.objects.filter(
        user=tenant, notification_type=Notification.NotificationType.VISIT_ACCEPTED
    ).count() == 1
    notification = Notification.objects.get(
        user=tenant, notification_type=Notification.NotificationType.VISIT_ACCEPTED
    )
    assert notification.data["visit_id"] == str(visit.id)
    assert notification.data["property_id"] == str(property_obj.id)
    assert notification.data["conversation_id"] == str(conversation.id)
    assert "phone" not in str(notification.data).lower()

    owner_detail = api_client.get(
        reverse("owner-visit-request-detail", kwargs={"id": visit.id})
    ).json()["data"]
    assert owner_detail["tenant"]["phone_number"] == "+201112345678"
    assert owner_detail["tenant"]["masked_phone_number"] == ""
    assert owner_detail["tenant"]["is_phone_revealed"] is True
    assert owner_detail["tenant"]["phone_notice"] == ""
    owner_list = api_client.get(reverse("owner-visit-request-list")).json()["data"]
    assert owner_list["results"][0]["tenant"]["phone_number"] == "+201112345678"
    legacy_owner_list = api_client.get(reverse("owner-visit-list")).json()["data"]
    assert legacy_owner_list["results"][0]["tenant"]["is_phone_revealed"] is True

    api_client.force_authenticate(tenant)
    tenant_detail = api_client.get(
        reverse("tenant-visit-request-detail", kwargs={"id": visit.id})
    ).json()["data"]
    assert tenant_detail["owner"]["phone_number"] == "+201001234567"
    assert tenant_detail["owner"]["is_phone_revealed"] is True

    property_data = api_client.get(
        reverse("property-detail", kwargs={"id": property_obj.id})
    ).json()["data"]
    assert property_data["owner"]["phone_number"] == "+201001234567"
    assert property_data["owner"]["is_phone_revealed"] is True

    conversation_data = api_client.get(
        reverse("conversation-detail", kwargs={"id": conversation.id})
    ).json()["data"]
    assert conversation_data["other_participant"]["phone_number"] == "+201001234567"
    assert conversation_data["other_participant"]["is_phone_revealed"] is True
    conversation_list = api_client.get(reverse("conversation-list")).json()["data"]
    assert conversation_list["results"][0]["other_participant"]["phone_number"] == (
        "+201001234567"
    )
    conversation_create = api_client.post(
        reverse("conversation-create"), {"user_id": str(owner.id)}, format="json"
    ).json()["data"]
    assert conversation_create["other_participant"]["is_phone_revealed"] is True

    cancelled = api_client.post(
        reverse("property-visit-cancel", kwargs={"id": visit.id}), {}, format="json"
    )
    assert cancelled.status_code == 200
    visit.refresh_from_db()
    assert visit.status == PropertyVisit.Status.CANCELED
    assert visit.accepted_at is not None
    after_cancel = api_client.get(
        reverse("conversation-detail", kwargs={"id": conversation.id})
    ).json()["data"]
    assert after_cancel["other_participant"]["is_phone_revealed"] is True

    owner.profile.phone_number = "+201009999999"
    owner.profile.save(update_fields=["phone_number"])
    refreshed = api_client.get(
        reverse("conversation-detail", kwargs={"id": conversation.id})
    ).json()["data"]
    assert refreshed["other_participant"]["phone_number"] == "+201009999999"


@pytest.mark.django_db
def test_property_scope_and_conversation_detail_privacy(
    api_client,
    user,
    another_user,
    superuser,
    apartment_type,
    cairo_city,
    cairo_governorate,
):
    tenant, owner = user, another_user
    set_phones(owner, tenant)
    accepted_property = make_property(
        owner, apartment_type, cairo_city, cairo_governorate, "Accepted property"
    )
    other_property = make_property(
        owner, apartment_type, cairo_city, cairo_governorate, "Other property"
    )
    visit = make_visit(accepted_property, tenant)
    visit.status = PropertyVisit.Status.CONFIRMED
    visit.accepted_at = timezone.now()
    visit.save(update_fields=["status", "accepted_at"])
    conversation = get_or_create_direct_conversation(user=tenant, other_user=owner)

    api_client.force_authenticate(tenant)
    accepted_data = api_client.get(
        reverse("property-detail", kwargs={"id": accepted_property.id})
    ).json()["data"]
    other_data = api_client.get(
        reverse("property-detail", kwargs={"id": other_property.id})
    ).json()["data"]
    assert accepted_data["owner"]["is_phone_revealed"] is True
    assert other_data["owner"]["is_phone_revealed"] is False

    api_client.force_authenticate(superuser)
    assert (
        api_client.get(
            reverse("conversation-detail", kwargs={"id": conversation.id})
        ).status_code
        == 403
    )
    api_client.force_authenticate(user=None)
    assert (
        api_client.get(
            reverse("conversation-detail", kwargs={"id": conversation.id})
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_rejected_or_pre_acceptance_cancelled_visit_never_discloses(
    api_client,
    user,
    another_user,
    apartment_type,
    cairo_city,
    cairo_governorate,
):
    tenant, owner = user, another_user
    set_phones(owner, tenant)
    property_obj = make_property(
        owner, apartment_type, cairo_city, cairo_governorate
    )
    rejected = make_visit(property_obj, tenant, PropertyVisit.Status.REJECTED)
    cancelled = PropertyVisit.objects.create(
        property=property_obj,
        tenant=tenant,
        visit_date=timezone.localdate() + timedelta(days=2),
        visit_time=time(14),
        status=PropertyVisit.Status.CANCELED,
    )
    conversation = get_or_create_direct_conversation(user=tenant, other_user=owner)
    api_client.force_authenticate(tenant)
    for visit in (rejected, cancelled):
        data = api_client.get(
            reverse("tenant-visit-request-detail", kwargs={"id": visit.id})
        ).json()["data"]
        assert data["owner"]["is_phone_revealed"] is False
        assert data["owner"]["phone_number"] == ""
    chat = api_client.get(
        reverse("conversation-detail", kwargs={"id": conversation.id})
    ).json()["data"]
    assert chat["other_participant"]["is_phone_revealed"] is False


@pytest.mark.django_db
def test_notices_localize_and_missing_granted_phone_stays_authorized(
    api_client,
    user,
    another_user,
    apartment_type,
    cairo_city,
    cairo_governorate,
):
    tenant, owner = user, another_user
    property_obj = make_property(
        owner, apartment_type, cairo_city, cairo_governorate
    )
    visit = make_visit(property_obj, tenant)
    api_client.force_authenticate(tenant)
    url = reverse("tenant-visit-request-detail", kwargs={"id": visit.id})
    english = api_client.get(url, HTTP_ACCEPT_LANGUAGE="en").json()["data"]
    arabic = api_client.get(url, HTTP_ACCEPT_LANGUAGE="ar").json()["data"]
    assert "after the owner accepts" in english["owner"]["phone_notice"]
    assert "بعد قبول المالك" in arabic["owner"]["phone_notice"]

    api_client.force_authenticate(owner)
    assert (
        api_client.post(
            reverse("owner-visit-request-accept", kwargs={"id": visit.id}),
            {},
            format="json",
        ).status_code
        == 200
    )
    api_client.force_authenticate(tenant)
    granted = api_client.get(url).json()["data"]["owner"]
    assert granted["is_phone_revealed"] is True
    assert granted["phone_number"] is None
    assert granted["masked_phone_number"] == ""
    assert granted["phone_notice"] == ""
