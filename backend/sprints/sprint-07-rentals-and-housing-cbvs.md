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
