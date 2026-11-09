"""A1-04: OTP attempts, consumption and resend cooldown are atomic (Sprint 01).

Row locks are only meaningful on PostgreSQL; run with `make test-postgres-races`.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import close_old_connections
from rest_framework.exceptions import ValidationError

from core_apps.users.services import otp_service

pytestmark = [pytest.mark.requires_postgres, pytest.mark.django_db(transaction=True)]


@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


def _parallel(fn, inputs):
    barrier = Barrier(len(inputs))

    def run(value):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return fn(value)
        except ValidationError as exc:
            return str(exc.detail)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=len(inputs)) as pool:
        return list(pool.map(run, inputs))


def _issue(user):
    with patch.object(otp_service, "send_otp_email", return_value=True):
        return otp_service.create_and_send_otp(user)


def test_parallel_invalid_attempts_cannot_exceed_the_budget(user):
    code = _issue(user)
    wrong = "000000" if code != "000000" else "111111"
    _parallel(lambda _: otp_service.verify_email_otp(user.email, wrong), list(range(12)))

    record = cache.get(f"otp:{user.email.lower()}")
    assert record is None or record["attempts"] == otp_service.MAX_OTP_ATTEMPTS
    # The real code no longer works once the budget is spent.
    with pytest.raises(ValidationError):
        otp_service.verify_email_otp(user.email, code)
    user.refresh_from_db()
    assert not user.is_email_verified


def test_one_code_is_consumed_exactly_once(user):
    code = _issue(user)
    results = _parallel(lambda _: otp_service.verify_email_otp(user.email, code), [1, 2, 3])
    winners = [r for r in results if not isinstance(r, str)]
    assert len(winners) == 1
    assert cache.get(f"otp:{user.email.lower()}") is None


def test_parallel_resends_issue_one_challenge(user):
    sent = []
    with patch.object(otp_service, "send_otp_email", side_effect=lambda **kw: sent.append(kw) or True):
        results = _parallel(lambda _: otp_service.resend_verification_otp(user.email), [1, 2, 3, 4])
    assert sum(1 for r in results if not isinstance(r, str) or "wait" not in r) == 1
    assert len(sent) == 1
