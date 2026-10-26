"""Local PostgreSQL proof of private, versioned bilateral negotiation."""
import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import connections
from django.utils import timezone

from core_apps.features.models import TermsProposal, TermsProposalVersion, ReservationHold, RentalInventoryDayLock
from core_apps.features.services.negotiation_terms import expire_due
from core_apps.features.services.rental_phase2 import add_months
from .test_rental_phase2 import authenticated, rental_participants, agreement_terms, complete_owner_onboarding
from .test_rental_lifecycle import policy, confirm, hold_body

API = '/api/v1/features/v1/'
pytestmark = pytest.mark.django_db


def create(rental_participants, *, tenant_authored=False, expires=None):
    owner, tenant, _, prop, offer = rental_participants
    start = timezone.localdate() + timedelta(days=10)
    interest = authenticated(tenant).post(API + 'rental-interests/', {
        'property_id': str(prop.id), 'offer_id': offer, 'offer_revision': 2,
        'desired_start': str(start), 'months': 1, 'occupants': 1,
        'request_key': str(uuid.uuid4()), 'expected_revision': 0,
    }, format='json')
    assert interest.status_code == 201, interest.data
    terms = agreement_terms(start, add_months(start, 1))
    terms['monthly_rent']['amount_minor'] = 850000
    body = {
        'interest_id': interest.data['resource']['id'], 'interest_revision': 1,
        'offer_id': offer, 'offer_revision': 2, 'terms': terms,
        'expires_at': (expires or (timezone.now() + timedelta(days=1))).isoformat(),
        'request_key': str(uuid.uuid4()), 'expected_revision': 0,
    }
    actor = tenant if tenant_authored else owner
    result = authenticated(actor).post(API + 'terms-proposals/', body, format='json')
    assert result.status_code == 201, result.data
    return TermsProposal.objects.get(id=result.data['resource']['id']), body, result


def decide(actor, proposal, decision='accept', **values):
    return authenticated(actor).post(API + f'terms-proposals/{proposal.id}/respond/', {
        'expected_revision': proposal.revision, 'request_key': str(uuid.uuid4()),
        'decision': decision, **values,
    }, format='json')


def edit(actor, proposal, source, **changes):
    body = copy.deepcopy(source)
    body.update(expected_revision=proposal.revision, interest_revision=proposal.interest.revision,
                request_key=str(uuid.uuid4()), **changes)
    return authenticated(actor).patch(API + f'terms-proposals/{proposal.id}/', body, format='json')


def test_counter_author_and_content_history_without_provider(rental_participants, settings):
    settings.RENTAL_PROVIDER_BACKEND = 'disabled'
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    owner, tenant, stranger, _, _ = rental_participants
    proposal, source, initial = create(rental_participants, tenant_authored=True)
    assert proposal.author == tenant
    assert proposal.accepted_by == [str(tenant.id)]
    assert not ReservationHold.objects.exists()
    read = authenticated(owner).get(API + f'terms-proposals/{proposal.id}/')
    assert set(read.data['allowed_actions']) == {'counter_terms', 'accept', 'reject', 'request_changes'}
    assert authenticated(stranger).get(API + f'terms-proposals/{proposal.id}/').status_code == 404
    assert edit(owner, proposal, source, action='edit_terms').status_code == 403
    terms = copy.deepcopy(source['terms'])
    terms['monthly_rent']['amount_minor'] = 900000
    counter = edit(owner, proposal, source, action='counter_terms', terms=terms)
    assert counter.status_code == 200, counter.data
    proposal.refresh_from_db()
    assert proposal.content_revision == 2 and proposal.author == owner
    assert proposal.accepted_by == [str(owner.id)]
    assert proposal.versions.count() == 2
    assert proposal.versions.get(version=1).terms['monthly_rent']['amount_minor'] == 850000
    stale = authenticated(tenant).post(API + f'terms-proposals/{proposal.id}/respond/', {
        'expected_revision': 1, 'request_key': str(uuid.uuid4()), 'decision': 'accept',
    }, format='json')
    assert stale.status_code == 409
    deadline = proposal.expires_at
    accepted = decide(tenant, proposal)
    assert accepted.status_code == 200, accepted.data
    proposal.refresh_from_db()
    assert proposal.status == 'accepted' and proposal.expires_at == deadline
    assert not ReservationHold.objects.exists()
    assert edit(owner, proposal, source).status_code == 403
    assert decide(tenant, proposal, 'withdraw').status_code == 400
    withdrawn = decide(tenant, proposal, 'withdraw', note='Changed plans')
    assert withdrawn.status_code == 200, withdrawn.data
    assert withdrawn.data['resource']['withdrawal_reason'] == 'Changed plans'
    assert len(withdrawn.data['resource']['history']) == 2
    replay = authenticated(tenant).get(API + f"rental-operations/{source['request_key']}/?subject_id={source['interest_id']}")
    assert replay.status_code == 200
    assert TermsProposalVersion.objects.count() == 2


