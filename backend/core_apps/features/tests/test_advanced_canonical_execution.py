"""Real workflow wiring with mocked provider transport; not connected evidence."""

from uuid import uuid4
from unittest.mock import patch
import pytest
from django.utils import timezone
from datetime import timedelta

from core_apps.features.models import (
    Lease,
    RentalSigningDocument,
    RentalProviderInstruction,
    PaymentAttempt,
    PaymentReceipt,
    PaymobPayment,
)
from core_apps.features.services import signwell_client, signing_jobs
from core_apps.features.services.paymob_payments import reconcile
from core_apps.features.services.advanced_execution.progress import reconcile_progress
from . import test_advanced_execution as execution
from . import test_paymob_invoice_payments as payments
from . import test_advanced_company_passport_v2 as company_execution
from .test_signwell_documents import send, complete
from .test_rental_phase2 import authenticated

scenario = execution.scenario
rental_participants = execution.rental_participants
paymob = payments.paymob
company_setup = company_execution.company_setup
policy = company_execution.policy
pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def canonical_mode(settings):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "test"
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "collective_tender_planning",
        "collective_tender_execution",
        "conditional_group_execution",
    ]
    settings.SIGNWELL_TEST_ENABLED = True
    settings.SIGNWELL_API_KEY = "synthetic-test-only"
    settings.SIGNWELL_WEBHOOK_ID = "synthetic-webhook"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.RENTAL_PROVIDER_BACKEND = "disabled"


def sign(lease):
    document = RentalSigningDocument.objects.get(id=lease.document_id)
    send(document)
    for actor in [lease.owner, lease.tenant]:
        lease.refresh_from_db()
        response = authenticated(actor).post(
            API + f"leases/{lease.id}/signing-session/",
            {
                "request_key": str(uuid4()),
                "expected_revision": lease.revision,
                "document_id": str(lease.document_id),
                "document_hash": lease.document_hash,
            },
            format="json",
        )
        assert response.status_code == 201, response.data
    assert complete(document) == "applied"
    lease.refresh_from_db()
    assert lease.status == "signed"


def test_prepare_only_queues_exact_document_and_rejects_mock_completion(scenario):
    plan = execution.ready(scenario)
    assert plan["provider_mode"] == "test" and not plan["simulated"]
    assert "advance" not in plan["allowed_actions"]
    lease = Lease.objects.get(id=plan["legs"][0]["lease_id"])
    assert lease.status == "pending_signatures" and not lease.signing_sessions.exists()
    assert RentalSigningDocument.objects.get(id=lease.document_id).status == "prepared"
    assert plan["legs"][0]["continuation_id"] == str(lease.id)
    execution.act(
        scenario[0],
        plan,
        "advance",
        403,
        leg_id=plan["legs"][0]["id"],
        step="sign",
        mock_outcome="confirmed",
    )
    assert not RentalProviderInstruction.objects.exists()
    assert not PaymentAttempt.objects.exists()
    assert Lease.objects.count() == 1


def test_signature_and_paymob_result_drive_original_leg_once(scenario, paymob):
    plan = execution.ready(scenario)
    lease = Lease.objects.get(id=plan["legs"][0]["lease_id"])
    sign(lease)
    view = execution.refresh(scenario[1], plan)
    assert view["legs"][0]["state"] == "signed" and view["state"] == "executing"
    client, invoice, body = payments.rental_checkout((lease.owner, lease.tenant, lease))
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=payments.intention,
    ) as create:
        response = payments.post_checkout(client, invoice, body)
        assert response.status_code == 201, response.content
        assert payments.post_checkout(client, invoice, body).status_code == 201
        assert create.call_count == 1
    view = execution.refresh(scenario[1], plan)
    assert view["state"] == "unknown" and view["legs"][0]["unknown_outcome"]
    payment = PaymobPayment.objects.get()
    with patch(
        "core_apps.features.services.paymob_client.inquiry",
        return_value=payments.snapshot(payment),
    ):
        reconcile(payment)
        reconcile(payment)
    assert execution.refresh(scenario[1], plan)["state"] == "completed"
    reconcile_progress()
    reconcile_progress()
    assert PaymentAttempt.objects.count() == PaymentReceipt.objects.count() == 1
    assert not RentalProviderInstruction.objects.exists()
    assert (
        lease.advanced_execution_leg.steps.filter(
            kind="canonical_progress", state="confirmed"
        ).count()
        == 1
    )


