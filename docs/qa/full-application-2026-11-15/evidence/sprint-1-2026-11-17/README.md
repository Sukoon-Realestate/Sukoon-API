# Sprint 1 continuation evidence — 17 November 2026

All fixes are local; see [Sprint 1](../../SPRINT-1.md) for the status and limits.

- `audit-before.json` / `audit-after.json`, `dependency-delta.json`: same pinned-package audit protocol, 124 advisories before and zero after. `pip-check.log` and `lock-verify.log` verify resolved dependency consistency and manifest hash.
- `backend-broad.log` / `.xml`: migrated PostgreSQL full MVP attempt, 6,172 passes, ten later-resolved assertion failures, 22 skips, 12 expected failures and a cluster lock-capacity teardown error. Started before small corrections.
- `affected-gate.log` / `.xml`: 3,702 passes, four later-resolved test/contract failures, one cluster lock-capacity schema-cleanup failure, ten skips and one expected failure. Started before the last test corrections.
- `drills.log` / `.xml`: both schema-preservation cases pass with adequate scratch lock capacity; one existing company-discussion expected failure remains under its deliberate gate. `teardown-rerun.*`: exact reserve/retry test passes, including teardown. Both owned clusters stopped.
- `verified.log` / `.xml`: 323 migrated PostgreSQL correction cases pass. `payload-final.*`: 24 final route-scoped challenge cases pass. Counts overlap.
- `frozen-before.log`, `other-frozen-before.log`: exact dependency message/required HTML field differences. `corrections.log` retains the model-only diagnostic's missing data-migration fixtures; its two commerce assertions pass on the fully migrated database.
- `provider-before.log`, `compat-after.log`, `storage-before.log`, `storage-after.log`: reproduce removed provider exception imports and ignored storage setting, then verify compatibility fixes. `static-fixture-before.log` demonstrates the obsolete test override's missing-manifest error.
- `social-upgrade.py` / `.log`: synthetic-only old SDK 0016 → new SDK 0020 association migration drill, preserving identity/data and checking backfills/constraints. No real account rows or private configuration are included.
- `visit-before.log` / `visit-after.log`, `mobile-focused.log`, `navigation-widgets.log`: remaining viewport test reproduction and targeted Flutter regressions.
- `native-back-summary.json`: verified stream subscriptions, navigation and event counts from one English native simulator journey. No Flutter.Error captured; intermittent defect remains open. Raw debug messages remain private outside the repository.
- `routing-snapshot.json`, `hosted-routing.json`, `association-runtime.json`, `link-hosts.json`: sanitized read-only ingress and status evidence; app requests return 503 while public responses are 504. Declared mobile link hosts also lack working associations.
- `association-routing-before.log`, `association-http.log`, `admin-tests.log`, `landing-tests.log`, `landing-build.log`: missing public-host rewrite reproduction, local exact proxy HTTP behavior and frontend regressions/build.

Private deployment snapshots, credentials, raw runtime/debug logs, disposable
clusters and virtual environments remain under private/local paths. Original
15–16 November artifacts have not been overwritten. Passing local checks do not
establish live signing, store acceptance, deployment or whole-app readiness.

Publication copies of retained test logs/XML normalize trailing whitespace and
line endings. The original raw files remain in the private task directories;
assertions, outcomes and failure details are preserved in these exports.
