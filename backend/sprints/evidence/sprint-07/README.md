# Sprint 07 — housing transport, commands and prepared reads

**Recorded 2026-11-14. Status: partially implemented; acceptance remains open.** Work stops at Sprint 07.
The starting source was `498e88e3`. Existing databases and production were not targeted; no schema migration, deployment
or dependency change was made. The task-owned PostgreSQL cluster was stopped after validation.

The 383 selected non-commerce housing patterns resolve to explicit classes: 336 converted aliases backed by 284 formerly
function-based handlers, plus 47 patterns already using classes. All 795 global patterns retain paths, names, methods,
authentication, permissions, parsers, throttles and MVP availability. Alias grouping was also checked. The 61 excluded
feature patterns retain their existing commerce/provider/catalog owner; [the exact exclusions](excluded-routes.json)
make the boundary reviewable. Private rental evidence/documents and the nested experience package are included.

`features.http.ActionPolicy` declares each method's stable resource/action and company/planning policy. Company roles
are never inferred from `get`, `post` or a new class name. The supported callable authorization helper also recognizes
class metadata and rejects unsupported company methods instead of falling through to an unknown class-name key.
Planning keeps capability-before-body-validation, typed/untyped POST handling, validation/error translation and privacy
headers. Existing raw signing, byte, parser, throttle, OPTIONS and unsupported-method behavior is retained.

Named services now own personal handover/maintenance state changes and command steps for applications, claims,
reservations, group bookings, operational cases, company tenancy/administration/portfolio, student housing and
scenario/tender actions. They receive explicit actor/typed input/original receipt/session inputs rather than an HTTP
request. Supported imports remain available through facades. Existing root locks, receipts, current authority and
committed dispatch remain in the owning domain boundaries.

Company tenancy read facts are prepared once and shared across agreement actions/details, change reviews, maintenance,
occupancy, financial and authority sections. Assignment/maintenance/event facts are reused for projection only; commands
continue querying current authority. Maintenance keeps its existing 30-event company history limit and privacy rules.
Personal maintenance uses the existing batch invoice-link selector. Validated company/lease constraints reach company
visibility selectors before candidate authority evaluation. Legacy complete collections/histories remain compatible.

## Evidence

- [Routes before conversion](routes-before.json), [global transport baseline](global-contract-before.json), and
  [coverage with remaining adapter signals](route-coverage.json): 383 scoped / 795 global patterns; zero scoped function
  callbacks. Regenerate reconciliation with `make sprint07-coverage`.
- [Frozen transport cases](transport-before.json) plus [original restoration overrides](transport-restoration-overrides.json): **5,800 cases per release mode / 11,600 checks** covering synthetic anonymous/account, English/Arabic, method,
  OPTIONS/HEAD/unsupported-method and error/privacy characterizations. These are negative/metadata contracts, not a
  complete positive resource/role matrix.
- [Frozen company method/role gates](company-policy-before.json): **744** source-derived method/role outcomes, checked
  through explicit policy metadata and the supported callable helper. Current resource authority remains independently
  enforced by services and the existing company suites.
- `test_sprint07_reads_commands.py`: direct company command/replay/revoked-signer checks; **zero SQL during the prepared
  company maintenance section** at 5 and 40 scopes, retaining 30 events each; **four SQL queries for complete personal
  maintenance collections** at 5 and 40 rows, with actual invoice links batched. These are scoped probes, not API-wide
  payload/heap/latency acceptance.
- [Source and retention ownership](SOURCE_RETENTION.md) and [all feature sources](source-ownership.json): 641 feature
  source modules, including portfolio, experience and all 25 new domain modules plus the shared transport policy module. No filename-keyword exclusion is used
  for the ownership ledger. Existing portfolio live/removed-media references and local/remote orphan tests are retained.

## Validation

[Machine-readable results](validation-results.json) retain the distinction between integrated full runs and final affected gates.

