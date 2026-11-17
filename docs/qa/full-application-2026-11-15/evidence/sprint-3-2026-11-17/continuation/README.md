# Sprint 3 continuation — 17 November 2026

**In progress.** The latest per-case ledger maps **475/497 historical records to passing tests; 22 remain open**. [Exact reconciliation](historical-reconciliation.json), [remaining files](REMAINING.md), and [run summaries](results.json). These are accumulated, mode-specific observations, not an uninterrupted final-tree application-suite success. Source changes continue concurrently in this shared workspace.

## Demonstrated fixes

- **Consent snapshot:** a confirmation opened for an earlier recipient could submit a replacement snapshot. `RentalActionForm.reviewIdentity` now rechecks identity after confirmation and after durable recovery-state preparation. Application sharing binds recipient, profile snapshot, expiry, digest, version and freshness. Four mutation cases assert no old-consent command and then successfully reopen/confirm the replacement review. Current validation is rechecked too. Unknown transmitted operations retain their existing recovery semantics.
- **Calendar availability:** an empty server date allowlist disabled the field tap but left its calendar icon enabled. Both now use `_canPick`, preserving the restored date and refusing any picker or write.
- **Company layout:** 320px/2× text left only 12px for a Column with a 48px fixed action, producing a 36px overflow. Continuation/company/role controls now live in the shared scrolling `pageHeader`; lazy operational lists retain ownership of their scrolling/state. All six roles and viewport/language/theme configurations pass; the dashboard matrix verifies scrolling to the lazy company body and returning to the header. Synthetic screenshots were inspected. No device/profile smoothness claim is made.
- **Company scope:** discovery no longer exposes unscoped contract/tenancy execution entries. The same entries remain inside the selected company/role destinations, and owner operations retain their owner-specific entries. The original scope regression now passes; no backend authorization rule changed.
- **Banner stall:** the test host defaulted to Individual, where owner uploads are deliberately refused. The explicit Owner fixture now reaches the intended command; its request wait has a five-second deadline. A cached-record test also awaited a timer under Flutter fake time; `runAsync` and a bounded await retain its rejection assertions without stalling. All 22 workflow cases terminate and pass.
- **Remaining fixtures:** banner UI tests specify the Owner workspace; Arabic page counters retain their bidi-isolation marks. Company badges may perform independent GETs while original-operation receipt recovery still waits for its explicit action and never issues a write. Company dashboard fixtures now return actual role-context projections and assert current inline workspace controls. Session revoke uses the current TextButton, refresh uses the current logo, custom localized housing hosts register their real workspace dependency, and the canonical-link fallback is the current `sukoon.rent` origin. Workflow, privacy, account-boundary and route assertions remain.
- **Screen audit:** the historical root file moved into `test/screen_audit/`; the runner now resolves a unique moved basename and rejects ambiguity. The audit restores Flutter's error handler in `finally`, forwards errors to the framework, records missing roots directly, and requires no runtime/build exceptions. A valid forwarding message and tour kind/revision replace invalid empty fixtures; support detail receives its actual ticket/reply providers. All 24 selected runtime cases now terminate and pass. Geometry notes are kept separately and are **not a green visual-acceptance claim**: 25 diagnostic notes across 18 cases (12 asymmetric gutters, 12 out-of-bounds text, one truncated text) still require review.

## Verification

| Run | Result |
|---|---|
| Historical 93-file rerun before stall repair | stopped with last active banner concurrency test; no successful terminal |
| Historical rerun after initial fixes | 1,726 pass / 61 errors / six failures; complete unsuccessful terminal |
| Shared core, complete package | **345 pass**, successful terminal |
| Banner workflow | **22 pass**, successful terminal |
| Banner UI, four files | **113 pass**, successful terminal |
| Company/calendar/recovery + initial consent/dashboard combined run | 229 pass / four old lazy-body/header finder errors; corrected dashboard rerun below |
| Final consent + dashboard matrix | **113 pass**, successful terminal |
| Default MVP consent/banner/calendar | **54 pass**, successful terminal |
| Session/refresh/canonical/housing/provider fixtures | 71 pass / one existing-account KYC case remains failing |
| Four moved audit destinations × six configurations | **24 pass**, successful terminal |
| Company admin rendered capture | **six pass**, successful terminal |
| Focused Dart analysis, 23 changed files | **No issues** |
| QA runner/parser tests | **six pass** |

Counts overlap. All raw streams above are retained as compressed JSONL. The standalone first-batch evidence remains unchanged. The existing-account KYC fixture still targets the retired complete-registration button rather than the current IdentityCorrectionScreen; no assertion was deleted or marked skipped. Other remaining cases are listed individually.

## Repeat and limits

From the mobile root: `make -C apps/sokoun_app sprint3ProductCheck` runs the product checks in MVP and full mode. The first-batch `sprint3RegressionCheck` remains. From the API root: `python3 docs/qa/full-application-2026-11-15/rerun.py --suite historical --mode full --timeout 600` selects all historical files, `--suite app` selects the complete app, and `--suite core` selects the complete shared package. A file selector resolves unique moved paths. The selected four audit destinations use `--dart-define=SCREEN_AUDIT_ONLY=ChatForwardBatchScreen,OwnerTourEditorScreen,SupportTicketDetailContentView,SupportHelpContentView`; its default mode is synthetic error-state transport. Runtime results and geometry findings remain distinct.

Complete final-tree app suites in both intended modes, the remaining 22 record dispositions, geometry review, and native/device acceptance remain open. No source commit, push, backend mutation, provider transaction or deployment occurred in this continuation. Concurrent UI/auth/splash/translations and generated captures were preserved; only task-owned tests/product fixes and reporting were edited.

## Recovery and unnamed-chat follow-up

Seven further original records now pass. The conversation header rendered an empty name while the inbox already used the translated unnamed-conversation label. The header now shares that fallback; the existing four Arabic/English, light/dark, 320px/2x-text regressions pass without weakened assertions. Rental-home and revenue recovery tests now recognize the active retry button while retaining pull-refresh success and clearing-error assertions. The disabled invitation fixture permits only its existing visit-detail read plus the independent read-only experience-capabilities query; invitation writes and paginated calls remain forbidden.

The four-file full-release rerun passes **127 cases**; the rental/chat MVP cross-check passes **22 cases**. Both JSON streams have successful terminal events, no failures and no active cases. Analysis of the four edited files reports no issues. These mode flags are explicitly `SUKOON_MVP=false` and `SUKOON_MVP=true`. Native-device interaction and motion were not reviewed.
