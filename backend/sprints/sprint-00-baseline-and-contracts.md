# Sprint 00 — Establish a trustworthy baseline and contracts

**Outcome:** changes can be evaluated against real behavior, supported clients and a runnable regression environment.
**Owners:** backend lead + QA; product/client owners for intentional contract changes.
**Evidence:** [baseline](BASELINE.md), A5-12, A6-12. This does not postpone urgent safety stories in Sprint 01.

## Work

- Restore a reproducible Python environment from the declared lock, including HEIF support. Resolve the missing
  `poll_voters` test import by deciding the actual contract: restore a scoped feature if required or update stale tests
  to the approved aggregate contract. Do not add a dummy implementation or delete the whole module to get green tests.
- Run collection first, then the meaningful suite. Separate SQLite, disposable PostgreSQL, provider/worker/storage and
  device-dependent tests; report skips/failures explicitly. Exclude injected audit benchmark cases from application coverage.
- Turn [API_INVENTORY.md](API_INVENTORY.md) into a maintained route/method/alias matrix. Add auth source, role/workspace,
  request schema, response/header contract, current-authority checks, mutation locks, receipts and tests per route family.
- Inventory uploads and intended feature availability. Identify real disabled/fake/staging paths versus public production
  functionality before any cleanup. Record supported legacy aliases and removal/deprecation requirements.
- Approve [ARCHITECTURE.md](ARCHITECTURE.md); update stale function-only/path/environment instructions in the repository.
- Establish fixture-backed query/payload budgets at small and large sizes, a lint/import baseline, and an evidence folder
  containing machine versions, settings, scope and tool outcomes. Obtain a disposable PostgreSQL target for race tests.

## Completion evidence

- Collection succeeds with zero unresolved import errors; environment/package versions and skipped categories are recorded.
- The actual full-suite result and valid exercised coverage are recorded. No percentage from import-only execution is used.
- Every API family has a named owner and compatibility matrix; every future migration batch has focused contract fixtures.
- Critical fixes have reproducible failing-before/passing-after cases even if broader environment recovery continues.
- No secrets, existing databases, media or production state are altered to manufacture a baseline.

**Next:** proceed by the dependencies in the roadmap; update counts when the source changes, rather than treating this
audit's file/route numbers as timeless constants.

## Results (2026-11-09)

Executed on `main` at `4d2556cf`; changes are uncommitted for review. Evidence: [evidence/sprint-00](evidence/sprint-00/README.md).
No existing database, media, secret or production system was altered (hashes verified before/after).

### Work items

| Item | Status | Result |
|---|---|---|
| Reproducible environment incl. HEIF | Done | `backend/.venv` from `Pipfile.lock` with hash checking; 113/113 packages, `pip check` clean, pillow-heif/libheif import |
| `poll_voters` contract | Done — needs product sign-off | No voter-identity helper, route or client ever existed (test added in `1bedcec2` without an implementation). Approved contract recorded as **aggregate counts + viewer's own choice**; the three stale tests were rewritten against it, link/vote/close/membership coverage kept, no dummy helper. A voter list would be a new privacy-reviewed feature |
| Collection, then suite; categories | Done | 4,285 collected / 0 errors. Full SQLite runs in MVP and restoration modes; 149 affected modules on disposable PostgreSQL; skips and failures classified per test |
| Route/method/alias matrix | Done (generated) | [ROUTE_MATRIX.md](ROUTE_MATRIX.md) via `make route-matrix`: methods, auth, permissions, throttles, parsers, schema hints, MVP availability, aliases, lock/receipt/authority/header/upload signals, test references, owning area/sprint |
| Uploads, feature availability, aliases | Done (code defaults) | [FEATURE_AVAILABILITY.md](FEATURE_AVAILABILITY.md); deployed env values not inspected |
| Architecture approval / stale guidance | Guidance done; approval open | `backend/CLAUDE.md`, root `CLAUDE.md` and the tracked `django-feature` skill (written for another project) now describe `core_apps/`, `config/settings/`, the lock-based env and the CBV + service target |
| Budgets, lint/import baseline, evidence, PostgreSQL target | Done | 13-screen 5/40 budgets pass; import 1,865/0; flake8 baselines; disposable PostgreSQL 18.6 used for race tests |

### Completion evidence

| Criterion | Met? | Notes |
|---|---|---|
| Collection succeeds with zero unresolved import errors; versions and skipped categories recorded | **Yes** | [environment.txt](evidence/sprint-00/environment.txt), skip categories in the evidence README |
| Actual full-suite result and valid exercised coverage recorded | **Yes** | MVP 2,303 pass / 1,188 fail+error; restoration 3,905 / 230; coverage 59.5 % / 86.1 % (exercised). The suite is **not green**: 108 genuine restoration failures + 15 PostgreSQL-only race failures, and 1,051 MVP-mode tests need deselection/marking |
| Every API family has a named owner and compatibility matrix | **Partly** | Every family has an owning area and sprint; **named individuals are not assigned** (needs the backend lead) |
| Every future migration batch has focused contract fixtures | **Yes (boundary level)** | `core_apps/common/test_route_contracts.py` + 189 committed family fixtures in `core_apps/common/route_contracts/`: every pattern/alias/method × anonymous/tenant/staff × MVP on/off — 6,072 observations of status, content type, envelope, data shape, error code, Cache-Control and serving URL name; PostgreSQL lane (`make route-contracts`). Unknown-ID/empty-body calls, so object-specific success payloads stay covered by each family's own tests |
| Critical fixes have failing-before cases | **Yes** | Strict-xfail repros for every High finding with an application fix: A1-01 avatar ownership, A1-02 inherited deletion, A1-03 social adoption, A3-01 portfolio media retention, A4-01 partial-refund commission, A5-01 edit moderation, A6-03 admin query growth; each verified to fail for its documented reason |
| No secrets, databases, media or production state altered | **Yes** | SHA-256 before/after identical |

### Open items handed to the owners

1. Product: approve the aggregate poll contract (or request a privacy-reviewed voter list).
2. Backend lead: approve [ARCHITECTURE.md](ARCHITECTURE.md); name an owner per area in ROUTE_MATRIX.
3. QA: extend `tools/qa/mvp_collection.py` (or mark tests) so MVP mode has no gate-explained failures; triage the 27
   mode-dependent and 108 + 15 genuine failures; replace random-UUID parametrize IDs in `test_purchase_events`.
4. Run SQLite-incompatible modules on PostgreSQL in CI (`make test-postgres-races`); provision the second independent
   cluster for the 5 recovery-drill tests.
5. Ops: confirm deployed values of the switches in FEATURE_AVAILABILITY.md.
6. Ruff/pip-audit and the Django 4.2 support-end upgrade remain for Sprint 01.
