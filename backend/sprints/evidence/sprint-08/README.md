# Sprint 08 — commerce classes, domain commands and prepared reads

**Recorded 2026-11-14. Overall acceptance: partial; stop after Sprint 08.**
No deployment, real provider transaction, existing database migration/reset/repair, dependency change or model migration
is included. Validation uses a newly initialized PostgreSQL 18.6 cluster on a private Unix socket under task-owned scratch
storage, with `.env` loading disabled and synthetic test settings. Existing database fingerprints are recorded separately.

All **73 original commerce decorated functions** are reconciled against source at audit commit `785dfc1d` by
[original-commerce-functions.json](original-commerce-functions.json). Twenty-one had already been converted with shared
housing workflows. This sprint converts the remaining 52 plus 16 explicitly deferred provider/catalog functions, and
both ordinary Paymob webhook/return views. The expanded scope has **93 route patterns**, including an existing dispute
alias. All resolve to explicit classes. The **795 global patterns** retain paths, names, aliases, declared authentication,
permissions, parsers, throttles and release availability. Ordinary callbacks now declare their original GET/POST methods;
their unsupported-method, signature and cache behavior is covered separately. See [route coverage](route-coverage.json),
[scope before conversion](routes-before.json) and [global baseline](global-contract-before.json).

## Implementation and compatibility

- `money_access`, `money_projection`, `money_result`, `rental_payment_commands`, `payout_commands`, `refund_commands` and
  `settlement_commands` expose actor/claims/body/proof interfaces for major money transitions. They preserve original root
  locks, idempotency fingerprints, receipts, amounts, ledger identities and replay behavior. Rental quote/checkout and
  settlement commands also recheck original session claims after taking their locks.
- Sensitive proof consumption has an explicit `consume_for_actor` interface. The existing request-based identity wrapper
  delegates to the same implementation, retaining current session, factor, freeze, action/resource/revision/payload and
  single-use proof checks. Finance roles and reconciliation continue to distinguish new instructions from original outcomes.
- Fake payment/rental events, signature application, shared timeline notifications and promotion operation receipts no
  longer import HTTP modules for those domain transitions. Existing callable/facade imports remain supported. Payable
  eligibility was already extracted in Sprint 03 and remains the shared domain invariant; immutable recognition and additive
  commission reversals were retained. No claim is made that its entire large-lease query/lock budget is now bounded.
- Verified Paymob callback intake is separate from HTTP response handling. The Django adapters retain original body parsing,
  signature-field ordering/verification, duplicate handling and cache/CSRF behavior. Store notifications still pass the exact
  body bytes to their configured authenticator. Browser returns remain display-only; they cannot confirm payment or grant
  fulfillment. Provider inquiry, claimed submission, durable confirmed proof and canonical accounting stay in their existing
  services. No provider key, adapter enablement, environment gate or sealed original-recipient identity changed.
- Billing pages prepare receipt identity and unresolved status with correlated queries, join fulfillment/case/organization
  facts, and batch plans, store products and purpose-specific service state **after paging**. Long payment histories are not
  prefetched. Prepared facts are per-read instances; commands continue checking current authority independently.
- Personal payables, payouts, refunds and disputes support **`projection=compact_v1`**, using the existing 20-row/default,
  100-row/maximum pagination policy, stable ordering, public UUIDs and summaries without nested histories. Only projected
  fields are selected. Existing default collections and detail histories retain their wire contracts. This is an explicit
  opt-in client transition, not completed performance acceptance for existing full-history clients.
- Document catalog GETs and virtual absent settlement drafts retain the earlier transition-intent/read-only design.
  Advertising GETs no longer restore a hard-coded fixture or fabricate artwork. Missing files remain unavailable. The
  `restore_advertising_media <advertisement_uuid> <original_file>` command verifies exact stored length and SHA-256,
  defaults to dry run, requires `--apply` to write, refuses existing destinations and leaves metadata unchanged. It was
  exercised only with synthetic data. A repair requiring metadata correction or replacement of an existing corrupt object
  still requires separate explicit operator review; GET never performs it.

The intended missing-artwork behavior change is explicit: a missing historical advertisement can no longer become available
by reading it or starting mock payment. Media remains 404 and invoice preparation can conflict until original bytes are
explicitly recovered. Valid stored artwork, successful checkout, response envelopes/localization, original receipts and
all existing default list/detail response shapes retain their contracts.

## Validation

[Machine-readable results](validation-results.json) separate initial characterization, integrated regressions and final gates.
Counts overlap and must not be summed.

- **1,536 frozen characterizations per release mode / 3,072 comparisons** exercise synthetic anonymous/account requests,
  English/Arabic, declared methods, OPTIONS, HEAD, unsupported methods, errors and privacy/cache headers. The generated
  profile identity is seeded to the original synthetic UUID; response fields are not discarded to obtain parity. These are
  boundary contracts, not an exhaustive positive resource/role matrix.
