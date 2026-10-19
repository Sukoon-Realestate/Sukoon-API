"""Behavioral proofs for consent, financial uncertainty, role boundaries and backfill."""

import copy
import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone

from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    ApplicationAccessGrant,
    Lease,
    RentalInventoryDayLock,
    RentalOperationalCase,
    PaymentAttempt,
    ProviderWebhookEvent,
    CheckoutSession,
    LedgerTransaction,
    GroupBookingProposal,
    GroupBookingParticipant,
    RentalConsentRecord,
    RentalVerificationClaim,
    RentalProviderInstruction,
)
from core_apps.features.planning_models import (
    HousingGroup,
    GroupMembership,
    GroupProcess,
)
from core_apps.features.services.rental_lifecycle.inventory import (
    expire_property_holds,
    hold_coverage,
    allocate_days,
)
from core_apps.features.services.rental_lifecycle.claims import claim_current
from core_apps.features.services.rental_lifecycle.cases import open_system_case
from core_apps.features.services.rental_phase3 import (
    generate_billing_schedule,
    process_provider_event,
)
from core_apps.features.tasks_parts.expire_rental_sources_and_holds import (
    reconcile_ambiguous_rental_payments,
)
from core_apps.features.tests.test_rental_lifecycle import (
    policy,
    rental_participants,
    command,
    post,
    PREFIX,
    proposal_for,
    confirm,
    hold_body,
)
from core_apps.features.tests.test_rental_phase2 import (
    authenticated,
    complete_owner_onboarding,
    agreement_terms,
)
from core_apps.features.tests.test_rental_phase3 import phase3_lease
from core_apps.properties.models import Property
from core_apps.users.models import User


def checkout(tenant, lease):
    invoice = list(generate_billing_schedule(lease))[0].invoice
    quote = post(
        tenant,
        f"rent-invoices/{invoice.id}/quote/",
        command(invoice.revision, action="quote"),
    )
    assert quote.status_code == 201, quote.data
    result = post(
        tenant,
        f"rent-invoices/{invoice.id}/checkout/",
        command(
            invoice.revision,
            invoice_id=str(invoice.id),
            quote_id=quote.data["resource"]["quote_id"],
        ),
    )
    assert result.status_code == 201, result.data
    return PaymentAttempt.objects.get(id=result.data["resource"]["payment_attempt_id"])


def event(attempt, kind, *, verified=True):
    payload = dict(amount_minor=attempt.amount_minor, currency=attempt.currency)
    return ProviderWebhookEvent.objects.create(
        provider="fake",
        provider_event_id=str(uuid.uuid4()),
        event_type=f"payment.{kind}",
        payment_attempt=attempt,
        payload_digest="a" * 64,
        signature_valid=verified,
        payload=payload,
    )


def operator(role):
    user = User.objects.create_user(
        email=f"{uuid.uuid4()}@example.test",
        password="pass",
        is_verified=True,
        is_staff=True,
    )
    StaffProfile.objects.create(user=user, role_name=role)
    return user


@pytest.mark.django_db
def test_unknown_checkout_retains_original_attempt_and_opens_case(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    CheckoutSession.objects.filter(attempt=attempt).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )
    result = reconcile_ambiguous_rental_payments.run()
    assert result["attempts_expired"] == 0
    attempt.refresh_from_db()
    assert attempt.payment_status in {"created", "pending", "authorized"}
    assert RentalOperationalCase.objects.filter(
        payment_attempt=attempt, kind="payment_unknown"
    ).exists()
    assert PaymentAttempt.objects.filter(invoice=attempt.invoice).count() == 1
    again = post(
        tenant,
        f"rent-invoices/{attempt.invoice.id}/checkout/",
        command(
            attempt.invoice.revision,
            invoice_id=str(attempt.invoice.id),
            quote_id=str(attempt.quote.id),
        ),
    )
    assert again.status_code == 409, again.data
    assert PaymentAttempt.objects.filter(invoice=attempt.invoice).count() == 1


