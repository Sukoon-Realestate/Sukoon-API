# Sprint 10 — Admin/shared boundaries and operational clarity

**Scope:** admin API, shared common code, app admin adapters, runtime/background/celery configuration, operational scripts.
**Evidence:** A6 findings and shared policies referenced by other domains.

## Work

- Route legacy/native/admin moderation writes through the same authorized domain command policy; record deliberate
  native-admin exceptions where a different supported workflow is justified, not accidental model-save bypasses.
- Keep existing thin admin CBVs; fix selectors/projections and typed command boundaries. Consolidate complete historical
  transaction/audit reads, current KYC predicates, grouped analytics and bounded campaign/content queries.
- Make shared auth, response/error contracts, idempotency and private-storage ownership/reference interfaces explicit.
  Use correlation-aware diagnostics without secrets/PII; narrow recovery exceptions only where state remains honest.
- Account for plain health/release/page/callback HTTP adapters under the CBV target using the appropriate Django/DRF class.
  Preserve health/stream/callback status, headers and raw content. Do not rewrite framework-owned admin internals.
- Align operational instructions with real Pipenv/settings paths; document worker/scheduler/storage dependency gates,
  source-version readiness, backups and supported recovery commands from actual configuration.

## Acceptance

- Current disabled staff profiles, role scope, independent reviewers and sensitive factors are enforced in every public
  admin alias and domain service, including replay. Intended support-role scope is preserved, not arbitrarily narrowed.
- All admin/shared project HTTP callbacks meet the explicit-class contract; views do not duplicate domain invariants.
- KYC/status/search/campaign/transaction/audit/content cases and query budgets pass beyond former source caps.
- Shared services have no view import dependencies; documented contracts make the correct use case easy to follow.
- Deployment/runtime/storage/backup checks have controlled acceptance evidence in Sprint 12. A synthetic `check --deploy`
  result is not used as proof that deployed TLS, workers, Redis, storage and recovery are configured correctly.


## Results — 2026-11-14

Implemented Sprint 10 source work and local validation; **acceptance remains partial** at the limits below.
Full implementation, reproduction, failed diagnostic attempts and final evidence are recorded in
[evidence/sprint-10/README.md](evidence/sprint-10/README.md) and its `validation.json`/JUnit artifacts.

- Preserved canonical property moderation across legacy/API/native aliases, including current authority, independence,
  explicit revision/key replay and original JWT session claims. Typed legacy/content/campaign boundaries are explicit.
- Report commands now own fresh staff/factor/session and independent-party checks; broad support/staff non-suspension
  scope is preserved. Native admin rejects disabled staff and unsafe sensitive actions. Supported native workflow
  differences are documented in [SHARED_CONTRACTS.md](SHARED_CONTRACTS.md), rather than accidental approval model saves.
- Converted every remaining project-owned plain callback, including custom app admin routes, to explicit Django classes;
  retained raw health/association/callback/HTML/file behavior and Django-owned admin internals. The resolver reconciles
  795 unchanged API contracts, 92 scoped admin/shared/native patterns and zero project function callbacks.
- Prepared campaign membership/consent/device batches and SQL audience constraints precede limits; roles are grouped;
  system health pages its audit sample in SQL. Complete historical reads, current KYC, analytics and catalog query budgets
  were revalidated beyond old source caps. Shared services have no project view imports; audit failures remain honest.
- Aligned real paths, worker/scheduler/source-version/storage gates, backup and supported recovery instructions in
  [OPERATIONS.md](OPERATIONS.md). No deployment or recovery readiness is inferred from synthetic tests.

Validation: complete PostgreSQL gate **1,104 passed / 7 skipped**; final SQLite admin/storage **346 passed / 2 skipped**;
last moderation/boundary compatibility gate **52 passed**. Both integrated PostgreSQL release modes passed **6,113**
with **21 skipped / 12 expected failures** each and no unexpected failures/errors. Integrated runs predate final small
native/boundary corrections; final affected gates cover them, without claiming a whole-backend final-tree rerun.
Django checks, migration consistency, 2,184 Python parses, 2,041 module imports, scoped lint and whitespace checks passed.

Unmet acceptance: exhaustive positive alias/method/role/factor/object/replay coverage; universal hard work/payload/lock-time
bounds for compatible complete legacy modes; two unavailable OpenCV checks and five independent drill checks; and
controlled deployed runtime/storage/backup/recovery acceptance belonging to Sprint 12. See the evidence README for
precise limits. All four existing database files have unchanged hashes; the new private-socket PostgreSQL cluster was
stopped. Existing databases and production were not modified. Stopped after Sprint 10.
