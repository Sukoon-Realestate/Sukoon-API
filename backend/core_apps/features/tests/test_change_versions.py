"""Version-specific amendment, renewal and payment extension authoring."""
import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import connections
from django.utils import timezone
from core_apps.features.models import RentalChange, RentInvoice, RentalChangeVersion
from .test_rental_phase5 import phase5_lease, client_for
from .test_rental_phase2 import agreement_terms

API = '/api/v1/features/v1/'
pytestmark = pytest.mark.django_db


def command(revision=0, **values):
    return {'expected_revision': revision, 'request_key': str(uuid.uuid4()), **values}


def create(lease, author, kind='amendment'):
    terms = copy.deepcopy(lease.terms) if kind == 'amendment' else agreement_terms(lease.end_date, lease.end_date + timedelta(days=90))
    terms['monthly_rent']['amount_minor'] = 900000
    result = client_for(author).post(API + f'leases/{lease.id}/{kind}s/', command(
        lease_revision=lease.revision, terms=terms, reason='Please update the rent',
        effective_on=str(timezone.localdate()) if kind == 'amendment' else str(lease.end_date),
    ), format='json')
    assert result.status_code == 201, result.data
    return RentalChange.objects.get(id=result.data['resource']['id'])


def edit(item, author, **values):
    data = command(item.revision, lease_revision=item.lease.revision, reason='Corrected proposal',
                   terms=item.terms, evidence_ids=[], invoice_id=str(item.invoice.id) if item.invoice_id else None)
    if item.effective_on: data['effective_on'] = str(item.effective_on)
    data.update(values)
    endpoint = 'payment-extension-requests' if item.kind == 'payment_extension' else item.kind + 's'
    return client_for(author).patch(API + f'{endpoint}/{item.id}/', data, format='json'), data


def respond(item, actor, action, **values):
    endpoint = 'payment-extension-requests' if item.kind == 'payment_extension' else item.kind + 's'
    return client_for(actor).post(API + f'{endpoint}/{item.id}/respond/', command(item.revision, action=action, **values), format='json')


@pytest.mark.parametrize('kind', ['amendment', 'renewal'])
def test_author_correction_requires_new_consent_and_preserves_signed_base(phase5_lease, kind):
    owner, tenant, lease = phase5_lease
    original = copy.deepcopy(lease.terms)
    item = create(lease, tenant, kind)
    assert edit(item, owner)[0].status_code == 403
    assert respond(item, tenant, 'request_changes').status_code == 403
    asked = respond(item, owner, 'request_changes', note='Please include water')
    assert asked.status_code == 200, asked.data
    item.refresh_from_db()
    assert item.approvals == []
    assert respond(item, owner, 'accept').status_code == 403
    terms = copy.deepcopy(item.terms); terms['included_services'] = ['Water']
    result, body = edit(item, tenant, terms=terms)
    assert result.status_code == 200, result.data
    item.refresh_from_db()
    assert item.content_revision == 2 and item.status == 'proposed'
    assert item.approvals == [str(tenant.id)]
    assert item.versions.count() == 2
    assert item.versions.get(version=1).snapshot['terms']['included_services'] == []
    assert result.data['resource']['comments'][0]['note'] == 'Please include water'
    replay = client_for(tenant).patch(API + f'{kind}s/{item.id}/', body, format='json')
    assert replay.status_code == 200 and replay.data == result.data
    stale = client_for(owner).post(API + f'{kind}s/{item.id}/respond/', command(1, action='accept'), format='json')
    assert stale.status_code == 409
    accepted = respond(item, owner, 'accept')
    assert accepted.status_code == 200, accepted.data
    item.refresh_from_db()
    assert item.status == 'accepted'
    assert edit(item, tenant)[0].status_code == 403
    lease.refresh_from_db()
    assert lease.terms == original
    assert item.previous_terms == original
    submit = client_for(owner).post(API + f'{kind}s/{item.id}/submit-for-signature/', command(item.revision), format='json')
    assert submit.status_code == 200, submit.data
    item.refresh_from_db()
    assert item.document_id and item.status == 'pending_signatures'
    assert edit(item, tenant)[0].status_code == 403


