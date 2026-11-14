# Sprint 09 — communication implementation and validation

Date: 2026-11-14 (Africa/Cairo). Scope stops at Sprint 09. The sprint specification
is `sprints/sprint-09-communication-cbvs.md`; the requested directory shorthand
does not identify a separate implementation folder.

## Implementation

- Converted all 14 routed productivity, forwarding, mentions and notification
  action functions into explicit resource CBVs. Existing support/notification
  CBVs remain. OS-action transaction and notification state changes now live in
  `chat/services/notification_actions.py`.
- Legacy REST, rich REST and Channels sends use `SendCommand` and the same `send`
  transaction. Optional legacy client identities, original fingerprints, rich
  membership fences, unread increments and durable committed events remain.
  Legacy conflict responses retain their existing adaptation. Strict legacy
  text fields support both JSON and multipart form bodies without DRF numeric
  coercion. Existing edit/delete/read/forward services remain the shared domain
  implementations; they were not rewritten as HTTP-specific workflows.
- `event_names` centralizes committed message event identities and moderation
  eligibility. Existing edit moderation, original retries after edit/deletion,
  digest source selection and renewable connection leases are preserved and
  covered by their existing regressions.
- `MessagePage` prepares history/context/lookup/starred/event/search pages with
  one eligible roster and relation plan per authorized conversation. Search
  reuses its conversation authorization/projection inside one response, while
  transcript/attachment access still reauthorizes at its own boundary.
- `ConversationPage` batches current direct inbox people, membership boundaries,
  restrictions, roommate consent, blocks, latest visible messages, workspace/list
  preferences, roster receipt counts and presence. Latest-message selection uses
  per-conversation indexed subqueries, rather than ranking complete histories.
  It is used only with
  moderation off and already-prepared direct memberships. Moderation-enabled,
  legacy-upgrade and non-direct paths retain their current authorization and
  enrollment/locking behavior. `ConversationRead` reuses those facts across
  fields. Nothing is stored in a global permission cache or used to authorize a
  later command, socket event, byte response or transcription result.
- Reader pages batch their timestamps/profiles. PostgreSQL read receipt creation
  uses one `INSERT ... SELECT ... ON CONFLICT DO NOTHING`, preserving the actual
  synchronous read timestamp and monotonic participant cursor. SQLite retains
  the existing 500-object batches. This bounds Python allocation; the database
  still does work proportional to the unread range while the authority lock is
  held.
- Forward destinations support a signed cursor with a maximum of 100 candidate
  inspections and 20 accepted results per request. Rejected candidates advance
  the cursor. Bindings include current account epoch, source membership,
  source message revision and search text. Current destination authority is
  checked again on every page and forward command.
- Message edit expansions have explicit per-message paging. Support reply and
  recovery can use compact receipts and avoid loading complete threads. Existing
  independently paged support messages/information/history/evidence remain.
- Private attachment authority moved from a view module to
  `services/attachment_access.py`, shared by bytes/search/transcription. The view
  retains its supported import. Existing decode/size, ready/attached/revoked,
  ownership, current-membership, no-store, attachment and nosniff rules remain.
- Removed `_notify_recipients`, `_broadcast_new_message` and the unrouted duplicate
  `GroupPreferencesAPIView` after checking production/task/registry/client
  references. Durable event/outbox registrations and routed preferences remain.
  No historical migration or rollout compatibility field was removed.

## Compatible opt-in contracts

Existing valid response bodies, URL names, authentication, permission/parser/throttle settings,
methods, status/error envelopes and complete legacy histories are preserved.
Invalid legacy scalar text now consistently fails typed validation with 400,
as required for REST/socket parity; valid legacy multipart text remains supported.
The route ledger reconciles 64 communication patterns and all 795 global patterns.
The 11 communication HTTP family fixture comparisons cover supported methods,
aliases, anonymous/tenant/staff boundaries and both release modes. They do not
constitute an exhaustive positive role/payload matrix.

