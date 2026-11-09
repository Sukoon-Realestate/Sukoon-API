# CLAUDE.md — Sukoon Backend API

---

For model/migration/endpoint/serializer work, prefer the `django-feature` skill.

## Project conventions (always honor)
- Use the `Makefile` targets. The environment is built from `Pipfile.lock` (Python 3.11, includes
  `pillow-heif`): `pipenv install`, or a hash-checked `backend/.venv` as described in the
  `django-feature` skill. There is no `./Venv/`.
- Settings live in `config/settings/` (`base.py` + one module per environment). Tests use
  `config.settings.test` (pytest.ini); PostgreSQL tests use `config.settings.postgres_test` with disposable
  `TEST_POSTGRES_*` values. Deployed env comes from the repo-root `.env`/platform; never read or edit it for tests.
- Apps live in `core_apps/<app>/` (urls → thin views → serializers → `services/`).
- Architecture target (user-approved; see `sprints/ARCHITECTURE.md`): new and converted HTTP endpoints are
  explicit class-based views; domain services own transactions, locks, authority and side effects. The existing
  526 `@api_view` routes are migration debt converted by sprints 05–10 — do not add new `@api_view` functions
  and do not change route names/aliases/contracts during conversion.
- DRF endpoints use cookie/SimpleJWT auth (`core_apps.common.cookie_auth`), django-filter and the configured
  pagination/renderer. Admin is Django admin plus the `admin_api` staff API (no django-unfold).
- The MVP release switch (`SUKOON_MVP`, default true) gates deferred routes in `core_apps/common/mvp_scope.py`;
  run both `make test-baseline-mvp` and `make test-baseline-restoration` for cross-cutting changes.
- Regenerate `sprints/ROUTE_MATRIX.md` (`make route-matrix`) whenever routes change.
- Never alter `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/`, `media/` or production state to make tests pass.
