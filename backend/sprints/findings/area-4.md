# Area 4 — commerce, billing, provider execution and advertising

> Audit notes and source evidence. The authoritative cross-domain sequence and finding-to-sprint assignment are in
> [the roadmap](../README.md) and [FINDINGS.md](../FINDINGS.md). Local suggested sprint numbers below describe phases,
> not an alternative implementation schedule. Companion scan manifests are summarized in [SOURCE_INVENTORY.md](../SOURCE_INVENTORY.md).


Read-only static review, 2026-11-08. Backend-relative evidence paths throughout. No application edits, imports of application code, tests, management commands, servers, providers, database access, network requests, environment secrets or media access. Only this report and reviewed-file manifest were written.

## Coverage and ownership

All 124 authoritative production files were read, including split parts, models, serializers, services, views and task wrappers; AST inspection covered the same full list (16,888 source lines). Additionally reviewed and owned: `core_apps/features/services/store_notifications.py` and `core_apps/features/services/fulfillment_cases.py`. Full manifest: `area-4-reviewed-files.txt` beside this report. Empty and docstring-only package files were inspected. Boundary context read: `providers.py`, `services/commands.py`, `services/company/tenancy_access.py` (relevant authority functions), `services/rental_lifecycle/locks.py`, `services/rental_lifecycle/provider_instructions.py`, `common/renderers.py`, selected non-secret settings declarations and tests for refund/history contracts. No existing `docs/health/area-4.md` found; this is an initial static baseline, not proof existing tests pass.

Measured architecture within the 124-file list: 73 DRF `@api_view` functions; 0 APIView/ViewSet/generic view subclasses; another 2 ordinary Django callback/return views in common/paymob_views.py. Longest inspected functions include execute_refund (219 lines), execute_settlement (176), prepare_settlement (172), invoice_payload (171), Paymob prepare (166), and verify_result (160). These are measurements, not a recommendation to split on an arbitrary line threshold. Stable public re-export modules retain many duplicated/unused imports, while domain services also import view modules for payable evaluation.

## Verified findings, prioritized

<a id="a4-01"></a>
### A4-01 — High / money correctness — partial refunds conflict with already-earned commission identity

Evidence: `core_apps/features/services/refunds_parts/execute_refund.py:96-118,165-174,214-229`; `core_apps/features/rental_phase4_views_parts/handover_respond.py:36-106`; `core_apps/features/services/rental_phase3_parts/issue_invoice.py:64-97`; hosted aftermath `core_apps/features/services/paymob_refunds.py:363-375`.

Trigger: first rent is captured and settled, move-in accepted and beneficiary ready, so evaluation creates immutable `commission-earned:{payable.id}`. Before owner payout, approve a partial rent refund. Example minor units: original rent 100000, commission 10000; refund rent 10000 reverses 1000 and changes payable commission to 9000. execute_refund then calls evaluate_owner_payables after marking the refund succeeded. With no other blockers, evaluation tries the same commission-earned source with 9000 instead of 10000; the ledger deliberately rejects it as financial_source_conflict. Mock execution rolls back. For hosted execution the provider refund proof has already been durably confirmed, so canonical refund accounting becomes accounting_pending. This is a code-path finding; enabled provider transports are sandbox/staging-gated, not evidence of a currently deployed live loss.

Sprint fix: preserve original commission recognition and post additive reversal/adjustment sources. Move payable evaluation into a domain service; ensure re-evaluation validates existing recognition without recomputing immutable historical entries from mutable payable totals. Acceptance: partial rent refund after recognition/before payout; rent/deposit split; repeated refunds and retries; full refund; refund before recognition and after payout. Assert balanced cumulative ledger, correct payable net/commission, exactly one external submission, and successful repair from confirmed provider proof.

<a id="a4-02"></a>
### A4-02 — Medium / authorization — personal payment readers and commands omit private-access revocation