| Gate | Result |
|---|---|
| Integrated full backend, MVP | 6,008 passed; 3 validation-fixture/seam failures; 21 skips; 12 expected failures |
| Integrated full backend, restoration | 6,007 passed; the same 3 failures plus the single-mode transport-fixture mismatch; 21 skips; 12 expected failures |
| Final Sprint 07 Makefile target, PostgreSQL | **2,339 passed**, 8 skips, 11 expected failures; no failures/errors |
| Final affected gates after corrections, PostgreSQL | **17 passed**, no skips/failures/errors; both transport modes, all policy rows, direct command/read budgets, session fence and reconciled contracts |
| Static/configuration gates | Django checks, no migration drift, 2,183 Python files parsed, 2,008 project modules imported, scoped lint and whitespace passed |

Counts overlap and must not be summed. The full runs started before the validation-only corrections described below
and the final small callable-policy, prepared-fact and authority-before-scope cleanup. Every failed case was rechecked
in the final 17-case gate. The full-backend targets were not repeated again on that last tree, so these are **not green
whole-backend final-tree results**. Final scoped checks and focused negative cases cover the changed paths.

The eight feature skips require fresh Flutter-generated request bodies. The full-run skips additionally include native
voice clips, optional OpenCV cases, an independent recovery-journal cluster and intentionally absent edit-screen aliases.
Expected failures preserve existing blocked discussion/authority and recovery cases; they are not represented as passes.
Raw XML, logs, cluster configuration, baseline source copy and database fingerprints remain in task-owned scratch storage.

Two property contract fixtures were already stale on the starting commit: the owner dashboard's existing `reviews_count`
field and the capture processing-job GET responses. Both failures were reproduced on a source-only copy of `498e88e3`.
Only those four field-shape entries and six GET cases were refreshed from the original source; no property/tour API
implementation changed. The old transport fixture covered MVP only. Original-source restoration characterization found exactly two differing workspace-summary GET records; the common fixture and checksummed restoration overrides now exercise both modes explicitly.

The session-revocation lock-wait test now injects revocation at the extracted maintenance service
lock seam and retains its 401/no-write/no-receipt assertions.

Tests use Python 3.11.15, Django 4.2.11 and a newly initialized PostgreSQL 18.6 cluster on a private Unix socket. Full modes
have distinct test database names and storage roots; `.env` loading is disabled. The cluster's lock table was increased
for the migration regression after the default allocation proved insufficient. SQLite checks are labeled separately and
are not evidence of PostgreSQL locking. Existing database file fingerprints are checked separately; nothing is seeded,
migrated, reset or repaired in an existing database.

Reproduce domain checks with `DOTENV_DISABLED=1 make test-sprint07-housing CYCLE_SETTINGS=<isolated_settings>
BASELINE_OUT=<scratch_directory>`. For the full checks, set `DJANGO_SETTINGS_MODULE` to an isolated test settings module
and run `make test-baseline-mvp` / `make test-baseline-restoration`; use distinct PostgreSQL TEST database names and
storage roots for simultaneous runs. Do not use deployed settings or the repository's existing databases.

## Unmet acceptance criteria

1. **Complete service architecture:** remaining planning/group/roommate/condition, legacy personal interest/invitation/
   agreement/closure, experience and some reputation/shared/advanced methods still own workflow logic or import helpers
   from view modules. The ledger flags 83 adapter methods with state-write/transaction signals for review. These are
   review pointers, not an exhaustive state-machine count. Explicit classes alone do not meet the complete target.
2. **Exhaustive positive parity:** frozen boundary/role contracts and existing positive/race suites do not establish every
   route × method × role × workspace × payload × retry combination. Current command-time authority must remain separate
   from HTTP role selection and prepared read facts.
3. **Family-wide performance budgets:** full-market company discovery and unscoped visibility need bounded candidate,
   query and heap proofs. Compatible full nested histories remain data-dependent. Production-volume payload, computation
   and lock-time budgets are not certified by the maintenance or existing solver/tender probes. The Sprint 04 ledger
   remains 27 partial-probe patterns and 768 unmeasured; API-wide performance acceptance is false.
4. **Complete retention acceptance:** source ownership and existing portfolio/purge tests do not certify every feature
   family's private-data erasure/retention behavior or live remote deletion. No real provider, device, deployment or
   production-volume load is represented as a local test pass.

No later sprint implementation, publication or rollout is included.
