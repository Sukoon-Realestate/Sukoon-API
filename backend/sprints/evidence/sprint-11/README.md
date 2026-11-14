# Sprint 11 — cleanup and standards evidence

Date: 2026-11-14. Scope: Sprint 11 only. **Status: implemented; local regression gates passed; acceptance is partial at the boundaries below.**
No deployment, existing-database operation, application migration, dependency update or Sprint 12 work was performed.

## Changes and retained contracts

- Consolidated the repeated read-only advertising media check in its existing module. Missing artwork stays unavailable;
  serving cannot restore fixture bytes or fabricate artwork. The explicit original-byte repair command still verifies
  recorded length/digest, defaults to dry-run and requires `--apply`; it now logs successful verification/repair identity,
  digest, length and apply status without source paths or artwork bytes. Keep the operational log sink with repair records.
- Preserved existing owner aggregate/no-history contracts from earlier sprints and corrected dummy-number documentation.
  Acceptance remains null without confirmed/rejected visits; reputation remains the canonical source for ratings/reviews.
- Removed a reviewed group of copied unused imports, unused local bindings and a duplicate JWT exception import. Staff
  invitation calls, auth exception behavior, canonical visit review policy and all model/route/task identities remain.
- Preserved 37 facade namespaces with explicit public `__all__` lists and narrowly documented private-import exceptions.
  Existing facade imports that might be external compatibility/test seams remain. This adds explicit contract declarations;
  it is not a claim that every imported helper is a required API. All 1,017 inventoried names remain available.
- Removed the blanket F401 ignore, added strict scoped lint and a visible classification/no-new-debt gate. Current F401
  warnings fell from 2,145 to 1,107, mostly through explicit exports rather than deletions. F811 fell from 1,110 to 1,107;
  F841 from 25 to 20. No global suppression or automatic import deletion was used. Uncertain candidates remain visible.
- Earlier sprints already removed obsolete chat broadcast/notification helpers and the unrouted preferences view. Retained
  current preferences/outbox and direct-service-tested `PropertyMediaMixin`, fake/test providers, gated QA tools, client
  upgrade responses, migrations and durable task/event names. No seed tool was executed.

[cleanup-decisions.md](cleanup-decisions.md) records caller/registration/migration/client decisions and replacement coverage.
[cleanup-changes.json](cleanup-changes.json) records individual removals. [facade-exports.json](facade-exports.json),
[facade-runtime.json](facade-runtime.json) and [facade-surface-parity.json](facade-surface-parity.json) record export evidence.
[source-digests.json](source-digests.json) identifies changed source versions. No obsolete private function was deleted.

## Validation

The authoritative case counts, skips/expected failures and failed diagnostic attempt are in [validation.json](validation.json).
Full MVP PostgreSQL regression: **6,140 passed, 21 skipped, 12 expected failures**, zero unexpected failures/errors.
Full restoration PostgreSQL regression: **6,140 passed, 21 skipped, 12 expected failures**, zero unexpected failures/errors.

- Focused SQLite regressions: **63 passed, 1 skipped**.
- Cleanup SQLite gate: **621 passed, 253 skipped**. Most skips are explicit PostgreSQL-dependent cases; this is not a
  PostgreSQL locking/JSON/transaction certification. The earlier sandbox attempt passed 620 with 253 skips and one
  live-server bind error. Permission-enabled rerun resolved that fixture error; the attempt remains recorded.
- Import validation: **2,041 modules imported, zero failures** under isolated settings.
- Query regression measurements retain admin property projection **1 / 1 / 1** queries at 5 / 40 / 100 rows;
  advertising owner pages **3 / 3 / 3** and rejected feeds **1 / 1 / 1** at 1 / 10 / 100. Local synthetic query counts
  are not production SLOs. Full metrics are retained in the JSONL files.
- All **795 API patterns** retain paths/names/methods/authentication/permissions/parsers/throttles/aliases/MVP metadata.
- **2,221 Python files** parse successfully, honoring the existing UTF-8 BOM. An initial diagnostic reader omitted BOM
  handling; the reader was corrected without changing that source file.
- Strict changed-file F401/F811/F841 lint and visible debt gate pass. All 37 facade public surfaces match their original
  implicit names. Public application signatures/annotations are unchanged. Django checks report no issues and
  `makemigrations --check --dry-run` reports no changes. The final scoped lint and runtime import checks also cover the last import-only/formatting corrections made after the
  full suites started; do not infer a separate full-suite rerun after those equivalent import declarations.
  No mypy/pyright dependency is configured or installed;
  AST signature/annotation compatibility is explicitly not whole-project static type verification.

All test settings use `DOTENV_DISABLED=1`, scratch database/storage roots under `/private/tmp/sukoon-sprint11` and simulated
provider outcomes with the existing network guards. No production secrets/settings were read. A newly initialized
PostgreSQL 18 cluster has TCP disabled, a private Unix socket and separate MVP/restoration databases. The initial sandbox
could not allocate PostgreSQL shared memory; the same new, task-owned setup was initialized with the required permission.
No pre-existing cluster was used. Scratch settings examples, versions and cluster details are retained beside this file.

The four existing repository SQLite files have identical before/after hashes in
[database-preservation.json](database-preservation.json). The task-owned PostgreSQL cluster was stopped after both full suites finished.

Reproduction from `backend/`, with fresh disposable settings/storage and a separate fresh PostgreSQL database per process:

```sh
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  make test-sprint11-cleanup CYCLE_SETTINGS=<isolated-module> BASELINE_OUT=<scratch-output>
make sprint11-standards
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  DJANGO_SETTINGS_MODULE=<isolated-module> .venv/bin/python tools/qa/import_baseline.py --json <scratch-output>/imports.json
```

For both complete release-mode runs, use `make test-baseline-mvp` / `make test-baseline-restoration` with an explicit
`BASELINE_PYTEST='.venv/bin/python -m pytest -p no:cacheprovider -o addopts="--strict-markers --tb=short" -q -rfE --ds=<scratch-module>'`.
The explicit `--ds` prevents pytest.ini from selecting default SQLite settings. The retained scratch settings examples
assign each mode its own media root and unique disposable database name. Provider/network results remain synthetic.

## Acceptance boundaries

- Uncertain imports remain candidates, with no claim that textually unused means dead. Every current selected diagnostic
  has a retained classification. The original selected audit's 2,476 F401 warnings used a different tree/scope; the available
  whole-backend Sprint 00 log has 3,000. [historical-f401-classification.json](historical-f401-classification.json) classifies
  that historical log by review ownership. Exact one-to-one reconciliation of the older 2,476 subset is **not established**.
- Full-tree lint is **not green**: 1,107 F401, 1,107 F811 and 20 F841 diagnostics remain visible (many are fixture registration
  and supported exports, others need semantic consumer review). The scoped passing gate does not certify their removal.
- Full-suite omissions remain **open**, not passing: two native voice clips, eight fresh Flutter request-body
  artifacts, four intentionally inapplicable edit-screen alias cases, two OpenCV checks and five independent PostgreSQL
  journal/drill checks. Twelve existing expected failures retain the deliberate company-chat role-audience lock and known
  company mandate/member authority gaps (BUG-AUTH-01). This cleanup does not accept or repair those product contracts.
- A full static type-checker pass is **not established**; unchanged signature/annotation and runtime import checks are the
  available scoped compatibility evidence.
- Deployed/provider/worker/backup/restore/device signoff remains Sprint 12 and was intentionally not performed. Existing
  acceptance limitations from prior sprints are not silently closed by this cleanup.

Stop after Sprint 11. No Sprint 12 implementation or rollout was executed.