Evidence: `core_apps/features/rental_phase3_views_parts/rent_invoice_quote.py:39-75` (_invoice/_attempt); `core_apps/features/services/company/tenancy_access.py:318-326` personal financial_read/can_pay; `core_apps/features/services/billing_invoices.py:27-85`; callers `rental_phase3_views_parts/rent_invoice_payments.py:15-29`, `owner_payables.py:135-172`. Contrast explicit deny checks in `rental_phase6_views_parts/final_settlement_propose.py:28-52`, `final_settlement_respond.py:119-143`, and company roles at tenancy_access.py:106-111.

Trigger: a personal lease participant receives PrivateAccessRevocation while their user remains active. Their personal financial_read/can_pay still returns true based solely on owner/tenant identity; history/detail and billing invoice routes retain access, and the tenant can quote/checkout while otherwise eligible. Company roles explicitly revoke access, so this is scoped to personal leases, not a company bypass. No cross-user access is asserted.

Sprint fix: agree and encode one revocation policy for private financial reads and new payment commands; apply it through central selectors, list filters and command authorization. If retained legally required receipts are intentional, expose a narrow retained-record projection explicitly rather than leaving the general private endpoints open. Acceptance: owner/tenant revocation across billing list/detail, payment list/detail/recovery, quote/checkout/resume, with company regression and original-instruction reconciliation behavior covered.

<a id="a4-03"></a>
### A4-03 — Medium / input validation and correctness — handover commands persist untyped input and return 500 for malformed revisions

Evidence: `core_apps/features/rental_phase4_views_parts/lease_handovers.py:43-101,124-148` directly calls int and assigns raw possession_on/condition/keys/meters/inventory; `handover_respond.py:132-139`, `rental_phase6_views_parts/disputes.py:127`, `rental_phase3_views_parts/rent_invoice_checkout.py:93-98` repeat unguarded conversion. `core_apps/common/renderers.py:34-45` maps unhandled ValueError/TypeError to generic 500.

Trigger: an authorized participant submits a nonnumeric expected_revision, null evidence_ids, or invalid date/shape in an otherwise complete handover request. int/len/model preparation errors bypass DRF validation; handover JSON structures also lack bounded per-field schema. These endpoints are authenticated and participant-checked; this is not anonymous code execution.

Sprint fix: typed command serializers with strict revisions (reject booleans), UUIDs, dates, bounded list/object/note fields and unknown-field policy; validate before idempotency/locks. Acceptance: malformed scalar/container/date/revision matrix returns stable 400 with no writes; valid legacy wire contracts remain compatible.

<a id="a4-04"></a>
### A4-04 — Medium / domain validation — rental refund endpoint crashes on a valid non-rental payment identity

Evidence: `core_apps/features/rental_phase6_views_parts/refund_requests.py:44-50` obtains PaymentAttempt without domain filter then dereferences `attempt.invoice.lease.id`; non-rental invoices deliberately have no lease (`billing_invoices.py:197-211` invoice construction).

Trigger: authenticated caller posts a known subscription/advertising/maintenance purchase attempt to refund-requests. AttributeError occurs before payer/domain validation and is converted to 500 by common/renderers.py:34-45. This does not grant a refund.

Sprint fix: select only eligible rental attempts under current user/lease authority and return defined 400/404 for unsupported purposes. Keep purchase refunds in their own adapter if implemented. Acceptance: own and other users' non-rental IDs, unknown IDs, malformed UUIDs and valid rental refund requests return expected status without writes or existence leakage.

<a id="a4-05"></a>
### A4-05 — Medium / query growth — billing invoice pagination still issues per-row relation and status queries

Evidence: `core_apps/features/billing_views.py:93-99,131-144` prefetches only lines, `services/billing_invoices.py:27-56` only joins lease/payer; `services/billing_projection.py:19-38,54-68,96-103,178-192,265-267`; `services/purchase_service_state.py:6-44` independently queries subscription/ad/promotion. Receipt provider relations, plans, fulfilled jobs/subscriptions, unresolved attempts and service state are resolved from each invoice.

Trigger/impact: a page of N purchase invoices causes at least receipt and unresolved-attempt queries per row, plus fulfillment/service/plan/provider work depending on purpose. The page is bounded to 100 but database round trips grow with its rows. No measured latency or fixed query count is claimed.