- **Integrated feature/advertising/common/identity run:** 4,084 passed, four characterization/seam/harness failures,
  13 skips and 11 expected failures. All four failed cases pass in the final 20-case correction gate; the full run was
  not repeated on the final tree. The skips/expected failures retain existing optional/native/deferred/recovery limits.
- **Final affected commerce gate: 342 passed**, no failures/errors/skips. Includes capture/order/inquiry, callback signature
  and display-only returns, refund/payout proof recovery and retry, original-recipient/authority checks, chargeback-derived
  payables, partial commission reversals, unsupported rental-versus-purchase inputs, subscription sandbox gates, existing
  billing contracts, fake provider/signature application and advertising tests. This run precedes the last compact
  reader field/UUID refinement; that final refinement is covered by the final correction gate.
- Prepared non-organization purchase invoice pages at **5 and 40 rows**, across web/iOS/Android and seven invoice purposes:
  **at most seven SQL queries for preparation; zero during projection**, with complete Arabic projection equality to the
  unprepared reader. These fixtures include captured/failed attempts and missing service records; they do not certify every
  rental, organization, entitlement or store-history combination.
- Compact payout/refund/dispute probes exercise **5/40 records with 40 historical entries/responses per record** and an
  explicit pagination/legacy-shape check. The final read gate passed **15 tests**, and the final combined correction
  gate passed **20 tests**, including public UUIDs and deferred dispute histories.
- Static/configuration checks: Django checks, no migration drift, project module imports, syntax parsing, scoped F-code lint,
  route reconciliation and whitespace checks: **2,197 Python files parsed; 2,030 project modules imported**, no
  migration drift or F-code diagnostics. All four existing SQLite file fingerprints are unchanged; see
  [database preservation](database-preservation.json).

The early focused run found an obsolete advertising auto-repair expectation and an approval-verification mock at the old
request interface. Tests now require explicit original-byte recovery and intercept `consume_for_actor` while retaining
proof-denial/replay assertions. The chargeback role-revocation injection now targets the extracted payout command seam,
retaining its 403/no-instruction/no-ledger assertions. Frozen transport profile UUIDs are explicitly seeded. New read-fixture
field mistakes were corrected before recording the final read gate. These corrections are test/interface maintenance,
not relaxed money or authority assertions. The general route-contract harness also retains its original rejected
GET/POST cases for the two Django callbacks after their runtime method declarations became explicit; the stored
`api-payments` fixture was not regenerated or weakened.

Reproduce route reconciliation with `DOTENV_DISABLED=1 make sprint08-coverage`. Run the integrated target with
`DOTENV_DISABLED=1 make test-sprint08-commerce CYCLE_SETTINGS=<isolated_settings> BASELINE_OUT=<scratch_directory>`.
The settings must explicitly select a new disposable database, fake providers, local caches and scratch storage; never
use the repository's existing databases or deployed settings. The task-owned cluster is stopped after validation. Raw
logs, XML, settings and initialization evidence remain under `/private/tmp/sukoon-sprint08/`.

## Unmet acceptance criteria

1. **Complete thin-service architecture:** explicit classes cover the full original inventory, but some beneficiary/onboarding,
   mock provider, checkout recovery, and shared evidence/dispute/document methods still orchestrate workflows or pass request
   context into existing services/projections. The route ledger flags **15 methods** with write/transaction signals; signals
   include harmless dictionary updates and read locks, and are review pointers rather than an exhaustive state-machine count.
   The new major money modules have no HTTP-view/request/renderer dependency; this is not a whole-backend independence claim.
2. **Complete performance acceptance:** current rental/company billing authority branches, payable funding/recognition under
   lock, default legacy finance histories, staff review histories, and advertising candidate/storage checks retain unbounded
   or per-row work. Compact personal summaries and sampled prepared purchase pages are measured; endpoint-wide query,
   heap, payload, contention and latency budgets are not certified. Changing existing default collections requires a client
   pagination transition to preserve behavior.
3. **Exhaustive positive and concurrency parity:** existing PostgreSQL races and focused accounting/authority suites pass in
   the final affected gate, but every route × role × payload × revision × provider outcome × retry interleaving has not been
   independently enumerated. Broad integrated outcomes and final-tree focused results are distinguished in the validation
   JSON. This report is not an assertion of a green final-tree whole-backend run.
4. **Authentic provider/production acceptance:** all external outcomes here are simulated. Fake-provider passes do not prove
   real settlement, PSP timing, storage availability, deployed behavior or production load. Unsupported native-store adapters
   remain disabled by default until authentic notification/current-state contracts are independently verified. No production,
   real provider, live funds, deployment or later sprint work is included.
