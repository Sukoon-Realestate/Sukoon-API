#!/usr/bin/env bash
# Real row-locking tests in an owned, temporary PostgreSQL cluster.
set -euo pipefail
capture_backend_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$capture_backend_dir"
capture_pg_port="${CAPTURE_TEST_PG_PORT:-55436}"
for capture_pg_command in initdb pg_ctl createdb; do
  command -v "$capture_pg_command" >/dev/null || {
    printf 'PostgreSQL command missing from PATH: %s\n' "$capture_pg_command" >&2
    exit 1
  }
done
.venv/bin/python - "$capture_pg_port" <<'PY'
import socket
import sys
try:
    port = int(sys.argv[1])
    if not 1024 <= port <= 65535:
        raise ValueError
except ValueError:
    raise SystemExit('CAPTURE_TEST_PG_PORT must be an integer between 1024 and 65535.')
with socket.socket() as sock:
    try:
        sock.bind(('127.0.0.1', port))
    except OSError:
        raise SystemExit('Test port is in use; existing PostgreSQL services will not be modified.')
PY
capture_pg_dir="$(mktemp -d "${TMPDIR:-/tmp}/sokoun-capture-pg.XXXXXX")"
capture_pg_started=false
finish_capture_pg() {
  if [[ "$capture_pg_started" == true ]]; then
    pg_ctl -D "$capture_pg_dir/data" -m fast -w stop >/dev/null
  fi
  printf 'Isolated PostgreSQL logs retained in: %s\n' "$capture_pg_dir"
}
trap finish_capture_pg EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
initdb -D "$capture_pg_dir/data" -U capture_qa --auth=trust --no-locale --encoding=UTF8 > "$capture_pg_dir/init.log"
pg_ctl -D "$capture_pg_dir/data" -l "$capture_pg_dir/server.log" -o "-h 127.0.0.1 -p $capture_pg_port -k $capture_pg_dir" -w start
capture_pg_started=true
createdb -h 127.0.0.1 -p "$capture_pg_port" -U capture_qa capture_qa
TEST_POSTGRES_DB=capture_qa TEST_POSTGRES_USER=capture_qa TEST_POSTGRES_PASSWORD='' \
  TEST_POSTGRES_HOST=127.0.0.1 TEST_POSTGRES_PORT="$capture_pg_port" \
  .venv/bin/python -m pytest --ds=config.settings.postgres_test core_apps/virtual_tours/tests --disable-warnings "$@"