Sprint fix: purpose-aware page selectors with annotations/Exists, select_related fulfillment/case/subscription/organization, filtered Prefetch for receipt attempts/provider relations, batch plan/service maps, and pure projections accepting prepared context. Acceptance: mixed purpose pages at 5 vs 40 rows; assert bounded query budget independent of row count and identical permissions/actions/localized values.

<a id="a4-06"></a>
### A4-06 — Medium / scalability — personal finance lists are unbounded, with nested history N+1 work

Evidence: `core_apps/features/rental_phase3_views_parts/owner_payables.py:181-210`; `rental_phase4_views_parts/operations_execute_payout.py:32-44`; `rental_phase6_views_parts/refund_requests.py:24-42`; `rental_phase6_views_parts/disputes.py:25-46`. Payout projection `handover_respond.py:189-230` queries current instruction and audit history for each payout; refund projection `final_settlement_respond.py:99-116` invokes refundable components and per-refund history/instructions (`services/refund_notifications.py:111-142`).

Trigger/impact: long-lived owner/tenant accounts load their entire financial/refund/dispute history into one response, despite presenting next/previous=null. Per-row historical scans amplify query and response cost; disputes prefetch evidence but not lease/participants. Staff queues are paginated but reuse similarly expensive per-row projections.

Sprint fix: shared bounded pagination and stable ordering; separate list summaries from detail history; batch instructions/audit histories and refundable aggregate context. Acceptance: 5/40/large-history fixtures, maximum rows/response size, correct next-page contracts, no skipped/duplicated records, and bounded list-query budgets.

<a id="a4-07"></a>
### A4-07 — Medium / transaction bottleneck — payable evaluation repeats lease-wide work while financial locks are held

Evidence: `core_apps/features/rental_phase4_views_parts/handover_respond.py:36-106` loops locked payables, lazy loads each invoice, queries payment profile per payable, repeats lease.refund_requests.exists per payable, and resolves funding through `services/chargebacks/projection.py:143-187`. Called by settlement/capture/refund and payout paths, including operations_execute_payout.py:97-99; `services/rental_phase3_parts/process_provider_event.py:70-76`.

Trigger/impact: a lease with many billing periods or settlement-created payables repeats invariant queries and funding traversals for every row. These costs occur in the money transaction and prolong the shared property/lease lock, increasing contention for otherwise independent financial actions on that root. No real lock-wait benchmark run.

Sprint fix: domain PayableEligibilityService accepting locked root and batch-loaded payable/funding/profile/refund context; use set-based updates for unchanged status where audit/revision semantics permit, retaining immutable ledger guarantees (A4-01). Acceptance: query growth at 5/40 payables, concurrency on capture/refund/payout in disposable PostgreSQL, deterministic lock order and unchanged eligibility/recognition outcomes.

<a id="a4-08"></a>
### A4-08 — Medium / public endpoint bottleneck — advertising feed limits output, not candidate/remote-storage work

Evidence: `core_apps/advertising/views_parts/tenant_home_placement.py:110-139` iterates all matching ACTIVE rows until 20 eligible results; `services_parts/activate_with_mock_payment.py:123-154` runs PaymentFulfillment.exists for each non-mock candidate and validates destination/media; `services_parts/ensure_media_persisted.py:167-175` invokes storage.exists. Owner list additionally runs source_invoices per row at `views_parts/owner_advertisement_collection.py:68-69,120`, despite joins.

Trigger/impact: many active-but-ineligible rows (unavailable destination, missing storage object, or unresolved fulfillment) force public GET to scan many/all candidates and make per-row DB/storage calls. Fewer than 20 results does not bound that work. Storage backend and latency are deployment-dependent, unmeasured.

Sprint fix: annotate verified fulfillment, batch source links; persist verified media readiness through upload/processing/repair events, use bounded cursor windows/scan budget and indexed eligibility where possible. Keep authority checks current. Acceptance: large ineligible prefix with 20 valid successors; cap DB and storage calls, deterministic feed order, no serving missing/ineligible ads and clear refresh behavior.

<a id="a4-09"></a>
### A4-09 — Medium / production cleanup and read semantics — public advertising GET contains one-off fixture restoration and fabricated-artwork code

