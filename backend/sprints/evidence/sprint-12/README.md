# Sprint 12 — acceptance and rollout evidence

Prepared 2026-11-14. **Local acceptance package implemented; whole-backend/release acceptance remains unmet.**
Work stops after Sprint 12. No deployment, provider transaction, existing-database migration, real-media erasure,
production inspection or production change was performed. No release authorization or exception is inferred here.

## Implemented scope

- Added `tools/qa/sprint12_acceptance.py` and `make sprint12-acceptance`: fresh runtime inventory, transport parity,
  project callback classification, relative/absolute service-to-view import detection, source digests and JUnit outcomes.
  Skips, expected failures and failures retain their test identities and reasons. Empty suites cannot pass. The report
  always leaves `release_accepted=false`; detectable local architecture/contract/regression gaps return nonzero.
- Extended `make test-sprint12-local-contracts` with JUnit output and six report-integrity regressions. It still exercises
  environment isolation, the opt-in staging HTTPS profile and performance instrumentation. There is no serving-code,
  dependency, migration or public API behavior change in Sprint 12.
- Added `make test-sprint12-client-export` to generate planning, cycle, refund and signing fixtures together before
  their grants expire. Updated two advertising class identities in the performance ledger's QA mapping; serving code
  is unchanged.
- Added the [compatibility, staged rollout and recovery plan](ROLLOUT.md), with cohort admission, observation windows,
  monitoring, stop conditions, schema/read-format rollback prerequisites and original-identity provider reconciliation.
- Linked all 72 original findings to their owning sprint evidence in [finding-links.json](finding-links.json).
  These are traceability links, not blanket finding closure. Earlier completed changes and remaining stories remain visible
  in [Sprint 00](../sprint-00/README.md), [01](../sprint-01/README.md), [02](../sprint-02/README.md),
  [03](../sprint-03/README.md), [04](../sprint-04/README.md), [05](../sprint-05/README.md),
  [06](../sprint-06/README.md), [07](../sprint-07/README.md), [08](../sprint-08/README.md),
  [09](../sprint-09/README.md), [10](../sprint-10/README.md) and [11](../sprint-11/README.md).

## Validation and environment

The source base is commit `fd7fb3829481c15d81a4bf00b96401fcc4c51e73`; this package is an uncommitted working-tree
change on that base. [acceptance.json](acceptance.json) identifies source digests and exercised inventory;
[validation.json](validation.json) records final command/test outcomes and omissions. Do not equate the base commit with a deployed image.

All checks use `DOTENV_DISABLED=1`, isolated test settings, private scratch storage and synthetic accounts/providers.
The application environment matches every locked package version; `pip check` passes. Python/Django/tool versions and
the lock digest are recorded in [versions.json](versions.json). No repository `.env` or production credentials were read.
The dependency auditor was installed into its own disposable virtual environment; the application `.venv` and lock were
unchanged. The advisory query sent only public package names/versions to PyPI.

A newly initialized PostgreSQL 18 cluster under `/private/tmp/sukoon-sprint12/pg` uses role `sprint12`, private Unix socket
`/private/tmp/sukoon-sprint12/pg/socket`, port identity 55452, `listen_addresses=''` and `max_locks_per_transaction=1024`.
Separate disposable databases are used for full-suite modes, client contracts, runtime clones and restore. No pre-existing
cluster was used. Cluster/process completion and database fingerprints are recorded in the final validation artifacts.

The initial sandbox PostgreSQL initialization could not allocate shared memory; the new cluster was initialized with
permission. PyPI installation/advisory queries initially failed sandbox DNS and were rerun with permission. These diagnostic
attempts are not hidden or counted as application regressions. No global software install was performed.

