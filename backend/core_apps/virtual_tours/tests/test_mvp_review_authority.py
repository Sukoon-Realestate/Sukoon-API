"""Private tour review uses current permissions and a distinct human reviewer."""
import pytest
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from core_apps.admin_api.models import StaffProfile
from core_apps.users.totp_models import StaffSecurityIdentity
from core_apps.virtual_tours import services, sessions
from core_apps.virtual_tours.errors import TourError
from .test_tours import ready_variant

pytestmark = pytest.mark.django_db


def test_tour_reviewer_cannot_use_another_account_of_the_same_person(property_obj, user, superuser):
    _, revision, _ = ready_variant(property_obj)
    revision.review_state = 'pending'
    revision.save(update_fields=['review_state'])
    for account in [user, superuser]:
        StaffSecurityIdentity.objects.update_or_create(user=account, defaults={
            'person_reference': 'synthetic-same-person',
            'evidence_reference': 'synthetic-private-evidence',
            'known_channel_reference': 'synthetic-known-channel',
        })
    with pytest.raises(TourError) as rejected:
        services.review(revision, superuser, {'decision': 'approved',
            'expected_source_hash': revision.source_hash, 'reason': 'Different account, same person'})
    assert rejected.value.status_code == 403
    revision.refresh_from_db()
    assert revision.review_state == 'pending'
    assert not revision.reviews.exists()


def test_private_staff_tour_session_rechecks_revoked_permission_on_each_read(property_obj, superuser):
    tour, revision, _ = ready_variant(property_obj)
    superuser.is_superuser = False
    superuser.save(update_fields=['is_superuser'])
    StaffProfile.objects.update_or_create(user=superuser, defaults={
        'role_name': 'property_reviewer', 'is_active': True,
    })
    permission = Permission.objects.get(content_type__app_label='virtual_tours', codename='view_tourrevision')
    superuser.user_permissions.add(permission)
    opened = sessions.create_session(tour, superuser, {'preview': True, 'revision_id': str(revision.id)})
    client = APIClient()
    exchanged = client.post('/api/v1/virtual-tour-viewer/exchange/',
        {'bootstrap_token': opened['bootstrap_token']}, format='json')
    assert exchanged.status_code == 200
    headers = {'HTTP_X_TOUR_CREDENTIAL': exchanged.data['credential']}
    path = f"/api/v1/virtual-tour-viewer/sessions/{opened['session_id']}/manifest/"
    assert client.get(path, **headers).status_code == 200
    # Exercise a previously used session after the actual permission is removed.
    superuser.user_permissions.remove(permission)
    assert client.get(path, **headers).status_code == 403


def test_tour_approval_does_not_approve_or_publish_pending_property(property_obj, superuser, user):
    tour, revision, _ = ready_variant(property_obj)
    property_obj.status, property_obj.is_verified = 'under_review', False
    property_obj.save(update_fields=['status', 'is_verified'])
    revision.review_state = 'pending'
    revision.save(update_fields=['review_state'])
    services.review(revision, superuser, {'decision': 'approved',
        'expected_source_hash': revision.source_hash, 'reason': 'Only this tour revision was reviewed'})
    property_obj.refresh_from_db()
    revision.refresh_from_db()
    assert revision.review_state == 'approved'
    assert property_obj.status == 'under_review' and not property_obj.is_verified
    with pytest.raises(TourError) as unavailable:
        sessions.create_session(tour, user, {})
    assert unavailable.value.status_code == 409