def test_proposal_edit_and_review_work_without_signing_provider(phase5_lease, settings):
    settings.RENTAL_PROVIDER_BACKEND = 'disabled'; settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    owner, tenant, lease = phase5_lease
    item = create(lease, owner)
    edited, _ = edit(item, owner)
    assert edited.status_code == 200, edited.data
    item.refresh_from_db()
    assert respond(item, tenant, 'accept').status_code == 200
    item.refresh_from_db()
    detail = client_for(owner).get(API + f'amendments/{item.id}/')
    assert 'submit_for_signature' not in detail.data['allowed_actions']
    assert item.document_id is None


def test_extension_revision_keeps_invoice_and_applies_once_after_new_consent(phase5_lease):
    owner, tenant, lease = phase5_lease
    invoice = RentInvoice.objects.create(lease=lease, purpose='rent', amount_minor=1000000,
        due_at=timezone.now(), due_date=timezone.localdate(), status='due')
    due = invoice.due_at
    result = client_for(tenant).post(API + f'leases/{lease.id}/payment-extension-requests/', command(
        lease_revision=lease.revision, invoice_id=str(invoice.id), requested_date=str(timezone.localdate() + timedelta(days=3)),
        reason='Delay salary',
    ), format='json')
    assert result.status_code == 201, result.data
    item = RentalChange.objects.get(id=result.data['resource']['id'])
    requested = timezone.localdate() + timedelta(days=5)
    edited, _ = edit(item, tenant, requested_date=str(requested))
    assert edited.status_code == 200, edited.data
    item.refresh_from_db(); invoice.refresh_from_db()
    assert invoice.deferred_until is None and invoice.due_at == due
    assert respond(item, owner, 'accept').status_code == 200
    item.refresh_from_db(); invoice.refresh_from_db()
    assert item.status == 'applied' and invoice.deferred_until.date() == requested
    assert invoice.due_at == due
    assert edit(item, tenant, requested_date=str(requested))[0].status_code == 403


@pytest.mark.django_db(transaction=True)
def test_edit_and_accept_cannot_approve_different_content(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = create(lease, owner)
    barrier = Barrier(2)
    def run(actor, editing):
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            return (edit(item, actor)[0] if editing else respond(item, actor, 'accept')).status_code
        finally: connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda pair: run(*pair), [(owner, True), (tenant, False)]))
    assert sorted(statuses) == [200, 409]
    item.refresh_from_db()
    assert (item.status, item.content_revision) in {('accepted', 1), ('proposed', 2)}


def test_changed_contract_base_needs_author_review_again(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = create(lease, owner)
    lease.terms = {**lease.terms, "included_services": ["Internet"]}
    lease.revision += 1
    lease.save()
    assert respond(item, tenant, "accept").status_code == 409
    item.refresh_from_db()
    item.lease = lease
    edited, _ = edit(item, owner)
    assert edited.status_code == 200, edited.data
    item.refresh_from_db()
    assert respond(item, tenant, "accept").status_code == 200


def test_settled_invoice_cannot_receive_pending_extension(phase5_lease):
    owner, tenant, lease = phase5_lease
    invoice = RentInvoice.objects.create(lease=lease, purpose="rent", amount_minor=1000000,
        due_at=timezone.now(), due_date=timezone.localdate(), status="due")
    created = client_for(tenant).post(API + f"leases/{lease.id}/payment-extension-requests/", command(
        lease_revision=lease.revision, invoice_id=str(invoice.id), requested_date=str(timezone.localdate() + timedelta(days=3)),
        reason="Delay salary"), format="json")
    assert created.status_code == 201, created.data
    item = RentalChange.objects.get(id=created.data["resource"]["id"])
    invoice.status = "paid"; invoice.save()
    assert respond(item, owner, "accept").status_code == 409
    invoice.refresh_from_db()
    assert invoice.deferred_until is None
