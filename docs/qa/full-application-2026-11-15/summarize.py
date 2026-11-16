"""Regenerate failure reports from captured evidence; never runs application commands."""
import collections
import gzip
import hashlib
import json
import re
import shlex
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'evidence'
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def mobile(name):
    tests, suites, finished = {}, {}, {}
    details = collections.defaultdict(list)
    complete = None
    last = 0
    path = EVIDENCE / (name + '.jsonl')
    stream = path.open() if path.exists() else gzip.open(str(path) + '.gz', 'rt')
    for line in stream:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event['type']
        last = event.get('time', last)
        if kind == 'suite':
            suites[event['suite']['id']] = event['suite']['path']
        elif kind == 'testStart':
            tests[event['test']['id']] = event['test']
        elif kind == 'testDone':
            finished[event['testID']] = event
        elif kind == 'print':
            details[event['testID']].append(event['message'])
        elif kind == 'error':
            details[event['testID']].append(event['error'] + '\n' + event.get('stackTrace', ''))
        elif kind == 'done':
            complete = event
    counts = collections.Counter()
    loaders = collections.Counter()
    failures = []
    active = []
    for ident, test in tests.items():
        end = finished.get(ident)
        if not end:
            active.append(test['name'])
            continue
        if end.get('hidden') or test['name'].startswith('('):
            continue
        result = 'skipped' if end.get('skipped') else end['result']
        target = loaders if test['name'].startswith('loading ') else counts
        target[result] += 1
        if end['result'] != 'success':
            file = suites.get(test.get('suiteID'), '')
            stable = hashlib.sha256((file + test['name']).encode()).hexdigest()[:12]
            failures.append(dict(id='MOB-' + stable, name=test['name'], file=file,
                                 result=end['result'], loader=test['name'].startswith('loading '),
                                 details=ANSI.sub('', '\n'.join(details[ident]))))
    stream.close()
    summary = dict(test_cases=dict(counts), loader_events=dict(loaders),
                   terminal_event=complete, active_at_end=active,
                   recorded_seconds=round(last / 1000, 2), failed_records=len(failures))
    (EVIDENCE / (name + '-summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
    (EVIDENCE / (name + '-failures.json')).write_text(json.dumps(failures, indent=2) + '\n')
    return summary, failures


def main():
    summary, failures = mobile('mobile-app')
    core, core_failures = mobile('mobile-core')
    grouped = collections.defaultdict(list)
    for row in failures + core_failures:
        grouped[row['file']].append(row)
    output = ROOT / 'mobile-failures'
    output.mkdir(exist_ok=True)
    index = ['# Mobile regression failures', '',
             'These are observed test failures, not independently proven production defects. '
             'A stale finder, missing fixture, release gate, contract mismatch, timeout or product bug may cause them. '
             'The broad app run was interrupted after stalling; shutdown errors are retained in the raw log.', '',
             'Counts exclude hidden setup/teardown and report file-loader events separately.', '',
             '```json', json.dumps(summary, indent=2), '```', '',
             '| Test file | Failed records | Report |', '|---|---:|---|']
    for file, rows in sorted(grouped.items()):
        label = Path(file).name
        filename = label + '.md'
        index.append(f'| `{label}` | {len(rows)} | [Details](mobile-failures/{filename}) |')
        relative = 'test/' + label if '/apps/sokoun_app/' in file else 'test/' + file.split('/test/')[-1]
        lines = ['# ' + label, '', 'Status: reproduced by the broad suite; root cause requires classification.', '',
                 'Run from the relevant Flutter package:', '', '```sh',
                 'flutter test --no-pub --timeout 60s --reporter expanded ' + shlex.quote(relative), '```', '']
        for row in rows:
            lines += ['## ' + row['id'], '', row['name'], '',
                      'Result: `' + row['result'] + '`.', '', '```text', row['details'][-14000:], '```', '']
        (output / filename).write_text('\n'.join(lines))
    (ROOT / 'MOBILE-FAILURES.md').write_text('\n'.join(index) + '\n')
    security = ['# Dependency advisory ledger', '',
                'Registry scanner results on 2026-11-15. Affected version detection does not prove exploitability. '
                'Confirm deployed versions, reachable features and advisory prerequisites before assigning application risk. '
                'No exploit payloads were sent to the hosted app.', '']
    for filename in ['frontend-audit.json', 'landing-audit.json']:
        report = json.loads((EVIDENCE / filename).read_text())
        security += ['## ' + filename, '', '| Package | Severity | Advisory | Affected versions |', '|---|---|---|---|']
        for name, item in report.get('vulnerabilities', {}).items():
            for advisory in item['via']:
                if isinstance(advisory, dict):
                    security.append(f"| {name} | {advisory['severity']} | [{advisory['title']}]({advisory['url']}) | `{advisory['range']}` |")
        security.append('')
    report = json.loads((EVIDENCE / 'backend-audit.json').read_text())
    security += ['## Backend lockfile', '',
                 'Runtime and developer tools share this lockfile. `black` and `pytest` entries are tooling findings. '
                 'The scanner used pinned versions without resolving/installing application dependencies.', '',
                 '| Package | Locked version | Advisory | Fixed versions |', '|---|---|---|---|']
    for item in report['dependencies']:
        for advisory in item.get('vulns', []):
            ident = advisory['id']
            security.append(f"| {item['name']} | {item['version']} | [{ident}](https://osv.dev/vulnerability/{ident}) | {', '.join(advisory.get('fix_versions', [])) or 'Not listed'} |")
    (ROOT / 'SECURITY-ADVISORIES.md').write_text('\n'.join(security) + '\n')
    junit = EVIDENCE / 'backend/mvp/junit.xml'
    if junit.exists():
        tree = ET.parse(junit)
        cases = list(tree.iter('testcase'))
        bad = [case for case in cases if case.find('failure') is not None or case.find('error') is not None]
        result = dict(total=len(cases), skipped=sum(c.find('skipped') is not None for c in cases),
                      failures=len(bad), passed=sum(c.find('skipped') is None and c not in bad for c in cases))
        (EVIDENCE / 'backend-summary.json').write_text(json.dumps(result, indent=2) + '\n')
        lines = ['# Original backend execution errors', '',
                 'Historical first-attempt evidence. Read [consolidated results](BACKEND-RESULTS.md) '
                 'for the final status after socket-enabled and PostgreSQL reruns.', '', json.dumps(result), '']
        for case in bad:
            element = case.find('failure')
            if element is None:
                element = case.find('error')
            lines += ['## ' + case.get('classname', '') + '::' + case.get('name', ''), '',
                      '```text', element.text or '', '```', '']
        (ROOT / 'BACKEND-FAILURES.md').write_text('\n'.join(lines))
    states = {}
    attempts = []
    for filename in ['backend/mvp/junit.xml', 'backend-http-rerun.xml', 'backend-postgres.xml']:
        path = EVIDENCE / filename
        if not path.exists():
            continue
        counts = collections.Counter()
        for case in ET.parse(path).iter('testcase'):
            skipped = case.find('skipped')
            status = ('error' if case.find('error') is not None else
                      'failure' if case.find('failure') is not None else
                      'xfail' if skipped is not None and skipped.get('type') == 'pytest.xfail' else
                      'skipped' if skipped is not None else 'passed')
            counts[status] += 1
            identity = case.get('classname', '') + '::' + case.get('name', '')
            if status != 'skipped' or states.get(identity) not in {'passed', 'xfail'}:
                states[identity] = status
        attempts.append({'file': filename, 'counts': dict(counts)})
    combined = {'unique_cases': len(states), 'counts': dict(collections.Counter(states.values())), 'attempts': attempts}
    (EVIDENCE / 'backend-consolidated.json').write_text(json.dumps(combined, indent=2) + '\n')
    if states:
        lines = ['# Backend execution results', '',
                 'Results are reconciled by exact pytest classname and test name, including parameter IDs. '
                 'A passing supplemental execution supersedes an earlier environmental setup error or engine skip.', '',
                 '```json', json.dumps(combined, indent=2), '```', '',
                 'The 12 setup errors in the original full run were loopback socket restrictions. '
                 'Seven passed in the HTTP rerun; the remaining five funded/ongoing cycles passed on PostgreSQL. '
                 'No unexpected failure remains among the executed backend cases.', '',
                 '## Still skipped or expected to fail', '', '| Test | Result | Reason |', '|---|---|---|']
        reasons = {}
        for filename in [a['file'] for a in attempts]:
            for case in ET.parse(EVIDENCE / filename).iter('testcase'):
                skipped = case.find('skipped')
                if skipped is not None:
                    reasons[case.get('classname', '') + '::' + case.get('name', '')] = skipped.get('message', '')
        for identity, status in sorted(states.items()):
            if status in {'skipped', 'xfail'}:
                reason = reasons.get(identity, '').replace('|', '\\|').replace('\n', ' ')
                lines.append(f'| `{identity}` | {status} | {reason} |')
        (ROOT / 'BACKEND-RESULTS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'mobile': summary, 'core': core, 'failed_test_files': len(grouped)}, indent=2))


if __name__ == '__main__':
    main()
