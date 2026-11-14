# Sprint 07 — Rentals, housing and planning architecture

**Scope:** non-commerce `core_apps/features/` routes/services, including personal/company/student/shared housing,
planning, transitions, experience, conditions, maintenance, signing and portfolio workflows.
**Evidence:** A3 findings; relevant A2/A4 boundary stories. This large package should be split by the batches below to fit
actual team capacity; there is no promise all 444 feature route patterns fit one calendar iteration.

## Batches

1. Personal rental interest, terms, applications, agreements, handovers, maintenance and lifecycle/closure commands.
2. Company tenancy/contract/staff/responsibility/negotiation/workspace and role-aware read projections.
3. Planning/group/roommate/condition/portfolio/student/shared-housing workflows and private evidence.
4. Advanced scenarios/tenders/transition matching, experience and reputation read models/jobs.

For each batch, extract named command and prepared read services, then convert to explicit CBVs. Break mixed projections
such as the 535-line company tenancy payload into understandable domain sections receiving shared preloaded facts, not
one unrelated micro-file per expression. Keep model/migration identities and supported service imports stable.

## Critical migration rule

`company_api` calls `role_routes.authorize(function, request)` and the role table keys on module/function names. Planning
and lifecycle wrappers also implement capability checks, type validation and response/privacy policies. Define explicit
resource/action policy metadata and per-method permission dispatch **before** changing those callable identities. Preserve
authorization-before-replay, current membership/mandates, root lock order and post-commit dispatch.

## Acceptance

- Each batch has route/method/role/workspace/payload/retry parity fixtures, including different GET/POST/PATCH authority.
  Changing a callable name to `post` does not accidentally broaden or deny a company's role policy.
- All project-owned feature handlers in the batch resolve as explicit classes; views do not own domain state machines.
- Commands reject bad/stale input, maintain receipts and durable evidence, and recheck current authority after locks.
- Company discovery/visibility, maintenance/reputation projections, private-data purge and computation lock-time budgets
  meet the performance stories without weakening privacy or replacing missing results with fake success.
- Source-reference/retention ownership includes portfolio consumers and any newly added app/module; no feature family is
  left out merely because its filename does not contain a commerce/planning keyword.

## Implementation results — 2026-11-14

**Status: partially implemented; Sprint 07 acceptance is not yet complete.** Work stopped at Sprint 07.
No production service, deployment, existing database or migration was targeted.

- All **383 selected non-commerce housing route patterns** now resolve to explicit classes, including **336 converted
  aliases / 284 former function handlers**. The other 47 patterns already used classes. Global transport metadata remains
  unchanged across all 795 patterns. The scope includes private evidence/documents and the nested experience package;
  the [61 excluded feature routes](evidence/sprint-07/excluded-routes.json) retain their commerce/provider/catalog owner.
- Explicit per-method `ActionPolicy` metadata preserves stable company resource/action identities, planning capability
  checks, validation/error precedence, privacy headers, parsers and throttles. The original company authorization import
  remains supported. Frozen source-derived fixtures cover **5,800** transport cases in each release mode (**11,600** checks) and **744** company method/role gates.
- Named handover, personal maintenance, lifecycle, company tenancy/administration/portfolio, student and tender/scenario
  command steps were extracted. Existing receipt, authority, root-lock and post-commit boundaries remain in place.
  Company tenancy projections now share prepared facts across agreement, changes, maintenance, occupancy, finance and
  authority sections. Personal maintenance invoice links are loaded in one batch; validated company/lease scopes are
  applied before visibility authority evaluation.
- Source/retention ownership explicitly includes portfolio storage and every feature source module, including experience
  and the new services. No app/model identity or schema migration changed.

See [recorded validation and limits](evidence/sprint-07/README.md),
[route coverage and remaining adapter signals](evidence/sprint-07/route-coverage.json), and
[source/retention ownership](evidence/sprint-07/SOURCE_RETENTION.md).

### Unmet acceptance criteria

- **Complete domain extraction:** explicit classes are not sufficient for acceptance. Planning/group/roommate/condition,
  legacy interests/invitations/agreements/closure, experience and some existing reputation/shared/advanced adapters still
  contain workflow logic or depend on helpers housed in view modules. The source ledger retains **83 adapter methods with
  state-write/transaction signals** as review pointers; this is not an exhaustive state-machine count.
- **Full per-route positive parity matrix:** frozen transport/role gates plus the existing domain suites do not constitute
  every route × method × role × workspace × payload × retry combination. Current command-time resource authorization is
  still required independently of the HTTP role gate.
- **Performance acceptance:** full-market company discovery and unscoped visibility still need bounded candidate/query/
  heap proofs. Compatible complete nested histories remain data-dependent; whole-family payload bounds and production-
  volume computation/lock-time budgets are not established by the focused read/solver tests.
- **Retention acceptance:** existing portfolio reference/purge behavior and new-module ownership are recorded and tested,
  but this work does not certify every feature family's private-data retention/erasure policy or live remote deletion.

No later sprint implementation or rollout is included.
