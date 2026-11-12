# Sprint 12 — Prove the outcome and roll out safely

**Outcome:** evidence demonstrates the agreed architecture, performance, security, correctness and cleanup goals across
the supported API surface. This is a future implementation/release stage; the audit did not deploy changes.

## Gates

1. **Architecture:** refresh the runtime route inventory. Zero project-owned authored function HTTP/API handlers remain;
   callbacks/HTML/streaming use suitable classes; Channels stay consumers. Inspect representative full use cases for
   actual service/selector/helper separation, not class shells around old functions. Domain services import no views.
2. **Contracts:** all supported aliases/methods/roles/workspaces/parsers/envelopes/locales/headers and intentional breaking
   security fixes are tested and documented with coordinated client migration.
3. **Correctness:** collectable, reproducible full suite; focused source-triggered regressions; disposable PostgreSQL races
   for money, inventory, OTP/current authority, uploads, commands and computation commits. Validate forward migrations
   and mixed-version compatibility separately; never run them on a user DB merely to claim a clean audit.
4. **Performance:** every route family has measured representative query/payload/candidate/lock/provider-I/O budgets and
   controlled load evidence. Include large/rejection-heavy histories and public endpoints. Retain a versioned benchmark
   baseline; the 13-screen sample is one subset, not the final global gate.
5. **Security/media:** supported audited lock, deployment TLS/origin/cookie settings, complete invalid-input/file matrix,
   current authority, private gateways, media ownership, quarantine where required, retention/cleanup and staff/provider
   signature/approval/replay checks. Any exception has an owner and bounded acceptance plan.
6. **Operations:** real controlled provider sandbox contracts, storage persistence/recovery, worker/scheduler/Redis readiness,
   backup restore, unknown-outcome reconciliation and monitoring. Device/native-media tests run where required rather than
   being silently skipped. Fake-provider success is not live acceptance.
7. **Cleanup:** no active fixture/fabricated-output branches or proven obsolete helpers remain; supported compatibility and
   test/seed providers are explicitly retained or deliberately deprecated.

## Release artifacts

- A fresh report with commit, environment, exercised scope, tool statuses, pass/fail/skip counts, before/after budgets,
  unresolved risks and links to every completed finding/story.
- Migration/client/dependency compatibility notes, staged rollout groups, observation windows and a concrete recovery plan.
  Reconcile already-confirmed external instructions; do not roll back money by submitting a second external operation.
- A final architecture/use-case walkthrough by a developer unfamiliar with the changes, demonstrating human readability.
- Current open findings remain visible. Partial/scoped success is not represented as whole-backend completion.

**Deployment authorization:** this plan does not itself deploy, send provider transactions, erase real media or modify
user data. Those operations need the concrete release/migration task and its established authorization.

## Local preparation — 2026-11-12

[Local checks and remaining external gates](evidence/sprint-12/LOCAL_ACCEPTANCE.md) record real disposable worker/scheduler and two-process Redis/ASGI recovery, scoped loopback load, mobile identity contracts, scratch backup/restore and an opt-in HTTPS staging profile. These do not satisfy real provider, physical-device, deployed TLS or API-wide load signoff. No deployment or production change was performed.
