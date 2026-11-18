"""Exercise admin HTTP reads against an explicitly disposable loopback fixture."""
import argparse
import json
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from probe_hosted import request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--origin', default='http://127.0.0.1:8037')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    origin = urlparse(args.origin)
    assert origin.hostname in {'localhost', '127.0.0.1', '::1'} and origin.scheme == 'http'
    fixture = json.loads(args.fixture.read_text())
    assert fixture['qa_only'] is True
    req = urllib.request.Request(args.origin + '/api/v1/auth/login/', data=json.dumps({
        'email': fixture['email'], 'password': fixture['password'],
    }).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        login = json.load(response)
    token = login.get('access') or login.get('data', {}).get('access')
    assert token, 'Login did not return an access token'
    headers = {'Authorization': 'Bearer ' + token}
    paths = [
        'session/', 'dashboard/', 'dashboard/executive/', 'followups/',
        'users/', 'users/?search=missing-qa-record', 'users/?page=99999',
        'kyc/', 'kyc/metrics/', 'properties/', 'properties/metrics/',
        'properties/?search=missing-qa-record', 'properties/?status=pending',
        'moderation/', 'moderation/metrics/', 'reports/', 'reports/metrics/',
        'reports/overview/', 'support/', 'support/metrics/', 'support/team/',
        'analytics/', 'analytics/?period=invalid', 'settings/',
        'system/health/', 'system/logs/', 'system/notifications/',
        'staff/', 'staff/roles/', 'permissions/', 'content/',
    ]
    rows = []
    for path in paths:
        expected = [200]
        if 'page=99999' in path:
            expected = [404]
        if 'period=invalid' in path:
            expected = [400]
        if path == 'system/health/':
            expected = [200, 503]  # Disposable harness has no worker/Redis.
        rows.append(request(args.origin, '/api/v1/admin/' + path, expected, headers))
    args.output.write_text(json.dumps(rows, indent=2) + '\n')
    for row in rows:
        print(row['outcome'], row.get('status'), row['path'])
    raise SystemExit(any(row['outcome'] != 'PASS' for row in rows))


if __name__ == '__main__':
    main()