| Surface | Explicit bounded form | Legacy default |
|---|---|---|
| Rich message history/context/lookup/starred/replay/search | `edits_page` and/or `edits_page_size`; default size 5, maximum 20; `edit_history_page` contains page/size/has_more | Complete `edit_history`; no additional metadata |
| Forward destinations | `bounded=true`, then returned signed `cursor`; `results`, `next_cursor`, `has_more`; an empty page can still have another cursor | Existing counted page-number response and complete candidate scan |
| Support GET | Existing `bounded=true` and independent relation page controls | Complete compatible thread/information histories |
| Support reply | `receipt=compact`; ticket identity/current revision/status and created `message_id`, no complete thread | Complete original ticket representation |
| Support creation/reply recovery | `receipt=compact`; existing outcome/key envelope with compact current ticket; reply recovery includes committed `message_id` | Complete current ticket representation |

Retain the compact/full reply choice with its original operation key. A reply
key cannot be reinterpreted as a different response command. Recovery reads
current ticket authority/state and does not replay a mutation. Paged detail
keeps older messages/evidence available. Internal notes remain staff-only.

Counterpart email remains the existing empty compatibility field, self-account
email remains authorized, and phone fields retain the disclosure policy. Direct
blocking/roommate withdrawal prevents new sends/live typing while preserving
legitimate historical reads under the existing policy. Sprint 09 does not
silently change that established historical-access contract.

## Validation and reproducibility

Final affected PostgreSQL gate: **724 passed, 2 skipped, 1 expected failure**
(727 cases), including indexed inbox selection, the 10,001-message history
regression and six explicit-membership/new-send/retry cases. Prior gates are
retained with their exact source phases in the machine record.
The two skips require authentic Android/iOS voice clips; the
expected failure is the intentionally locked company discussion audience
contract. Final HTTP fixture gate: **11 passed**. The eight send/receive session,
epoch and expiry boundary cases are included in the communication gate and also have
a standalone passing run. Focused post-correction inbox parity: **56 passed**;
latest send/retry/membership checks on SQLite: **56 passed, 1 PostgreSQL-only
skip**. Compact-receipt/prepared-inbox checks also passed (22 cases, one
PostgreSQL-only skip). These counts describe overlapping runs and must not be
summed as independent tests.

The machine-readable `validation.json`, JUnit XML, logs and metrics record actual
completed runs and distinguish intermediate runs from the final focused tree.
`route-coverage.json` is generated by `make sprint09-coverage`. Source import,
syntax, lint, formatting and migration checks are recorded separately. An
initial cleared-history parity failure was corrected with a viewer-scoped
subquery; its positive/negative regression is retained. Final review also
restored the original explicit-membership fence for null/empty/invalid values;
those values cannot become an omitted fence on a new send or retry.

Scratch root: `/private/tmp/sukoon-sprint09`. Every executed pytest used a custom
settings module pointing only at scratch SQLite or a newly initialized local
PostgreSQL 18 cluster. PostgreSQL uses its private Unix socket, port 55449 and
TCP disabled. Initial runs used its default lock capacity; the schema retry
uses `max_locks_per_transaction=1024` as described below. Independent runs use distinct `test_sprint09_*` database names.
No application environment file, existing database, production server, real
provider or deployment was used. Provider outcomes are simulated and test
network guards remain active. Four existing repository SQLite files are
SHA-256 checked before/after; see `database-preservation.json`.

Reproduce by making a fresh equivalent scratch settings module (example retained
as `scratch-settings.example.py`), initializing a new disposable PostgreSQL
cluster, and supplying its socket/user/database settings. Use distinct test names
for concurrent runs:

```sh
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  make test-sprint09-communication CYCLE_SETTINGS=<scratch_module> \
  BASELINE_OUT=<scratch-output>
make sprint09-coverage
DOTENV_DISABLED=1 make route-matrix
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  .venv/bin/python -m pytest core_apps/common/test_route_contracts.py \
  -k 'chat or notifications or support' --ds=<scratch_module>
```

The full MVP and restoration targets were also run with separate scratch test
settings and storage. Their exact outcomes are in `validation.json`; those
integrated runs started before the final prepared-inbox correction, so their
results are not described as final-tree whole-backend certification. The final
communication gate and retained parity tests cover the final affected code.

## Full baseline outcomes and scratch capacity

Both required integrated targets completed their 6,084-case collections:

| Run | Pytest result |
|---|---|
| MVP | 6,050 passed, 1 failed, 1 teardown error, 21 skipped, 12 expected failures |
| Restoration | 6,049 passed, 2 failed, 21 skipped, 12 expected failures |

