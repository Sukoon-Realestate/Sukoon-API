# Canonical rental chargeback resolution

Inspection and implementation date: 2026-10-19. This backend change applies to personal and company leases through the existing invoice, payment, ledger, refund, payable, case and company-budget records. Provider events and money movements in the executed checks were synthetic and local. These checks do not establish real provider execution. A later guarded live preparation applied additive migration 0060; canonical hashes for 10 leases, two invoices and empty payment/payable/company-tenancy sets remained unchanged. Application deployment is verified separately; no historical data was rewritten.

## Problem and resulting behavior

Previously, `payment.chargeback` permanently blocked closure through historical `PaymentAttempt.payment_status=chargedback`, even after a provider dispute could finish. It also changed paid or in-flight owner payables to `held`; later recalculation could make them eligible again. There was no canonical final-decision/restored-cash path. Reusing ordinary capture for replacement payment would allocate the original owner obligation a second time.

The original payment remains `chargedback` as historical evidence. `RentalChargeback` now owns its reconciliation, independently of the provider's final decision, actual restored funds, a replacement capture and its settlement, and any excess owed back to the payer. Closure and payout eligibility use those obligations. Existing unrelated invoice, refund, deposit, possession and settlement requirements still apply.

## Records and invariants

| Record | Responsibility |
| --- | --- |
| `RentalChargeback` | One supported full-amount episode per original payment; immutable original payment/event/provider/dispute/amount/currency/exponent and opening snapshot. `outcome` is `open`, `won`, `lost` or `reversed`. `resolved_at` is set only when canonical blockers clear. |
| `ChargebackRestoration` | Authenticated cash receipt, separate from the outcome. Stores exact cash reference, invoice contribution, earlier-refund overlap, excess and component attribution. |
| `ChargebackReplacementPayment` | Links a new capture to the original allocation. Records its funded contribution and excess, without creating another owner payable, commission or deposit collection. |
| `RefundRequest(purpose="chargeback_excess")` | Exact independently reviewed obligation to return evidenced excess; references the actual restoration or replacement source. |
| Existing ledger and operational case | Original debit, reopened invoice receivable, actual funding and exact return remain traceable. A case note cannot satisfy missing financial evidence. |

Migration `features.0060_canonical_chargeback_resolution` creates only the three new canonical tables and constraints. Provider/dispute identity and provider/cash reference are unique. It does not rewrite historical payments or payouts. Original source fields reject mutation through model saves; all new history admin pages are read-only.

All amounts are integer minor units in the original payment currency and exponent. No fee, write-off, forgiveness, chargeback penalty, new debt allocation or exceptional financial policy is introduced. Replacement funding reuses the original invoice's rent/deposit allocation and existing commission rounding.

The shared lock order begins with the current actor for operator commands, then current finance profile, company/property financial roots, lease, and the original payment/event or refund. Database uniqueness and the existing operation receipt protect duplicated effects. Company membership and independence are checked again after the company root is locked.

## Provider event contract

The existing payment webhook dispatches the new events. Its implemented ingress is the explicitly enabled, signed non-production fake provider at `/api/v1/features/v1/provider-webhooks/payments/`. It returns 404 when that adapter is unavailable. A production adapter must authenticate and map real provider facts; operators cannot submit provider decisions or received-cash facts through the new review endpoint.

Every event retains `event_id`, `payment_attempt_id`, `type`, `currency`, and integer `amount_minor`. Existing event identity/digest checks reject changed content under the same event ID.

