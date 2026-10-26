"""Closure exclusion survives weaker FK-compatible business row locks."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from django.db import connection, connections, transaction, OperationalError
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User, AccountClosureRequest
from core_apps.users.services import account_closure
from core_apps.users.services.new_business import require_new_business
from core_apps.features.planning_models import HousingRequest, PlanningEvent
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from .test_account_closure import request

pytestmark = pytest.mark.django_db(transaction=True)


def test_business_guard_blocks_closure_lock_but_allows_existing_obligation_notice(user):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row and FK locks")

    def independent():
        try:
            with pytest.raises(OperationalError):
                with transaction.atomic():
                    User.objects.select_for_update(nowait=True).get(pk=user.pk)
            # FK insertion must commit without waiting for a protected creation.
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL lock_timeout = '500ms'")
                return PlanningEvent.objects.create(
                    recipient=user,
                    event_key="existing-obligation-local-lock-test",
                    destination={"workspace": "account"},
                ).pk
        finally:
            connections.close_all()

    with transaction.atomic():
        require_new_business(user.pk)
        with ThreadPoolExecutor(max_workers=1) as executor:
            notice_id = executor.submit(independent).result(timeout=5)
    assert PlanningEvent.objects.filter(pk=notice_id).exists()


def test_new_business_and_real_account_closure_request_have_serial_order(user):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locking")
    req = request(user)

    def run(index):
        if index == 0:
            try:
                row = HousingRequest.objects.create(
                    user=user,
                    title="Concurrent local request",
                    criteria={},
                    expires_at=timezone.now() + timedelta(days=1),
                )
                return row.pk
            except PermissionDenied:
                return None
        account_closure.submit(req, {"expected_revision": 0, "reason": "Close"})
        return None

    created, _ = parallel_calls(run)
    closure = AccountClosureRequest.objects.get(user=user, active=True)
    if created is not None:
        assert HousingRequest.objects.get(pk=created).created_at <= closure.created_at
    else:
        assert not HousingRequest.objects.filter(user=user).exists()
    with transaction.atomic(), pytest.raises(PermissionDenied):
        require_new_business(user.pk)
