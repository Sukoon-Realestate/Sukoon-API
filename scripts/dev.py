#!/usr/bin/env python
"""
Unified Development Runner for Sukoon Real Estate Platform.
Runs both Django Backend (on local SQLite) and Next.js Frontend with a single command.
"""

import argparse
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

# ANSI colors for nice console logs
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def stream_logs(process, prefix, color):
    """Stream stdout/stderr from a child process with a colored prefix."""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            print(f"{color}{BOLD}{prefix}{RESET} {line.rstrip()}", flush=True)
    except Exception:
        pass


def run_command_sync(cmd, env=None, cwd=None):
    """Execute a synchronous setup command."""
    return subprocess.run(
        cmd,
        cwd=cwd or BASE_DIR,
        env=env or os.environ.copy(),
        shell=True,
    )


def prepare_database(reset=False, seed=False):
    """Check, migrate and seed SQLite database."""
    db_file = BASE_DIR / "dev.sqlite3"
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.local_sqlite"

    needs_init = reset or not db_file.exists() or seed

    if needs_init:
        print(f"\n{CYAN}{BOLD}[INIT]{RESET} Setting up SQLite development database...")
        
        # Determine pipenv prefix if available
        py_exec = sys.executable

        # 1. Apply migrations to SQLite DB
        print(f"{CYAN}{BOLD}[INIT]{RESET} Applying migrations to {db_file.name}...")
        res = subprocess.run(
            [py_exec, "manage.py", "migrate", "--settings=config.settings.local_sqlite"],
            cwd=BASE_DIR,
            env=env,
        )
        if res.returncode != 0:
            print(f"{RED}[ERROR] Migrations failed!{RESET}")
            return False

        # 2. Seed database
        reset_flag = ["--reset"] if reset else []
        print(f"{CYAN}{BOLD}[INIT]{RESET} Seeding database tables with test data...")
        res = subprocess.run(
            [py_exec, "manage.py", "seed_db", "--settings=config.settings.local_sqlite", *reset_flag],
            cwd=BASE_DIR,
            env=env,
        )
        if res.returncode != 0:
            print(f"{RED}[ERROR] Seeding failed!{RESET}")
            return False

        print(f"{GREEN}{BOLD}[SUCCESS] Database prepared & seeded!{RESET}\n")

    return True


def main():
    parser = argparse.ArgumentParser(description="Sukoon Unified Frontend & Backend Runner")
    parser.add_argument("--seed", action="store_true", help="Seed database before starting")
    parser.add_argument("--reset", action="store_true", help="Reset SQLite DB and re-seed from scratch")
    parser.add_argument("--backend-only", action="store_true", help="Start only backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Start only frontend server")
    parser.add_argument("--backend-port", default="8000", help="Backend port (default: 8000)")
    parser.add_argument("--frontend-port", default="3000", help="Frontend port (default: 3000)")

    args = parser.parse_args()

    # Change to root directory
    os.chdir(BASE_DIR)

    # 1. Prepare SQLite DB unless running frontend only
    if not args.frontend_only:
        db_ready = prepare_database(reset=args.reset, seed=args.seed)
        if not db_ready:
            print(f"{RED}Failed to prepare database. Exiting.{RESET}")
            sys.exit(1)

    processes = []

    def shutdown(signum=None, frame=None):
        print(f"\n{YELLOW}{BOLD}[SHUTDOWN]{RESET} Stopping servers gracefully...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for p in processes:
            try:
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print(f"{GREEN}[SHUTDOWN] All servers stopped.{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    print(f"{BOLD}{MAGENTA}======================================================{RESET}")
    print(f"{BOLD}{MAGENTA}  🚀 Starting Sukoon Unified Development Environment  {RESET}")
    print(f"{BOLD}{MAGENTA}======================================================{RESET}")

    py_exec = sys.executable
    backend_env = os.environ.copy()
    backend_env["DJANGO_SETTINGS_MODULE"] = "config.settings.local_sqlite"
    backend_env["PYTHONUNBUFFERED"] = "1"

    # Start Backend
    if not args.frontend_only:
        backend_cmd = [
            py_exec,
            "-m",
            "uvicorn",
            "config.asgi:application",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.backend_port),
        ]
        print(f"{GREEN}{BOLD}Backend:{RESET}  http://localhost:{args.backend_port}")
        p_back = subprocess.Popen(
            backend_cmd,
            cwd=BASE_DIR,
            env=backend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(p_back)
        t_back = threading.Thread(target=stream_logs, args=(p_back, "[BACKEND]", GREEN), daemon=True)
        t_back.start()

    # Start Frontend
    if not args.backend_only:
        frontend_env = os.environ.copy()
        frontend_env["PORT"] = str(args.frontend_port)
        frontend_env["NEXT_PUBLIC_API_URL"] = f"http://localhost:{args.backend_port}"

        # On Windows use npm.cmd, on POSIX use npm
        npm_bin = "npm.cmd" if os.name == "nt" else "npm"
        frontend_cmd = [npm_bin, "run", "dev", "--", "-p", str(args.frontend_port)]

        print(f"{CYAN}{BOLD}Frontend:{RESET} http://localhost:{args.frontend_port}")
        p_front = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            env=frontend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(p_front)
        t_front = threading.Thread(target=stream_logs, args=(p_front, "[FRONTEND]", CYAN), daemon=True)
        t_front.start()

    print(f"\n{YELLOW}Press Ctrl+C to stop both servers.{RESET}\n")

    try:
        # Wait for any process to exit
        while True:
            for p in processes:
                ret = p.poll()
                if ret is not None:
                    print(f"{RED}A process exited with code {ret}. Shutting down.{RESET}")
                    shutdown()
            import time
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
