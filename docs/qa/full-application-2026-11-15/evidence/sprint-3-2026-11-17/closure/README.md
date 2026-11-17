# Sprint 3 regression recovery — completed 18 November 2026

**Complete for the Sprint 3 regression-recovery scope.** All 497 original records are reconciled (495 passing matches, two verified replacements for the current startup contract). Complete app: **13,757 passes / 45 intentional skips / zero failures**, all 456 files, exit zero and no active cases. Shared core: **345 passes**. Final MVP identity/count/navigation checks: **132 passes / one deliberate deferred-group skip**, alongside the 264-case MVP matrix and 35-case guide/UI cross-check. Counts overlap.

The strict iOS simulator run passes **53 widget journeys**, including account retry/session interruption, direct company account access, account-review preparation/acknowledgement without logout, partial identity correction, Home help and update dialogs with normal/reduced motion. The driver verifies named required journeys and rejects empty/partial runs. All 53 ledger results are success; process exits zero. [Native ledger](native-complete-results.json), [complete summaries](results.json), [historical dispositions](historical-reconciliation.json), [authored hashes](authored-source-hashes.json).

The native app uses `com.app.sokoon.sprint3qa` and fixture transport/protected storage. The installed user app and its account data were preserved. Connected backend/provider acceptance, exhaustive device/platform matrices, geometry review and physical-device profile performance remain Sprint 4 work; this is not production release approval. Earlier diagnostic progress below records rejected attempts and is historical.


All 497 historical records are reconciled: 495 map to passing reruns; two startup contracts are explicitly superseded by passing current splash/Login/Home checks. See historical-reconciliation.json. This is distinct from completion of the full app and native gates.

Product corrections in this continuation:

- Dashboard account retry uses the mounted shell recovery transition through AccountRetryScope. Successful cookie hydration restores workspace identity and navigation; logout, replacement and disposal checks remain.
- Company dashboard account settings and the Individual Home guide have visible header controls again. Existing scoped destinations, guide targets and eligibility guards remain.
- Partial identity correction stays on the form with server feedback. A settled partial response clears the old upload draft; a second submission requires fresh explicit input.
- Termination create/accept confirmation binds the immutable review identity and preserves the changed-contract recovery message instead of stopping first at a reset acknowledgement.
- Empty radio choices avoid an overflowing empty intrinsic Column; update version badges wrap at accessible text sizes; short owner-action sheets scroll.

Fixture repairs preserve meaningful checks: company role-context transport and current mandate destinations, independent capability reads without writes, current search pickers and exact filters, owner advertising context, scroll-before-tap for long translated content, current back controls, required audit providers and real scroll hosts, duplicate-save disabling and error-overlay cleanup.

Verified focused batches: 304 passes plus one stale search finder in the consolidated original-case run; the corrected search file subsequently passes all six cases. The complete MVP-specific matrix plus navigation/guide/consent/calendar/banner recovery passes 264 cases. Complete-suite follow-ups pass 82 cases; the two owner-submission cases pass a separate bounded recheck. Counts overlap. Source-owned analysis is clean after removing the reported unused profile-test import. Full-app analysis separately retains pre-existing diagnostics outside this continuation.

The exploratory complete-app process was intentionally stopped after moving to a fixed source snapshot because concurrent work continues in the shared checkout. It is incomplete and is not a green gate. The native build is being sequenced after app tests to reduce resource contention. Native QA uses a separate bundle ID and fixture transport/storage, preserving the installed app and account data.

Final gate status and raw evidence are still being added. No commit, push, merge, deployment or live provider transaction occurred in this continuation.

## Final complete-suite follow-up

The first isolated all-456-file run terminates with 13,746 passes, 43 skips, ten errors and one failure. It exposes two MVP-only checks needing explicit full-mode skips, Student badge assertions using the legacy personal counter, current back/app-bar finders, and a real recovery defect: global confirmed-operation refresh omitted already loaded Student scopes. `refresh()` now retains startup's existing two-scope load contract while also refreshing other current loaded/in-flight scopes. The corrected tests require exact Student refresh counts and preserve no-refresh assertions for failed/unconfirmed operations. The combined six-file follow-up passes 159 cases with two intended mode skips. The dedicated MVP guide/UI run passes 35 cases.

A second uninterrupted complete-app run is now executing against the final snapshot. The source manifest is versioned because only this follow-up's explicit fixture repairs, badge fix and native harness were added after the initial snapshot. Native binary launch is guarded by its actual built Info.plist identifier; a flavor override was caught before installation, the queued drive process was stopped, and every Runner flavor in the isolated project was corrected. The user checkout's native project was not changed.