@pytest.mark.django_db
def test_unknown_payment_protects_expired_inventory(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    lease.offer_snapshot = {"rental_scope": "entire_property"}
    lease.save()
    with transaction.atomic():
        prop = Property.objects.select_for_update().get(pk=lease.property_id)
        allocate_days(
            prop=prop,
            snapshot=lease.offer_snapshot,
            offer_id=lease.offer_id,
            starts_on=lease.start_date,
            ends_on=lease.end_date,
            expires_at=timezone.now() - timedelta(seconds=1),
            lease=lease,
        )
        before = lease.inventory_day_locks.count()
        expire_property_holds(prop)
        assert lease.inventory_day_locks.count() == before
    assert RentalOperationalCase.objects.filter(
        lease=lease, kind="payment_unknown"
    ).exists()
    attempt.refresh_from_db()
    assert attempt.payment_status != "expired"


@pytest.mark.django_db
def test_chargeback_before_capture_and_duplicate_events_are_monotonic(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    reversal = event(attempt, "chargeback")
    process_provider_event(reversal)
    reversal.refresh_from_db()
    assert reversal.processed is False
    process_provider_event(event(attempt, "captured"))
    attempt.refresh_from_db()
    assert attempt.payment_status == "chargedback"
    reversal.refresh_from_db()
    assert reversal.processed
    process_provider_event(event(attempt, "captured"))
    process_provider_event(event(attempt, "failed"))
    duplicate = event(attempt, "chargeback")
    duplicate.payload = {**duplicate.payload, "dispute_id": reversal.provider_event_id}
    duplicate.save()
    process_provider_event(duplicate)
    attempt.refresh_from_db()
    assert attempt.payment_status == "chargedback"
    assert (
        LedgerTransaction.objects.filter(
            payment_attempt=attempt, kind="chargeback"
        ).count()
        == 1
    )
    assert attempt.invoice.applied_minor == 0


@pytest.mark.django_db
def test_unsigned_event_cannot_move_money(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    from core_apps.features.services.rental_phase2 import RentalConflict

    with pytest.raises(RentalConflict):
        process_provider_event(event(attempt, "captured", verified=False))
    attempt.refresh_from_db()
    assert attempt.payment_status not in {"captured", "chargedback"}
    assert not LedgerTransaction.objects.filter(payment_attempt=attempt).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["expired", "cancelled"])
def test_late_initial_capture_records_money_without_reclaiming_allocated_accommodation(
    phase3_lease, status
):
    owner, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    lease.status, lease.activated_at = status, None
    lease.hold_expires_at = timezone.now() - timedelta(minutes=1)
    lease.save()
    other = User.objects.create_user(
        email="replacement-allocation@example.test", password="pass", is_verified=True
    )
    successor = Lease.objects.create(
        property=lease.property,
        owner=owner,
        tenant=other,
        start_date=lease.start_date,
        end_date=lease.end_date,
        offer_id=lease.offer_id,
        rent_amount_minor=lease.rent_amount_minor,
        status="active",
        legacy_read_only=False,
    )
    with transaction.atomic():
        prop = Property.objects.select_for_update().get(pk=lease.property_id)
        allocate_days(
            prop=prop,
            snapshot={"rental_scope": "entire_property"},
            offer_id=lease.offer_id,
            starts_on=lease.start_date,
            ends_on=lease.end_date,
            expires_at=None,
            lease=successor,
        )
    before = set(successor.inventory_day_locks.values_list("id", flat=True))
    process_provider_event(event(attempt, "captured"))
    process_provider_event(event(attempt, "captured"))
    lease.refresh_from_db()
    attempt.refresh_from_db()
    assert lease.status == status and lease.activated_at is None
    assert (
        attempt.payment_status == "captured"
        and attempt.failure_code == "activation_review_required"
    )
    assert (
        RentalOperationalCase.objects.filter(
            payment_attempt=attempt, kind="capture_after_release"
        ).count()
        == 1
    )
    assert (
        LedgerTransaction.objects.filter(
            reference=f"payment-captured:{attempt.id}"
        ).count()
        == 1
    )
    assert set(successor.inventory_day_locks.values_list("id", flat=True)) == before
    assert lease.inventory_day_locks.count() == 0


@pytest.mark.django_db
def test_cases_require_responsible_role_and_executed_remedy(phase3_lease):
    owner, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    support = operator("support")
    finance = operator("psp_reconciliation")
    item = open_system_case(
        kind="payment_unknown",
        source_key="unknown-test",
        lease=lease,
        attempt=attempt,
        reason="Unknown outcome",
        next_action="Query original reference",
    )
    assert (
        authenticated(support).get(PREFIX + f"rental-cases/{item.id}/").status_code
        == 404
    )
    assert (
        authenticated(tenant).get(PREFIX + "operations/rental-cases/").status_code
        == 403
    )
    result = post(
        finance,
        f"rental-cases/{item.id}/actions/",
        command(
            1,
            action="assign",
            assignee_id=str(finance.id),
            reason="Finance takes responsibility",
        ),
    )
    assert result.status_code == 200, result.data
    result = post(
        finance,
        f"rental-cases/{item.id}/actions/",
        command(
            2,
            action="resolve",
            resolution_code="no_action_required",
            reason="Time elapsed",
        ),
    )
    assert result.status_code == 409, result.data
    assert (
        post(
            tenant,
            f"rental-cases/{item.id}/actions/",
            command(
                2, action="resolve", resolution_code="corrected", reason="Close it"
            ),
        ).status_code
        == 403
    )
    reply = post(
        tenant,
        f"rental-cases/{item.id}/actions/",
        command(
            2, action="reply", reason="Please keep the original payment reference."
        ),
    )
    assert reply.status_code == 200, reply.data
    assert (
        reply.data["resource"]["replies"][0]["text"]
        == "Please keep the original payment reference."
    )
    attempt.payment_status = "failed"
    attempt.save()
    result = post(
        finance,
        f"rental-cases/{item.id}/actions/",
        command(
            3,
            action="resolve",
            resolution_code="refund_executed",
            reason="Cannot invent a refund",
        ),
    )
    assert result.status_code == 409
    result = post(
        finance,
        f"rental-cases/{item.id}/actions/",
        command(
            3,
            action="resolve",
            resolution_code="no_action_required",
            reason="Provider verified no capture",
        ),
    )
    assert result.status_code == 200, result.data
    assert result.data["resource"]["status"] == "resolved"


@pytest.mark.django_db
def test_answer_becomes_new_terms_and_invalidates_prior_free_hold(
    rental_participants, policy
):
    owner, tenant, _, prop, offer = rental_participants
    confirm(prop)
    proposal = proposal_for(tenant, prop, offer)
    result = post(tenant, "reservation-holds/", hold_body(proposal))
    assert result.status_code == 201, result.data
    body = command(
        proposal.revision,
        field="included_services",
        wording="Internet is included in the monthly rent.",
    )
    result = post(owner, f"terms-proposals/{proposal.id}/propose-answer/", body)
    assert result.status_code == 200, result.data
    proposal.refresh_from_db()
    assert proposal.status == "proposed"
    assert proposal.accepted_by == [str(owner.id)]
    assert proposal.previous_terms[0]["included_services"] == []
    assert not RentalInventoryDayLock.objects.exists()
    assert (
        post(owner, f"terms-proposals/{proposal.id}/propose-answer/", body).data
        == result.data
    )
    assert RentalConsentRecord.objects.filter(subject_id=proposal.id).count() == 1


@pytest.mark.django_db
def test_hold_coverage_rejects_shifted_dates_even_when_row_count_matches(
    rental_participants, policy
):
    owner, tenant, _, prop, offer = rental_participants
    confirm(prop)
    proposal = proposal_for(tenant, prop, offer)
    result = post(tenant, "reservation-holds/", hold_body(proposal))
    from core_apps.features.models import ReservationHold
    from core_apps.features.services.rental_lifecycle.reservations import transfer_hold

    hold = ReservationHold.objects.get(id=result.data["resource"]["id"])
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        rent_amount_minor=1000000,
        start_date=hold.starts_on,
        end_date=hold.ends_on_exclusive,
        offer_id=offer,
        offer_snapshot=hold.selection_snapshot,
        terms=proposal.terms,
        legacy_read_only=False,
    )
    with transaction.atomic():
        Property.objects.select_for_update().get(pk=prop.pk)
        assert transfer_hold(lease, proposal)
    assert hold_coverage(lease)
    lease.inventory_day_locks.filter(stay_on=lease.start_date).update(
        stay_on=lease.end_date
    )
    assert not hold_coverage(lease)


@pytest.mark.django_db
def test_property_claim_cannot_survive_owner_or_review_change(rental_participants):
    owner, _, stranger, prop, _ = rental_participants
    reviewer = operator("property_reviewer")
    claim = RentalVerificationClaim.objects.create(
        subject_kind="property_authority",
        subject_user=owner,
        property=prop,
        claim_code="ownership_documents",
        public_wording="Ownership documents reviewed",
        reviewer=reviewer,
        evidence_reference="review-1",
        checked_at=timezone.now(),
    )
    assert claim_current(claim)
    prop.status = "pending"
    prop.save()
    claim.refresh_from_db()
    assert not claim_current(claim)
    prop.status = "verified"
    prop.owner = stranger
    prop.save()
    claim.refresh_from_db()
    assert not claim_current(claim)


def booking_setup(participants):
    owner, tenant, other, prop, old_offer = participants
    rooms = [str(uuid.uuid4()), str(uuid.uuid4())]
    offers = [str(uuid.uuid4()), str(uuid.uuid4())]
    inventory = copy.deepcopy(prop.rental_inventory)
    inventory["mode"] = "partial"
    inventory["rooms"] = [
        {"id": v, "name": f"Room {i+1}", "beds": []} for i, v in enumerate(rooms)
    ]
    inventory["offers"] = [
        dict(
            id=v,
            revision=1,
            rental_scope="room",
            room_ids=[room],
            name=f"Room {i+1}",
            availability="available",
            archived=False,
            capacity=1,
            terms={"price": "10000", "price_period": "monthly"},
        )
        for i, (v, room) in enumerate(zip(offers, rooms))
    ]
    prop.rental_inventory = inventory
    prop.save()
    complete_owner_onboarding(owner)
    group = HousingGroup.objects.create(name="Consent test group")
    for user in [tenant, other]:
        GroupMembership.objects.create(group=group, user=user)
    application = GroupProcess.objects.create(
        group=group,
        initiated_by=tenant,
        property=prop,
        kind="application",
        roster_revision=1,
        status="approved_to_proceed",
        participant_ids=[str(tenant.id), str(other.id)],
    )
    start = timezone.localdate() + timedelta(days=5)
    end = start + timedelta(days=30)
    body = command(
        application_id=str(application.id),
        application_revision=application.revision,
        roster_revision=1,
        booking_model="independent",
        deadline=(timezone.now() + timedelta(days=1)).isoformat(),
        participants=[
            dict(
                tenant_id=str(user.id),
                offer_id=offer,
                offer_revision=1,
                terms=agreement_terms(start, end),
            )
            for user, offer in zip([tenant, other], offers)
        ],
    )
    return application, body


@pytest.mark.django_db
def test_group_each_member_consents_only_for_self_no_automatic_lease_or_charge(
    rental_participants, policy
):
    owner, tenant, other, prop, _ = rental_participants
    application, body = booking_setup(rental_participants)
    created = post(owner, "group-booking-proposals/", body)
    assert created.status_code == 201, created.data
    proposal = created.data["resource"]
    base = f"group-booking-proposals/{proposal['id']}/"
    submitted = post(owner, base + "submit/", command(1))
    assert submitted.status_code == 200, submitted.data
    result = post(
        tenant,
        base + "consents/",
        command(2, decision="accept", terms_digest=proposal["terms_digest"]),
    )
    assert result.status_code == 200, result.data
    rows = list(
        GroupBookingParticipant.objects.filter(proposal__id=proposal["id"]).order_by(
            "pk"
        )
    )
    assert [row.consent_status for row in rows] == ["accepted", "pending"]
    assert rows[0].invitation_id and not rows[1].invitation_id
    assert not Lease.objects.exists() and not PaymentAttempt.objects.exists()
    assert (
        post(
            owner,
            base + "consents/",
            command(3, decision="accept", terms_digest=proposal["terms_digest"]),
        ).status_code
        == 409
    )
    application.group.roster_revision += 1
    application.group.save()
    assert (
        post(
            other,
            base + "consents/",
            command(3, decision="accept", terms_digest=proposal["terms_digest"]),
        ).status_code
        == 409
    )
    assert GroupBookingParticipant.objects.get(tenant=other).consent_status == "pending"


@pytest.mark.django_db
def test_group_conditional_bundle_and_overlapping_allocations_disabled(
    rental_participants, policy
):
    owner, *_ = rental_participants
    _, body = booking_setup(rental_participants)
    assert (
        post(
            owner,
            "group-booking-proposals/",
            {**body, "booking_model": "conditional_bundle"},
        ).status_code
        == 409
    )
    body["participants"][1]["offer_id"] = body["participants"][0]["offer_id"]
    assert post(owner, "group-booking-proposals/", body).status_code == 409
    assert not GroupBookingProposal.objects.exists()


@pytest.mark.django_db
def test_inventory_backfill_dry_run_and_safe_apply(rental_participants):
    owner, tenant, _, prop, offer = rental_participants
    proposal = proposal_for(tenant, prop, offer)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        rent_amount_minor=1000000,
        offer_id=offer,
        offer_snapshot=proposal.offer_snapshot,
        start_date=proposal.terms["starts_on"],
        end_date=proposal.terms["ends_on_exclusive"],
        legacy_read_only=False,
    )
    row = RentalInventoryDayLock.objects.create(
        property=prop,
        lease=lease,
        offer_id=offer,
        stay_on=lease.start_date,
        kind="occupied",
    )
    call_command(
        "reconcile_rental_inventory", property_id=str(prop.id), stdout=StringIO()
    )
    row.refresh_from_db()
    assert row.unit_id is None
    call_command(
        "reconcile_rental_inventory",
        property_id=str(prop.id),
        apply=True,
        stdout=StringIO(),
    )
    assert lease.inventory_day_locks.count() == 1
    assert lease.inventory_day_locks.get().unit_id is not None