@pytest.mark.parametrize('field,value', [('termination_policy', {'notice_days': 60}), ('renewal_policy', {'automatic': True}), ('commission_rate_bps', 0)])
def test_nonnegotiable_policy_fields_rejected(rental_participants, field, value):
    owner, _, _, _, _ = rental_participants
    proposal, source, _ = create(rental_participants)
    terms = copy.deepcopy(source['terms']); terms[field] = value
    assert edit(owner, proposal, source, terms=terms).status_code == 400
    proposal.refresh_from_db()
    assert proposal.content_revision == 1


def test_fixed_deadline_stops_accept_and_new_holds(rental_participants, policy):
    owner, tenant, _, prop, _ = rental_participants
    proposal, _, _ = create(rental_participants)
    TermsProposal.objects.filter(pk=proposal.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    proposal.refresh_from_db()
    assert decide(tenant, proposal).status_code == 409
    assert expire_due() == 1
    assert expire_due() == 0
    proposal.refresh_from_db()
    assert proposal.status == 'expired'
    assert not proposal.accepted_by == [str(owner.id), str(tenant.id)]
    assert not RentalInventoryDayLock.objects.exists()


def test_agreed_price_survives_public_price_but_not_unit_change(rental_participants, policy):
    owner, tenant, _, prop, _ = rental_participants
    proposal, _, _ = create(rental_participants)
    assert decide(tenant, proposal).status_code == 200
    proposal.refresh_from_db()
    inventory = copy.deepcopy(prop.rental_inventory)
    inventory['revision'] += 1
    inventory['offers'][0]['revision'] += 1
    inventory['offers'][0]['terms']['price'] = '12000'
    prop.rental_inventory = inventory; prop.save(update_fields=['rental_inventory'])
    confirm(prop)
    body = hold_body(proposal)
    body['offer_revision'] = 3; body['inventory_revision'] = 2
    held = authenticated(tenant).post(API + 'reservation-holds/', body, format='json')
    assert held.status_code == 201, held.data
    hold = ReservationHold.objects.get(id=held.data['resource']['id'])
    assert hold.terms_digest
    assert proposal.terms['monthly_rent']['amount_minor'] == 850000
    assert decide(owner, proposal, 'withdraw', note='Changed plans').status_code == 409
    assert edit(owner, proposal, {'terms': proposal.terms, 'offer_id': proposal.interest.offer_id,
        'offer_revision': 3, 'interest_id': str(proposal.interest.id), 'expires_at': proposal.expires_at.isoformat()}).status_code == 403
    complete_owner_onboarding(owner)
    # A hold accepted before expiry continues under its existing hold deadline.
    TermsProposal.objects.filter(pk=proposal.pk).update(expires_at=hold.created_at + timedelta(microseconds=1))
    proposal.refresh_from_db()
    interest = proposal.interest
    invitation = authenticated(owner).post(API + 'tenancy-invitations/', {
        'request_key': str(uuid.uuid4()), 'expected_revision': 0,
        'interest_id': str(interest.id), 'interest_revision': interest.revision,
        'property_id': str(prop.id), 'tenant_id': str(tenant.id),
        'offer_id': interest.offer_id, 'offer_revision': 2, 'terms_proposal_id': str(proposal.id),
    }, format='json')
    assert invitation.status_code == 201, invitation.data
    assert expire_due() == 0
    invite = invitation.data['resource']
    accepted = authenticated(tenant).post(API + f"tenancy-invitations/{invite['id']}/respond/", {
        'decision': 'accepted', 'revision': invite['revision'], 'request_key': str(uuid.uuid4()),
    }, format='json')
    assert accepted.status_code == 200, accepted.data
    lease_result = authenticated(owner).post(API + 'leases/', {
        'invitation_id': invite['id'], 'invitation_revision': accepted.data['revision'],
        'property_id': str(prop.id), 'offer_id': interest.offer_id, 'offer_revision': 2,
        'tenant_id': str(tenant.id), 'terms': proposal.terms,
        'request_key': str(uuid.uuid4()), 'expected_revision': 0,
    }, format='json')
    assert lease_result.status_code == 201, lease_result.data
    from core_apps.features.models import Lease
    from core_apps.features.services.rental_phase3 import generate_billing_schedule
    lease = Lease.objects.get(id=lease_result.data['resource']['id'])
    hold.refresh_from_db()
    assert hold.lease_id == lease.pk
    assert lease.rent_amount_minor == 850000
    assert list(generate_billing_schedule(lease))[0].invoice.amount_minor == 850000
    inventory['offers'][0]['capacity'] = 1
    prop.rental_inventory = inventory; prop.save(update_fields=['rental_inventory'])
    from core_apps.features.services.negotiation_terms import current_selection
    from core_apps.features.services.rental_phase2 import RentalConflict
    proposal.interest.property = prop
    with pytest.raises(RentalConflict): current_selection(proposal)


@pytest.mark.django_db(transaction=True)
def test_accept_and_edit_are_serialized(rental_participants):
    owner, tenant, _, _, _ = rental_participants
    proposal, source, _ = create(rental_participants)
    barrier = Barrier(2)
    def run(actor, editing):
        connections.close_all()
        barrier.wait()
        try:
            item = TermsProposal.objects.select_related('interest').get(pk=proposal.pk)
            # Both participants act on the same reviewed revision.
            item.revision = proposal.revision
            if editing:
                return edit(actor, item, source).status_code
            return decide(actor, item).status_code
        finally: connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda args: run(*args), [(owner, True), (tenant, False)]))
    assert sorted(results) == [200, 409]
    proposal.refresh_from_db()
    assert proposal.revision == 2
    assert (proposal.status, proposal.content_revision) in [('accepted', 1), ('proposed', 2)]


