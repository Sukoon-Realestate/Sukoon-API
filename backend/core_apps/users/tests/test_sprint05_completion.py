"""Populated/rejection-heavy read budgets and compatible opt-in pagination."""
from datetime import timedelta
import importlib.util
import json
import os
from pathlib import Path
import time
import tracemalloc
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from core_apps.users.models import (
    AccountClosureRequest, AccountClosureDecision, AccountProfileErasureFile,
    TotpRecoveryRequest, TotpRecoveryDecision, StaffSecurityIdentity, User, AuthSession,
)
from core_apps.users.services import account_closure, totp_recovery
from core_apps.users.services.closure_reads import prepare_projections
from core_apps.users.services.closure_blockers import blockers_for_users
from core_apps.users.services.recovery_reads import authorized_rows
from core_apps.users.read_pages import HistoryPage, collection_page
from core_apps.users.selectors import active_sessions, staff_identities
from core_apps.users.services.sessions import issue_refresh
from .test_totp_recovery import staff, request

pytestmark = pytest.mark.django_db


def measure(name, size, call, query_budget, payload_budget):
    # Warm import/compiler paths before the timed, traced observation.
    call()
    tracemalloc.start()
    started = time.perf_counter()
    cpu = time.process_time()
    failure = AssertionError("Read performed provider I/O")
    with patch("requests.sessions.Session.request", side_effect=failure) as provider:
        with CaptureQueriesContext(connection) as queries:
            value = call()
            payload = json.dumps(value, default=str).encode()
        assert provider.call_count == 0
    elapsed, cpu_elapsed = time.perf_counter() - started, time.process_time() - cpu
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(queries) <= query_budget
    assert len(payload) <= payload_budget
    # Generous local regression caps; deterministic query/row/byte gates are primary.
    assert elapsed < 15 and cpu_elapsed < 15 and peak < 64 * 1024 * 1024
    plans = os.getenv("SPRINT05_PLANS")
    if plans and connection.vendor == "postgresql" and size == 100:
        observed = []
        with connection.cursor() as cursor:
            for query in queries.captured_queries:
                if query["sql"].lstrip().upper().startswith("SELECT"):
                    cursor.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query["sql"])
                    observed.append(cursor.fetchone()[0])
        with Path(plans).open("a") as output:
            output.write(json.dumps({"name": name, "size": size, "plans": observed}) + "\n")
    destination = os.getenv("SPRINT05_METRICS")
    if destination:
        with Path(destination).open("a") as output:
            output.write(json.dumps({"name": name, "size": size, "queries": len(queries),
                                     "payload_bytes": len(payload), "seconds": elapsed,
                                     "cpu_seconds": cpu_elapsed, "peak_heap_bytes": peak,
                                     "provider_calls": 0}) + "\n")
    return value


def closures(size, history=25):
    rows = []
    for number in range(size):
        user = User.objects.create_user(email=f"closure-{number}@example.invalid")
        item = AccountClosureRequest.objects.create(user=user, reason="Synthetic closure")
        AccountClosureDecision.objects.bulk_create([
            AccountClosureDecision(request=item, actor=user, action="requested", revision=index + 1,
                                   reason="Synthetic decision") for index in range(history)
        ])
        AccountProfileErasureFile.objects.create(request=item, public_id="synthetic-owned-asset")
        rows.append(item)
    return rows


@pytest.mark.parametrize("size", [1, 20, 100])
def test_closure_prepared_page_budget_and_complete_legacy_history(size):
    rows = closures(size)

    def project():
        page = list(AccountClosureRequest.objects.select_related("user").order_by("pk")[:20])
        prepare_projections(page, page=HistoryPage(1, 5))
        return [account_closure.projection(item, review=True) for item in page]

    values = measure("closure-page", size, project, 5, 128 * 1024)
    assert len(values) == min(size, 20)
    assert all(len(item["history"]) == 5 and item["history_page"]["count"] == 25 for item in values)
    legacy = AccountClosureRequest.objects.select_related("user").get(pk=rows[0].pk)
    prepare_projections([legacy])
    legacy = account_closure.projection(legacy)
    assert len(legacy["history"]) == 25 and "history_page" not in legacy
    assert legacy["erasure_pending"]


