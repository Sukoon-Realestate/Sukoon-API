# Support thread performance follow-up — 2026-11-12

Status: locally implemented; **Sprint 04 acceptance remains open**. The source ledger maps 27 of 795 route patterns to partial probes and leaves 768 unmeasured. Route/method/alias parity remains intact. No route receives an invented exception or API-wide acceptance.

## Changes and compatible use

Staff detail now prepares messages and attachments in two queries, caches the authorized ticket back-reference and omits stored attachment binary content from projection reads. Evidence availability still verifies the current attachment UUID, message association, status and digest. Nested serializers retain their existing fields and child types.

Consumer ticket detail and staff ticket detail accept `bounded=true`. Omitting it, or supplying `bounded=false`, retains complete legacy lists with no added page metadata. Creation, reply and recovery receipts retain their legacy shape; GET controls cannot cause a pagination error after a reply has committed.

For example, a consumer can request `?workspace=tenant&bounded=true&messages_page=2&messages_page_size=20&information_requests_page_size=10&history_page_size=5&evidence_versions_page_size=5`. Staff detail additionally pages internal notes and transitions. Each returned parent retains the original child list keys.

| Collection | Default size | Maximum size | Metadata location |
|---|---:|---:|---|
| messages | 20 | 100 | ticket `pages.messages` |
| information_requests | 20 | 100 | ticket `pages.information_requests` |
| internal_notes, transitions (staff only) | 20 | 100 | ticket `pages.<collection>` |
| history, evidence_versions | 5 | 20 | information request `pages.<collection>` |
| attachments | 3 | 20 | message `pages.attachments` |

Every collection uses `<collection>_page` and `<collection>_page_size`. Page numbers are 1–10,000. Invalid explicit bounded controls return 400, after ownership/workspace/staff authorization. Pages beyond the current end return an empty list with the current count. Metadata contains `count`, `page`, `page_size` and `has_next`. Information-request page metadata is present only when structured requests are policy-eligible; other tickets keep an empty request list. Nested page controls apply independently to each selected parent; they never apply one global slice across all parents. Chronological ordering has a primary-key tie-breaker. Counts and pages are current reads, not a frozen history snapshot; clients should retain the ticket revision and refresh after changes.

Only selected information requests receive per-parent window-prefetched events/evidence versions. Counts are grouped by selected parent in two SQL queries; current file proof is fetched once for the selected versions. Consumer responses never acquire internal notes/transitions. Fresh staff-role revocation is checked before parsing or reading page relations.

## Measurement protocol and evidence

Synthetic fixtures contain 1/10/100 information requests. The legacy comparison has one history event, one evidence version, one primary message with an attachment and one evidence message per request. It exercises the actual staff projection on baseline `eca22ee3` and the changed projection. Query counts were **11/29/209 → 10/10/10**. Baseline SQLite and changed PostgreSQL produced the same projection byte counts (2,566/17,975/172,326) for these synthetic fixtures, but this is not a latency comparison or proof of identical arbitrary payloads. Existing legacy contract tests and field/page oracles supply compatibility evidence. The old-code budgets intentionally fail at 10 and 100 requests; those failures are retained locally.

A separate bounded PostgreSQL fixture has six events, evidence versions and attachments per primary message, with every page size set to two. At 1/10/100 requests, measured projection SQL stayed **17/17/17**, payload estimates were **3,932/5,762/5,766 bytes**, and traced Python peaks were about **132/145/144 KiB** in the initial run. There were no measured HTTP provider calls, storage existence calls or newly entered transaction spans. Instrumentation includes query capture overhead; values are projection JSON estimates, not rendered HTTP transport bytes. These observations do not set production SLOs.

Environment: Python 3.11.15, Django 4.2.11, PostgreSQL 18.6; `integration_pg_settings` targets an owned Unix-socket-only scratch cluster. SQLite tests use in-memory test databases and scratch storage. `.env` loading is disabled. Raw logs, XML, process/config diagnostics and database contents remain outside the repository.