| Local check | Outcome / evidence |
|---|---|
| Offline acceptance contracts | 31 passed; [log](logs/local-contracts.log), JUnit retained with final results |
| Full PostgreSQL MVP | **6,140 passed, 21 skipped, 12 expected failures**, zero unexpected failures/errors; [JUnit](full/mvp/junit.xml), [log](logs/full-mvp.log) |
| Full PostgreSQL restoration | **6,140 passed, 21 skipped, 12 expected failures**, zero unexpected failures/errors; [JUnit](full/restoration/junit.xml), [log](logs/full-restoration.log) |
| Final report integrity tests | Six passed after expanding the scan to view-parts modules; overlaps the 31-case local gate, not six additional product scenarios; [JUnit](junit/report-final.xml) |
| Fresh resolver inventory | 795 API patterns; no added/removed routes or transport metadata differences; zero project-owned function callbacks |
| Domain import boundary | **Unmet**: 29 import statements in 13 service modules reference planning views or view-parts modules; exact statements/symbols in [acceptance.json](acceptance.json) |
| Runtime module imports | 2,042 imported, zero failures; [imports.json](imports.json) |
| Framework/model checks | Django check passes; migration source consistency reports no changes; [logs](logs/) |
| Forward migrations | All migrations apply to a new empty scratch PostgreSQL database; second pass has no migrations to apply; [forward](logs/forward-migrations.log), [no-op](logs/migrations-noop.log) |
| Worker/scheduler/recovery | Queued job consumed, planning inbox delivered, interrupted job recovered once, scheduled probe executed; [worker-runtime.json](worker-runtime.json) |
| Two ASGI processes/shared Redis | Lost-ack recovery, conflicting replay, peer receipts, outsider denial, suspension/socket/session revocation; [chat-runtime.json](chat-runtime.json) |
| Scoped controlled load | 120 requests, concurrency 4, three warmups, one-message fixture; 108 expected successes, 12 expected denials, zero unexpected outcomes; p50 21.45 ms, p95 26.13 ms, 158.8 requests/s, maximum response 478 bytes |
| Local backup/restore | 367 table counts/content digests and sequence values match in a separate restored database; [backup-restore.json](backup-restore.json) |
| Dependency audit | **Unmet**: 124 advisories in 13 locked packages; [dependency-audit.json](dependency-audit.json), [log](logs/dependency-audit.log). No dependency upgrade or risk exception was made |
| Fresh client contracts | Backend export: 35 passed; Flutter planning/refund/mock-provider parsers/DTOs: 21 passed; Django replay of eight actual Flutter request bodies: eight passed; [client-contracts.json](client-contracts.json) |
| Separate Flutter rental-cycle contract | **Unmet**: three passed, one failed. The stale positive hosted-onboarding test conflicts with the client's explicit `OwnerPaymentData.onboardingEnabled=false`; [log](logs/flutter-cycle-contract.log). No disabled flow was re-enabled |
| Syntax/scoped lint | 2,237 Python files parse; changed QA/test F401/F811/F841 lint passes. Whole-project lint debt remains inherited; [syntax.json](syntax.json) |

Worker/network helpers stopped their owned processes and dropped their cloned databases. The backup check includes a new
synthetic account and migration/reference data; it verifies a local database dump, not remote media/configuration backup
or production RPO/RTO. The probe scheduler certifies transport/execution, not every production schedule's business effect.
The task-owned PostgreSQL cluster is stopped; [scratch-cluster.json](scratch-cluster.json) records remaining scratch data.
All four pre-existing repository SQLite databases have identical before/after fingerprints in
[database-preservation.json](database-preservation.json). No serving application/configuration source changed. The final
QA scanner, fixture-export and performance-ledger metadata updates happened after the full suites started; their own
scoped checks passed. No separate post-update full-suite claim is made for those QA modules.

The 21 full-suite skips in each mode are two authentic native clips, eight fresh Flutter body inputs, four intentionally
inapplicable edit-screen aliases, two OpenCV cases and five independent PostgreSQL journal/drill checks. The eight Flutter
body cases subsequently passed in the fresh focused replay; the original full-suite skip counts remain unchanged. The
12 expected failures retain the known company mandate/member authority gap and deliberately locked company-chat audience.
No skipped or expected-failing case is counted as a passing acceptance scenario. Full runs overlap; do not add counts to
claim distinct scenario coverage.

