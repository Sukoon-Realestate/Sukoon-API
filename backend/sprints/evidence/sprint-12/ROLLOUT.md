# Sprint 12 release, compatibility and recovery plan

Prepared 2026-11-14. **Not executed. Release is blocked by the acceptance register in README.md.**
This task authorizes local implementation and isolated validation only. No deployment, provider transaction,
real-media deletion, shared-database migration or change to user data is part of this result.

## Release identity and prerequisites

Pin a reviewed immutable source commit, locked image and migration artifact. The report identifies the source commit
and working-tree source digests; this uncommitted acceptance package is not an approved release image. Record the actual
API, worker, scheduler, migration job and client versions plus runtime configuration identities before any rollout.
Assign named owners to the backend lead, security/dependency owner, client lead, SRE and QA roles below. Role ownership
in this plan does not imply that an individual accepted a risk. No exception is currently approved.

Close each release blocker with linked evidence or a separately reviewed, time-bounded exception before proceeding.
In particular, update to a supported dependency set through its own compatibility review, preserve deliberately locked
company discussions, and resolve BUG-AUTH-01 through a product authority decision. Passing fake-provider tests cannot
substitute for Google/Apple/email/storage/payment/signing/push/provider sandbox contracts or physical-device tests.

## Compatibility and migrations

- Sprint 12 changes only QA tooling, tests, Make targets and release documentation. It adds no application dependency,
  schema migration, route or serving behavior. Existing cookies, aliases, parsers, methods, envelopes and locale behavior
  retain their earlier contracts. The refreshed resolver diff covers declared transport metadata; behavioral tests cover
  specific exercised cases, not every role/workspace/header/locale combination.
- [Sprint 01](../sprint-01/README.md), [Sprint 02](../sprint-02/README.md) and
  [Sprint 05](../sprint-05/README.md) document earlier identity/input security fixes. Clients must use server-recorded owned
  media, reviewed account closure, bound sessions, cookie CSRF verification and current revision/idempotency contracts.
  Do not restore an insecure alias to make an older client succeed. Obtain explicit client-version and security signoff.
- Keep opt-in bounded collection/history forms documented in [Sprint 05](../sprint-05/README.md),
  [Sprint 08](../sprint-08/README.md) and [Sprint 09](../sprint-09/README.md). Legacy full histories remain compatible and
  data-dependent. A new default cap requires a separately coordinated client migration; it is not a hidden release fix.
- Run `migrate_release` only in the separately authorized target environment, after verifying database identity and backups.
  Serialize forward migration jobs with the existing release lock. Do not fake migration history or reverse financial,
  receipt, authority or private-media schema/data merely to recover an older application version.
- Fresh-database migrations and a second no-op migration pass were exercised locally. Existing-data upgrade,
  mixed-version rolling traffic and older-worker/new-schema compatibility remain separate open gates. Test historical model
  writes, receipts, tasks, event names and callback replay in an isolated clone with approved synthetic history before release.
- `SAVED_SEARCH_ITEMIZED_READS` stays false unless explicitly activated after every reader/worker understands the new format.
  Properties migrations 0046/0047 and rollback conversion requirements are documented in the
  [read-format rollout](../sprint-04/read-followup-2026-11-12.md). Never roll an older reader back over live itemized receipts.
- The opt-in `config.settings.staging_acceptance` profile requires explicit verified hosts/origins, secure cookies and
  an operator-selected HSTS duration. Trust proxy headers only at ingress that strips untrusted forwarded headers.
  Its W005/W021 warnings are explicit limited-host policy, not deployed TLS evidence. Inspect actual HTTPS redirects,
  cookies, CSRF/origins and private-byte responses from a real browser/device on the selected isolated host.

## Stages and observation windows

These are proposed minimum windows. They must be accepted with numeric per-family latency, query, payload,
candidate, lock and provider-I/O budgets before execution; no production SLO is inferred from loopback measurements.

