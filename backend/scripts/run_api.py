"""Supervise the optional policy worker inside the existing API service budget."""

import os
import signal
import subprocess
import sys
import time


def main():
    processes = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    processes.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "config.asgi:application",
                "-k",
                "uvicorn.workers.UvicornWorker",
                "--bind",
                "0.0.0.0:" + os.environ.get("PORT", "8080"),
                "--worker-tmp-dir",
                "/dev/shm",
            ]
        )
    )
    # In off mode this process only maintains retention, already-created notices
    # and the existing event outbox. It makes no Gemini calls.
    processes.append(
        subprocess.Popen([sys.executable, "manage.py", "run_chat_policy_worker"])
    )
    code = 0
    try:
        while not stopping:
            failed = next((p for p in processes if p.poll() is not None), None)
            if failed is not None:
                code = failed.returncode or 1
                break
            time.sleep(0.5)
    finally:
        stop()
        for process in processes:
            try:
                process.wait(timeout=35)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return code


if __name__ == "__main__":
    sys.exit(main())