def test_private_property_projection_has_no_other_account_or_unit_terms(rental_participants):
    _, tenant, stranger, prop, offer = rental_participants
    proposal, _, _ = create(rental_participants)
    assert decide(tenant, proposal).status_code == 200
    query = {'workspace': 'individual', 'property_id': str(prop.id), 'offer_id': offer, 'active_agreements': True}
    own = authenticated(tenant).get(API + 'terms-proposals/', query)
    assert own.status_code == 200
    assert [row['id'] for row in own.data['results']] == [str(proposal.id)]
    assert authenticated(stranger).get(API + 'terms-proposals/', query).data['results'] == []
    assert authenticated(tenant).get(API + 'terms-proposals/', {**query, 'offer_id': 'other-unit'}).data['results'] == []
    assert authenticated(tenant).get(API + 'terms-proposals/', {**query, 'workspace': 'student'}).data['results'] == []
    assert authenticated(tenant).get(API + 'terms-proposals/', {**query, 'property_id': 'invalid'}).status_code == 400


def test_stale_notification_keeps_recorded_change_and_opens_current_decision_history(rental_participants):
    from unittest.mock import patch
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.planning_notifications import deliver_planning_events

    owner, tenant, _, _, _ = rental_participants
    proposal, source, _ = create(rental_participants)
    changed = decide(tenant, proposal, 'request_changes', note='Please include water')
    assert changed.status_code == 200, changed.data
    proposal.refresh_from_db()
    edited = edit(owner, proposal, source)
    assert edited.status_code == 200, edited.data
    assert edited.data['resource']['decisions'][1]['note'] == 'Please include water'
    with patch('core_apps.notifications.services.fcm_service.FCMService.send_push_to_user', return_value=1):
        deliver_planning_events()
        assert deliver_planning_events() == 0
    old = PlanningEvent.objects.get(recipient=tenant, destination__event_kind='terms.proposed')
    assert old.notification_id is not None
    assert old.notification.data['content_version'] == 1
    assert old.notification.scope == 'individual'
    assert old.notification.data['terms_proposal_id'] == str(proposal.id)
    current = authenticated(tenant).get(API + f'terms-proposals/{proposal.id}/').data
    assert current['content_revision'] == 2 and len(current['history']) == 2
    assert any(row['note'] == 'Please include water' for row in current['decisions'])
