import uuid
from datetime import timedelta
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIRequestFactory
import pytest
from core_apps.features.models import (
    AccountSubscription,
    PaymentAttempt,
    PaymentQuote,
    RentInvoice,
    SubscriptionPlan,
)
from core_apps.features.catalog_models import PromotionOption
from core_apps.features.tests.test_billing_subscriptions import (
    buyer,
    client,
    plan,
    body,
    issue,
    pay,
    ROOT,
)
from core_apps.features.tests.test_rental_phase3 import phase3_lease, client_for
from core_apps.features.services.rental_phase3 import generate_billing_schedule

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("language", ["ar", "en"])
def test_canonical_private_user_journey_survives_all_projections(
    client, buyer, plan, language
):
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = language
    expected = {
        "is_subscriped": True,
        "has_completed_registration": False,
        "available_workspaces": ["tenant", "owner"],
        "subscription_summary": {"tenant": None, "owner": None},
    }
    for path, nested in (
        ("/api/v1/auth/users/me/", False),
        (reverse("my-account"), True),
        (reverse("account-summary"), True),
    ):
        value = body(client.get(path))
        value = value["user"] if nested else value
        for key, field in expected.items():
            assert value[key] == field, (path, key, value)
    invoice = body(issue(client, plan)[0], 201)
    body(pay(client, invoice)[0])
    user = body(client.get("/api/v1/auth/users/me/"))
    assert user["subscription_summary"]["owner"]["invoice_id"] == invoice["id"]
    assert user["subscription_summary"]["tenant"]["status"] == "active"


def test_invoice_issuance_lookup_cancel_filters_and_no_new_charge(
    client, plan, settings
):
    response, request = issue(client, plan)
    invoice = body(response, 201)
    lookup = body(
        client.get(ROOT + f"billing/invoice-operations/{request['request_key']}/")
    )
    assert lookup["invoice"]["id"] == invoice["id"] and not lookup["absence_confirmed"]
    settings.RENTAL_CHECKOUT_ENABLED = False
    fresh = body(client.get(ROOT + f"billing/invoices/{invoice['id']}/"))
    assert fresh["allowed_actions"] == ["cancel"]
    command = {"expected_revision": 1, "request_key": str(uuid.uuid4())}
    path = ROOT + f"billing/invoices/{invoice['id']}/cancel/"
    cancelled = body(client.post(path, command, format="json"))
    assert cancelled["status"] == "cancelled" and cancelled["revision"] == 2
    assert body(client.post(path, command, format="json"))["revision"] == 2
    assert (
        body(client.post(path, {**command, "expected_revision": 2}, format="json"), 409)
        is None
    )
    listing = body(
        client.get(
            ROOT + "billing/invoices/",
            {"workspace": "owner", "status": "cancelled", "purpose": "subscription"},
        )
    )
    assert [item["id"] for item in listing] == [invoice["id"]]
    assert (
        body(client.get(ROOT + "billing/invoices/", {"from": "2026-99-00"}), 400)
        is None
    )
    assert not PaymentAttempt.objects.exists()


def test_stale_expired_foreign_quotes_leave_unpaid_invoice(client, plan):
    invoice = body(issue(client, plan)[0], 201)
    path = ROOT + f"billing/invoices/{invoice['id']}/"
    quote = body(
        client.post(
            path + "quote/",
            {"expected_revision": 1, "request_key": str(uuid.uuid4())},
            format="json",
        ),
        201,
    )
    PaymentQuote.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    command = {
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
        "quote_id": quote["id"],
    }
    response = client.post(path + "checkout/", command, format="json")
    assert (
        body(response, 409) is None and response["X-App-Error-Code"] == "quote_expired"
    )
    assert (
        body(
            client.post(
                path + "checkout/",
                {**command, "quote_id": str(uuid.uuid4())},
                format="json",
            ),
            404,
        )
        is None
    )
    assert (
        not PaymentAttempt.objects.exists()
        and RentInvoice.objects.get().status == "due"
    )


def test_plan_and_promotion_admin_edit_reaches_api_with_immutable_history(
    client, buyer, plan
):
    request = APIRequestFactory().post("/admin/")
    request.user = buyer
    model_admin = admin.site._registry[SubscriptionPlan]
    assert not model_admin.has_change_permission(request)
    plan.name_ar = "خطة محدثة"
    plan.amount_minor = 45000
    model_admin.save_model(request, plan, None, True)
    result = body(client.get(ROOT + "subscription-plans/", HTTP_ACCEPT_LANGUAGE="ar"))[
        0
    ]
    assert result["name"] == "خطة محدثة" and result["revision"] == 2
    assert result["amount_minor"] == 45000
    assert (
        body(client.get(ROOT + "subscriptions/current/", HTTP_ACCEPT_LANGUAGE="ar"))[
            "plans"
        ][0]
        == result
    )
    option = PromotionOption.objects.get(id="week")
    option.duration_days = 9
    admin.site._registry[PromotionOption].save_model(request, option, None, True)
    catalog = body(client.get(ROOT + "configuration/", {"workspace": "owner"}))
    assert catalog["boost_options"][0]["duration_days"] == 9
    option.duration_days = 0
    with pytest.raises(ValidationError):
        option.full_clean()
    for model in (RentInvoice, PaymentAttempt, AccountSubscription):
        assert not admin.site._registry[model].has_change_permission(request)
        assert not admin.site._registry[model].has_delete_permission(request)


def test_local_rental_mock_pay_captures_once_without_provider_form(
    phase3_lease, settings
):
    settings.RENTAL_FAKE_AUTO_CAPTURE = True
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(tenant)
    path = ROOT + f"rent-invoices/{invoice.id}/"
    quote = body(
        client.post(
            path + "quote/",
            {
                "action": "quote",
                "expected_revision": invoice.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        ),
        201,
    )["resource"]
    command = {
        "invoice_id": str(invoice.id),
        "quote_id": quote["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(uuid.uuid4()),
    }
    paid = body(client.post(path + "checkout/", command, format="json"), 201)[
        "resource"
    ]
    assert paid["status"] == "captured"
    assert (
        body(client.post(path + "checkout/", command, format="json"), 201)["resource"]
        == paid
    )
    invoice.refresh_from_db()
    assert invoice.status == "paid" and invoice.payment_attempts.count() == 1
    assert not AccountSubscription.objects.exists()


def test_purchase_cannot_enter_rent_only_handlers(client, plan):
    invoice = body(issue(client, plan)[0], 201)
    assert body(client.get(ROOT + f"rent-invoices/{invoice['id']}/"), 404) is None
    assert (
        body(
            client.post(
                ROOT + f"rent-invoices/{invoice['id']}/quote/",
                {
                    "action": "quote",
                    "expected_revision": 1,
                    "request_key": str(uuid.uuid4()),
                },
                format="json",
            ),
            404,
        )
        is None
    )

    assert (
        body(
            client.post(
                ROOT + f"rent-invoices/{invoice['id']}/external-payment-claims/",
                {},
                format="json",
            ),
            404,
        )
        is None
    )
    from rest_framework.exceptions import NotFound
    from core_apps.features.services.rental_foundation import (
        get_authorized_rental_subject,
    )

    with pytest.raises(NotFound):
        get_authorized_rental_subject(client.handler._force_user, invoice["id"])
    attempt = body(pay(client, invoice)[0])
    with pytest.raises(NotFound):
        get_authorized_rental_subject(client.handler._force_user, attempt["id"])
