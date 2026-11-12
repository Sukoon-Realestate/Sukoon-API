# Public reviews and saved-search follow-up — 2026-11-12

Status: implemented and locally validated; Sprint 04 as a whole remains partially accepted. The ledger has 26 partial-probe patterns and 769 unmeasured patterns.

## Public review reads

The property review resource now counts and pages its combined current/imported/historical sources in SQL before rendering cards. Ordinary generated viewing rows apply approved/public/released/not-revoked and exact current decision/owner/property/revision checks in SQL. Imported legacy reviews remain excluded from verified averages and are not duplicated. Historical cross-context combinations still pass the existing source validator; that exceptional path is explicitly data-dependent and is not credited as a bounded source family.

At 1/10/100 current reviews plus the same number of historical reviews, the unchanged-main baseline made 10/64/604 queries; the new path makes 5/5/5. The same probes check deterministic timestamp/UUID ordering, counts and private-cache headers. Tests also compare SQL eligibility with existing visibility for revoked, unreleased, private, pending and stale source facts, plus import exclusion, historical fallback and exact half-up averages. No per-reviewer identities are added to the public cards.

## Saved-search snapshots

Catalog scans now run outside the shared account transaction. Before publishing a receipt, the service locks the account again, checks the current session/account and rechecks the exact search definition and watermark revision. Concurrent revocation, epoch changes, definition changes and acknowledgments succeed during the scan and prevent stale receipt publication.

An optional row-based format streams complete membership/version/change facts in batches of at most 500. Its ready receipt stores empty versions/changes JSON; SQL membership and change selectors precede counts and paging. A page reads version facts only for its displayed listings. Failed/incomplete builds are never accepted for reading or acknowledgment. Receipt-local batch locks prevent late inserts after retirement; shared account locks do not span the catalog scan or these batches.

For 1/100/2,000-property probes, traced peak Python allocations were approximately 0.10/0.20/1.33 MB and maximum observed transaction spans 2.7/6.7/75.3 ms. Instrumentation includes captured SQL strings and is not a production memory or latency guarantee. Full snapshot creation necessarily scans/writes matching membership; exact counts and one-time conversion from an existing legacy JSON baseline remain data-dependent. This is not an invented constant-work guarantee.

### Compatibility and rollout

`SAVED_SEARCH_ITEMIZED_READS` defaults to false. Existing public request/response shapes, read IDs, explicit acknowledgment, delta counts, successful-read watermark, current visibility, expiration and legacy receipts remain supported. Existing contract tests run in both storage modes. The runtime configuration identity exposes the flag so mixed settings can be detected.

Properties migrations 0046/0047 add nullable metadata, the normalized item table and an expiry index. Old historical model classes can still insert visits/receipts after the forward schema. Deploy the schema and new reader code to every API/worker before enabling creation of the new format; no activation or migration was performed on an existing database.

For rollback to older application code: disable itemized creation on every process, drain in-flight requests and the 15-minute live receipt window, then repeatedly run `materialize_saved_search_baselines --apply --retire-expired-receipts` in the established release environment. The command is read-only without --apply and refuses apply while creation is enabled. It restores active legacy baseline JSON outside shared locks with a fresh revision check, clears closed-account baselines without copying them, and retires expired child rows in bounded batches while retaining the expired receipt identity (410 remains 410). Both baselines_remaining and itemized_receipts_remaining must be zero before older readers/workers are restored. Source-changed results require review/retry; they are not overwritten. This command was tested only on disposable data.

## Cleanup and plans

Cleanup deletes at most 500 item rows and 100 eligible receipts per invocation, preserves active acknowledged watermarks and resumes from durable remaining rows. Membership cleanup follows the unique read/property key. With 10,000 fresh and ten expired receipts, PostgreSQL initially filtered 10,000 fresh rows; an `(expires_at, pkid)` index selected the ten expired entries directly (0.313→0.025 ms in one ordered local plan). The migration builds/drops this index concurrently on PostgreSQL and supports SQLite tests. No speculative index or existing-database change was made. Production cadence/volume acceptance remains external.

## Validation

- Complete MVP and restoration runs: each **5,475 passed, 490 skipped, 10 expected failures**, zero failures/errors (5,975 cases).
- PostgreSQL public-review/source/saved-search/advertising gates: 106 passed before the format extension.
- Settled row-format, both-mode contracts, cleanup, rollback, runtime and authority gates: 80 PostgreSQL cases passed; a later metadata/edge-case recheck passed 71. Counts overlap.
- SQLite focused gates: 60 passed, eight explicit PostgreSQL-only skips.
- Paired legacy/row-format measurement probes: three passed on PostgreSQL, checking identical selected rows.
- Fresh final-schema local worker/scheduler recovery and two-ASGI/shared-Redis checks passed again. A new owned backup/restore matched 367 table counts.
- Django checks, model/migration consistency, scoped lint and whitespace pass. Raw initial fixture/configuration failures, expected failing baseline budgets, plans and logs remain local. No failures remain in the final named gates.

No production, existing databases, real providers or physical devices were used. This work does not complete the remaining admin/campaign/visit/company/financial/advertising/chat/support budgets or external Sprint 12 signoff.