The sprint plan's connected acceptance and physical-device/profile matrices belong to Sprint 4 (COVERAGE.md, suggested sprint 4). Selected fixture-only native runtime checks here do not replace those acceptance matrices.

## Verified final application gate — 18 November 2026

The final run including partial-identity revision refresh and its two new regressions completed successfully: **13,757 passes / 45 skips / zero failures**, all **456 test files**, exit zero, successful terminal event and no active cases. Source: `reruns/20261117-231822`. Final shared core: **345 passes**, successful terminal. MVP-specific matrix: 264 passes; its additional guide/UI cross-check: 35 passes. Final MVP identity/count/navigation checks: **132 passes / one deferred-group skip**, successful terminal. Identity/account/badge regressions: 150 passes. Counts overlap.

The 45 full-mode skips comprise MVP-only contracts and environment-gated connected/Django/provider tests; exact identities are retained in results.json. They are not hidden failures. Connected hosted/provider and physical-device/profile acceptance belong to Sprint 4. No source-owned application file drift was found between the authored fixes and the tested isolated snapshot. Concurrent checkout changes outside those files are not certified by the snapshot run.

The native build succeeds and its QA bundle ID and kernel identity are verified before launch. Earlier empty/failed native runs are explicitly rejected. The corrected strict native rerun remains in progress; it must include the required journey ledger to pass.

## Native fixture progress — 18 November 2026

The bundled-translation native run executes the repaired account hydration, company account entry, partial identity, Home help, and normal/reduced-motion update-dialog cases successfully. It remains rejected overall because four account-closure preparation assertions run before the native form is ready; the strict ledger correctly rejects the partial result. A bounded eight-second readiness wait was added to the fixture, retaining actual scrolling, hit-testability, acknowledgement, exact read/no-write/no-logout assertions. All four affected cases pass on the VM after the fixture change. The strict native rerun is in progress. Rejected logs are retained separately and never reported as successful evidence.

The subsequent native diagnostic established that the account acknowledgement sits in the form's inner list, while the old fixture scrolled the outer page header. The final fixture waits for AccountClosureBody, scrolls only its own list, requires a hit-testable checkbox, and retains exact read/no-write/no-logout assertions. The four affected VM cases pass. Only the final strict native run may close that native check; intermediate attempts remain rejected.

The VM logging trace corrected the earlier layout hypothesis: a Flutter `expect()` inside the asynchronous fake account repository throws `TestAsyncUtils.guardSync` on the native engine. The app correctly normalizes this fixture exception as a failed read. The fixture now records the method and asserts exact GET in the test body after successful account preparation. It retains account identity, scrolling/hit-testability, acknowledgement, exact read/no-write/no-logout checks. All four affected VM cases pass; the final native rerun is underway. The exact normalized-error stack is in native-fixture-root-cause.txt. No product error handling was changed to bypass the failure.

## Repeat commands

From the API QA worktree:

```sh
python3 docs/qa/full-application-2026-11-15/rerun.py --suite app --mode full --app-root /private/tmp/sprint3-final-snapshot --timeout 3600
python3 docs/qa/full-application-2026-11-15/rerun.py --suite core --mode full --timeout 600
```

From the mobile app, `make sprint3RegressionCheck` and `make sprint3ProductCheck` retain the focused two-mode checks. The native harness is `integration_test/sprint3_workspace_regression_test.dart` with `test_driver/sprint3_driver.dart`; it must use the isolated QA bundle ID and an output path supplied through `SOKOUN_VERIFY_REPORT_PATH`. The driver rejects missing expected journeys and empty runs. Native runs use copied source/config and fixture transport/storage, never the installed account. A native prebuilt binary is checked against its actual Info.plist and kernel before launching.

## Final disposition

The final strict native process completed with zero failures. `native-complete-results.json` has exactly 53 successful widget-test identities and `required_journeys_passed: true`; compressed terminal logs and the verified binary kernel hash are retained. The only fixture change after the complete-app gate moved a background GET-method assertion into the test body, retained explicit preparation/scroll/hit/acknowledgement checks, and passed all four VM cases plus the complete native harness. No production source changed after the successful complete-app gate. Six QA-parser tests and whitespace checks pass. Source changes remain local and uncommitted; no push, merge, deployment or live provider transaction occurred in this continuation.
