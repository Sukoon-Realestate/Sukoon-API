# Sprint 04 — Bound work across every API family

**Outcome:** measured query, memory, payload, provider-I/O and lock budgets replace assumptions based on visible page size.
**Evidence:** A2-07/A2-08/A2-09/A2-12/A2-13; A3-04…A3-09; A4-05…A4-08/A4-11;
A5-04…A5-08; A6-03…A6-09; A1-09.

## Work packages

| Family | Required change |
|---|---|
| Admin property/KYC/reports/content | Prepare counts/role/evidence/related catalog data in selectors; eliminate per-item SQL and unnecessary prefetch payloads |
| Dashboard, analytics, campaigns | Group date aggregates; batch campaign summaries/eligible-device facts; avoid repeated complete dashboard computations |
| Visits and appointment slots | Batch decisions/invitations/rosters/current authority; fetch closure intervals once; bound busy-visit date windows |
| Saved searches and public reviews | Bounded snapshot/cursor/read-item design; page before projection; stable multi-source review ordering without loading all history |
| Capture sessions/jobs | Lightweight bounded summaries, prepared latest relations and explicit detail/history resources |
| Company discovery/tenancies/contracts | Apply validated scope filters before evaluation; batch authority/scope/location/availability; avoid full-market suitability work for page one |
| Public reputation | Set-based invoice exclusion/payment facts and policy-aware aggregates; no four extra queries per invoice |
| Maintenance and finance | Bounded collections and compact list projections; batch invoice/receipt/fulfillment/plan/refund/payout history; no duplicated lease-wide eligibility work under locks |
| Advertising | Bound candidate scans; annotate fulfillment; verified persisted media readiness, not remote storage checks for every candidate |
| Chat and support | One request-scoped authorized projection context; batch reader/reply/poll data; bounded forward scans, receipt materialization, edits and evidence/thread history |
| Periodic maintenance | Process only unpurged private discoveries in resumable keyset batches; stop reprocessing all expired history |
| Computation and delivery | Snapshot versioned solver inputs, compute outside long locks, revalidate at commit; durable post-commit email/outbox work |

## Method

For **each route family in API_INVENTORY**, choose realistic small/large and rejection-heavy fixtures, baseline its query
count, rows inspected/returned, response size, heap/CPU, provider calls and transaction/lock duration. Include role/workspace
and nested/history variants, not only the happy-path first page. Record budgets before optimization, then compare identical
fixtures. Prefer select_related, filtered Prefetch, Exists/aggregates and explicit page maps where they fit the actual query.

A constant query count alone does not prove speed: a single full-table query, enormous JSON snapshot, combinatorial search
or remote call can still be a bottleneck. Use PostgreSQL EXPLAIN/representative plans and contention tests for relevant
indexes/locks. Do not add indexes or caches from text matches alone. Cache only where invalidation and current authority
are demonstrably correct; never cache a private projection across users/workspaces.

## Acceptance

- All 795 baseline route patterns/aliases are mapped to a measured family or an explicit justified exception, updated as
  routes change. No claim that the existing 13-screen sample covers all APIs.
- At 1/10/100 or agreed 5/40/large histories, read query count grows by necessary relation types, not one query per row/
  field; returned payload and inspected candidates have explicit bounds. Record any irreducible data-dependent algorithm.
- Admin property serialization no longer shows the measured 7→42 query growth. Similar gates cover the identified families.
- Unauthorized rows are excluded **before** counts/disclosure. Fresh revocation, group/company membership and provider
  proof checks remain correct; an optimization cannot remove safety work.
- Long computation/provider calls do not hold shared financial/property/account/chat locks unnecessarily. A short final
  transaction revalidates versions and invariants; race tests prove correctness on disposable PostgreSQL.
- Before/after evidence includes runtime versions/settings, fixture sizes, protocol and failures. Do not extrapolate
  APIClient latency into production SLOs; final controlled staging/load acceptance is Sprint 12.

## Implementation record — 2026-11-11

**Partial implementation; acceptance remains open.** Prepared admin/content/campaign reads, grouped reporting,
slot closure windows, reputation exclusion facts, chat history/event context, evidence availability and resumable
indexed discovery cleanup now have focused performance/recovery evidence. Route identities remain unchanged.

The [implementation report](evidence/sprint-04/README.md) records comparable measurements, validation,
query plans, data-preservation checks and every outstanding work package. The source coverage tool links 20 patterns to partial service probes and leaves 775 unmeasured; it grants no artificial exceptions.
The all-family budget, bounded-history and shared-lock/solver criteria are not complete. Do not mark Sprint 04 accepted
or infer readiness for later sprints from the passing local probes. Existing database/production operations were not
part of implementation; the report records the concurrently changed development-database hash separately.
