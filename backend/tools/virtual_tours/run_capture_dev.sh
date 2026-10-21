#!/usr/bin/env bash
# Isolated loopback workbench. Existing servers/databases are not modified.
set -euo pipefail
capture_backend_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$capture_backend_dir"
capture_python="$capture_backend_dir/.venv/bin/python"
"$capture_python" - <<'PY'
import socket
with socket.socket() as sock:
    try:
        sock.bind(('127.0.0.1', 8026))
    except OSError:
        raise SystemExit('Port 8026 is already in use. Keep the existing workbench or stop its process first.')
PY
capture_api_pid=''
capture_worker_pid=''
capture_pg_owned=false
stop_capture() {
  if [[ -n "$capture_worker_pid" ]]; then kill "$capture_worker_pid" 2>/dev/null || true; fi
  if [[ -n "$capture_api_pid" ]]; then kill "$capture_api_pid" 2>/dev/null || true; fi
  if [[ -n "$capture_worker_pid" ]]; then wait "$capture_worker_pid" 2>/dev/null || true; fi
  if [[ -n "$capture_api_pid" ]]; then wait "$capture_api_pid" 2>/dev/null || true; fi
  if [[ "$capture_pg_owned" == true ]]; then
    "$capture_python" tools/virtual_tours/capture_dev_postgres.py stop
  fi
}
trap stop_capture EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
capture_pg_state="$("$capture_python" tools/virtual_tours/capture_dev_postgres.py start)"
if [[ "$capture_pg_state" == 'started' ]]; then capture_pg_owned=true; fi
"$capture_python" manage.py migrate --settings=config.settings.capture_dev --noinput
"$capture_python" manage.py prepare_property_capture_demo --settings=config.settings.capture_dev
"$capture_python" manage.py check_property_capture_config --settings=config.settings.capture_dev --strict
"$capture_python" manage.py runserver 127.0.0.1:8026 --settings=config.settings.capture_dev --noreload &
capture_api_pid=$!
"$capture_python" manage.py run_property_capture_worker --settings=config.settings.capture_dev &
capture_worker_pid=$!
while kill -0 "$capture_api_pid" 2>/dev/null && kill -0 "$capture_worker_pid" 2>/dev/null; do
  sleep 1
done
printf '%s\n' 'Capture API or worker stopped; shutting down this workbench.' >&2
exit 1
