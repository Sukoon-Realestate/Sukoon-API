# Full-application QA — 15 November 2026

**Release blockers were found. This pass does not certify the app as production-ready or establish that every button/cycle is covered.** The work includes the Flutter mobile app, hosted API, public frontend and Next.js admin portal. Product fixes were left for a later sprint in the original pass; local remediation began on 16 November.

## Sprint 1 progress — 16 November 2026

Local fixes cover **MOB-001**, **PRIV-001** and **ADM-001**. **WEB-001** now truthfully identifies unavailable download links. Both JavaScript trees use Next.js 16.4.6; repeat audits report **zero critical/high findings**, with seven moderate development-toolchain findings remaining per tree.

See [Sprint 1 fixes, reproductions, verification and unresolved blockers](SPRINT-1.md). **Sprint 1 remains incomplete:** MOB-002 was not reproduced by repeated widget journeys, HOST-001 still returns 504, Python dependency remediation and real release/store acceptance remain open. Nothing was deployed. The tables below preserve the original 15 November baseline.

Start with [findings and reproduction steps](FINDINGS.md), then [coverage, limitations and four proposed fix sprints](COVERAGE.md).

| Check | Result |
|---|---|
| Backend, 6,202 unique cases reconciled across SQLite/HTTP/PostgreSQL runs | **6,168 passed; 22 skipped; 12 expected failures**; no remaining unexpected failure |
| Supplemental PostgreSQL transaction/race/HTTP cases | 477 passed, 5 skipped, 2 expected failures |
| Full mobile app attempt | **13,124 passed; 32 skipped; 497 failed/error cases**; stalled and interrupted, no successful terminal event |
| Independent mobile rerun, three representative files | 166 passed, 7 failed |
| Mobile shared core | 345 passed |
| Mobile static analysis | No compile errors; 1 async warning and style notices |
| Next.js standalone admin regressions | 56 passed |
| Merged website/admin build-configuration tests | 3 passed |
| Standalone and merged production builds | Both passed |
| Frontend lint | **91 errors, 7 warnings** |
| Hosted read-only probe repeat | 54/56 met status expectations; both association endpoints returned 504 |
| Authenticated disposable admin HTTP checks | 31 passed |
| JavaScript dependency audits | Critical advisory findings in both lockfiles; standalone tree also has 3 high-severity affected packages |
| Python lockfile audit | 124 advisory entries across 13 packages, including development tools |

The 497 mobile cases are **not 497 proven unique product bugs**. They include outdated finders/fixtures, contract expectations, runtime errors and shutdown effects. The grouped reports retain exact assertions for classification. Dependency advisories identify affected versions; no successful exploitation was demonstrated.

The main observed issues include the broken Accepted Visits filter, an intermittent new-property Back-flow dead end, stale-language Home categories, contradictory phone-privacy statements, fabricated admin behavior scores, an inert CSV button, missing store links and unavailable app-association endpoints. Additional source-confirmed reliability issues and security-hardening/dependency findings are distinguished in the findings report.

## Reports

- [Findings](FINDINGS.md): priority, actual/expected behavior, reproduction, source locations and fix direction.
- [Backend results](BACKEND-RESULTS.md): reconciled results and every remaining skip/expected-failure reason.
- [Mobile failure index](MOBILE-FAILURES.md): 93 per-file reports with exact failed test names and assertions.
- [Security advisory ledger](SECURITY-ADVISORIES.md): advisory links, affected versions and Python fixed versions.
- [Coverage and sprint backlog](COVERAGE.md): native/browser/API evidence, remaining cycles and environment limits.
- [Source inventory](evidence/inventory/control_inventory_summary.json): 79 feature areas, 884 action families and 4,583 mobile/web control candidates. Discovery is not execution coverage.
- [Source provenance](evidence/provenance.json): tested checkouts; deployed revisions and the installed app's compiled revision were not proven equal to them.

## Run the report again

From the API repository root, with Flutter and the existing mobile dependencies installed:

```sh
# Repeat one failing mobile file; produces a fresh timestamped log and result.
python3 docs/qa/full-application-2026-11-15/rerun.py \
  --file rental_listing_categories_test.dart --app-root ../sokoun

# Repeat exactly one case using its MOB-... ID from a per-file report.
python3 docs/qa/full-application-2026-11-15/rerun.py --case MOB-REPLACE_WITH_CASE_ID

# Repeat bounded read-only hosted checks. No login or business writes.
python3 docs/qa/full-application-2026-11-15/rerun.py --hosted

# Rebuild Markdown ledgers from retained JSON/JSONL/JUnit evidence.
python3 docs/qa/full-application-2026-11-15/summarize.py
```

The replay tool accepts `--timeout`; it stops its own process group on a wall-clock timeout and reports exit code 124. Test failures normally return a nonzero exit code. Its reproduction was verified against `company_role_work_status_test.dart` and correctly returned failure without timing out.

Frontend checks, after the lockfile-defined install:

```sh
cd frontend
node --test tests/*.test.cjs
npm run build
npm run lint
npm audit --json
cd landing
node --test scripts/vercel-build.test.mjs
npm run build
npm audit --json
```

Full backend reproduction uses the existing Make target with a lockfile-compatible Python:

```sh
cd backend
make test-baseline-mvp CYCLE_PYTHON=/path/to/backend/python BASELINE_OUT=/tmp/sukoon-release-qa
```

For the 484 captured PostgreSQL/HTTP cases, supply `TEST_POSTGRES_DB`, `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD`, `TEST_POSTGRES_HOST` and `TEST_POSTGRES_PORT` for a disposable loopback cluster, then run from the repository root:

```sh
python3 docs/qa/full-application-2026-11-15/rerun_postgres.py --python /path/to/backend/python
```

The helper requires an explicitly named QA/test/scratch database and writes private media and JUnit results to a fresh temporary directory. It does not initialize a cluster or use production credentials. The temporary cluster used for this pass was stopped after verification.

`probe_local_admin.py` can repeat the admin reads against a separately prepared disposable backend. It requires a private fixture with `qa_only: true`, email and password. Credentials and the temporary database are intentionally outside the report.

## Evidence notes

Raw logs, original and supplemental JUnit, dependency audit JSON, machine-readable mobile failures and source-discovery ledgers are retained under `evidence/`. The large mobile event stream is losslessly compressed as `mobile-app.jsonl.gz`; the summarizer reads it directly. `BACKEND-FAILURES.md` preserves the original sandbox socket errors as historical evidence; use `BACKEND-RESULTS.md` for their final disposition.

Manual UI checks cover real interactions but do not exhaust the source inventory. Authenticated hosted staff/provider cycles, physical devices, complete accessibility/responsiveness and independent infrastructure/security acceptance remain open. No hosted account credentials or customer chat content are included in these reports.