The initial Flutter attempt recorded eight passes and six failures (including a missing-file loader) using default MVP
mode and incomplete signing fixtures. The complete fresh export plus `SUKOON_MVP=false` resolved that setup attempt; its
[log](logs/flutter-contracts-initial.log) remains. The separate hosted-onboarding cycle test is still a real compatibility
gap: reconcile the obsolete positive test with supported prepared-beneficiary/current-authorization contracts in a client
task. Preserve the intentionally disabled legacy flow. The client checkout was not modified; its source identity and fixture
digests are in [client-contracts.json](client-contracts.json).

## Versioned performance evidence

[performance-coverage.json](performance-coverage.json) accounts for all 795 patterns: **27 partial service/route probes,
768 unmeasured**, with API-wide acceptance false. [performance-baseline.json](performance-baseline.json) retains 90 matching
case/size pairs against Sprint 11, plus both fresh raw [MVP](metrics-mvp.jsonl) and [restoration](metrics-restoration.jsonl)
observations. Admin property projections remain **1/1/1 queries** at 5/40/100 rows; advertising owner pages remain **3/3/3**
and rejection-heavy feeds **1/1/1** at 1/10/100. JSONL includes sampled payload, candidate, transaction/lock, heap and provider-I/O
measurements where instrumented. The baseline is versioned local synthetic evidence; host noise/concurrent tests make timings
unsuitable as production SLOs. Null candidate measurements are unknown, not zero. Neither these probes nor the one-message
chat load certify every route family's large-history, rejection, provider, payload or contention budget.

## Gate disposition and unmet criteria

No gate is promoted from a scoped passing check to whole-backend acceptance. Owners below are required operational roles;
named assignees and risk acceptance have **not** been supplied. Each open item blocks admission to rollout group 0 unless
the release owner records a separately reviewed, bounded exception with a named person and expiry. No such exception exists.

| Sprint 12 gate | Disposition | Remaining acceptance / owner / bound |
|---|---|---|
| Architecture | Partial; explicit project CBVs and resolver parity established | Planning service-to-view dependencies and incomplete cohesive extraction in Sprints 07–09; domain modules outside `services/` and dynamic imports need review. Backend lead must complete before group 0. Class count alone is insufficient |
| Contracts | Partial; existing negative/boundary and domain contracts exercised | Exhaustive positive alias × method × role × workspace × parser × envelope × locale × header/replay matrix and coordinated client-version migration/signoff. Backend/client leads before group 0 |
| Correctness | Local regression/races and fresh schema evidence only | Known company mandate/member authority BUG-AUTH-01 and deliberately locked company-chat audience; native/optional omissions; representative existing-data forward upgrades, mixed-version traffic and complete required interleavings. Product/backend/QA before group 0 |
| Performance | Partial measured probes and scoped loopback load | Every family's representative query, payload, candidate, lock, provider-I/O and controlled-load budgets, rejection-heavy/large/public histories. Compatible full legacy responses remain data-dependent. Performance/backend owner must agree and meet numeric budgets before group 0 |
| Security/media | Blocked; audited dependency findings remain | Supported audited lock, actual deployed TLS/origins/cookies, full invalid-file/input matrix, quarantine/scanner policy, complete ownership/retention/cleanup and real staff/provider signature/approval/replay acceptance. Security/media owners before group 0; opaque-file policy still needs product signoff |
| Operations | Partial local worker/Redis/restore evidence | Authentic sandbox provider contracts, selected storage persistence/failure recovery, physical Android/iOS/native media, all production schedule/monitoring evidence, independent durable backups/RPO/RTO and unknown-outcome reconciliation. SRE/provider/mobile owners before group 0 |
| Cleanup | Partial; earlier removals/retained compatibility documented | Uncertain imports and full-tree lint debt remain; fabricated-output/fixture/obsolete-code review and provider retention/deprecation need complete semantic signoff. Sprint 11's scoped lint/import passes do not certify global cleanup. Backend owner before group 0 |
| Release artifacts / human review | Plan and local report supplied; execution/review unmet | Independent developer architecture/use-case walkthrough, named release owners, client/dependency compatibility signoffs, real staged observation and demonstrated recovery. Reviewer/release owner before rollout; no independent human review is claimed |