@pytest.mark.django_db
def test_provider_instruction_identity_unknown_recovery_and_production_gate(
    phase3_lease, settings
):
    from core_apps.features.services.rental_lifecycle.provider_instructions import (
        prepare_instruction,
        mark_unknown,
        execute_local_instruction,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict

    _, _, lease = phase3_lease
    item = prepare_instruction(
        kind="refund",
        subject=lease,
        request_key="same-key",
        payload={"amount_minor": 100},
    )
    assert (
        prepare_instruction(
            kind="refund",
            subject=lease,
            request_key="same-key",
            payload={"amount_minor": 100},
        ).pk
        == item.pk
    )
    with pytest.raises(RentalConflict):
        prepare_instruction(
            kind="refund",
            subject=lease,
            request_key="same-key",
            payload={"amount_minor": 101},
        )
    mark_unknown(item)
    with pytest.raises(RentalConflict):
        execute_local_instruction(
            kind="refund",
            subject=lease,
            request_key="same-key",
            payload={"amount_minor": 100},
        )
    settings.RENTAL_PROVIDER = "unconfigured"
    with patch(
        "core_apps.features.services.rental_lifecycle.provider_instructions.fake_provider_available",
        return_value=False,
    ):
        with pytest.raises(RentalConflict):
            execute_local_instruction(
                kind="refund",
                subject=lease,
                request_key="new-key",
                payload={"amount_minor": 100},
            )
    assert RentalProviderInstruction.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_refunds_reserve_remaining_capture_once(phase3_lease):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, connections
    from core_apps.features.models import RefundRequest

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL connections required")
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    attempt.refresh_from_db()
    barrier = Barrier(2)

    def request_refund(_):
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            return post(
                tenant,
                "refund-requests/",
                command(
                    payment_attempt_id=str(attempt.id),
                    lease_id=str(lease.id),
                    payment_revision=attempt.revision,
                    amount={
                        "amount_minor": attempt.amount_minor,
                        "currency": "EGP",
                        "exponent": 2,
                    },
                    reason="Request original capture back",
                ),
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(request_refund, range(2)))
    assert sorted(statuses) == [201, 409], statuses
    assert (
        sum(RefundRequest.objects.values_list("amount_minor", flat=True))
        == attempt.amount_minor
    )


@pytest.mark.django_db
def test_overdue_case_escalation_has_one_audit_effect(phase3_lease):
    from core_apps.features.services.rental_lifecycle.jobs import (
        reconcile_lifecycle_deadlines,
    )
    from core_apps.features.models import RentalAuditEvent

    _, _, lease = phase3_lease
    item = open_system_case(
        kind="access_failure",
        source_key="overdue-access",
        lease=lease,
        reason="No keys",
        next_action="Contact owner",
    )
    RentalOperationalCase.objects.filter(pk=item.pk).update(
        due_at=timezone.now() - timedelta(minutes=1)
    )
    assert reconcile_lifecycle_deadlines()["escalated_cases"] == 1
    assert reconcile_lifecycle_deadlines()["escalated_cases"] == 0
    assert (
        RentalAuditEvent.objects.filter(
            subject_id=item.id, action="case.escalated"
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_export_lifecycle_contracts_from_http(rental_participants, policy):
    """Optional sanitized artifact consumed by the Flutter contract test."""
    import json, os
    from pathlib import Path

    owner, tenant, _, prop, offer = rental_participants
    artifacts = {}
    saved = authenticated(tenant).patch(
        PREFIX + "application-profile/",
        command(
            desired_start=str(timezone.localdate() + timedelta(days=5)),
            months=2,
            occupants=1,
            introduction="Synthetic application fixture",
        ),
        format="json",
    )
    assert saved.status_code == 200, saved.data
    artifacts["profile"] = saved.json()
    version = post(tenant, "application-profile/versions/", command(1))
    assert version.status_code == 201
    artifacts["version"] = version.json()
    preview_body = dict(
        version_id=version.data["resource"]["id"],
        property_id=str(prop.id),
        categories=["rental_preferences", "introduction"],
        expires_at=(timezone.now() + timedelta(days=1)).isoformat(),
    )
    review = post(tenant, "application-shares/preview/", preview_body)
    assert review.status_code == 200
    artifacts["share_review"] = review.json()
    shared = post(
        tenant,
        "application-shares/",
        command(1, **preview_body, consent_digest=review.data["consent_digest"]),
    )
    assert shared.status_code == 201
    artifacts["share"] = shared.json()
    confirm(prop)
    proposal = proposal_for(tenant, prop, offer)
    held = post(tenant, "reservation-holds/", hold_body(proposal))
    assert held.status_code == 201
    artifacts["hold"] = held.json()
    decision = authenticated(tenant).get(
        PREFIX + f"properties/{prop.id}/decision-summary/",
        {"offer_id": offer, "offer_revision": 2},
    )
    assert decision.status_code == 200
    artifacts["decision"] = decision.json()
    deal = authenticated(tenant).get(PREFIX + f"deals/{proposal.id}/")
    assert deal.status_code == 200
    artifacts["deal"] = deal.json()
    for envelope in artifacts.values():
        assert set(envelope) == {"message", "data"} and envelope["message"]
    if output := os.environ.get("SOKOUN_RENTAL_GAP_CONTRACT"):
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "environment": "isolated-postgresql-mock-only",
                    "responses": artifacts,
                },
                indent=2,
            )
        )