Evidence: `core_apps/advertising/services_parts/ensure_media_persisted.py:100-164` imports audit constants, reads/restores exact fixed-ID asset, deletes/saves storage data and updates media metadata; generic fallback generates a solid 600x300 image without updating digest/size/type. `media_is_available:171-173` and `views_parts/tenant_home_placement.py:174-175` call it for literal UUID `85295dd1-f8bd-4c82-a903-9bdc3d90af98`. `core_apps/advertising/audit_asset.py:6-30` binds recovery to a historical logo hash and workspace/bundled asset.

Trigger/impact: public media/feed eligibility GET for that historical fixture can mutate storage/database and replace uploaded artwork with repo assets. The generic generated-banner branch exists in production helper code but no general public caller was found; do not present it as all uploads silently replaced. This is concrete fixture leakage/unsafe repair semantics, not an arbitrary-file-write exploit.

Sprint fix: remove fixture ID/asset/generated-artwork branches from production request flow; isolate historical repair in an explicit audited maintenance command with verified source bytes. Missing content remains unavailable until repaired. Acceptance: all read endpoints are storage/DB side-effect free even with missing/corrupt fixture objects; hashes match persisted bytes after explicit repair; missing assets do not fabricate customer artwork.

<a id="a4-10"></a>
### A4-10 — Medium / architecture and requested migration — APIs remain FBVs and views own domain mutations

Evidence: 73 decorated FBVs and 0 API CBVs in complete owned-file AST inventory. `rental_phase3_views_parts/rent_invoice_checkout.py:32-187` orchestrates validation, locks, provider/session records and idempotency in a view; `rental_phase4_views_parts/operations_execute_payout.py:69-189` owns approval/reservation; `rental_phase6_views_parts/final_settlement_propose.py:99-210` owns proposal transition. `services/refunds_parts/execute_refund.py:226-229`, settlements_parts/execute_settlement.py:197-200 and rental_phase3_parts/process_provider_event.py:65 import domain evaluation from a view module. Re-export shims retain copied import lists.

Impact: current architecture does not meet the user's explicit CBV + service/helper target, and domain services depend back on HTTP modules, making authority/transaction changes difficult to reason about. FBVs alone are not a security defect and existing service-backed routes should not be mechanically split by filename/line count.

Sprint fix: first extract money command and eligibility services with selectors/pure projections; then migrate route families to thin APIViews/generics while preserving URL names, methods, auth/throttles/renderers, localized envelopes, sensitive approvals and replay semantics. Remove proven unused imports/re-export plumbing after caller audit. Acceptance: route/method/permission parity inventory, service modules free of view imports, money commands independently testable, no FBV APIs left in migrated families, provider gating and reconciliation tests preserved.

<a id="a4-11"></a>
### A4-11 — Medium / GET side effects and query growth — document catalog performs per-record creation on every read

Evidence: `core_apps/features/rental_phase6_views_parts/lease_reviews.py:53-94` GET creates contract/receipt/change RentalDocument rows with get_or_create, loops every historical receipt and signed/applied change, and then returns all documents; initial final settlement GET also creates a draft at `final_settlement_propose.py:86-98`.

Trigger/impact: opening document catalog first time performs writes from GET and assigns requested_by to reader; subsequent reads still run per-source lookups across history. Result set is unbounded. A read can create document jobs/records for company users before final document-type filtering (53-91), although returned types are filtered and no privilege bypass is asserted here.

Sprint fix: create durable document intents in originating signing/capture/change transitions or an explicit idempotent backfill; make catalog a paginated read selector. Represent absent settlement draft virtually or create it via a command. Acceptance: document GETs have zero writes, long histories remain bounded, contract/receipt/change jobs created exactly once by transitions, company commercial/financial document visibility remains intact.

## Checklist and positive guard evidence

