"""Property promotion keeps its catalog selection and original creation identity."""

# flake8: noqa: F401,F811

import uuid
import pytest
from core_apps.features.catalog_models import PromotionOption
from core_apps.features.models import BoostCampaign, RentInvoice
from core_apps.features.services.promotion_commands import create, resolve
from core_apps.features.tests.test_promotion_visibility import home
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from core_apps.features.tests.test_billing_subscriptions import body
from core_apps.properties.models import Property
from core_apps.users.models import AccountClosureRequest

pytestmark = pytest.mark.django_db
ROOT = "/api/v1/features/v1/boost-campaigns/"


@pytest.fixture
def selection(home):
    home.status, home.is_verified = Property.Status.VERIFIED, True
    home.save()
    option = PromotionOption.objects.create(
        id="recovery-promotion", title_ar="ترويج", title_en="Promotion", duration_days=7
    )
    return (
        home,
        option,
        {
            "property_id": str(home.id),
            "option_id": option.id,
            "option_revision": option.revision,
            "request_key": str(uuid.uuid4()),
        },
    )


@pytest.mark.parametrize("amount", [0, 1500])
def test_lost_creation_reply_resolves_original_without_creating_a_purchase(
    selection, api_client, amount
):
    home, option, command = selection
    option.amount_minor = amount
    option.save()
    api_client.force_authenticate(home.owner)
    response = api_client.post(ROOT, command, format="json")
    receipt = body(response, 201)
    recovered_receipt = {**receipt, "message": response.json()["message"]}
    assert receipt["status"] == ("pending" if amount else "active")
    result = body(api_client.post(ROOT + "resolve/", command, format="json"))
    assert result["status"] == "confirmed" and result["receipt"] == recovered_receipt
    # Source publication/catalog/account changes cannot erase the saved receipt.
    home.status = Property.Status.UNDER_REVIEW
    home.save(update_fields=["status"])
    option.active = False
    option.save()
    AccountClosureRequest.objects.create(user=home.owner, reason="local")
    assert body(api_client.post(ROOT, command, format="json"), 201) == receipt
    assert (
        body(api_client.post(ROOT + "resolve/", command, format="json"))["receipt"]
        == recovered_receipt
    )
    assert BoostCampaign.objects.count() == 1 and RentInvoice.objects.count() == int(
        bool(amount)
    )


def test_final_absence_fences_a_late_create_and_allows_new_explicit_attempt(
    selection, api_client
):
    home, _, command = selection
    api_client.force_authenticate(home.owner)
    assert (
        body(api_client.post(ROOT + "resolve/", command, format="json"))["status"]
        == "absent_final"
    )
    assert api_client.post(ROOT, command, format="json").status_code == 409
    assert not BoostCampaign.objects.exists()
    fresh = {**command, "request_key": str(uuid.uuid4())}
    assert api_client.post(ROOT, fresh, format="json").status_code == 201
    assert BoostCampaign.objects.count() == 1


def test_catalog_change_requires_review_and_account_closure_blocks_new_work(
    selection, api_client
):
    home, option, command = selection
    api_client.force_authenticate(home.owner)
    option.revision += 1
    option.duration_days = 14
    option.save()
    assert api_client.post(ROOT, command, format="json").status_code == 409
    assert not BoostCampaign.objects.exists()
    AccountClosureRequest.objects.create(user=home.owner, reason="local")
    command["option_revision"] = option.revision
    assert api_client.post(ROOT, command, format="json").status_code == 403
    assert not BoostCampaign.objects.exists()


def test_same_key_cannot_change_terms_or_target(selection, api_client):
    home, _, command = selection
    api_client.force_authenticate(home.owner)
    assert api_client.post(ROOT, command, format="json").status_code == 201
    assert (
        api_client.post(
            ROOT, {**command, "option_revision": 99}, format="json"
        ).status_code
        == 409
    )
    assert (
        api_client.post(
            ROOT + "resolve/",
            {**command, "property_id": str(uuid.uuid4())},
            format="json",
        ).status_code
        == 409
    )
    assert BoostCampaign.objects.count() == 1


@pytest.mark.parametrize("change", ["retired", "blocked", "unverified", "review"])
def test_unpublished_property_cannot_start_a_new_promotion(
    selection, api_client, change
):
    from django.utils import timezone

    home, _, command = selection
    if change == "retired":
        home.retired_at = timezone.now()
        home.status = Property.Status.HIDDEN
    elif change == "blocked":
        home.moderation_blocked = True
    elif change == "unverified":
        home.is_verified = False
    else:
        home.status = Property.Status.UNDER_REVIEW
    home.save()
    api_client.force_authenticate(home.owner)
    assert api_client.post(ROOT, command, format="json").status_code == 400
    assert not BoostCampaign.objects.exists() and not RentInvoice.objects.exists()


@pytest.mark.parametrize("change", ["missing_revision", "client_price"])
def test_creation_requires_reviewed_catalog_and_rejects_client_price(
    selection, api_client, change
):
    home, _, command = selection
    api_client.force_authenticate(home.owner)
    if change == "missing_revision":
        command.pop("option_revision")
    else:
        command["amount_minor"] = 1
    assert api_client.post(ROOT, command, format="json").status_code == 400
    assert not BoostCampaign.objects.exists() and not RentInvoice.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_resolve_and_late_create_are_serialized(selection):
    home, _, command = selection
    from rest_framework.exceptions import APIException

    def run(index):
        try:
            return (
                create(home.owner, command) if index else resolve(home.owner, command)
            )
        except APIException as error:
            return error.status_code

    resolved, created = parallel_calls(run)
    if resolved["status"] == "absent_final":
        assert created == 409 and not BoostCampaign.objects.exists()
    else:
        assert created[1] == 201 and resolved["receipt"] == created[0]
        assert BoostCampaign.objects.count() == 1
