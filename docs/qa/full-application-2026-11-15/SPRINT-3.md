# Sprint 3 — mobile regression recovery

**Started 17 November 2026; in progress.** Scope follows Coverage's suggested Sprint 3: reconcile the 497 recorded failed/error cases, distinguish obsolete test contracts and intentional release gates from product defects, repair demonstrated causes, bound stalled runs and obtain successful complete mobile/core suites. Keep Arabic, English, accessibility, recovery and authorization assertions. Sprint 1 release blockers and Sprint 2 live-backend/hosted acceptance remain separate.

## Current continuation — 17 November 2026

The historical ledger now has **475/497 records with matching passing reruns; 22 remain open**. This reconciles prior failures with current mode-specific evidence; it does not mean 475 new production bugs were fixed or that an uninterrupted final-tree app suite is green. [Per-case reconciliation](evidence/sprint-3-2026-11-17/continuation/historical-reconciliation.json) and [remaining cases](evidence/sprint-3-2026-11-17/continuation/REMAINING.md).

The latest recovery/chat follow-up passes 127 full-release cases and 22 MVP cases, with clean four-file analysis. It fixes blank unnamed-conversation headers and updates retry/capabilities assertions while preserving pull-refresh and disabled-write checks.

Product fixes cover changed consent during an open share confirmation, server-disabled calendar controls, company large-text header/body overflow, and company discovery exposing execution entries without a selected company. Recovery identities, role-scoped destinations and existing owner entries remain. The consent identity is checked after confirmation and after recovery-state preparation; changed recipient/content/expiry/digest requires a new review.

A stalled banner test was waiting for an owner-only request from an Individual fixture. Its Owner setup and bounded await now pass all 22 workflow cases. Updated banner UI, company role/session/housing fixtures and current rich controls preserve meaningful behavior assertions. The moved screen-audit harness now restores its error handler on every exit and fails on runtime/build exceptions; valid forwarding/tour/support fixtures make its selected 24 cases pass. Geometry notes are separately retained for review, not declared solved.

Verification includes a **complete 345-case shared-core pass**, **113 banner UI passes**, **113 final consent/dashboard passes**, **54 MVP product passes**, **24 moved audit runtime passes**, six rendered company admin cases, clean analysis of 23 changed files and six QA-parser tests. Counts overlap. The wider 93-file baseline now terminates: 1,726 passes / 61 errors / six failures before the later focused repairs. A further fixture batch has 71 passes and one unresolved KYC-route fixture failure. [Raw evidence, screenshots, exact results and limits](evidence/sprint-3-2026-11-17/continuation/README.md).

The complete final-tree app runs in intended release modes, the 22 remaining historical dispositions, geometry review and native/device acceptance remain open. No commit, push or deployment occurred. Concurrent user changes were preserved. The original first-batch counts below are historical.

## First batch completed

The exact three-file repeat reproduced **166 passes / seven errors** on the merged baseline. Seven historical case IDs are mapped individually in [case-dispositions.json](evidence/sprint-3-2026-11-17/case-dispositions.json).

- **Three release-mode fixture failures:** company work is deliberately deferred in default MVP. The unmodified company/payment tests pass in full mode. The status test now asserts localized refusal and no capability/page traffic in MVP, while retaining every resource label in full mode. The company payment journey is explicitly skipped only in MVP; a new owner variant verifies the same double-tap, timeout, persisted request identity and receipt recovery in both modes. No production feature was enabled or permission changed.
- **Three obsolete presentation finders:** saved-card tests now target FavoritePropertySummary and its rich text; exact prices and spoken amount/unit/basis remain required. Offer navigation taps the actual accommodation label and still requires the precise property/offer IDs. No product UI was changed to satisfy a historical widget type.
- **One pagination test race:** scrolling the fallback load-more control into view can trigger automatic pagination and remove that control. The test now taps only if it still exists. It still requires exactly pages 1 and 2, in order, and both expected bed records.
- **Lifecycle verification:** MVP refusal exposes a real read-error toast. Its test-owned timer is dismissed after checking the visible error and before widget invariants run. Pending-timer assertions remain enabled.

Final focused matrix: **179 passes / one intentional skip in MVP; 180 passes / zero skips in full-release mode**. Both runs terminate successfully with no active tests. Three-file analysis reports no issues. No existing business assertion was removed. [Evidence and repeat commands](evidence/sprint-3-2026-11-17/README.md).

## Regression-runner work

`rerun.py --mode mvp|full` makes the release flag explicit and captures Flutter JSON events. Its existing process-group timeout remains. The new summary distinguishes skips/hidden lifecycle events, identifies active/failed cases, and rejects an incomplete event stream as successful evidence even if the process exits zero. Four parser unit tests pass, and the bounded CLI successfully re-ran the company MVP refusal cases.

`make sprint3RegressionCheck` in the mobile app repeats this four-file matrix. Code is on local `codex/sprint-03-mobile-regression`; QA tooling/reporting is on local `codex/sprint-03-qa`. Work is uncommitted and has not been pushed or deployed.

## Remaining work

1. Reproduce and classify the remaining **22 historical failure records** (the first batch originally left 490). Some may already be resolved by prior work; do not count them closed without a current run.
2. Repair remaining fixture/finder/release-mode mismatches and independently demonstrated product defects, preserving meaningful checks.
3. Reconcile stalled cases with bounded logs and run complete app/core suites successfully under their intended release modes. This first batch does not establish that the original full-suite stall is fixed.
4. Keep device/runtime acceptance and product-release readiness separate from widget and contract test counts.

Concurrent header/profile/owner-control edits from the user were preserved and are outside this batch. The first batch changed no mobile product source, dependency, release scope or backend behavior; later continuation product fixes are listed above.