@pytest.mark.django_db
def test_policy_install_is_validated_dry_run_and_append_only(policy, tmp_path):
    import json
    from django.core.management.base import CommandError
    from core_apps.features.models import RentalCommercialPolicy
    from core_apps.features.tests.test_rental_lifecycle import RULES

    source = tmp_path / "reviewed-policy.json"
    value = {
        "version": "test-reviewed-v2",
        "base_policy_version": policy.version,
        "lifecycle_rules": {
            **RULES,
            "approval_reference": "Synthetic policy review fixture",
        },
    }
    source.write_text(json.dumps(value))
    call_command(
        "configure_rental_lifecycle_policy", input=str(source), stdout=StringIO()
    )
    assert not RentalCommercialPolicy.objects.filter(version=value["version"]).exists()
    call_command(
        "configure_rental_lifecycle_policy",
        input=str(source),
        apply=True,
        stdout=StringIO(),
    )
    installed = RentalCommercialPolicy.objects.get(version=value["version"])
    assert installed.commission_rate_bps == policy.commission_rate_bps
    assert installed.renewal_commission_rate_bps == 0
    with pytest.raises(CommandError, match="immutable"):
        call_command(
            "configure_rental_lifecycle_policy",
            input=str(source),
            apply=True,
            stdout=StringIO(),
        )
    value["version"] = "test-invalid-v3"
    value["lifecycle_rules"]["hold_minutes"] = 0
    source.write_text(json.dumps(value))
    with pytest.raises(CommandError):
        call_command(
            "configure_rental_lifecycle_policy",
            input=str(source),
            apply=True,
            stdout=StringIO(),
        )
    assert not RentalCommercialPolicy.objects.filter(version=value["version"]).exists()


