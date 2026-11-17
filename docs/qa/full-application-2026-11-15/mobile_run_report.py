"""Summarize Flutter JSON events without calling an unfinished run successful."""
import collections
import json
from pathlib import Path


def summarize(path):
    counts = collections.Counter()
    active = {}
    tests = {}
    suites = {}
    case_results = []
    failures = []
    terminal = None
    with path.open(errors='replace') as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue  # Flutter startup diagnostics can precede its JSON stream.
            if not isinstance(event, dict):
                continue
            kind = event.get('type')
            if kind == 'suite':
                item = event['suite']
                suites[item['id']] = item.get('path', '')
            elif kind == 'testStart':
                item = event['test']
                active[item['id']] = item['name']
                tests[item['id']] = item
            elif kind == 'testDone':
                name = active.pop(event['testID'], None)
                result = 'skipped' if event.get('skipped') else event['result']
                if result not in {'success', 'skipped'}:
                    failures.append(name)
                if not event.get('hidden'):
                    counts[result] += 1
                    item = tests.get(event['testID'], {})
                    case_results.append({
                        'file': Path(suites.get(item.get('suiteID'), '')).name,
                        'name': name,
                        'result': result,
                    })
            elif kind == 'error':
                failures.append(active.get(event.get('testID'), 'runner/setup error'))
            elif kind == 'done':
                terminal = event.get('success')
    return {
        'test_cases': dict(counts),
        'terminal_success': terminal,
        'active_at_end': list(active.values()),
        'failed_cases': list(dict.fromkeys(failures)),
        'case_results': case_results,
        'completed_successfully': terminal is True and not active and not failures,
    }
