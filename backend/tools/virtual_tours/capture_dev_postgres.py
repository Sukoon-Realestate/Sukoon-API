"""Own only the isolated capture development database; never use production DSNs."""

import os
import secrets
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import psycopg2

BACKEND = Path(__file__).resolve().parents[2]
ROOT = BACKEND / ".capture-dev-postgres"
DATA = ROOT / "data"
PASSWORD = BACKEND / ".envs" / "property-capture-postgres-password"
PORT = 55435


def run(*arguments, check=True):
    return subprocess.run(
        arguments,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def status():
    return (
        DATA.exists()
        and run("pg_ctl", "-D", str(DATA), "status", check=False).returncode == 0
    )


def stop():
    if status():
        run("pg_ctl", "-D", str(DATA), "-m", "fast", "-w", "stop")


def start():
    for name in ("initdb", "pg_ctl"):
        if not shutil.which(name):
            raise RuntimeError(f"Install PostgreSQL and put {name} on PATH.")
    if ROOT.is_symlink() or DATA.is_symlink() or PASSWORD.is_symlink():
        raise RuntimeError("Capture database paths must not be symbolic links.")
    ROOT.mkdir(mode=0o700, exist_ok=True)
    ROOT.chmod(0o700)
    PASSWORD.parent.mkdir(mode=0o700, exist_ok=True)
    if not PASSWORD.exists():
        if (DATA / "PG_VERSION").exists():
            raise RuntimeError(
                "Existing capture database password is missing; restore its protected password file."
            )
        descriptor = os.open(PASSWORD, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as file:
            file.write(secrets.token_urlsafe(48) + "\n")
            file.flush()
            os.fsync(file.fileno())
    PASSWORD.chmod(0o600)
    was_running = status()
    if not was_running:
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", PORT))
            except OSError as error:
                raise RuntimeError(
                    "Port 55435 is occupied; existing PostgreSQL services will not be modified."
                ) from error
        if not (DATA / "PG_VERSION").exists():
            initialized = run(
                "initdb",
                "-D",
                str(DATA),
                "-U",
                "capture_dev",
                "--auth=scram-sha-256",
                "--pwfile",
                str(PASSWORD),
                "--no-locale",
                "--encoding=UTF8",
            )
            (ROOT / "init.log").write_text(initialized.stdout)
        run(
            "pg_ctl",
            "-D",
            str(DATA),
            "-l",
            str(ROOT / "postgresql.log"),
            "-o",
            f"-h 127.0.0.1 -p {PORT} -k {ROOT}",
            "-w",
            "start",
        )
    try:
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=PORT,
            dbname="postgres",
            user="capture_dev",
            password=PASSWORD.read_text().strip(),
            connect_timeout=5,
        )
        try:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("SHOW data_directory")
                if Path(cursor.fetchone()[0]).resolve() != DATA.resolve():
                    raise RuntimeError(
                        "Refusing a different PostgreSQL data directory."
                    )
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = 'capture_dev'"
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "CREATE DATABASE capture_dev ENCODING 'UTF8' TEMPLATE template0"
                    )
        finally:
            connection.close()
    except Exception:
        if not was_running:
            stop()
        raise
    print("reused" if was_running else "started")


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["start"]:
            start()
        elif sys.argv[1:] == ["stop"]:
            stop()
        else:
            raise RuntimeError("Usage: capture_dev_postgres.py start|stop")
    except subprocess.CalledProcessError as error:
        # No command includes a password value. Keep stderr out of automation
        # output; PostgreSQL diagnostics live in the private workbench directory.
        raise SystemExit(
            f"PostgreSQL {Path(error.cmd[0]).name} failed; inspect {ROOT} logs."
        )
    except (RuntimeError, psycopg2.Error) as error:
        raise SystemExit(str(error))
