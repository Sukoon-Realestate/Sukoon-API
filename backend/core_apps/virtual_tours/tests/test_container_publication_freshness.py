"""Cached container objects cannot preserve revoked public-tour authority."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core_apps.properties.models import ResidentialBuilding, ResidentialComplex
from core_apps.virtual_tours.policy import public_property

pytestmark = pytest.mark.django_db


@pytest.fixture(params=[ResidentialBuilding, ResidentialComplex])
def container(request, user, another_user):
    model = request.param
    values = {"declared_units": 1} if model is ResidentialBuilding else {}
    return model.objects.create(
        manager=user, name="Synthetic container", code="synthetic",
        address="Synthetic address", authority_status="verified",
        authority_reviewed_by=another_user, authority_reference="synthetic-proof",
        **values,
    )


@pytest.mark.parametrize("change", [
    {"archived": True}, {"authority_status": "pending"},
    {"authority_reviewed_by_id": None}, {"authority_reference": ""},
])
def test_current_container_revocation_wins_over_cached_fields(container, change):
    assert public_property(container)
    type(container).objects.filter(pk=container.pk).update(**change)
    assert not public_property(container)


def test_current_manager_replacement_is_checked(container, another_user):
    type(another_user).objects.filter(pk=another_user.pk).update(closed_at=timezone.now())
    type(container).objects.filter(pk=container.pk).update(manager=another_user)
    assert not public_property(container)


def test_eligible_container_and_current_manager_state_use_one_query(container, user):
    with CaptureQueriesContext(connection) as queries:
        assert public_property(container)
    assert len(queries) == 1
    type(user).objects.filter(pk=user.pk).update(closed_at=timezone.now())
    assert not public_property(container)


def test_pending_manager_closure_and_withdrawal_are_current(container, user):
    from core_apps.users.models import AccountClosureRequest

    closure = AccountClosureRequest.objects.create(user=user)
    assert not public_property(container)
    AccountClosureRequest.objects.filter(pk=closure.pk).update(active=False, status="withdrawn")
    assert public_property(container)
