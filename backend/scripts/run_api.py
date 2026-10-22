"""Supervise the optional policy worker inside the existing API service budget."""

import os
import signal
import subprocess
import sys
import time


def main():
    # The same release owns its schema. Complete it before starting API/workers,
    # while the previous deployment still serves traffic. The command holds a
    # PostgreSQL session lock across migrations and rejects an incomplete plan.
    schema = subprocess.run([sys.executable, "manage.py", "migrate_release"])
    if schema.returncode:
        return schema.returncode
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
    if os.environ.get("SOKOUN_GENERAL_BACKGROUND_ENABLED", "false").lower() == "true":
        # Share one Django process between the solo worker and a beat thread.
        # Its admitted maintenance tasks replace the separate chat process.
        processes.append(subprocess.Popen([sys.executable, "manage.py", "run_general_worker"]))
    else:
        # In off mode this only maintains retention, notices and the outbox.
        processes.append(subprocess.Popen([sys.executable, "manage.py", "run_chat_policy_worker"]))
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
