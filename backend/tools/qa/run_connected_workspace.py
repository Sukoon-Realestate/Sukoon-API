"""Create a fresh local PostgreSQL/API workspace for native acceptance.

Keeps private credentials and database files outside the repository. On shutdown
only this process's HTTP server and PostgreSQL cluster are stopped; files remain
for diagnosis. No shared database, application account or existing run is reset.
"""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid


BACKEND = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--http-port", type=int, default=8018)
    parser.add_argument("--postgres-port", type=int, default=55447)
    parser.add_argument("--release-mode", choices=["mvp", "restoration"], default="mvp")
    args = parser.parse_args()
    root = args.root.resolve()
    if (root == BACKEND.parent or BACKEND.parent in root.parents
            or not root.name.startswith("sukoon-sprint4-connected-") or root.exists()):
        parser.error("Use a new sukoon-sprint4-connected-* directory outside the repository")
    if not all(1024 <= port <= 65535 for port in (args.http_port, args.postgres_port)):
        parser.error("Ports must be between 1024 and 65535")
    root.mkdir(mode=0o700, parents=True)
    database = "sprint4_connected_" + uuid.uuid4().hex[:12]
    marker = {"purpose": "disposable_connected_acceptance", "database": database,
              "http_port": args.http_port, "postgres_port": args.postgres_port,
              "release_mode": args.release_mode}
    (root / "workspace.json").write_text(json.dumps(marker, indent=2) + "\n")
    env = {**os.environ, "SPRINT4_QA_ROOT": str(root), "TEST_POSTGRES_DB": database,
           "TEST_POSTGRES_USER": "sprint4_qa", "TEST_POSTGRES_PASSWORD": "",
           "TEST_POSTGRES_HOST": "127.0.0.1", "TEST_POSTGRES_PORT": str(args.postgres_port),
           "DJANGO_SETTINGS_MODULE": "config.settings.connected_acceptance"}
    cluster = root / "postgres"
    server = None
    started = False

    def run(command, **kwargs):
        return subprocess.run(command, cwd=BACKEND, env=env, check=True, **kwargs)

    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        run(["initdb", "-D", str(cluster), "-U", "sprint4_qa", "--auth-local=trust",
             "--auth-host=trust", "--no-locale", "-E", "UTF8"], stdout=subprocess.DEVNULL)
        run(["pg_ctl", "-D", str(cluster), "-l", str(root / "postgres.log"),
             "-o", f"-h 127.0.0.1 -p {args.postgres_port} -k {root}", "-w", "start"])
        started = True
        run(["createdb", "-h", "127.0.0.1", "-p", str(args.postgres_port), "-U", "sprint4_qa", database])
        with (root / "migrations.log").open("w") as output:
            run([sys.executable, "manage.py", "migrate", "--noinput"], stdout=output, stderr=subprocess.STDOUT)
        with (root / "fixture-setup.log").open("w") as output:
            run([sys.executable, "manage.py", "shell", "-c", PREPARE], stdout=output, stderr=subprocess.STDOUT)
        server = subprocess.Popen([sys.executable, "manage.py", "runserver", "--noreload",
                                   f"127.0.0.1:{args.http_port}"], cwd=BACKEND, env=env)
        print(f"Connected acceptance workspace ready: {root}; providers disabled", flush=True)
        return server.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        if started:
            subprocess.run(["pg_ctl", "-D", str(cluster), "-m", "fast", "-w", "stop"],
                           stdout=subprocess.DEVNULL, check=False)


PREPARE = "from tools.qa.prepare_connected_fixture import prepare; prepare()"


if __name__ == "__main__":
    raise SystemExit(main())
