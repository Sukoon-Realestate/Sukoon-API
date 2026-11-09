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