## Validation

- Each full backend mode collected 5,994 cases: 5,487 passed, 485 skipped, ten expected failures and 12 local HTTP server setup errors (`socket.bind` was denied by the sandbox). The exact 12 setup-error nodes were rerun with loopback socket access, together with the final 25 support/chat boundary cases: each mode passed 32 and skipped five. De-duplicating by test identity yields **6,000 unique cases per mode: 5,500 passed, 490 skipped, ten expected failures, zero unresolved failures/errors**. This is a full run plus exact reruns/additional cases, not a single uninterrupted clean run.
- Complete support suite after the nested serializer change: **127 PostgreSQL passes**. A later equal-timestamp traversal passed on SQLite and PostgreSQL. The focused SQLite boundary suite passed 20 cases.
- Complete chat suite plus support page boundaries after the UUID correction: **474 PostgreSQL passes, two skips, one expected failure** (477 cases).
- Final original-serializer value oracles and support boundaries: **25 PostgreSQL passes**. This includes every legacy chat field/value, fresh presence expiry, page-specific authors, unavailable-presence fallback, staff revocation, ownership/workspace-before-count checks, current evidence proof/revocation and full legacy reply receipts. Counts overlap.
- Django checks, model/migration consistency, scoped lint, whitespace and the 795-pattern route/method/alias ledger pass. No schema migration was added in this follow-up.

The first support prototype hit Django 4.2's sliced-prefetch relation-cache limitation; named prepared attributes fixed it. The first chat prototype confused numeric user primary keys with presence's UUID foreign key; UUID binding fixed it. Both initial failures and sandbox setup-error logs remain local, with passing final gates above. Raw diagnostics are not published.

Reproduce focused gates with `DOTENV_DISABLED=1`, a disposable `DJANGO_SETTINGS_MODULE` and `python -m pytest core_apps/support/tests core_apps/chat/tests`. The `test-sprint04-performance` Make target includes both new performance test files. PostgreSQL is required for the complete authority/concurrency coverage; local HTTP tests need loopback socket access.

## Legacy direct-message follow-up

Legacy direct history previously inherited poll/star/vote prefetches from the rich message selector and queried renewable presence once per message. It now drops those unused relation loads, defers unused rich JSON columns and fetches current presence in one query for the selected page's author UUIDs. Authorization and pagination happen first. Presence maps live only in the serializer's response context; later requests observe lease expiry. Other projections retain their previous fallback, and presence failures still render offline. No shared private response cache was added.

The same 1/10/100-message fixture has one unused poll/vote/star per message plus 10 KB of unused rich JSON. Baseline query counts were **16/25/115**, versus **14/14/14** after the change. Baseline and changed runs use SQLite and PostgreSQL respectively, so only query shape/growth is compared. The final 100-message run rendered about 36 KB with about 702 KiB traced Python peak; these are local observations, not universal byte or latency limits. A same-row oracle compares every response value with the original nested serializer without the prepared context, avoiding any inference from independent random fixture byte counts. Unauthorized users never trigger the presence read; expired leases change the next response immediately.

## Remaining acceptance criteria

Legacy full-list behavior is an explicit compatibility path and still scales in payload/heap with complete history. Opt-in row limits bound returned collections, but exact counts and SQL window ranking can inspect data proportional to authorized relation sizes. Imported historical text/JSON fields do not have an established universal byte bound. This work therefore does **not** certify a hard candidate or payload-byte bound for arbitrary support data. Receipt materialization, all role/large-history variants and request-wide fanout/lock budgets still need coverage.

The other open Sprint 04 families remain in the [previous report](read-followup-2026-11-12.md). Final controlled load, real provider accounts, physical devices and an actual deployment/rollback exercise remain Sprint 12 work; local tests do not certify them. No existing database or production service was targeted, migrated, restored or deployed to. This follow-up has not been pushed to `main`.