def test_unknown_signature_survives_expiry_without_releasing_or_resubmitting(scenario):
    plan = execution.ready(scenario)
    lease = Lease.objects.get(id=plan["legs"][0]["lease_id"])
    document = RentalSigningDocument.objects.get(id=lease.document_id)
    with patch.object(
        signwell_client,
        "create",
        side_effect=signwell_client.SigningTransportError("unknown", uncertain=True),
    ) as create:
        assert signing_jobs.run(document.id) == "unknown"
        lease.hold_expires_at = timezone.now() - timedelta(minutes=1)
        lease.save()
        plan = execution.refresh(scenario[1], plan)
        assert plan["state"] == "unknown"
        execution.act(scenario[1], plan, "withdraw", 409, leg_id=plan["legs"][0]["id"])
        plan = execution.act(scenario[1], plan, "reconcile")
        assert plan["state"] == "unknown"
        assert create.call_count == 1
    assert lease.inventory_day_locks.exists()
    assert not lease.signing_sessions.exists()


def test_conditional_threshold_applies_at_canonical_invoice_endpoint(scenario, paymob):
    execution.ready(scenario, "conditional_package", two=True)
    leases = list(Lease.objects.order_by("pk"))
    sign(leases[0])
    invoice = leases[0].invoices.get()
    response = authenticated(leases[0].tenant).post(
        API + f"rent-invoices/{invoice.id}/quote/",
        {
            "expected_revision": invoice.revision,
            "request_key": str(uuid4()),
        },
        format="json",
    )
    assert response.status_code == 409, response.data
    assert not PaymentAttempt.objects.exists()
    sign(leases[1])
    response = authenticated(leases[0].tenant).post(
        API + f"rent-invoices/{invoice.id}/quote/",
        {
            "expected_revision": invoice.revision,
            "request_key": str(uuid4()),
        },
        format="json",
    )
    assert response.status_code == 201, response.data


def test_saved_history_is_available_without_provider_configuration(scenario, settings):
    plan = execution.ready(scenario)
    settings.SIGNWELL_TEST_ENABLED = False
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "disabled"
    history = execution.refresh(scenario[1], plan)
    assert history["provider_mode"] == "test"
    assert history["allowed_actions"] == []
    assert history["legs"][0]["continuation_id"] == plan["legs"][0]["lease_id"]


def test_declined_transaction_stays_unknown_without_an_automatic_retry(
    scenario, paymob
):
    plan = execution.ready(scenario)
    lease = Lease.objects.get(id=plan["legs"][0]["lease_id"])
    sign(lease)
    client, invoice, body = payments.rental_checkout((lease.owner, lease.tenant, lease))
    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=payments.intention,
    ) as create:
        assert payments.post_checkout(client, invoice, body).status_code == 201
        payment = PaymobPayment.objects.get()
        with patch(
            "core_apps.features.services.paymob_client.inquiry",
            return_value=payments.snapshot(payment, success=False),
        ):
            reconcile(payment)
        reconcile_progress()
        result = execution.refresh(lease.tenant, plan)
        assert result["state"] == "unknown"
        assert result["legs"][0]["state"] == "signed"
        assert result["legs"][0]["unknown_outcome"]
        assert create.call_count == 1
    assert PaymentAttempt.objects.count() == 1 and not PaymentReceipt.objects.exists()


def test_only_preparation_is_blocked_when_signing_configuration_is_missing(
    scenario, settings
):
    plan = execution.ready(scenario, prepare=False)
    settings.SIGNWELL_API_KEY = ""
    result = execution.refresh(scenario[1], plan)
    assert result["state"] == "ready"
    assert (
        "consents" in result["allowed_actions"]
        and "prepare" not in result["allowed_actions"]
    )
    assert result["blocking_reasons"] == ["signing_provider_unavailable"]
    assert not Lease.objects.exists()


