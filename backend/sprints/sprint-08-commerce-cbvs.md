# Sprint 08 — Commerce services independent of HTTP

**Scope:** billing, checkout, payments, refunds, payables/payouts, settlement, subscriptions, store/provider adapters,
advertising and shared Paymob callbacks. **Evidence:** A4 findings; financial stories in Sprints 01–04.

## Work

- Extract PayableEligibilityService and money command/read interfaces from rental view modules. Refund/settlement/
  provider-event services must not import `rental_phase4_views` to evaluate a domain invariant.
- Separate quote/prepare, claimed external submission, inquiry/proof, canonical accounting and user receipt/recovery.
  Preserve original-recipient and immutable-source identities, unknown-outcome reconciliation and sensitive approvals.
- Convert invoice/checkout/refund/settlement/payout/subscription/advertising route families to thin explicit classes.
  Preserve exact signed callback bytes and display-only return semantics; do not parse/re-encode before HMAC verification.
- Use purpose-aware prepared invoice/list read models and compact paginated financial projections. Remove creation and
  storage repair from document/advertising GETs through the explicit transition/backfill design.

## Acceptance

- All 73 direct decorated functions in the original commerce scope, plus the two ordinary provider callback/return views,
  are accounted for by the updated runtime inventory and appropriate explicit class adapters.
- Domain modules import no HTTP view modules. Money rules are testable independently of request objects/renderers.
- Capture/refund/payout/chargeback/order/retry/confirmed-proof repair matrices pass, including partial commission reversals
  and unsupported purchase-versus-rental inputs. Exact amounts/currency, ledger balance and authority are unchanged.
- New financial commands obey current revocation/roles/factors; original external-instruction reconciliation is preserved.
- List budgets cover mixed invoice purposes and long payout/refund/dispute histories; no per-row provider/storage work.
- Fake/staging/live gates remain explicit. Passing fake-provider tests is not recorded as real settlement/provider acceptance.
  Unsupported store adapters remain disabled until their authentic notification and current-state contracts are verified.