| Event | Additional input | Canonical effect |
| --- | --- | --- |
| `payment.chargeback` | Optional `dispute_id`; otherwise the first opening event ID is the canonical dispute ID. Amount must equal the full original capture. | Preserve the original debit and snapshot, reopen only the remaining original invoice contribution, hold eligible unpaid payables, retain paid/submitted/processing/cancelled payout facts. |
| Duplicate `payment.chargeback` | Same original event, or explicit original `dispute_id` on another delivery. | No duplicate invoice, ledger or payable change. A new unidentified or different episode is rejected. |
| `payment.chargeback.decided` | Exact `chargeback_event_id` of the original opening event; optional matching `dispute_id`; `outcome` of `won`, `lost` or `reversed`; full original amount. | Record the final decision only. Conflicting final outcomes are rejected. Winning is not a cash acknowledgment. |
| `payment.chargeback.restored` | Exact original `chargeback_event_id`; optional matching `dispute_id`; `funds_status="received"`; nonempty `cash_reference`; positive amount within remaining original disputed amount. | Record actual receipt, satisfy earlier-refund overlap first, apply only the remaining original invoice contribution, and create an exact excess refund where necessary. |

Partial cash-restoration receipts are supported within the single full dispute. Partial disputes, a second dispute episode on the same payment, and a chargeback of a replacement capture are explicitly unsupported. They are rejected rather than collapsed into the original episode. Currency mismatch and malformed outcome/cash evidence are rejected before waiting for an opening event.

A valid final/cash event arriving before its opening stays unprocessed. Processing the exact opening replays its matching facts. Rejected later facts remain available as source evidence and cannot roll back an authenticated opening debit. The original capture's missing settlement remains a separate blocker; late original settlement can be recorded without rewriting its `chargedback` history.

## End-to-end paths

1. **Opening:** the authenticated provider event locks the original financial roots and payment. The remaining invoice contribution is reopened once. A finance case is created. Historical payout state and physical inventory remain unchanged. The payer sees the reopened original invoice; authorized company commercial participants see the chargeback summary. Employees do not receive commercial chargeback details.
2. **Won or reversed, cash missing:** the final provider decision is recorded, but the invoice, original funding requirement and case remain unresolved. An operator cannot mark cash received by entering a case note or approving an unrelated refund.
3. **Won or reversed, funds restored:** the exact receipt funds the original invoice once. When settlement and all chargeback obligations are satisfied, `resolved` becomes true. Existing financial-closure rules decide whether the whole lease can close. Original paid/in-flight payout facts are preserved.
4. **Lost, replacement required:** the currently authorized payer opens the existing invoice quote and checkout. The quote is capped to the exact remaining original contribution, and discloses any ordinary invoice debt that will remain afterwards. Capture credits the reopened receivable without a second owner/deposit/commission allocation. It remains unresolved until settlement is acknowledged. No employee is made the company debtor or payer by this path.
5. **Replacement and restoration both arrive:** either ordering is serialized. Only the remaining original contribution is applied. Excess becomes an exact refund obligation and blocks chargeback closure. Neither an overpaid invoice nor a second payable is created.
6. **Excess review and return:** an independent current financial approver/refund operator approves the exact source-bound refund. The existing protected refund execution command requires its normal sensitive-action proof and provider instruction. Only confirmed execution records returned funds and clears that obligation. Provider absence leaves the approved obligation visible and unexecuted.
7. **Ordinary refund after reconciliation:** existing refund component, commission, owner-recovery and invoice rules apply to the original allocation even if cash came from replacement. Returned replacement funds are deducted from retained funding. A full payment reversal can leave ordinary invoice debt; resolving the old provider dispute does not forgive it. Pending replacement refunds also reserve the original payable at payout dispatch.
8. **Chargeback after company closure:** the same original company budget exposure reopens. Proven restoration or a settled replacement can close the financial obligation again when other closure requirements are satisfied. No new inventory allocation or additional tenancy is created.

Earlier successful refunds are frozen in the opening snapshot. Their overlap with a full provider debit requires actual provider restoration, rather than a second charge to the payer. New checkout is unavailable while that overlap remains unresolved; a capture already in flight is retained as refundable excess. Once actual restoration covers the overlap, the remaining original contribution can be quoted and settled as replacement funding, including after a final `lost` result. Ordinary debt created by the earlier payment reversal remains a separate disclosed invoice balance and uses ordinary checkout after reconciliation. This does not charge the overlap again or require an unnecessary excess-refund roundtrip. A historical `chargedback` attempt without canonical original evidence remains explicitly blocked for reconciliation; the additive migration fabricates no evidence.

