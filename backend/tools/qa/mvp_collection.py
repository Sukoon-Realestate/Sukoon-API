"""Collection-only MVP branch projection; deselections are never pass evidence."""
import json
import os
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    if os.environ.get('SUKOON_MVP', 'true').lower() == 'false':
        target = os.environ.get('MVP_COLLECTION_REPORT')
        if target:
            Path(target).write_text(json.dumps({'mode': 'restoration',
                'selected': [item.nodeid for item in items], 'deferred': []}, indent=2), encoding='utf-8')
        return
    selected, deferred = [], []
    # Explicit reviewed branches; shared synthetic property/user fixtures remain
    # eligible. These positive deferred tests belong to disabled-mode restoration.
    deferred_nodes = {
        'test_housing_districts.py': {'test_matching_inventory_filter_uses_the_same_district_scope', 'test_districts_publish_read_edit_and_unknown_receipt'},
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
    forbidden = {'chat_group', 'company_setup', 'company_request',
                 'group_setup', 'student_setup', 'housing_group', 'group_context'}
    for item in items:
        fixtures = forbidden.intersection(item.fixturenames)
        parameters = getattr(getattr(item, 'callspec', None), 'params', {})
        group_parameter = any(str(value) == 'chat_group' for value in parameters.values())
        deferred_class = getattr(item, 'cls', None)
        deferred_class = deferred_class.__name__ if deferred_class is not None else ''
        name = item.originalname or item.name.split('[')[0]
        filename = item.path.name
        contextual = filename == 'test_contextual_viewings.py'
        deferred_parameter = filename == 'test_viewing_event_history.py' and parameters.get('kind') in {'student', 'company'}
        if contextual or deferred_parameter or name in deferred_nodes.get(filename, set()):
            deferred.append({'nodeid': item.nodeid, 'reason': 'Explicit deferred group/student/company or rental-negotiation positive branch; restoration only'})
        elif deferred_class in {'TestOwnerRevenuesAPI', 'TestAccountSummaryScreenAPI'}:
            deferred.append({'nodeid': item.nodeid, 'reason': 'Deferred revenue or rental account-summary positive API branch'})
        elif fixtures or group_parameter:
            deferred.append({'nodeid': item.nodeid, 'reason': 'Deferred group/company/student fixture branch',
                             'fixtures': sorted(fixtures), 'group_parameter': group_parameter})
        else:
            selected.append(item)
    if deferred:
        removed = {row['nodeid'] for row in deferred}
        config.hook.pytest_deselected(items=[item for item in items if item.nodeid in removed])
    items[:] = selected
    target = os.environ.get('MVP_COLLECTION_REPORT')
    if target:
        Path(target).write_text(json.dumps({'selected': [i.nodeid for i in selected],
                                           'deferred': deferred}, indent=2), encoding='utf-8')


# Providers must be mocked. Fail before an accidental Python network connection
# leaves the local test host; PostgreSQL still uses its explicit loopback DSN.
import socket
import pytest

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
