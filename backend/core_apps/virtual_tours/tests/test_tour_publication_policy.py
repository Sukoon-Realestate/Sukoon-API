"""A2-02: tour availability follows the canonical publication policy (Sprint 01).

A pending owner closure used to leave public tour sessions, availability and signed byte
grants working. Every public path now uses public_properties(); owner previews stay
separately authorized.
"""

import pytest

from core_apps.users.models import AccountClosureRequest
from core_apps.virtual_tours import sessions
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import TourViewerSession

from .test_tours import ready_variant

pytestmark = pytest.mark.django_db


def _load(session_id):
    return TourViewerSession.objects.select_related("variant__revision__tour__property", "user").get(id=session_id)


def test_pending_closure_denies_existing_and_new_public_access_and_withdrawal_restores(
    property_obj, user, another_user
):
    property_obj.status = "verified"
    property_obj.save()
    tour, revision, variant = ready_variant(property_obj)
    assert sessions.available(property_obj)
    opened = sessions.create_session(tour, another_user, {})
    credential = sessions.exchange(_load(opened["session_id"]))["credential"]

    closure = AccountClosureRequest.objects.create(user=property_obj.owner)

    with pytest.raises(TourError, match="no longer published"):
        sessions.authenticate_session(_load(opened["session_id"]), credential)
    with pytest.raises(TourError, match="no longer published"):
        sessions.create_session(tour, another_user, {})
    assert sessions.available(property_obj) == []
    # The owner's separately authorized preview is unaffected.
    preview = sessions.create_session(tour, user, {"preview": True, "revision_id": str(revision.id)})
    assert preview["session_id"]

    closure.active = False
    closure.status = "withdrawn"
    closure.save()
    sessions.authenticate_session(_load(opened["session_id"]), credential)
    assert sessions.available(property_obj)


@pytest.mark.parametrize("change", [{"moderation_blocked": True}, {"status": "hidden"}])
def test_other_unpublished_states_deny_public_sessions(property_obj, another_user, change):
    property_obj.status = "verified"
    property_obj.save()
    tour, _, _ = ready_variant(property_obj)
    type(property_obj).objects.filter(pk=property_obj.pk).update(**change)
    property_obj.refresh_from_db()
    with pytest.raises(TourError, match="no longer published"):
        sessions.create_session(tour, another_user, {})