Every failure/error above is PostgreSQL `out of shared memory` with the explicit
`max_locks_per_transaction` hint, while dropping synthetic migration schemas or
flushing the disposable test database. The affected cases are
`common/test_release_compatibility.py::test_coordinated_upgrade_preserves_previous_account_property_and_chat`,
`common/test_release_compatibility.py::test_local_unpublished_column_removal_can_be_repaired_without_history_loss`
(teardown), and
`features/tests/test_billing_migrations.py::test_billing_upgrade_preserves_paid_rent_receipt_and_ledger`.
No application behavior assertion accounts for these failures.

The scratch cluster was restarted with `max_locks_per_transaction=1024` for a
focused retry of all three cases in a fresh database. Its exact outcome is
recorded as `schema-capacity-retry` in `validation.json` and its own JUnit/log:
**all three passed** (171.78 s). This addresses every failure/error above on the
correctly sized disposable cluster.
The original full runs remain failed records; the entire integrated suite was
not repeated after changing scratch capacity. A green final-tree whole-backend
run therefore remains unaccepted. Use the increased scratch setting when
reproducing concurrent schema-heavy baselines; production configuration was not
read or changed. Pytest may count a passed call plus teardown error separately;
the machine record retains both JUnit case counts and terminal outcome counts.

## Measured budgets

Measurements are local synthetic probes, not production SLOs or device evidence.
Read the engine/run labels in `metrics.jsonl`; cold import overhead affects the
one-thread measurement. Assertion budgets live in tests.

| Probe | Measured result |
|---|---|
| Direct inbox, 1/20/100 conversations, moderation off | 17 queries at all three sizes (initial characterization: 24/385/1,905) |
| Group history, 1/30/100 messages | 13 queries at all three sizes |
| Rich events with polls/replies, 1/30/100 events | 16 queries at all three sizes |
| Edit-heavy history, 1/30/100 messages, 40 edits each, five selected edits | 13 queries, about 1.4/42/140 KB projection JSON |
| Read receipts, 10,000 unread messages, PostgreSQL | One statement, 0.27 s, about 21 KB traced Python allocation; original times survive retry |
| Compact support reply, 1/100/1,000 old messages | 14 queries; final receipt 254 rendered bytes independent of thread size |
| Compact reply recovery, 1/100/1,000 old messages | Three queries; final envelope 343 rendered bytes independent of thread size |
| Independently paged support information/history/evidence, 1/10/100 parents | 17 queries with selected nested limits |

## Unmet acceptance and limits

1. **Unconditional bounded responses conflict with preserved legacy contracts.**
   Full legacy edit histories, counted forwarding candidate scans, support
   thread/reply/recovery bodies remain data-dependent. Explicit bounded forms
   are implemented and tested; default truncation/removal requires a client
   contract migration. No universal hard payload/work cap is claimed for the
   compatible full modes. Group/moderation-enabled inboxes retain per-thread
   authority work; constant-query evidence applies to the prepared direct path.
2. **The entire command family is not one consolidated typed service.** Send has
   one typed transaction across transports; existing edit/delete/read/forward
   services remain shared with their established validation/receipt/locking
   rules. This is substantial reuse, not a claim that every command has been
   migrated to a single typed facade. Full consolidation and an exhaustive
   positive transport × role × revision × retry matrix remain unaccepted.
3. **Large read work is still proportional in PostgreSQL.** Database-side receipt
   insertion removes Python materialization and round-trip growth, and the
   10,000-row local bound passes. It does not prove a fixed lock/latency budget
   for an arbitrarily long unread history or deployed concurrent load.
4. **Native/provider/deployment evidence remains unavailable.** The two native
   Android/iOS voice-clip tests require supplied authentic clips and are skipped.
   Company discussions remain deliberately locked pending a verified per-message
   role audience (existing expected failure). No authentic FCM/moderation/
   transcription provider, device delivery or production runtime was tested.
5. **Opaque file policy still needs product sign-off from Sprint 02.** The
   implemented explicit private opaque-download contract and ready/scan rules
   are preserved; sign-off or a new allowlist/scanner product decision is not
   invented here. Direct historical access after blocking is also preserved as
   described above; a blanket denial of all historical bytes after every block
   would require an approved policy/contract change.

6. **No green final-tree whole-backend certification.** The full runs and their
   scratch lock-capacity failures are retained above. The focused communication
   gate passes, but does not replace a repeated final integrated run with the
   corrected scratch capacity.

These limits are recorded as unmet criteria, not silently marked complete.
