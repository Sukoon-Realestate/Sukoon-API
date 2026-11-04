import subprocess
import sys
from core_apps.virtual_tours.processor_lock import claim_process_lock


def attempt(path):
    code = '''
import sys
from core_apps.virtual_tours.processor_lock import claim_process_lock
with open(sys.argv[1], 'a') as stream:
    try:
        claim_process_lock(stream)
    except BlockingIOError:
        sys.exit(2)
'''
    return subprocess.run([sys.executable, '-c', code, str(path)],
                          capture_output=True, text=True, timeout=10)


def test_process_lock_is_exclusive_and_released_on_close(tmp_path):
    target = tmp_path / 'processor.lock'
    with target.open('a') as stream:
        claim_process_lock(stream)
        blocked = attempt(target)
        assert blocked.returncode == 2, blocked.stderr
    released = attempt(target)
    assert released.returncode == 0, released.stderr