def test_resuming_second_leg_does_not_repeat_first_signature_or_charge(
    scenario, paymob
):
    plan = execution.ready(scenario, two=True)
    leases = list(Lease.objects.order_by("pk"))

    def create_intention(payment, billing, return_url):
        value = payments.intention(payment, billing, return_url)
        return {
            **value,
            "id": f"pi_test_{payment.id}",
            "intention_order_id": 600000 + payment.pk,
        }

    def fund(lease):
        client, invoice, body = payments.rental_checkout(
            (lease.owner, lease.tenant, lease)
        )
        assert payments.post_checkout(client, invoice, body).status_code == 201
        payment = PaymobPayment.objects.get(attempt__invoice=invoice)
        proof = payments.snapshot(
            payment,
            id=900000 + payment.pk,
            order={
                "id": payment.order_id,
                "merchant_order_id": payment.reference,
            },
        )
        with patch(
            "core_apps.features.services.paymob_client.inquiry", return_value=proof
        ):
            reconcile(payment)

    with patch(
        "core_apps.features.services.paymob_client.create_intention",
        side_effect=create_intention,
    ) as create:
        sign(leases[0])
        fund(leases[0])
        interim = execution.refresh(scenario[0], plan)
        assert interim["confirmed_count"] == 1 and interim["state"] != "completed"
        reconcile_progress()
        first_attempt = PaymentAttempt.objects.get(invoice__lease=leases[0]).id
        sign(leases[1])
        fund(leases[1])
        reconcile_progress()
        reconcile_progress()
        assert execution.refresh(scenario[0], plan)["state"] == "completed"
        assert create.call_count == 2
    assert PaymentAttempt.objects.count() == PaymentReceipt.objects.count() == 2
    assert PaymentAttempt.objects.get(invoice__lease=leases[0]).id == first_attempt
    assert all(lease.signing_sessions.count() == 2 for lease in leases)


def test_company_plan_retains_independent_contract_reviews_and_private_destinations(
    company_setup, settings
):
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "corporate_housing_simulation",
        "corporate_housing_execution",
        "conditional_group_execution",
    ]
    plan, actors = company_execution.corporate_execution_setup(company_setup)
    company_execution.consent_and_prepare(plan, actors)
    response = authenticated(actors[1]).get(API + f"advanced-executions/{plan.id}/")
    assert response.status_code == 200, response.data
    assert all(
        row["continuation_kind"] == "company_prepare" for row in response.data["legs"]
    )
    assert not Lease.objects.exists() and not PaymentAttempt.objects.exists()
    assert all(row["available_steps"] == [] for row in response.data["legs"])
    employee = authenticated(actors[-1]).get(API + f"advanced-executions/{plan.id}/")
    assert employee.status_code == 200, employee.data
    assert all(
        row["continuation_kind"] == ""
        and row["terms"] == {}
        and not row["can_withdraw"]
        for row in employee.data["legs"]
    )
    leg = plan.legs.first()
    denied = company_execution.execution_command(
        plan, actors[-1], "withdraw", leg_id=str(leg.id)
    )
    assert denied.status_code in {403, 404}, denied.data
    result = company_execution.execution_command(
        plan, actors[1], "withdraw", leg_id=str(leg.id)
    )
    assert result.status_code == 200, result.data
    assert result.data["resource"]["state"] == "manual_resolution"


def test_company_preparation_cannot_change_execution_participants(
    company_setup, settings
):
    from core_apps.features.services.advanced_execution.progress import (
        validate_company_preparation,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict
    from core_apps.features.models import CompanyBookingItem

    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "corporate_housing_simulation",
        "corporate_housing_execution",
        "conditional_group_execution",
    ]
    plan, actors = company_execution.corporate_execution_setup(company_setup)
    leg = plan.legs.first()
    terms = leg.specification["terms"]
    booking = CompanyBookingItem.objects.get(id=leg.canonical_id)
    snapshot = {
        **{
            key: terms[key]
            for key in [
                "signer_id",
                "owner_id",
                "starts_on",
                "ends_on_exclusive",
                "deposit_minor",
                "full_term_rent_minor",
            ]
        },
        "payer_id": terms["payer_authorizer_id"],
        "booking_digest": terms["snapshot_digest"],
        "placements": [
            {"employee_id": row["actor_id"], "property_id": row["property_id"]}
            for row in terms["placements"]
        ],
    }
    validate_company_preparation(booking, snapshot)
    with pytest.raises(RentalConflict):
        validate_company_preparation(
            booking, {**snapshot, "signer_id": str(actors[-1].id)}
        )
    with pytest.raises(RentalConflict):
        validate_company_preparation(booking, {**snapshot, "placements": []})