@pytest.mark.django_db
def test_changed_beneficiary_holds_worker_instruction_and_opens_one_case(phase3_lease):
    from core_apps.features.models import OwnerPaymentProfile, PayoutBatch, RentalPayout
    from core_apps.features.tasks import reconcile_approved_payouts
    from core_apps.features.planning_models import PlanningEvent

    owner, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    profile = OwnerPaymentProfile.objects.create(
        owner=owner,
        status="ready",
        payout_ready=True,
        provider="fake",
        provider_account_id="synthetic-reviewed-beneficiary",
    )
    batch = PayoutBatch.objects.create(
        approved_by=operator("payout_operator"), request_key=uuid.uuid4()
    )
    payout = RentalPayout.objects.create(
        batch=batch,
        owner=owner,
        lease=lease,
        amount_minor=attempt.owner_payable.net_minor,
        beneficiary_profile_revision=profile.revision,
        beneficiary_provider=profile.provider,
        beneficiary_account_id=profile.provider_account_id,
    )
    payout.payables.add(attempt.owner_payable)
    payout.payables.update(payout_status="submitted")
    OwnerPaymentProfile.objects.filter(pk=profile.pk).update(
        revision=profile.revision + 1,
        provider_account_id="changed-beneficiary-must-not-be-paid",
    )
    assert reconcile_approved_payouts()["paid"] == 0
    assert reconcile_approved_payouts()["paid"] == 0
    payout.refresh_from_db()
    assert payout.status == "held"
    assert payout.failure_code == "beneficiary_changed"
    assert payout.provider_payout_id == ""
    assert payout.payables.get().payout_status == "submitted"
    assert not LedgerTransaction.objects.filter(
        reference=f"payout:{payout.id}"
    ).exists()
    item = RentalOperationalCase.objects.get(payout=payout)
    assert item.kind == "beneficiary_issue" and item.team == "finance"
    assert (
        PlanningEvent.objects.filter(destination__target_id=str(item.id)).count() == 2
    )
    assert (
        RentalProviderInstruction.objects.get(subject_id=payout.id).status == "pending"
    )
