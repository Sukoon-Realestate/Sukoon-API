---
name: django-feature
description: Build or change Sukoon backend features the right way. Use when adding or changing a model, migration, DRF endpoint, serializer, filter, permission or service in Sukoon-API/backend, or when running its tests. Encodes the real layout (core_apps/ apps, config/settings/ split, Pipfile.lock environment, SimpleJWT cookie auth, django-filter, MVP release scope) and the approved CBV + service architecture in sprints/ARCHITECTURE.md.
---

# Sukoon backend feature workflow

Django 4.2 + DRF 3.15 + SimpleJWT + Channels. Read `sprints/ARCHITECTURE.md` before changing an HTTP route;
it is the target this skill follows. Existing function views are migration debt, not a pattern to copy.

## Layout

```
config/settings/      base.py + one module per environment (test, postgres_test, local, local_sqlite,
                      production, staging, ...). Tests use config.settings.test (pytest.ini).
config/urls.py        mounts each app under api/v1/<area>/ (features under api/v1/features/v1/)
core_apps/<app>/      users, profiles, properties, virtual_tours, features, chat, notifications,
                      support, advertising, admin_api, common
  urls.py             stable paths/names; aliases are client contracts — never drop one silently
  views/ or *_views.py  thin transport adapters
  serializers/        command (input) and response serializers
  services/           domain commands: invariants, authority, transactions, locks, receipts
  tests/              pytest modules (test_*.py)
```

## Environment

- `backend/.venv` built from the lock: `pipenv requirements --hash > /tmp/req.txt` then
  `python3.11 -m venv .venv && .venv/bin/pip install --require-hashes --no-deps -r /tmp/req.txt`.
  `pipenv install` (Makefile `install`) also works. Python 3.11; `pillow-heif` is required.
- Never point tests or scripts at `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/`, `media/` or the
  root `.env`. Under pytest, `config.settings.test` uses an in-memory SQLite test DB, but a management
  command run with that module opens `db.sqlite3` — use `config.settings.postgres_test` with a disposable
  `TEST_POSTGRES_*` database instead.

## Views (approved target)

- New and converted HTTP endpoints are explicit classes: DRF generic views for ordinary resource reads,
  `APIView` for commands/stateful workflows, Django `View` only for raw signed callbacks or byte streaming.
  Do not add new `@api_view` functions; do not wrap a long function body in `post()` and call it done.
- A view parses input with a command serializer, checks current authority, calls one service/selector and
  formats the response. Business state changes, `transaction.atomic`, `select_for_update`, receipts and
  `on_commit` side effects live in `services/`. Services never import view modules.
- Keep route names, aliases, methods, status codes, headers and response envelopes identical unless a
  separately approved fix says otherwise. Company routes are authorized by `features/services/company/role_routes.py`
  keyed on the callable — replace that policy explicitly before changing callable identity.

## DRF defaults (config/settings/base.py)

Auth `core_apps.common.cookie_auth.CookieAuthentication`; default permission `IsAuthenticated`; pagination
`core_apps.common.pagination.StandardResultsSetPagination` (PAGE_SIZE 10); filter backend `DjangoFilterBackend`;
renderer `GenericJsonRenderer`; exception handler `custom_exception_handler`; anon/user throttles.
Staff endpoints use role permissions in `core_apps/admin_api/permissions.py` (e.g. `IsPropertyReviewer`).

## MVP release scope

`SUKOON_MVP` (default true) makes `core_apps/common/mvp_scope.py` refuse deferred routes and group/company/student
workflows with `403 mvp_feature_deferred`. A new route must be classified there. Tests run in two modes:

```bash
make test-baseline-mvp          # production default; deferred tests deselected and listed
make test-baseline-restoration  # SUKOON_MVP=false; whole suite
```

## Checks before finishing

- Focused tests for valid, invalid-input, permission and edge cases; add a query budget for list endpoints
  (pattern: `core_apps/common/test_api_budgets.py`).
- Migrations: `make check-owner-tenant` (Django check + `makemigrations --check --dry-run` on
  `config.settings.postgres_test`; export disposable `TEST_POSTGRES_*` values first).
- After route changes, regenerate the matrix: `make route-matrix` and review `sprints/ROUTE_MATRIX.md`.
- `make lint` (flake8; F401 is ignored by config, so check unused imports manually).
- Log the task in `../WORKLOG.md`.
