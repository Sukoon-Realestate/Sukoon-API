"""Run each test in the release mode it was written for (loaded by the root conftest.py).

The production default is SUKOON_MVP=true, which refuses deferred group/company/student and other
deferred workflows. Tests of those deferred workflows run in the same session with the gate off
(`mvp_deferred`); tests asserting MVP-only refusals run with it on (`mvp_scope`); every other test
follows the SUKOON_MVP environment value (default true). Nothing is deselected, so a green run
covers both scopes. Set MVP_COLLECTION_REPORT=/path.json to write the classification.
"""

import json
import os
import socket
from pathlib import Path

import pytest

from tools.qa.engine_test_modes import POSTGRES_ONLY_TESTS
from tools.qa.mvp_test_modes import DEFERRED_TESTS, MVP_SCOPE_TESTS

# Explicit reviewed branches; shared synthetic property/user fixtures remain eligible.
DEFERRED_NODES = {
    'test_housing_districts.py': {'test_matching_inventory_filter_uses_the_same_district_scope',
                                  'test_districts_publish_read_edit_and_unknown_receipt'},
    'test_viewing_event_history.py': {
        'test_group_request_notifies_all_consented_participants_after_link',
        'test_reassigned_attendee_cannot_receive_old_event_or_private_identifiers',
    },
    'test_viewing_listing_changes.py': {
        'test_visited_group_and_recorded_decisions_are_not_rewritten',
        'test_group_loses_availability_with_one_consistent_process_history',
        'test_listing_price_does_not_reprice_accepted_negotiation',
        'test_membership_withdrawal_and_listing_change_share_lock_order',
        'test_attendance_committing_during_listing_edit_cannot_be_erased',
    },
}
DEFERRED_FIXTURES = {'chat_group', 'company_setup', 'company_request',
                     'group_setup', 'student_setup', 'housing_group', 'group_context'}
DEFERRED_CLASSES = {'TestOwnerRevenuesAPI', 'TestAccountSummaryScreenAPI'}


def pytest_configure(config):
    config.addinivalue_line("markers", "mvp_deferred: exercises a deferred workflow; runs with SUKOON_MVP=False")
    config.addinivalue_line("markers", "mvp_scope: asserts MVP-only behavior; runs with SUKOON_MVP=True")
    config.addinivalue_line("markers", "requires_postgres: needs PostgreSQL semantics; skipped on SQLite")


def _postgres():
    from django.conf import settings

    return settings.DATABASES["default"]["ENGINE"].endswith("postgresql")


def _listed(table, item, name):
    path = item.path.relative_to(item.config.rootpath).as_posix()
    entry = table.get(path)
    if entry is None:
        return False
    cls = getattr(item, 'cls', None)
    key = f"{cls.__name__}::{name}" if cls is not None else name
    return entry == "*" or key in entry


def classify(item):
    """Return (mode, reason) where mode is 'deferred', 'mvp' or None."""
    name = item.originalname or item.name.split('[')[0]
    if item.get_closest_marker('mvp_scope') or _listed(MVP_SCOPE_TESTS, item, name):
        return 'mvp', 'MVP-only behavior'
    if item.get_closest_marker('mvp_deferred'):
        return 'deferred', 'marked mvp_deferred'
    filename = item.path.name
    parameters = getattr(getattr(item, 'callspec', None), 'params', {})
    cls = getattr(item, 'cls', None)
    if filename == 'test_contextual_viewings.py' or name in DEFERRED_NODES.get(filename, set()):
        return 'deferred', 'explicit deferred group/student/company or negotiation branch'
    if filename == 'test_viewing_event_history.py' and parameters.get('kind') in {'student', 'company'}:
        return 'deferred', 'deferred student/company viewing branch'
    if cls is not None and cls.__name__ in DEFERRED_CLASSES:
        return 'deferred', 'deferred revenue or rental account-summary API'
    if DEFERRED_FIXTURES.intersection(item.fixturenames) or any(
            str(value) == 'chat_group' for value in parameters.values()):
        return 'deferred', 'deferred group/company/student fixture'
    if _listed(DEFERRED_TESTS, item, name):
        return 'deferred', 'fails behind the MVP gate, passes without it (mvp_test_modes.py)'
    return None, ''


def pytest_collection_modifyitems(config, items):
    report = {'mvp_env': os.environ.get('SUKOON_MVP', 'true'), 'deferred': [], 'mvp_scope': [],
              'postgres_only': []}
    postgres = _postgres()
    skip_sqlite = pytest.mark.skip(reason='Requires PostgreSQL (row locks, JSON containment or engine '
                                          'semantics); run with config.settings.postgres_test')
    for item in items:
        name = item.originalname or item.name.split('[')[0]
        if item.get_closest_marker('requires_postgres') or _listed(POSTGRES_ONLY_TESTS, item, name):
            report['postgres_only'].append(item.nodeid)
            if not postgres:
                item.add_marker(skip_sqlite)
        db = item.get_closest_marker('django_db')
        if postgres and db is not None and db.kwargs.get('transaction'):
            # A transactional test flushes every table at teardown, deleting rows that
            # migrations seed (plans, catalogs, property types). Restore them so later
            # tests see the same database as on a fresh run.
            item.add_marker(pytest.mark.django_db(**{**db.kwargs, 'serialized_rollback': True}), append=False)
        mode, reason = classify(item)
        if mode == 'deferred':
            item.add_marker(pytest.mark.mvp_deferred)
            report['deferred'].append({'nodeid': item.nodeid, 'reason': reason})
        elif mode == 'mvp':
            item.add_marker(pytest.mark.mvp_scope)
            report['mvp_scope'].append(item.nodeid)
    target = os.environ.get('MVP_COLLECTION_REPORT')
    if target:
        report['total'] = len(items)
        Path(target).write_text(json.dumps(report, indent=2), encoding='utf-8')


@pytest.fixture(autouse=True)
def release_scope(request):
    """Apply the test's release mode; a test that sets SUKOON_MVP itself still wins."""
    if request.node.get_closest_marker('mvp_scope'):
        value = True
    elif request.node.get_closest_marker('mvp_deferred'):
        value = False
    else:
        yield
        return
    settings = request.getfixturevalue('settings')
    settings.SUKOON_MVP = value
    yield


# Providers must be mocked. Fail before an accidental Python network connection
# leaves the local test host; PostgreSQL still uses its explicit loopback DSN.
@pytest.fixture(autouse=True)
def local_test_network_only(monkeypatch):
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def check(address):
        if isinstance(address, tuple) and address[0] not in {'127.0.0.1', '::1', 'localhost'}:
            raise AssertionError('External network is disabled in MVP automated tests')

    def local_connect(stream, address):
        check(address)
        return connect(stream, address)

    def local_connect_ex(stream, address):
        check(address)
        return connect_ex(stream, address)

    monkeypatch.setattr(socket.socket, 'connect', local_connect)
    monkeypatch.setattr(socket.socket, 'connect_ex', local_connect_ex)
