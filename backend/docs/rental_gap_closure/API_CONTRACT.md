# Rental lifecycle additive API contract

Base: `/api/v1/features/v1/`. Authentication and object relationships are required. Bodies are JSON. The [OpenAPI slice](openapi.json) is generated from the strict request serializers; [django_contract.json](django_contract.json) contains actual synthetic test HTTP responses. Existing rental routes continue to use their existing contracts.

## Wire shape and command recovery

Every success/error has exactly `message` and `data`; there is no new `key/msg` envelope. Errors preserve status and `X-App-Error-Code`; `X-Correlation-ID` identifies server diagnostics. Feature responses set `Cache-Control: private, no-store` and `Pragma: no-cache`.

A mutation receives a UUID `request_key` and integer `expected_revision`. New profile/hold/group records use revision 0; commands on existing records use the last fresh revision. Freezing/sharing uses the current profile/version revision. Case creation uses the agreement revision. A confirmation/fact upsert uses its own confirmation/fact revision, not the property revision; `inventory_revision` independently guards selection topology.

```json
{
  "message": "...localized server message...",
  "data": {
    "resource": {"id": "resource-uuid", "revision": 2},
    "operation_receipt": {
      "id": "receipt-uuid", "subject_id": "resource-uuid",
      "request_key": "request-uuid", "revision": 2, "status": "confirmed"
    }
  }
}
```

The resource/receipt placeholders above describe shape, not valid UUID values. See the exported fixture for actual examples. Same actor/operation/key and identical payload replays the original receipt. Changed payload gives 409. Authorization is rechecked before replay. After timeout, use existing `GET rental-operations/{request_key}/?subject_id={original_subject}`; retain the original key until the outcome is known. Read the fresh resource after recovery before another decision. Sharing or revocation never relies on a cached receipt as current permission.

Lists return `data: [...]`; pagination uses `X-Page`, `X-Per-Page`, `X-Total-Count`, `X-Total-Pages`, and optional `X-Next-Page` / `X-Previous-Page`. Default page size 20, maximum 100. No new pagination controller is required in Flutter.

## Routes and authority

| Family | Routes | Fresh authorization / inputs |
|---|---|---|
| Application | `application-profile/` GET/PATCH; `application-profile/versions/` POST; `versions/{id}/` GET | Applicant only. Preferences: desired_start, months, occupants, introduction. Frozen snapshots remain immutable when the profile changes. |
| Sharing | `application-shares/preview/` POST; `application-shares/` GET/POST; `{id}/` GET; `{id}/revoke/` POST | Owner name/ID, property, categories, UTC expiry and exact consent digest reviewed before creation. Categories are rental_preferences and/or introduction. Applicant lists own grants; recipient reads only a current grant for their currently owned property. No KYC document payload. |
| Decision | `properties/{id}/decision-summary/` GET with offer_id/offer_revision and optional paired start/end dates | Authorized owner or verified public property. Exact-selection costs/facts, distinct claims, confirmation revision, unknowns. Unknown cost amount is null. This projection does not create an invoice. |
| Owner facts | `properties/{id}/decision-facts/` POST | Owner; owner_reported/estimated/unknown or exact current staff claim for verified wording. Fact code and offer scope are validated. |
| Availability | `properties/{id}/availability-confirmation/` POST | Owner, current inventory revision and current confirmation revision. |
| Allocation | `reservation-holds/` GET/POST, `{id}/` GET, `{id}/extend/`, `{id}/release/`; `availability-blocks/` GET/POST | Free tenant hold requires accepted proposal, exact terms digest/revision/dates and availability confirmation. External/operational block requires owner and reason. All writes lock the property and allocate canonical units. No charge is created. |
| Deal | `deals/{subject_id}/` GET; `owner-application-queue/` GET | Existing participant/owner relationship. Projection links existing records; no mutation endpoint for a deal status. |
| Cases | `rental-cases/` or `move-in-cases/` GET/POST; `rental-cases/{id}/` GET; `{id}/actions/` POST | Participants see their case/agreement/hold; staff see assigned role's team scope. Evidence must be the actor's clean, undeleted evidence from that agreement. reply is participant-safe; assign/triage/reopen/resolve require operations role; link_remedy requires finance role. |
| Operations | `operations/rental-cases/`; `operations/rental-cases/{id}/actions/`; `operations/verification-claims/`; claim revoke | Explicit staff role required. Cases do not grant refund/payout execution permissions. Claim identity requires approved KYC; property scope requires approved current property review. |
| Group booking | `group-booking-proposals/` GET/POST; `{id}/` GET; submit/consents/withdraw POST | Owner creates from a current group application. Only independent room/bed/room-group allocations, common period, distinct units, active roster and per-person terms. Consent is actor-specific and revision/digest bound. No automatic lease/signature/payment. |
| Answer conversion | `terms-proposals/{id}/propose-answer/` POST | Owner chooses included_services or excluded_services and wording. Optional source_message_id must be their own undeleted direct message with the applicant. Clears old consent, preserves prior terms, releases unconsumed free holds and revokes unconsumed invitations. |

Existing rental-interest commands now accept optional `application_share_id` on creation and `request_information`, `provide_information`, `mark_under_review`, `withdraw` on response. Existing proposal/signature/invitation provenance checks remain required. Generic chat text has no legal side effect.

## Conflicts and explicit uncertainty

Typical 409 codes: `stale_revision`, `document_changed`, `offer_changed`, `offer_unavailable`, `inventory_conflict`, `inventory_mapping_required`, `availability_confirmation_required`, `policy_not_configured`, `capability_unavailable`, `hold_limit_reached`, `reconciliation_required`, `beneficiary_changed`. Errors use normal localized renderer messages. Unknown/unsupported request fields fail validation on new commands. Unrelated UUIDs are not a public existence oracle.

Dates are local civil `[starts_on, ends_on_exclusive)` values. Turnover extends blocked dates explicitly. Expiry/deadline timestamps are timezone-aware server instants. Flutter's countdown uses server_time plus monotonic elapsed time, then requests refresh; it does not grant eligibility. Unknown payment retains the allocation until an authoritative outcome or reviewed remedy; a missed reconciliation deadline escalates the case, not the money.

## Financial and provider contracts

The authoritative objects remain RentInvoice, PaymentQuote, PaymentAttempt, InvoicePaymentAllocation, LedgerTransaction/Entry, RefundRequest, OwnerPayable and RentalPayout. Duplicate ledger references must match the entire posting/source identity. Refund reservations use existing captured component balances. New payout snapshots include internal beneficiary provider/account/profile revision; API payloads continue to expose only masked beneficiary data.

`RentalProviderInstruction` stores stable kind/subject/request identity, fingerprint, reference, status, attempts and next-attempt time. The current execution path is deterministic mock-only. A real dispatcher must commit an instruction before network I/O, reconcile timeout by that same provider reference, preserve unknown outcomes, authenticate merchant/account/currency/amount, and complete local postings exactly once. No production implementation of that transport is supplied in this delivery.