@pytest.mark.parametrize("size", [1, 20, 100])
def test_recovery_page_filters_authority_before_count_and_projection(size):
    owner = staff("owner", "system_owner")
    actor = request(owner)
    actor.query_params = {"bounded": "true", "page_size": "20"}
    applicants = []
    for number in range(size):
        applicant = staff(f"applicant-{number}")
        identity = StaffSecurityIdentity.objects.get(user=applicant)
        item = TotpRecoveryRequest.objects.create(user=applicant, identity=identity,
                                                  person_reference=identity.person_reference, reason="Lost factor")
        TotpRecoveryDecision.objects.bulk_create([
            TotpRecoveryDecision(recovery=item, actor=owner, revision=index + 1,
                                 decision="request_information", reason="Synthetic") for index in range(25)
        ])
        applicants.append(item)
    # Rejection-heavy applicants must be excluded before count and page selection.
    for index in range(100):
        identity = StaffSecurityIdentity.objects.get(user=owner)
        TotpRecoveryRequest.objects.create(user=User.objects.create_user(
            email=f"same-person-{index}@example.invalid"), identity=identity,
            person_reference="owner", reason="Cannot self-review")
    data = measure("recovery-page", size, lambda: totp_recovery.review_queue(actor), 13, 128 * 1024)
    assert data["count"] == size and len(data["results"]) == min(size, 20)
    assert all(len(item["decisions"]) == 5 and item["decisions_page"]["count"] == 25
               for item in data["results"])
    assert all(item["review_available"] for item in data["results"])
    # Current revocation is still evaluated on the next call.
    owner.sensitive_actions_frozen = True
    owner.save(update_fields=["sensitive_actions_frozen"])
    assert totp_recovery.review_queue(actor)["count"] == 0


def test_designated_reviewer_query_matches_command_authority():
    actor = staff("independent", "security_recovery_reviewer")
    owner = staff("sole-owner", "system_owner")
    identity = StaffSecurityIdentity.objects.get(user=actor)
    item = TotpRecoveryRequest.objects.create(
        user=owner, identity=StaffSecurityIdentity.objects.get(user=owner),
        person_reference="sole-owner", owner_request=True, reason="Lost factor",
        designated_reviewer_ids=[str(identity.id)],
    )
    profile = actor.staff_profile
    assert list(authorized_rows(actor, profile).values_list("pk", flat=True)) == [item.pk]
    totp_recovery._can_review(actor, profile, item)
    other = staff("available-owner", "system_owner")
    with pytest.raises(PermissionDenied):
        totp_recovery._can_review(actor, profile, item)
    assert not authorized_rows(actor, profile).exists()
    other.sensitive_actions_frozen = True
    other.save(update_fields=["sensitive_actions_frozen"])
    assert authorized_rows(actor, profile).filter(pk=item.pk).exists()
    item.designated_reviewer_ids = []
    item.save(update_fields=["designated_reviewer_ids"])
    assert not authorized_rows(actor, profile).exists()


def test_legacy_blocker_parity_against_independent_incoming_source(user):
    directory = os.getenv("SPRINT05_BEFORE")
    from core_apps.profiles.models import Contract
    Contract.objects.create(tenant=user, property_title="Historical lease", status="active",
                            start_date=timezone.localdate(), end_date=timezone.localdate() + timedelta(days=1))
    actual = blockers_for_users([user])[user.pk]
    assert [value["code"] for value in actual] == ["legacy_contract"]
    assert actual[0]["count"] == 1
    if directory:
        source = Path(directory) / "services/closure_blockers.py"
        spec = importlib.util.spec_from_file_location("incoming_closure_blockers", source)
        incoming = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(incoming)
        assert actual == incoming.blockers(user)


@pytest.mark.parametrize("kind", ["sessions", "staff"])
def test_opt_in_collection_pages_preserve_legacy_lists(user, kind):
    now = timezone.now()
    if kind == "sessions":
        AuthSession.objects.bulk_create([AuthSession(user=user, security_epoch=0,
                                                     expires_at=now + timedelta(days=1)) for _ in range(130)])

        def call(params):
            return active_sessions(user, {}, params)
        legacy = call({})["results"]
    else:
        User.objects.bulk_create([User(email=f"staff-row-{index}@example.invalid", is_superuser=True)
                                  for index in range(130)])

        def call(params):
            return staff_identities(user, params)
        legacy = call({})
    page = call({"bounded": "true", "page_size": 20})
    assert len(legacy) == page["count"] == 130 and len(page["results"]) == 20
    assert page["next_page"] == 2
    from rest_framework.exceptions import ValidationError
    with pytest.raises(ValidationError):
        call({"page_size": 101})


def test_http_bounded_closure_history_and_unknown_page(user):
    token = issue_refresh(user)
    item = AccountClosureRequest.objects.create(user=user)
    AccountClosureDecision.objects.bulk_create([
        AccountClosureDecision(request=item, actor=user, action="requested", revision=i + 1) for i in range(40)
    ])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    url = "/api/v1/auth/account-closure/"
    legacy = client.get(url).json()["data"]
    page = client.get(url, {"bounded": "true", "history_page": 2}).json()["data"]
    assert len(legacy["history"]) == 40 and "history_page" not in legacy
    assert len(page["history"]) == len(page["request"]["history"]) == 5
    assert page["history_page"]["count"] == 40 and page["history_page"]["page"] == 2
    assert client.get(url, {"history_page_size": 21}).status_code == 400


