# Backend improvement sprints

**Reviewed:** 2026-11-08 · **Baseline:** `main` at `785dfc1d` · **Audience:** developers, technical lead and product owner.

The backend does **not yet meet** the requested all-CBV, consistently modular, bounded-performance and validated-input
target. This folder contains the evidence and an ordered implementation plan. Application code was not changed by this
audit. Findings are backlog, not completed fixes, and the review does not certify that every API is secure or bug-free.

The scan covered all **2,018 tracked Python files** for syntax, including tests and migrations. Detailed structural
analysis covered **1,196 application/configuration files, 146,908 lines and 11 apps**, plus seven backend scripts.
Selected security, state, storage, money and query paths were manually traced. This is whole-backend static coverage,
not an assertion that every branch received exhaustive manual review. See [baseline and limits](BASELINE.md).

## Fix these before broad mechanical refactoring

| Priority | Evidence | Required result |
|---|---|---|
| High | Avatar accepts arbitrary Cloudinary references; closure queues those references for provider deletion | Only owned, server-recorded assets can be attached or erased; [identity findings](findings/area-1.md) |
| High | Inherited Djoser account deletion remains routed; isolated request returned 200 and physically removed a synthetic account | All deletion aliases honor reviewed account closure and retention obligations |
| High | Tour-storage cleanup omits live residential portfolio blobs | Active portfolio media survives cleanup; [A3-01](findings/area-3.md#a3-01) |
| High | Visit creation and tour serving diverge from canonical listing/closure eligibility | Unavailable inventory cannot start visits or leak tour bytes; [property findings](findings/area-2.md) |
| High | Edited messages emit a different event name from the moderation enqueue whitelist | Every eligible committed revision receives moderation; [communication findings](findings/area-5.md) |
| High | Partial refunds can repost an existing commission identity with a changed amount | Additive, balanced accounting and safe provider reconciliation; [commerce findings](findings/area-4.md) |

The small benchmark is healthy: all 13 sampled screens returned 200 and had stable query counts at 5 versus 40 records.
It is **not API-wide performance evidence**. A separate admin-property serialization probe grew from **7 to 42 queries**
for 5 versus 40 properties. Other source-proven query-growth paths are listed in the findings.

## Sprint sequence

These are ordered work packages, not invented calendar estimates. Size stories after Sprint 00 establishes reliable tests.
Split an oversized domain package into consecutive iterations using the route-family checklists. Critical safety fixes
can begin immediately with their own focused regression tests; they need not wait for the entire baseline backlog.

| Sprint | Outcome | Depends on |
|---|---|---|
| [00 — Baseline and contracts](sprint-00-baseline-and-contracts.md) | Collectable tests, endpoint/role/upload inventory and agreed readable architecture | None |
| [01 — Security and data preservation](sprint-01-security-and-data-preservation.md) | Close alternate-route, identity, publication, moderation and retention gaps | Focused regression setup from 00 |
| [02 — Typed inputs and uploads](sprint-02-inputs-and-uploads.md) | Complete command schemas and explicit file-content contracts | 00; preserve 01 policies |
| [03 — Correctness and recovery](sprint-03-correctness-and-recovery.md) | Financial, retry, notification, matching and historical-read correctness | 00–02 as relevant |
| [04 — API performance](sprint-04-api-performance.md) | Bounded queries, payloads, scans, lock time and background work | Route baselines; preserve 01–03 rules |
| [05 — Identity CBVs/services](sprint-05-identity-cbvs.md) | One explicit identity transport/service architecture, including inherited aliases | 01–03 identity fixes |
| [06 — Properties and tours CBVs](sprint-06-properties-and-tours-cbvs.md) | Cohesive listing/visit/media/tour command and read services | 01–04 relevant stories |
| [07 — Rentals and housing CBVs](sprint-07-rentals-and-housing-cbvs.md) | Explicit per-method capability policies and readable housing workflows | 01–04; role-policy parity fixtures |
| [08 — Commerce CBVs/services](sprint-08-commerce-cbvs.md) | Money services independent of HTTP modules, thin transport adapters | Financial correctness in 03 |
| [09 — Communication CBVs/services](sprint-09-communication-cbvs.md) | Shared chat commands across transports, bounded read models | 01–04 communication fixes |
| [10 — Admin/shared architecture](sprint-10-admin-and-shared.md) | One moderation path, consistent admin selectors and operational boundaries | 01–04; domain service interfaces |
| [11 — Cleanup and standards](sprint-11-cleanup-and-standards.md) | Remove verified obsolete/fixture code and redundant plumbing safely | Caller/contract inventories; can run in small earlier PRs |
| [12 — Acceptance and rollout](sprint-12-acceptance-and-rollout.md) | Evidence that all goals hold for the agreed production scope | All applicable stories complete |

Sprints 05–10 can proceed independently after shared contracts and safety stories are stable. Do not mix large mechanical
view conversion, behavior fixes, dependency upgrades and schema changes into one unreviewable PR.

## How to use the folder

1. Read [BASELINE.md](BASELINE.md), [ARCHITECTURE.md](ARCHITECTURE.md) and [UPLOADS.md](UPLOADS.md).
2. Use [FINDINGS.md](FINDINGS.md) to connect evidence IDs to owning sprints. Detailed area reports contain triggers,
   source locations, proposed changes and acceptance cases.
3. Track each route in [API_INVENTORY.md](API_INVENTORY.md). Its declared permission is an inventory value, not proof of
   object authorization. A generated DRF `WrappedAPIView` around a function does not satisfy the authored-CBV target.
4. Use [SOURCE_INVENTORY.md](SOURCE_INVENTORY.md) for the application/configuration scope and area ownership. Every
   changed workflow needs its own caller, permission, input, query, retry and side-effect checks.
5. Mark a story complete only with the evidence required by its sprint. Keep untested PostgreSQL, provider, storage,
   deployment and device behavior explicitly open. Do not claim completion from a file move or a passing 13-screen sample.

## Final definition of done

- Every project-owned routed HTTP/API view is an explicit CBV, including aliases; raw callbacks/viewer pages retain their
  required byte/signature/HTML semantics through suitable Django `View` adapters. Channels consumers remain consumers.
- Views adapt requests/responses; typed serializers validate commands; domain services own transactions and state changes;
  selectors prepare bounded read data; projections do not hide repeated database/provider calls.
- Each API family has permission/role, invalid-input, edge-case, query/payload and retry evidence. PostgreSQL checks establish
  actual locking behavior where required; APIClient/SQLite results are labeled correctly.
- File formats and resource limits are explicit, content is verified, ownership is server-established, and private bytes,
  deletion and retention share the same authorization/reference rules.
- No fabricated customer-facing statistics/artwork or historical fixture repair remains in serving code. Obsolete code is
  removed only after checking routes, imports, tasks, signals, admin registries, migrations, tests and supported clients.
- Existing public contracts remain stable except separately approved security/bug fixes with client migration notes.

This folder is the requested planning deliverable. Executing its application changes is a separate task.
