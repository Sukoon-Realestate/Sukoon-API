# Tablet responsiveness — 2026-11-15

Implemented in the adjacent `/Users/demo23home/code/sukoon/sokoun` Flutter repository.

## Changes

- Shared AppScaffold now measures toolbar titles and action overflow against its actual available width, including split views and the rail's remaining viewport. Toolbars, workspace chrome and page headers align to the form/readable/wide content limits already used by the body and footer. Safe-area horizontal insets participate in measurement.
- Main navigation retains its existing destinations, role gates, guide and visited-tab tree. Rail labels gain 104–160 logical pixels according to text scaling; the rail is protected from system cutouts. Below 600 logical pixels, or when a rail would leave less than 480 pixels for the page, the existing bottom navigation is used.
- Shared profile and settings pages use the wide content limit. Verification, activity, account details and role sections, plus preferences/security/legal/help settings, reflow into at most two columns. Local available width and text scaling determine the column count; phones and larger text keep one column. The identity remains above the profile sections; logout and account deletion remain below settings sections.
- Shared modal sheets explicitly cap at 640 logical pixels unless a caller supplies constraints. Legacy sheet bodies fill their local constraints instead of requesting the screen width. Typed results, dismissal and keyboard inset ownership are preserved.
- Updated `sokoun/docs/ui-refactor/REFERENCE-ADAPTATION.md`. Preserved unrelated existing edits, including the combined profile/visits/chat header changes.

## Verification

- **189 focused app tests passed**, covering the new 29 tablet/resizing/settings cases plus shared scaffold, combined headers, bottom navigation, glass navigation and account-page regressions. New cases cover English/Arabic, 390/768/1366 widths, portrait/landscape, locally constrained 496-pixel forms, 100%/200% text, all four workspaces' settings, last rail destination reachability, draft retention during resize, and tablet sheet bounds/keyboard consumption.
- **Two shared-core sheet tests passed**: typed selection/keyboard ownership and configurable dismissal.
- **Scoped analysis: no issues** in all 11 changed/test targets. Broad app analysis initially reported existing warnings/info plus one redundant import added during implementation; that import was removed. Whitespace validation passed.
- Broader dashboard/workspace checks: 122 passed and 40 failed. An isolated copy using the original shared scaffold/layout/toolbar/rail/sheet source reproduced exactly the same 40 failure names. Examples include expecting four workspace options where two are available and missing company fixture content. This comparison covers these two suites only.
- Required full app suite was attempted. It stalled on the owner concurrent-submission case and the screen audit, encountered timeouts, and was interrupted after about 18 minutes. Final progress: 13,125 passed, 32 skipped, 497 failures (including shutdown errors). These broader failures have not all been baseline-classified; the full suite is not a release gate pass.
- Inspected a rendered Arabic landscape profile fixture. Its placeholder identity/activity labels are fixture content, not production copy.

## Evidence and limits

Evidence: `output/tablet-responsiveness/` contains focused/core test logs, scoped analysis summary, the 40-name baseline comparison and an Arabic profile fixture PNG. Full-suite log: `/tmp/tablet-full-suite.log`; broader comparison logs: `/tmp/tablet-layout-regressions.log` and `/tmp/tablet-baseline-comparison.log`.

The only connected iOS simulator is an iPhone; no tablet device/simulator was available. Tablet checks are rendered widget tests, not a live tablet journey or physical-device performance certification. No frame-rate claim, deployment, account write or feature retirement was made.