| Check | Static assessment | Evidence / finding |
|---|---|---|
| Integer minor units/Decimal money | Pass with correctness exception | PaymentAttempt/Refund/Paymob models use integer minor units; refund proportions use Decimal; A4-01 |
| Durable capture/refund/payout identity | Substantial controls present | PaymobPayment order/transaction unique; PaymobRefund/Payout conditional current constraints; provider instruction records; no exactly-once runtime guarantee claimed |
| Provider signatures and callback authority | Pass for implemented static path | common/paymob.py signing order/type validation and compare_digest; common/paymob_views.py:14-72 verifies HMAC/integration/currency, persists then calls server inquiry; browser return display-only |
| Unknown outcomes/replay/order | Substantial controls present | paymob_payments checkout commits before HTTP; refunds claim and confirmed proof before accounting; payouts stage/claim, sealed original recipient and reference inquiries; out-of-order rental settled/open chargeback facts retained |
| Live/fake gates | Pass static, runtime configuration not inspected | providers.py:102-108 confines fake to development/test/staging; paymob_client credentials/checkout/refund enforce test keys plus non-production env; payouts host fixed staging plus evidence flags; no current live adapter demonstrated |
| Public fake webhook | Pass static | fake_payment_webhook checks fake_provider_available and HMAC; rejects Paymob-backed attempts in apply_fake_payment_event; no arbitrary public capture claim |
| Store notification authenticity | Pass architectural boundary, concrete adapter not checked | commerce_views.py:58-67 public POST delegates handle_notification; store_notifications.py:48-65 demands configured adapter.verify_notification and VerifiedStoreEvent; record checks account/environment/event ID/observation ordering; settings defaults COMMERCE_STORE_ADAPTERS={} so no public body-to-entitlement bypass found |
| Financial roles and sensitive confirmation | Substantial controls present | financial_authority current role/factor/freeze; refund/payout sensitive_actions.consume; queued dispatch rechecks authorization_context; original reconciliation can continue after authorization changes |
| Recipient retention/privacy | Pass static | paymob_payout_targets seals recipient with digest; process unseals original and proof validates original account/amount; payout account binding; beneficiary input separate from verified readiness |
| Personal revocation | Fail | A4-02 |
| Upload validation | Partial | ad bytes limited 10MiB, PIL verification/decompression warning rejection and format allowlist; private evidence upload uses common private_media_policy.inspect with bounded read, remains pending; worker scanning/storage lifecycle outside owned boundary |
| Input and unsupported domains | Fail | A4-03/A4-04 |
| Query growth/list bounds | Fail | A4-05/A4-06/A4-07/A4-08/A4-11 |
| Requested CBV/service architecture | Fail target, not security conclusion | A4-10 |
| Dummy/one-off code removal | Fail | A4-09; mock providers themselves intentionally gated and not simply dead code |

## Unverified candidates / limits

- Advertising property_is_publishable uses owner active plus status VERIFIED, unlike some property/promotion predicates also checking is_verified. Area 2 should determine whether canonical publication requires both fields or additional moderation flags; no confirmed advertising moderation bypass asserted.
- Settlement deposit application computes commission with amount//10 on sequence 1 (settlements_parts/execute_settlement.py:132-136), while capture explicitly excludes continuous renewal commission (capture_attempt.py:102-121). A reachable renewal deposit-funded settlement scenario was not fully traced; candidate only, not a verified overcharge.
- Store event correctness depends on configured adapter authenticating source/bundle/package/environment and returning trusted current state. No production concrete adapter found in inspected commerce routes; defaults are disabled. Future live enablement needs independent provider contract acceptance, renewal/revocation/overlap proof and tests; no currently reachable forged-store entitlement finding.
- Paymob chargeback/reversal snapshots deliberately route to manual review; ordinary fake event endpoint refuses Paymob-backed attempts. Unsupported Paymob excess-refund/chargeback automation must not be described as a public live exploit.
- Concurrency reasoning is from locks/constraints/control flow only. No PostgreSQL race, SQLite behavior, measured SQL count, storage/network latency, deployed configuration, current provider contract, migration state or passing-test assertion was established. Proposed acceptance tests are future sprint work, not tests run in this review.
- Individual shared-housing/company lifecycle, private-media scanner implementation, staff administration and deployment are other areas. Relevant boundary calls were checked, not comprehensively re-audited.