Local tests use the existing network guards and fake/test provider seams. They do not prove settlement, receipt timing,
real signatures/notifications, push delivery, transcription/moderation/scanning or remote storage durability. Company chat
remains intentionally locked; these tests do not change its policy. The retired independent recovery journal remains retired;
its skipped/disabled checks are not repaired or silently certified by a successful `pg_restore`.

## Reproduction

Run from `backend/` with fresh task-owned PostgreSQL/settings and private storage. Never use a repository database or a
shared service. The committed `scratch-*.example.py` files document the exact local settings and require a new scratch root
and private cluster before reuse; they contain no production credentials.

```sh
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  make test-sprint12-local-contracts CYCLE_SETTINGS=<scratch-sqlite-module> BASELINE_OUT=<scratch-output>
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  make sprint12-acceptance CYCLE_SETTINGS=<scratch-module> BASELINE_OUT=<scratch-output> \
  SPRINT12_JUNIT='<copied-junit-path> <other-junit-path>'
```

The acceptance CLI currently returns **1**, correctly exposing the inherited architecture import gap; `make` reports **2**.
This nonzero status is expected evidence of unmet criteria, not a hidden passing release gate. An empty `SPRINT12_JUNIT` inventories
source only and certifies no tests. Reproduce full modes with `make test-baseline-mvp` and `make test-baseline-restoration`,
explicit `BASELINE_PYTEST` containing `--ds=<fresh-postgres-module>`, and distinct test databases per process. Do not let
pytest.ini select repository-default settings inadvertently. Keep all raw artifacts and original provider identities.

For fresh cross-language contracts, run `make test-sprint12-client-export CYCLE_SETTINGS=<fresh-postgres-module>
BASELINE_OUT=<scratch-output>` with the same isolated environment. Immediately run the existing Flutter tests against
`<scratch-output>/client`, before the five-minute capability grants expire:

```sh
# From sokoun/apps/sokoun_app; existing Flutter SDK/dependencies required.
flutter test --no-pub test/remaining_rental_finance_test.dart \
  test/django_remaining_contract_test.dart test/django_mock_provider_contract_test.dart \
  --dart-define=SUKOON_MVP=false --dart-define=SOKOUN_DJANGO_REMAINING=<scratch-output>/client
flutter test --no-pub test/django_cycle_contract_test.dart \
  --dart-define=SUKOON_MVP=false \
  --dart-define=SOKOUN_DJANGO_CONTRACT=<scratch-output>/client/django-cycle-contract.json
```

The second command currently fails the deliberately disabled hosted-onboarding positive contract; keep that result open.
From `backend/`, replay the first command's actual DTO output with `make test-flutter-request-bodies
CYCLE_SETTINGS=<fresh-postgres-module> CYCLE_EVIDENCE=<scratch-output>/client`, again with isolated settings/storage and
`DOTENV_DISABLED=1`. A stale fixture or fabricated JSON body is not equivalent evidence. No mobile source was edited.

The historical [LOCAL_ACCEPTANCE.md](LOCAL_ACCEPTANCE.md) remains dated evidence from November 12. It is not rewritten
as a fresh Sprint 12 result. Follow [ROLLOUT.md](ROLLOUT.md) only as part of a separately authorized release task after the
open criteria are addressed. No Sprint beyond 12 was started.
