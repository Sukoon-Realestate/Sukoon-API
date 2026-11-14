# Sprint 10 — admin/shared architecture evidence

Date: 2026-11-14. Scope: Sprint 10 only. **Status: implemented; local validation passed; acceptance remains partial at the limits below.** No application migration, dependency update, deployment, production operation,
existing database mutation or later-sprint implementation was performed. Existing staged Sprint 09 work was preserved.

## Implemented

- Preserved thin admin API classes and canonical property moderation across legacy/API/native adapters. Original JWT
  claims now reach decision replay; malformed legacy command containers/versions fail as client errors. Existing legacy
  bodyless-client success/conflict behavior, explicit-key receipts and persisted fingerprint contents are retained.
- Report decisions now reload/lock current staff inside the command, enforce sensitive access, fence original sessions
  and reject decisions by the reporter or reported account.
  Broad active staff/support dismiss/reactivate scope remains supported; account suspension/ban still requires manager scope.
  Missing current staff accounts fail closed. Native admin login/requests reject disabled staff profiles, and unsafe requests
  check current sensitive access. Native public-content saves enforce system-owner authority and retain audit/revision writes.
- Converted health and app associations plus every project-owned custom KYC, policy, chargeback, mandate, portfolio,
  reputation and tour native callback to explicit Django classes. Django's session, CSRF, native message/template and file
  behavior remain in place. Reputation change URLs still redirect to reasoned inspection. Tour review transactions and
  emergency suppression now have domain command boundaries. Framework-owned admin internals were left intact.
- Shared typed content/campaign containers live outside views. Command/receipt, response/error/correlation and private
  ownership/reference contracts are explicit in [SHARED_CONTRACTS.md](../../SHARED_CONTRACTS.md), including deliberate
  native workflow differences. Operational logs no longer include reviewer/account emails. Audit-source database failures
  propagate instead of returning silently incomplete history; known private-storage failures use narrow recovery boundaries.
- Campaign previews constrain actual membership/audience predicates in SQL before scan/recipient limits, prepare consent
  and valid-device facts in 500-account batches, preserve preference initialization, and bulk-create immutable recipients/
  deliveries. Dispatch still reloads current authority/consent/device state. Roles use one grouped count. System health
  selects its six audit rows through SQL pagination, preserving complete history without full-history materialization.
- Revalidated earlier complete transaction/audit filtering, current KYC predicates, status/search, grouped analytics,
  campaign summaries and relational content fetch plans. Added repeatable Make gates, global resolver/import inventory,
  [actual operational paths/gates](../../OPERATIONS.md), source records and the results below.

## Validation and reproduction

Authoritative counts, failed diagnostic attempts, skips and JUnit paths are in [validation.json](validation.json).
The pre-change admin/common SQLite baseline passed **525**, with **201 skipped**. Early post-change regressions passed
552 with 203 skipped, and the first PostgreSQL focused run passed 805 with five independent-journal skips.

| Gate | Result |
|---|---|
| Complete Sprint 10 PostgreSQL gate (`completion-postgres`) | **1,104 passed, 7 skipped**, no failures/errors |
| Final admin/storage SQLite gate | **346 passed, 2 skipped** |
| Last moderation compatibility/boundary gate | **52 passed** |
| Full MVP PostgreSQL baseline | **6,113 passed, 21 skipped, 12 expected failures**, no unexpected failures/errors |
| Full restoration PostgreSQL baseline | **6,113 passed, 21 skipped, 12 expected failures**, no unexpected failures/errors |

The complete gate includes native adapters, source/HTTP contracts and row-lock tests. The last moderation gate additionally
preserves a supplied whitespace version as a stale command (409), rather than accidentally normalizing it into the bodyless
legacy fallback. Its serializer/boundary correction was checked after the complete PostgreSQL gate.
The preceding complete `verified-postgres` gate passed 1,094 with seven skipped.
The full MVP/restoration runs are broader regressions, not a deployed certification. They started before the last native
callback/template, command-boundary and test-fixture corrections; the final complete scoped gate covers those final changes.
No green *whole-backend final-tree rerun* is inferred from overlapping runs.

The seven complete-gate skips are five independent PostgreSQL journal/drill cases (separate cluster not supplied),
plus two tour-capture cases requiring OpenCV, which is absent from the lock/runtime. These are not accepted as passing.

The retained failed attempts are diagnostic evidence, not passing results. The initial PostgreSQL sandbox run could not
open the new private Unix socket; it was rerun with permission against the same disposable cluster. Early native callback
conversions had an incorrect template-context attribute, corrected before final acceptance. New parity fixtures initially
omitted required housing expiry and used an invalid public-page slug; both were corrected and rechecked. One early
`new-sqlite` log received overlapping diagnostic output; use its JUnit and later independent gates for authoritative outcomes.

