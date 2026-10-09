import uuid

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from core_apps.features.models import (
    CheckoutSession,
    IdempotencyRecord,
    Lease,
    RentInvoice,
)
from core_apps.properties.models import City, Governorate, Property, PropertyType
from core_apps.users.models import User


def authenticated(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_capabilities_are_fresh_private_and_account_scoped():
    user = User.objects.create_user(
        email="rental-capabilities@example.com",
        password="pass",
        first_name="Rental",
        last_name="User",
        is_verified=True,
    )
    response = authenticated(user).get(
        f"/api/v1/features/v1/rental-capabilities/?subject_id={user.id}&action=checkout"
    )

    assert response.status_code == 200
    assert response.data == {
        "account_id": str(user.id),
        "account_verified": True,
        "enabled_capabilities": ["rental_interests", "rental_agreements"],
        "policy_version": "rental-policy-v1",
        "allowed_actions": ["onboard"],
        "blocking_reasons": ["The requested rental action is not available yet."],
    }
    assert response["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_capabilities_do_not_disclose_another_account():
    user = User.objects.create_user(
        email="rental-capabilities-owner@example.com",
        password="pass",
        first_name="Owner",
        last_name="Account",
        is_verified=True,
    )
    stranger = User.objects.create_user(
        email="rental-capabilities-stranger@example.com",
        password="pass",
        first_name="Other",
        last_name="Account",
        is_verified=True,
    )

    response = authenticated(stranger).get(
        f"/api/v1/features/v1/rental-capabilities/?subject_id={user.id}"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_operation_lookup_returns_confirmed_receipt_for_exact_subject():
    user = User.objects.create_user(
        email="rental-operation@example.com",
        password="pass",
        first_name="Rental",
        last_name="Operation",
        is_verified=True,
    )
    request_key = uuid.uuid4()
    record = IdempotencyRecord.objects.create(
        user=user,
        operation="rental.test",
        request_key=str(request_key),
        fingerprint="0" * 64,
        response_data={},
        is_rental_operation=True,
        request_subject_id=user.id,
        result_subject_id=user.id,
        result_revision=3,
    )

    response = authenticated(user).get(
        f"/api/v1/features/v1/rental-operations/{request_key}/?subject_id={user.id}"
    )

    assert response.status_code == 200
    assert response.data == {
        "request_key": str(request_key),
        "request_subject_id": str(user.id),
        "status": "confirmed",
        "operation_receipt": {
            "id": str(record.id),
            "subject_id": str(user.id),
            "request_key": str(request_key),
            "revision": 3,
            "status": "confirmed",
        },
    }


@pytest.mark.django_db
def test_missing_operation_is_unknown_not_final_absence():
    user = User.objects.create_user(
        email="rental-operation-missing@example.com",
        password="pass",
        first_name="Missing",
        last_name="Operation",
        is_verified=True,
    )
    request_key = uuid.uuid4()

    response = authenticated(user).get(
        f"/api/v1/features/v1/rental-operations/{request_key}/?subject_id={user.id}"
    )

    assert response.status_code == 200
    assert response.data["status"] == "unknown"
    assert response.data["operation_receipt"] is None


@pytest.mark.django_db
@override_settings(RENTAL_CHECKOUT_ENABLED=False)
def test_placeholder_checkout_is_disabled_by_default():
    owner = User.objects.create_user(
        email="checkout-owner@example.com",
        password="pass",
        first_name="Checkout",
        last_name="Owner",
        is_verified=True,
    )
    tenant = User.objects.create_user(
        email="checkout-tenant@example.com",
        password="pass",
        first_name="Checkout",
        last_name="Tenant",
        is_verified=True,
    )
    governorate = Governorate.objects.create(name="Checkout Cairo")
    city = City.objects.create(name="Checkout City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="Checkout apartment", slug="checkout-apartment"
    )
    property_obj = Property.objects.create(
        owner=owner,
        title="Checkout home",
        price=10000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="District",
        status=Property.Status.VERIFIED,
        is_verified=True,
    )
    lease = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date="2026-11-01",
        end_date="2026-12-01",
        rent_amount_minor=1000000,
    )
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="RENT-FOUNDATION-1",
        due_date="2026-11-01",
        amount_minor=1000000,
    )

    detail = authenticated(tenant).get(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/"
    )
    response = authenticated(tenant).post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/checkout/",
        {"invoice_id": str(invoice.id), "quote_id": str(uuid.uuid4()), "expected_revision": invoice.revision, "request_key": str(uuid.uuid4())},
        format="json",
    )

    assert detail.data["can_pay"] is False
    assert detail.data["allowed_actions"] == []
    assert response.status_code == 403
    assert response.json()["code"] == "capability_unavailable"
    assert CheckoutSession.objects.count() == 0
