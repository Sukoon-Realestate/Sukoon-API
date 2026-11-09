"""A1-05: an identity submission authenticated before revocation cannot resume after it."""

import threading
import time

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, transaction
from rest_framework.exceptions import PermissionDenied

from core_apps.admin_api.models import KYCSubmission
from core_apps.profiles.models import Profile
from core_apps.profiles.tests.test_identity_corrections import evidence
from core_apps.users.services.identity_submission import submit_identity
from core_apps.users.services.sessions import revoke_all

User = get_user_model()


def _unchanged(user):
    profile = Profile.objects.get(user=user)
    return not profile.id_face and not KYCSubmission.objects.filter(profile=profile).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("key", [None, "identity-key"])
def test_request_authenticated_before_revocation_is_rejected(user, key):
    authenticated = User.objects.get(pk=user.pk)  # request.user as loaded by authentication
    revoke_all(user, action="test.revoke")

    with pytest.raises(PermissionDenied):
        submit_identity(authenticated, evidence(), request_key=key)
    assert _unchanged(user)


@pytest.mark.django_db
def test_current_session_still_submits(user):
    result = submit_identity(User.objects.get(pk=user.pk), evidence(), request_key="ok")
    assert result["submission_id"]


@pytest.mark.requires_postgres
@pytest.mark.django_db(transaction=True)
def test_revocation_committed_while_submission_waits_for_the_lock(user):
    authenticated = User.objects.get(pk=user.pk)
    locked = threading.Event()
    outcome = {}

    def revoker():
        close_old_connections()
        try:
            with transaction.atomic():
                User.objects.select_for_update().get(pk=user.pk)
                locked.set()
                time.sleep(0.5)  # the submission is now blocked on this row
                revoke_all(user, action="test.revoke")
        finally:
            close_old_connections()

    def submitter():
        close_old_connections()
        try:
            locked.wait(timeout=5)
            submit_identity(authenticated, evidence(), request_key="in-flight")
            outcome["result"] = "accepted"
        except PermissionDenied:
            outcome["result"] = "rejected"
        finally:
            close_old_connections()

    threads = [threading.Thread(target=revoker), threading.Thread(target=submitter)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    assert outcome["result"] == "rejected"
    assert _unchanged(user)