@pytest.mark.parametrize("size", [1, 20, 100])
def test_compatible_closure_read_matches_incoming_projection_and_reduces_queries(size):
    closures(size, history=25)
    directory = os.getenv("SPRINT05_BEFORE")
    if directory:
        def load(module, file):
            spec = importlib.util.spec_from_file_location(module, Path(directory) / "services" / file)
            loaded = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loaded)
            return loaded
        incoming = load("core_apps.users.services._incoming_closure", "account_closure.py")
        incoming.blockers = load("_incoming_blockers", "closure_blockers.py").blockers

        def before():
            page = AccountClosureRequest.objects.select_related("user").order_by("pk")[:20]
            return [incoming.projection(item, review=True) for item in page]

        expected = measure("closure-before-compatible", size, before, 500, 512 * 1024)
    else:
        expected = None

    def after():
        rows = list(AccountClosureRequest.objects.select_related("user").order_by("pk")[:20])
        prepare_projections(rows)
        return [account_closure.projection(item, review=True) for item in rows]

    actual = measure("closure-after-compatible", size, after, 4, 512 * 1024)
    if expected is not None:
        assert actual == expected
    assert all(len(item["history"]) == 25 for item in actual)


@pytest.mark.parametrize("size", [1, 20, 100])
def test_profile_and_inherited_read_family_http_budgets(user, another_user, size, settings):
    settings.SUKOON_MVP = False
    from datetime import date, time as civil_time
    from core_apps.profiles.tests.test_screen_views import create_test_property
    from core_apps.properties.models import PropertyVisit, PropertyVisitReview

    prop = create_test_property(another_user)
    for number in range(size):
        visit = PropertyVisit.objects.create(tenant=user, property=prop, visit_date=date(2026, 7, 20),
                                             visit_time=civil_time(14, number % 60), status="confirmed")
        PropertyVisitReview.objects.create(visit=visit, overall_rating=5, cleanliness_rating=5,
                                           listing_accuracy_rating=5, owner_interaction_rating=5)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_refresh(user).access_token}")
    paths = ["auth/users/", "auth/users/me/", "profiles/user/my-profile/", "profiles/user/update/",
             "profiles/my-account/", "profiles/account-summary/", "profiles/edit/", "profiles/settings/",
             "profiles/verification-status/", "profiles/contracts/", "profiles/owner/unread-counts/",
             "profiles/tenant/unread-counts/", "profiles/my-rates/", "profiles/identity-expiry/"]
    for path in paths:
        def read():
            response = client.get("/api/v1/" + path, {"bounded": "true"})
            assert response.status_code == 200, (path, response.data)
            return response.json()
        measure(path, size, read, 32, 256 * 1024)


@pytest.mark.django_db(transaction=True)
def test_postgres_bounded_recovery_read_and_revocation_serialize():
    if connection.vendor != "postgresql":
        pytest.skip("Requires disposable PostgreSQL account row locks")
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event
    from django.db import close_old_connections
    from rest_framework_simplejwt.exceptions import AuthenticationFailed
    from core_apps.users.services import recovery_reads
    from core_apps.users.services.sessions import revoke_all

    owner = staff("locking-owner", "system_owner")
    actor = request(owner)
    actor.query_params = {"bounded": "true"}
    applicant = staff("locking-applicant")
    identity = StaffSecurityIdentity.objects.get(user=applicant)
    TotpRecoveryRequest.objects.create(user=applicant, identity=identity,
                                       person_reference="locking-applicant", reason="Lost factor")
    entered, release = Event(), Event()
    original = recovery_reads.prepare_projections

    def pause(*args, **kwargs):
        entered.set()
        assert release.wait(timeout=10)
        return original(*args, **kwargs)

    def run(call):
        close_old_connections()
        try:
            return call()
        finally:
            close_old_connections()

    with patch.object(recovery_reads, "prepare_projections", side_effect=pause), \
            ThreadPoolExecutor(max_workers=2) as pool:
        reader = pool.submit(run, lambda: totp_recovery.review_queue(actor))
        assert entered.wait(timeout=10)
        revoker = pool.submit(run, lambda: revoke_all(owner))
        try:
            with pytest.raises(TimeoutError):
                revoker.result(timeout=0.15)
        finally:
            release.set()
        assert reader.result(timeout=10)["count"] == 1
        revoker.result(timeout=10)
    with pytest.raises(AuthenticationFailed):
        totp_recovery.review_queue(actor)
