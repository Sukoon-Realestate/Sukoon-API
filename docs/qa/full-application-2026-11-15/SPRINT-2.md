# Sprint 2 — admin reliability (started 17 November 2026)

**Local implementation and controlled browser verification complete; live-backend/hosted acceptance remains open.** The user explicitly requested starting Sprint 2 after publication. Sprint 1 remains incomplete: intermittent native Back exception capture/device acceptance, authentic production/Apple identities, store links and live association acceptance remain open. See [Sprint 1](SPRINT-1.md).

## Publication boundary

At this task's start, both main branches were clean and already contained all previously published work. Fetch/fast-forward/push confirmed API `45793c5f0e8f9799c8ccf0c1f32a71bd1f935e19` and mobile `a5935ae7da6585b413502257cfc9b8928f763650` were up to date. No empty commit or redundant merge was created. The Sprint 2 changes below are new local work, started after that synchronization. Concurrent mobile test/translation/image edits appeared afterward and were preserved. No deployment or release upload was performed.

## Reproduction and changes

- **ADM-003:** Before editing, the real audit page run in a controlled TypeScript/React-hook harness failed 503-error visibility, filter stale-row invalidation and malformed-pagination cases. It now distinguishes unavailable results from successful empty results, offers retry, immediately hides old-query rows and suppresses late/unmounted responses. Pagination exposes subsequent audit pages and validates response metadata/row identity. This is a product defect, not an obsolete assertion.
- **ADM-002:** Before editing, the page harness reproduced the absent CSV handler. Export now downloads exactly the loaded, displayed page under the current filters/search. The button and adjacent Arabic explanation explicitly say **current page only**, not complete history. Loading, failure and empty states disable export. UTF-8 BOM, Arabic text, delimiters, quotes/newlines, formula/control prefixes, download failures and object-URL cleanup are covered. No new server export or complete-history export is claimed.
- **COPY-001:** Before editing, a rendering regression failed the read-only label requirement. The permissions matrix now says it is read-only and has no interactive cell styling. Existing authorized staff-grant paths remain unchanged; no permission mutation was added.
- **Demo compatibility:** A new regression reproduced missing pagination metadata in the explicit mock audit response before changing that response. Added the three live-contract metadata fields; both populated pages validate. Demo data remains opt-in and never replaces failed live reads.
- **Merged app:** The first build reproduced a missing alias bridge for the new shared audit helper. Added the same re-export bridge used by neighboring API helpers. The next build compiled/type-checked but could not resolve the live legal-policy host in the restricted environment. The network-enabled repeat passed; no legal-content fallback or assertion suppression was added.
- **Lint baseline, partial:** 91 errors/seven warnings → **five errors/seven warnings**. A scoped CommonJS import exception applies only to Node test harnesses and test scripts; application rules remain enabled. Five reserved `module` harness bindings were renamed without changing assertions. Remaining errors: StaffIdentitySetup effect state update (one), API client explicit-any types (three), shared API types explicit-any (one). The full lint gate remains red.

## First-slice verification and limits

[Retained evidence](evidence/sprint-2-2026-11-17/) includes failing pre-fix reproductions, final **82/82 admin tests**, **3/3 merged build-configuration tests**, passing scoped lint, both production webpack build logs and lint comparison. The tests execute actual TypeScript components/helpers with deterministic hook/API timing; they are not browser end-to-end or hosted acceptance. No backend source changed; prior backend full-mode results remain historical rather than a new backend rerun.

Remaining Sprint 2 work includes browser fault injection and a real browser CSV download, populated role-specific review/support/catalog workflows, competing/stale revisions, the five application lint errors and seven warnings, and the security-hardening backlog. None of these are implied complete by this first slice. Sprint 1 blockers remain separately tracked.


## Continuation — lint, hardening and browser acceptance

The user requested continuing Sprint 2. The five remaining application lint errors are fixed: API bodies/responses default to `unknown` with explicit error narrowing, permissions rows have a bounded index type, and staff identity loading updates state only in the asynchronous response callback while retaining abort/unmount guards. JSON falsy values are serialized without losing their values. The credential rejection redirect deliberately reloads the document to discard private client state and has one explained local lint exemption. Full admin ESLint now passes with **zero errors/six existing native-image warnings**; no application-wide rule was disabled.

**SEC-003 local fix:** both standalone and merged admin routes emit response-level CSP `frame-ancestors 'none'`, X-Frame-Options `DENY`, nosniff, and strict-origin-when-cross-origin referrer policy. Chrome rejects the admin document even in a same-origin iframe. This is verified locally, including the merged production server; deployed headers still require verification after deployment.

**Final verification:** **88/88 admin tests**, **38/38 merged tests**, standalone TypeScript and edited merged-file lint pass. Both webpack production builds pass. **Six Chrome scenarios pass in each app layout (12 executions)**, covering real CSV download bytes, audit fault/retry/empty/pagination/stale queries, support role recovery, property stale-version recovery, owner catalog conflicts and saving, read-only permissions, denied support navigation to owner settings, and blocked framing. All server responses in these browser scenarios are synthetic intercepts, not a live backend. Existing application hooks/components and actual compiled app pages execute unchanged.

A broader merged regression run exposed stale navigation/footer harness expectations. The tests now load actual TypeScript bridge modules and assert all existing route destinations, the current account group, localized published legal/support paths, and valid HTTPS overrides. The failing-before log and explanation are retained; no product behavior was changed for these test corrections.

[Continuation evidence and repeat commands](evidence/sprint-2-2026-11-17/continuation/README.md) include logs, lint details, source hashes, synthetic CSVs and browser screenshots. Changes remain local and uncommitted. No backend source, dependencies or lockfiles changed. No deployment or release upload occurred.

**Remaining acceptance:** real staff sessions against a disposable live backend under competing revisions and network faults, then hosted behavior/headers after deployment. Browser intercepts do not prove server authorization or actual database concurrency. Six advisory image warnings remain. Sprint 1 release blockers remain open. The earlier first-slice pending list above is historical and is superseded by this continuation.