The quote's optional `chargeback_replacement` object contains `chargeback_id`, `currency`, `exponent`, `quote_total_minor`, `original_funding_minor`, `excess_refund_minor` and `remaining_invoice_minor`. The final field means invoice debt remaining **after** the proposed original-funding contribution. New capped quotes normally have zero excess; a later provider event may still change the actual funding outcome. Checkout revalidates the current bounded amount as well as the invoice revision, quote expiry and current payer authority.

## Operator authority, actions and privacy

`GET /api/v1/features/v1/operator/chargebacks/{id}/` requires a current active finance reviewer role: `financial_approver`, `refund_operator` or `psp_reconciliation` (or the existing superuser rule). Frozen actors are refused. The landlord, personal tenant and any member of the lease's company are excluded from independent review, including an otherwise privileged actor. Ordinary users are denied before resource lookup. Company tenancy/payment projections continue to use their existing relationship-based read rules.

`POST` to the same endpoint accepts only:

```json
{
  "request_key": "a UUID for this logical approval",
  "expected_revision": 4,
  "action": "approve_excess_refund",
  "refund_id": "the exact excess refund UUID",
  "reason": "Independent evidence review, at most 2000 characters"
}
```

Only `financial_approver` or `refund_operator` may approve. Current authority and independence are enforced before receipt replay; role revocation cannot be bypassed by replaying an old successful request. Stale revisions and changed input under an old key are rejected. The serializer normalizes validated numeric revisions consistently for API and admin calls. The action changes approval state and records audit/receipt; it does not execute a refund or record provider facts.

Django admin exposes the canonical chargeback list and its **Inspect original evidence** review form. The three new model changelists and object views require current finance authority and exclude personally/company-conflicted records. Merely granting Django model-view permission is insufficient. The review form approves only a requested exact excess refund. Ordinary support resolution cannot bypass the canonical chargeback guard. The existing refund execution API retains its step-up requirement; this admin form has no money-execution shortcut.

## Read projection

The existing payment, finance case and authorized company-tenancy projections include:

| Field | Meaning |
| --- | --- |
| `resolved`, `resolved_at` | Explicit canonical chargeback resolution and timestamp/null. This is not complete tenancy closure. |
| `provider_outcome` | Historical provider decision; it does not prove cash receipt. |
| `amount_minor`, `currency`, `exponent` | Original dispute amount and scale. |
| `invoice_reopened_minor` | Original remaining contribution reopened at dispute entry. |
| `funds_restored_minor` | Sum of authenticated restoration receipts. |
| `replacement_captured_minor`, `replacement_settled_minor` | Original contribution funded by replacement; capture and settlement remain separate. |
| `retained_original_funding_minor` | Applied restoration plus settled replacement, less successful ordinary refunds of that allocation. |
| `original_allocation_released_by_refund_minor` | Existing allocations released by later successful ordinary refunds. |
| `remaining_funding_minor` | Required original funding minus retained funding, floored at zero. Zero does not satisfy missing provider decisions, settlement, restoration evidence or excess returns. |
| `excess_refund_remaining_minor`, `excess_refunds` | Exact remaining return obligation and source-bound refund IDs/states/amounts. |
| `blocking_reasons` | Current chargeback waits. Clients must not infer resolution from missing fields or an empty default list. |

The source payment ID, chargeback ID and revision are included. Private opening snapshots and raw provider payloads are not added to ordinary company/member projections. Each new canonical chargeback fact advances the lease revision so company notification identities can distinguish later outcomes and restored funds. Existing generic planning notifications lead to reauthorized tenancy/case reads. Notification delivery is not completion evidence.

## Verification and limits

### Follow-up: deposit-derived payables and current operator authority

An independently derived regression found that a settlement-created payable has no direct `payment_attempt`, so checking only directly linked payments left its original deposit funding unchecked. The local before-fix sequence reproduced three unsafe outcomes: payout reservation, execution of an already queued payout, and manual payout reconciliation after a chargeback of the deposit source. These were isolated synthetic operations, not observed production losses.