| Group | Admission | Minimum observation | Advance only with |
|---|---|---|---|
| 0: isolated HTTPS staging | Owned synthetic accounts; provider sandbox credentials; separately approved infrastructure | 24 hours including one scheduler/cleanup cycle; extend for longer configured jobs | Sandbox callbacks/signatures/replays, Android/iOS native media, storage restart/failure recovery, browser cookie/origin checks, controlled all-family load, migrations and restore evidence |
| 1: internal canary | Explicit internal test cohort; no unapproved financial operations | 24 hours and at least one completed relevant business cycle | No unexpected authorization, private-media, duplicate-instruction or reconciliation outcomes; agreed budgets hold; scheduled jobs complete with the same SHA/config |
| 2: limited cohort | Explicitly selected small cohort with rollback-compatible clients; operator-approved percentage | 48 hours including background/retry cycles | Error/latency/lock/queue/storage metrics within agreed budgets; sampled contracts and receipts match; no unresolved provider uncertainty |
| 3: broader rollout | Operator-approved increasing cohorts after group 2 signoff | 72 hours through next scheduled billing/retention cycle as applicable | Release owner, client lead, security and SRE signoffs with durable evidence |

Record UTC start/end, cohort definition, request and job counts, p50/p95/p99 latency, 4xx/5xx by expected outcome,
query/payload/candidate distributions, lock waits/deadlocks, provider duration/errors, queue age/retries, scheduled
completions, upload quarantine/scan failures, private storage persistence, reconciliation age and retention backlog.
Verify monitoring/alerts with a synthetic failure; a configured dashboard alone is not delivery evidence.

Stop expansion immediately for any unexpected authority/media exposure, duplicate money effect, missing confirmed
instruction, ledger imbalance, schema/config mismatch, stale authority acceptance, lost durable work or exceeded agreed
budget. Preserve correlation IDs and original receipts without recording secrets, document bytes or personal data.

## Recovery

1. Stop expansion and isolate affected commands/provider dispatch through the established operational topology. Preserve
   durable receipts, ledger/audit records, upload claims, provider identities and unknown-outcome records. Do not delete
   evidence or start a second external operation to compensate for uncertainty.
2. Compare actual source/config/schema versions across API, scheduler and workers. Stop duplicate publishers; keep the
   supported single scheduler topology. Investigate with current-authorized read-only status before re-enabling work.
3. For an already confirmed provider action, reconcile its original instruction/reference and commit only missing local
   recognition using existing idempotent workflows. For an unknown outcome, inquire with the provider under the same
   identity, retain durable uncertainty and use the domain's retry/reconciliation policy. Never submit a new payment,
   refund or payout key as a rollback technique. Browser return pages are not confirmation evidence.
4. Prefer a forward code correction compatible with the applied schema. Application rollback needs a demonstrated
   old-code/new-schema contract. For saved searches, disable itemized creation everywhere, drain in-flight work and the
   15-minute receipt window, then use the documented materialization/retirement command in the authorized environment.
   Require both remaining counters to reach zero before restoring older readers. Never run this against user data merely
   to obtain acceptance evidence.
5. Restore backups only into a new isolated target first. Verify table contents, sequence state, migration history,
   media digests/ownership and external instruction reconciliation against independent provider facts. Database dumps
   do not include remote media/config/secrets. Production backup durability, failure-domain independence, retention,
   approved RPO/RTO and recovery authorization remain unmet; the retired recovery journal is not a reopening mechanism.
6. Re-run the failing use case, current authority/replay checks, privacy checks and required observation window. A release
   owner approves resumption only with recorded evidence. Do not mark the release accepted based on this local package.

## Independent walkthrough handoff

A developer unfamiliar with these changes must trace registration/session rotation, listing/visit eligibility, a money
command plus unknown-outcome reconciliation, REST/socket message send, support private attachment access and staff moderation.
For each, follow URL/class → typed input → service locks/current authority/receipt → prepared read projection → committed
outbox/provider effects and retry. Use direct-service tests and negative/replay tests to demonstrate behavior. Review the
remaining planning service-to-view imports in `acceptance.json` and mixed adapters listed by Sprints 07–09.
Record reviewer identity, reviewed source SHA, findings and disposition. This walkthrough was not performed by an independent
human in this task; no agent self-review is presented as that acceptance.
