"""A distinct account is insufficient when the reviewer is the same person."""
import pytest
from rest_framework.exceptions import PermissionDenied

from core_apps.users.models import AccountClosureRequest
from core_apps.users.totp_models import StaffSecurityIdentity
from .test_account_closure import decision, submit, reviewer  # noqa: F401

pytestmark = pytest.mark.django_db


def test_closure_review_rejects_a_second_account_with_the_same_verified_person(user, reviewer):
    item = submit(user)
    for account in [user, reviewer]:
        StaffSecurityIdentity.objects.create(user=account,
            person_reference='synthetic-same-person', evidence_reference='synthetic-private-proof',
            known_channel_reference='synthetic-known-channel')
    with pytest.raises(PermissionDenied):
        decision(reviewer, item, 'reject')
    current = AccountClosureRequest.objects.get(id=item['id'])
    assert current.status == item['status'] and current.active
    assert current.revision == item['revision']
