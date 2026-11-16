"""Run a captured mobile case/file or repeat hosted checks; no fixes or deployments."""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='MOB-... ID from the failure ledger')
    parser.add_argument('--file', help='Failed mobile test filename, e.g. rental_listing_categories_test.dart')
    parser.add_argument('--hosted', action='store_true', help='Repeat bounded read-only hosted checks')
    parser.add_argument('--app-root', type=Path, default=REPO.parent / 'sokoun')
    parser.add_argument('--timeout', type=int, default=300, help='Wall-clock timeout in seconds')
    args = parser.parse_args()
    if sum(bool(v) for v in [args.case, args.file, args.hosted]) != 1:
        parser.error('Choose exactly one of --case, --file, --hosted')
    output = HERE / 'reruns' / time.strftime('%Y%m%d-%H%M%S')
    output.mkdir(parents=True, exist_ok=False)
    if args.hosted:
        command = [sys.executable, str(HERE / 'probe_hosted.py'), '--output', str(output / 'hosted.json')]
        cwd = REPO
    else:
        ledger = json.loads((HERE / 'evidence/mobile-app-failures.json').read_text())
        matches = [r for r in ledger if r['id'] == args.case] if args.case else [r for r in ledger if Path(r['file']).name == args.file]
        if not matches:
            parser.error('No captured failure matches that case or filename')
        file = Path(matches[0]['file']).name
        cwd = args.app_root / 'apps/sokoun_app'
        command = ['flutter', 'test', '--no-pub', '--timeout', '60s', '--reporter', 'expanded', 'test/' + file]
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
    (output / 'result.json').write_text(json.dumps({'exit_code': code, 'timed_out': code == 124}, indent=2) + '\n')
    print('Evidence:', output)
    raise SystemExit(code)


if __name__ == '__main__':
    main()
