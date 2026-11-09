# Sprint 00 evidence

**Run:** 2026-11-09 (Africa/Cairo) · **Source:** `main` at `4d2556cf` plus the uncommitted Sprint 00 changes listed in
[sprint-00](../../sprint-00-baseline-and-contracts.md#results-2026-11-09). Machine and package versions:
[environment.txt](environment.txt), [pip-freeze.txt](pip-freeze.txt).

## Scope and safety

- Environment: fresh `backend/.venv` (git-ignored) installed from `Pipfile.lock` with `--require-hashes --no-deps`;
  113/113 packages, `pip check` clean, `pillow-heif` 1.8.1 / libheif 1.23.6 importable. The existing pipenv
  virtualenvs were not modified.
- Tests used `config.settings.test` with every storage root (`MEDIA_ROOT`, chat/support/tour/evidence private
  roots, `STATIC_ROOT`) redirected to a temporary directory by a scratch-only settings wrapper. pytest-django used its
  in-memory SQLite test database. External network was blocked by `tools/qa/mvp_collection.py`.
- PostgreSQL: a disposable PostgreSQL 18.6 cluster created with `initdb` in a temporary directory (127.0.0.1:55432,
  TCP only, `fsync=off`), used through `config.settings.postgres_test`, then stopped. No shared or existing server.
- Protected state: SHA-256 of `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/database.sqlite3`, the 33 files in
  `media/` and the root `.env` (hashed, not read) were identical before and after all runs. No repository private-media
  directory was created. Nothing was deployed and no production system was contacted.

## Collection

`make test-collect`: **4,285 tests collected, 0 errors** (previously aborted on the `poll_voters` ImportError and on the
missing `pillow_heif`). No injected audit benchmark cases exist in the tree (the audit injected them only into temporary
copies), so none needed excluding. The Sprint 00 budget/repro tests are listed separately below and were not part of
the coverage runs.

## Test results

Full results, per-test classifications and node lists: [test-results.json](test-results.json).

| Run | Tests | Passed | Failed | Errors | Skipped | Deselected | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|
| SQLite, MVP scope (`SUKOON_MVP=true`, production default) | 4,270 | 2,303 | 984 | 204 | 99 | 680 | 4m42s |
| SQLite, restoration (`SUKOON_MVP=false`) | 4,270 | 3,905 | 224 | 6 | 135 | 0 | 12m20s |
| PostgreSQL, restoration, 149 affected modules | 1,912 | 1,787 | 124 | 0 | 1 | 0 | 12m22s |

Each failure was classified by running it in every mode, not by guessing from the message.

**Restoration (all features enabled):** 230 SQLite failures/errors =
- **121** SQLite engine artifacts: pass on PostgreSQL (`NotSupportedError`/`OperationalError`, e.g. visit-request
  endpoints return 500 on SQLite only). Treat SQLite results for these modules as invalid, not as regressions.
- **108 genuine failures** that also fail on PostgreSQL, concentrated in company/rental-value, account-policy,
  company-discussion and admin content modules (44 modules; list in `test-results.json` → `genuine_restoration`).
- **1** Sprint 00 test bug (`test_closed_poll_reports_closed_and_rejects_new_votes` read a cached poll); fixed and
  re-run green after the full run.
- Plus **15 PostgreSQL-only failures** in race/migration tests that SQLite skips (connected-authority concurrency,
  company discussions, saved lists, billing/statement migrations, release compatibility). 104 other
  PostgreSQL-only tests pass.

**MVP scope (what production runs by default):** 1,188 failures/errors =
- **1,051** gate-explained: deferred-feature tests that `mvp_collection.py` does not deselect; the MVP middleware/
  `authorize()` returns `403 mvp_feature_deferred` (often seen as `'JsonResponse' object has no attribute 'data'`).
  They pass with `SUKOON_MVP=false`. The deselection list is incomplete — harness drift, not product failure.
- **92** SQLite engine artifacts (pass on PostgreSQL).
- **27** mode-dependent: pass in restoration, fail under MVP with ordinary assertions (admin catalog/commerce editors,
  workspace campaigns, business-policy export). Each needs a decision: MVP behavior intended (mark/deselect) or MVP bug.
- **18** genuine (also fail in restoration on both engines).

Skipped categories (restoration): 124 PostgreSQL-required (run above; 5 need a second independent cluster for the
recovery drill and were not run), 8 Flutter-generated request fixtures, 2 native device voice clips, 1 requires
`cv2` (OpenCV is not in `Pipfile.lock`).

Determinism note: `test_purchase_events::test_event_identity_is_exact` parametrizes with random UUIDs, so its node IDs
change every run; fix before relying on node-level comparison or parallel runs.

## Coverage

Exercised statement coverage of application code (migrations/tests excluded), measured while the full suite ran:
**86.1 %** in restoration mode, **59.5 %** in MVP mode (65,027 statements). Per app: [coverage-by-app.md](coverage-by-app.md).
No import-only figure is used. PostgreSQL-only paths are not included in these numbers.

## Query/payload budgets

[`core_apps/common/test_api_budgets.py`](../../../core_apps/common/test_api_budgets.py), measurements in
[query-payload-budgets.json](query-payload-budgets.json). 13 screens at 5 and 40 rows: all **pass**, query counts flat
and equal to the audit benchmark (account 9, profile 1, settings 1, anonymous/tenant catalog 4/5, detail 9, owner 3,
saved 5, governorates 2, cities 2, types 1, notifications 7, unread 2). Growing screens are asserted to actually
include the added rows. Admin property list: **10 → 45 queries** over HTTP (A6-03), recorded as strict xfail.

## Failing-before cases for critical findings

| Finding | Test | Current result |
|---|---|---|
| A1-02 inherited Djoser deletion | `core_apps/users/tests/test_inherited_deletion_alias.py` | strict xfail; `--runxfail` shows "account removed with HTTP 200" |
| A6-03 admin property query growth | `core_apps/common/test_api_budgets.py::test_admin_property_list_query_count_is_flat` | strict xfail; 45 ≠ 10 |

Strict xfail means the fixing PR must remove the marker (the test turns red when the defect is fixed and the marker
stays). The other High findings (A1-01, A1-03, A2/A3 eligibility and storage, A4 refunds, A5-01 edit moderation) do
**not** yet have failing-before cases.

## Static baselines

| Check | Result | File |
|---|---|---|
| Import every `core_apps`/`config` module (test settings) | 1,865 imported, 0 failed | [import-baseline.json](import-baseline.json) |
| Django `check` (postgres_test) | no issues | — |
| `makemigrations --check --dry-run` (postgres_test) | no changes | — |
| flake8, repository config (`.flake8`, F401/W503 ignored) | 3,151 diagnostics (1,110 F811, 749 E501, 441 E231, 314 E128, 25 F841, …) | [flake8-configured.txt](flake8-configured.txt) |
| flake8 `--isolated --select=F` | 4,140 (3,000 F401, 1,110 F811, 25 F841, 2 F405, 2 F402, 1 F541) | [flake8-isolated-F.txt](flake8-isolated-F.txt) |
| Ruff, pip-audit | not run — not in the lock; not installed to avoid changing the declared environment | — |

The configured flake8 count differs from the audit's "8 diagnostics" because the audit linted a selected subset; this is
the whole backend. `.flake8` now excludes `.venv` (without it `make lint` scanned site-packages: 486,958 lines).

## Route matrix

`make route-matrix` regenerates [ROUTE_MATRIX.md](../../ROUTE_MATRIX.md) and [route-matrix.json](route-matrix.json):
795 API patterns (526 decorated FBV, 243 DRF CBV, 22 viewset, 2 plain callbacks, 2 router-generated), 189 families,
193 patterns sharing a handler, 413 refused under MVP scope, 350 without an HTTP-level test reference. These numbers
match the audit's runtime inventory exactly.

## Reproduce

```bash
cd backend
make test-collect
make test-baseline-mvp BASELINE_OUT=/tmp/sukoon-baseline
make test-baseline-restoration BASELINE_OUT=/tmp/sukoon-baseline
TEST_POSTGRES_DB=<disposable> TEST_POSTGRES_USER=<user> TEST_POSTGRES_HOST=127.0.0.1 TEST_POSTGRES_PORT=<port> \
  make test-postgres-races PG_TESTS="<modules>"
make route-matrix import-baseline
```