The payout evaluator and final provider-instruction validator now resolve a settlement payable through its canonical deposit agreement/invoice. Every captured or charged-back source must have reconciled funding. Missing source evidence blocks dispatch. Pending refunds against either an original source or its replacement also reserve that funding. Existing submitted, processing and paid history is retained. The payout worker uses the shared company/property/lease lock order. Manual reconciliation revalidates the financial operator inside the transaction as well as at entry, so a revoked role cannot use a request admitted before revocation.

The four deposit-funding regressions passed after repair. An additional deterministic authority-revocation check and adjacent phase-four/settlement checks passed in a 15-test focused run. The combined 58-test financial run then passed 57 and exposed one stale wording assertion: the blocking reason needed to identify the chargeback rather than only say the source was unreconciled. After correcting that explanation, the one affected test passed on rerun. These are distinct retained runs, not a claim that the first combined run was entirely green. Their private artifacts are `chargeback-derived-after.xml`, `chargeback-derived-regressions.xml`, `chargeback-financial-final.xml` and `chargeback-specific-reason.xml` in the `2026-10-19-company-complete-controls` QA directory.

The additional source is [deposit-derived payout and authority regression coverage](../backend/core_apps/features/tests/test_chargeback_deposit_payable.py). No historical deposit, payout, financial policy or production record was rewritten. Schema migration 0060 was applied only to the isolated native database in this recheck. Deployed coverage remains a separate step.

The focused local run completed **43 PostgreSQL tests**. It includes an actual threaded capture/restoration race, HMAC-authenticated webhook routing, incorrect signatures, duplicate event content, provider-disabled rejection, immutable source facts, exact replay/stale revision/current authority, all three admin history surfaces, refund/payout reservation, original payout history, both closed-company resolution branches, the prior-refund-overlap/lost/replacement path, and adjacent original quote/checkout/refund/closure regressions. No test failed or skipped. Follow-up inspection also checks that a reconciliation-only admin can read the case without being offered an approval control.

Retained JUnit artifacts are under the private local QA directory `2026-10-19-policy-configuration`: `chargeback-final.xml`, `chargeback-admin-final.xml`, and `chargeback-company-final.xml`. The test settings use the dedicated PostgreSQL database `test_sokoun_chargeback_resolution_20261019`, separate from the native API's database. Django system checks, feature migration drift against that isolated database, scoped Black/Flake8 and whitespace checks were also executed.

Focused test sources:

- [Canonical chargeback and admin/ingress/race checks](../backend/core_apps/features/tests/test_chargeback_resolution.py).
- [Company budget, commercial privacy and closure](../backend/core_apps/features/tests/test_chargeback_company.py).
- [Existing provider ordering and unsigned-event checks](../backend/core_apps/features/tests/test_rental_lifecycle_safety.py).
- [Existing combined-invoice refund regressions](../backend/core_apps/features/tests/test_combined_invoice_refunds.py).
- [Existing phase-six closure/refund regressions](../backend/core_apps/features/tests/test_rental_phase6.py).

Implementation entry points are [provider event processing](../backend/core_apps/features/services/rental_phase3_parts/process_provider_event.py), [canonical chargeback services](../backend/core_apps/features/services/chargebacks/), [operator API](../backend/core_apps/features/chargeback_views.py), [guarded admin](../backend/core_apps/features/chargeback_admin.py), and [migration 0060](../backend/core_apps/features/migrations/0060_canonical_chargeback_resolution.py).

Live provider authentication, real bank acknowledgments, real collection/refund execution and historical-data reconciliation remain separate evidence boundaries. A final `lost` outcome without actual replacement funding stays unresolved; this code invents neither collection nor forgiveness. An unavailable external adapter remains unavailable. No claim is made that this bounded chargeback change covers partial disputes, repeat dispute episodes, every financial exception or the entire product.