All application tests used `DOTENV_DISABLED=1`, scratch settings and private storage under `/private/tmp/sukoon-sprint10`.
The new PostgreSQL 18 cluster had TCP disabled, its own Unix socket/role and `max_locks_per_transaction=1024`;
separate test names isolated concurrent databases. The retained settings examples and `scratch-cluster.json` describe
this local synthetic setup, without production inputs. Provider outcomes are simulated; test network guards remained active. The task-owned PostgreSQL cluster was stopped
after every PostgreSQL process completed. [database-preservation.json](database-preservation.json) confirms identical
before/after SHA-256 values for all four existing repository SQLite files.

From `Sukoon-API/backend/`, initialize an equivalent fresh disposable cluster and choose fresh scratch settings/names:

```sh
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  SPRINT10_TEST_DB=<unique-disposable-name> \
  SPRINT04_METRICS=<scratch-output>/metrics.jsonl \
  make test-sprint10-admin-shared CYCLE_SETTINGS=<scratch-module> BASELINE_OUT=<scratch-output>
DOTENV_DISABLED=1 make sprint10-coverage
DOTENV_DISABLED=1 make route-matrix
DOTENV_DISABLED=1 make import-baseline
```

Both integrated targets were run with `CYCLE_SETTINGS=sprint10_postgres`, separate test names and an explicit
`BASELINE_PYTEST='.venv/bin/python -m pytest -p no:cacheprovider -o addopts="--strict-markers --tb=short" -q -rfE --cov=core_apps --cov-report= --ds=sprint10_postgres'`.
The explicit `--ds` matters: the existing baseline targets' default command otherwise follows pytest.ini's SQLite module.
Use `make test-baseline-mvp` and `make test-baseline-restoration`, with different `BASELINE_OUT` values. Native fixture and
physical-provider skips remain visible in their JUnit. No production environment or installed existing database is a valid
replacement for the disposable settings.

## Measured query budgets

PostgreSQL synthetic measurements, recorded in `metrics-postgres.jsonl`; these are local query counts, not production SLOs.
SQLite measurements are separately retained in `metrics.jsonl` (SQLite insert batching adds one query at 100 preview users).

| Case | Fixture sizes | Queries |
|---|---|---|
| Property projection | 5 / 40 / 100 | 1 / 1 / 1 |
| Current KYC / report projections | 1 / 20 / 100 each | 1 at every size |
| Analytics rolling windows | 7 / 30 / 90 days | 14 at every size |
| Executive dashboard | 30 days | 14 |
| Campaign summary history | 1 / 10 / 100 | 5 at every size |
| Relational content (cities, districts, campuses, plans, benefits) | 1 / 25 each | 1 at every size |
| Campaign preview, including initialized preferences and receipt writes | 1 / 20 / 100 eligible accounts | 13 at every size |
| Role summary | All configured roles | 1 (asserted) |

History regressions reach 505 matching payment attempts and 106 cross-source audit entries, asserting SQL page hydration
budgets and stable ordering/search/counts beyond old 500/100 caps. The 5,001-account campaign fixture now uses a real
eligible landlord beyond the former source cap, rather than a monkeypatched eligibility predicate. Prepared membership
facts are compared with canonical current eligibility across six audiences and both release modes.

## Acceptance status and remaining limits

- Resolver/source acceptance: all **795 API patterns** preserve path/name/method/authentication/permission/parser/throttle/
  alias/MVP metadata; **92 admin/shared/native patterns** are inventoried; zero project-owned function callbacks remain
  across the full resolver. The **956 framework-owned admin callbacks** are identified separately. Shared services do not
  import project views. These are structural assertions; they do not replace command/result tests.
- Current role, disabled profile, independence, sensitive access, stale revisions, duplicate/conflicting keys and replay
  have selected positive/negative HTTP/native/direct-service coverage. An exhaustive positive method × alias × role ×
  factor × object × replay matrix is **not established**. Global route fixtures predominantly use empty commands and
  unknown resource IDs; do not describe them as exhaustive successful workflow coverage.
- Legacy full service histories and content-detail audit histories remain complete and data-dependent for compatibility.
  Public admin history pages and the health sample use SQL selection. Campaign previews retain explicit configurable scan
  and recipient limits (defaults 100,000 / 5,000), and batching bounds Python/query fan-out rather than guaranteeing constant
  database work or lock duration for every population/device distribution. Universal hard payload/scan/lock-time budgets
  are **not accepted** from these local measurements.
- Two capture/OpenCV checks and five independent PostgreSQL drill checks remain skipped, as detailed above.
- Controlled deployed TLS, source-version/process identity, real Redis/worker/scheduler/storage/scanner delivery, provider
  outcomes, backup restore and approved recovery/RPO/RTO evidence remain **Sprint 12 acceptance**, intentionally unperformed.
  No synthetic deployment check is offered as deployed readiness. The independent recovery journal remains a separately
  retired product feature; local command presence is not reopening approval.

Stop after Sprint 10. No Sprint 11 cleanup or Sprint 12 rollout/acceptance was executed.
