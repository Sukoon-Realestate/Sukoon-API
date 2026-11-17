"""Run bounded mobile cases/suites or repeat hosted checks; no deployments."""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from mobile_run_report import summarize

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def mobile_test_path(package, filename):
    direct = package / 'test' / filename
    if direct.is_file():
        return direct.relative_to(package).as_posix()
    matches = list((package / 'test').rglob(filename))
    if len(matches) != 1:
        raise ValueError(f'Expected one test file for {filename}; found {len(matches)}')
    return matches[0].relative_to(package).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='MOB-... ID from the failure ledger')
    parser.add_argument('--file', help='Failed mobile test filename, e.g. rental_listing_categories_test.dart')
    parser.add_argument('--suite', choices=['historical', 'app', 'core'], help='Run the historical failing files, complete app, or shared core suite')
    parser.add_argument('--hosted', action='store_true', help='Repeat bounded read-only hosted checks')
    parser.add_argument('--app-root', type=Path, default=REPO.parent / 'sokoun')
    parser.add_argument('--timeout', type=int, default=300, help='Wall-clock timeout in seconds')
    parser.add_argument('--mode', choices=['mvp', 'full'], default='mvp', help='Mobile release scope; full enables deferred tests without changing product defaults')
    args = parser.parse_args()
    if sum(bool(v) for v in [args.case, args.file, args.suite, args.hosted]) != 1:
        parser.error('Choose exactly one of --case, --file, --suite, --hosted')
    output = HERE / 'reruns' / time.strftime('%Y%m%d-%H%M%S')
    output.mkdir(parents=True, exist_ok=False)
    if args.hosted:
        command = [sys.executable, str(HERE / 'probe_hosted.py'), '--output', str(output / 'hosted.json')]
        cwd = REPO
    else:
        cwd = args.app_root / ('packages/core' if args.suite == 'core' else 'apps/sokoun_app')
        matches = []
        if args.suite in {'app', 'core'}:
            files = ['test']
        else:
            ledger = json.loads((HERE / 'evidence/mobile-app-failures.json').read_text())
            if args.suite == 'historical':
                files = [mobile_test_path(cwd, name) for name in sorted({Path(row['file']).name for row in ledger})]
            else:
                matches = [r for r in ledger if r['id'] == args.case] if args.case else [r for r in ledger if Path(r['file']).name == args.file]
                if not matches:
                    parser.error('No captured failure matches that case or filename')
                files = [mobile_test_path(cwd, Path(matches[0]['file']).name)]
        command = ['flutter', 'test', '--no-pub', '--timeout', '60s', '--reporter', 'json',
                   '--concurrency', '3',
                   '--dart-define=SUKOON_MVP=' + ('true' if args.mode == 'mvp' else 'false'), *files]
        if args.case and not matches[0]['loader']:
            command += ['--plain-name', matches[0]['name']]
    (output / 'command.json').write_text(json.dumps({'cwd': str(cwd), 'argv': command}, indent=2) + '\n')
    with (output / 'output.log').open('w') as log:
        process = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    result = {'exit_code': code, 'timed_out': code == 124}
    if not args.hosted:
        result.update(summarize(output / 'output.log'))
        result['mode'] = args.mode
        result['suite'] = args.suite
        if code == 0 and not result['completed_successfully']:
            code = 125
            result['exit_code'] = code
        result['completed_successfully'] = code == 0 and result['completed_successfully']
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Evidence:', output)
    raise SystemExit(code)


if __name__ == '__main__':
    main()
