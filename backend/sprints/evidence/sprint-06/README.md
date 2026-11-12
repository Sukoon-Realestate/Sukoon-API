# Sprint 06 — properties, appointments and virtual tours

Sprint 06 was reconciled with `main` at `5ca495f8` for publication on 2026-11-12. The original shared working directory and its unrelated local work were preserved.

## Published scope

The 17 property and 42 custom-decorated tour endpoint definitions now use explicit method classes: 85 converted aliases in the 127-pattern scoped inventory. Both HTML viewer aliases use a Django View. Listing/image/availability/appointment/capture/coaching/viewer mutations delegate to named domain commands; tour receipt execution passes its locked current actor. Prepared selectors supply owner/review/capture data. Public tour eligibility continues to use the canonical publication, closure and moderation policy, including already-issued public access; private previews remain separately authorized.

Publication retains the newer `main` implementations for typed finance commands, session fences, chat validation/rate limits, public reviews, saved-search storage, support pages and presence batching. Image mutation locks/authority moved into the image command service. Capture collection summaries, GET processing-job history, per-session 20-job/two-revision limits, deterministic ordering and prepared review reasons were reconciled with the new classes, rather than overwritten by older local versions.

The refreshed [route baseline](routes-before.json) records current `main`, and [route coverage](route-coverage.json) accounts for all 127 scoped patterns plus both HTML aliases. The global inventory still has 795 API patterns, with unchanged route/name/method/alias identities; 85 former function routes now resolve to classes. The maintained inventory and Sprint 04 evidence mapper were updated accordingly. Native Django admin hooks remain separate from these custom API conversions.

[Transport fixtures](transport-before.json) contain **1,100** synthetic negative/metadata characterizations from pre-conversion `main`, including the processing-job GET added after the original Sprint 06 work. They cover aliases, supported methods, OPTIONS/HEAD, anonymous/account requests and English/Arabic rendering. Positive flows and races are covered by the domain suites. Allow header ordering is compared as a set, preserving the established contract.

## Publication validation

| Gate | Result |
|---|---|
| Complete PostgreSQL property/tour suite on the integrated tree | **745 passed**, no skips or expected failures |
| Final adapter/contract/race/retained identity/chat/support/security gates, MVP mode | **652 passed** |
| Same final gates, restoration mode | **652 passed** |
| Main baseline characterization generation | One test passed; **1,100** characterizations |
| Scoped route reconciliation | **127** patterns, **85** converted aliases, zero remaining scoped function callbacks; two HTML aliases |
| Global route/method/alias parity | **795** patterns; parity preserved |
| Django checks, migration consistency, scoped lint, Python parsing and whitespace | Passed; no schema migration added |

Counts overlap and must not be summed. The complete property/tour run preceded the final small capture-read adapter cleanup; the final gates rechecked the changed adapters, all frozen transport cases, capture read budgets, publication policy, selection races and retained identity/chat/support behavior after that cleanup. The original Sprint 06 full-backend runs were performed on the older local tree and are not represented as full-backend publication-tree results.

Python 3.11.15, Django 4.2.11 and PostgreSQL 18.6 were used. PostgreSQL databases were newly cloned from a task-owned migrated disposable template in a Unix-socket-only cluster. Simultaneous processes used distinct test database names. Tests disabled `.env` loading and used scratch storage. Already-pinned OpenCV and locked local media validators were enabled for worker coverage. No existing database, production service, deployment, dependency lock or production migration was targeted.

Raw test XML/logs, environment/configuration diagnostics, database fingerprints and local preservation records remain local. This directory contains source-derived route fixtures, synthetic transport contracts and this sanitized summary. Original local source/evidence files were not deleted or reset during publication.

## Limits and reproduction

Existing complete legacy histories and authoring/output documents remain data-dependent compatibility paths. Sprint 06 conversion does not certify hard byte/candidate bounds across every family. The Sprint 04 ledger retains **27 partial-probe patterns and 768 unmeasured**, with API-wide acceptance false; publication does not erase those gaps. Live-provider, physical-device, controlled production-volume load and actual deployment/rollback signoff remain deferred Sprint 12 criteria, not passes inferred from local tests.

Run `make test-sprint06-properties-tours CYCLE_SETTINGS=<disposable_settings> BASELINE_OUT=<scratch_directory>` with `DOTENV_DISABLED=1`. Use isolated media/storage, a new test database and a private-socket PostgreSQL cluster for concurrency semantics. To reproduce worker coverage, supply the pinned CPU-worker dependencies and locked validator root. Regenerate the route ledger with `python tools/qa/sprint06_inventory.py`. No later sprint implementation is included.

## Local-work reconciliation follow-up

A final comparison of the preserved local files identified one useful remaining policy difference: building/complex eligibility is now selected from current database state, including the current manager, archival status and authority review. A cached container cannot preserve public tour eligibility after those fields change. Canonical unit eligibility and the existing account-publication helper remain compatible. The local finance helpers were older alternatives to the already-published canonical typed validators; they were archived rather than reintroduced.

The stale-container regressions first reproduced 12 failures on prior main. After selecting the local policy implementation, the complete tour suite passed 158 PostgreSQL cases; additional closure/withdrawal coverage is recorded in the worklog. All local tracked/untracked changes were copied and hash-verified into a private backup outside the repository before cleanup. Raw diagnostics and superseded local artifacts remain in that backup. No schema migration, production or existing-database operation is part of reconciliation.
