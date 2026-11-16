"""Repeat the captured PostgreSQL cases using explicitly supplied disposable credentials."""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable, help='Python with backend lockfile dependencies')
    parser.add_argument('--collect-only', action='store_true')
    args = parser.parse_args()
    for key in ['TEST_POSTGRES_DB', 'TEST_POSTGRES_USER', 'TEST_POSTGRES_HOST', 'TEST_POSTGRES_PORT']:
        if not os.environ.get(key):
            parser.error('Set ' + key + ' for a disposable PostgreSQL database')
    if os.environ['TEST_POSTGRES_HOST'] not in {'localhost', '127.0.0.1', '::1'}:
        parser.error('This replay helper only accepts a loopback disposable database')
    if not any(word in os.environ['TEST_POSTGRES_DB'].lower() for word in ['test', 'qa', 'scratch']):
        parser.error('Use an explicitly named test/qa/scratch database')
    here = Path(__file__).resolve().parent
    nodes = (here / 'evidence/postgres-nodeids.txt').read_text().splitlines()
    root = Path(tempfile.mkdtemp(prefix='sukoon-pg-replay-'))
    env = dict(os.environ, DOTENV_DISABLED='true')
    for key, folder in [('CHAT_PRIVATE_MEDIA_ROOT', 'chat'), ('SUPPORT_PRIVATE_MEDIA_ROOT', 'support'),
                        ('VIRTUAL_TOUR_PRIVATE_ROOT', 'tours'), ('EVIDENCE_PRIVATE_ROOT', 'evidence')]:
        env[key] = str(root / folder)
    command = [args.python, '-m', 'pytest', *nodes, '--ds=config.settings.postgres_test',
               '-p', 'no:cacheprovider', '-o', 'addopts=--strict-markers --tb=short', '-q',
               '--junitxml=' + str(root / 'junit.xml')]
    if args.collect_only:
        command.append('--collect-only')
    print('Disposable evidence directory:', root, flush=True)
    raise SystemExit(subprocess.call(command, cwd=here.parents[2] / 'backend', env=env))


if __name__ == '__main__':
    main()
