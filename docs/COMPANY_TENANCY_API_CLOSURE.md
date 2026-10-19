# Canonical company tenancy increment

Date: 19 October 2026. Baseline: `92dcf9d32fda1ebd7471345cae9461246d050895`.

A ready company package can now create a canonical company-renter lease after current independent execution-mandate verification. The company remains the debtor; employees remain individual occupants. Corporate tenancy servicing uses the existing inventory, billing, payment, deposit, settlement, private-document and operation-receipt records.

## Entry and ownership

- `GET /api/v1/features/v1/company-tenancies/` and `/{id}/` return current role-specific projections. Employees receive their own placement/unit-service information without the commercial roster, terms, invoices or documents.
- `POST /api/v1/features/v1/company-contract-preparations/{id}/agreement/` requires the currently assigned coordinator, reviewed source, active exact portfolio hold and independently verified sign/pay mandates.
- `POST /api/v1/features/v1/company-mandates/{id}/execution-review/` and the Django-admin execution-review form share current independent staff checks, evidence reference, expiry, expected revision and original operation identity.
- `POST /api/v1/features/v1/company-tenancies/{id}/{action}/` accepts only the typed `company_tenancy_serializers.py` action contract. Current authorization precedes receipt replay. Minimal receipts contain identity/revision; clients reload current authorized state.

Actions cover exact agreement review/document submission/signing sessions; unsigned cancellation; company handover; actual employee arrival/departure; independently consented replacement; unit maintenance/appointment/access/cost/work/resolution; billing-boundary termination; existing-rule funded settlement/refunds; current delegate/coordinator succession; reconciliation and operator cases. Private receipts/statements reuse canonical endpoints and recheck authority at download time.

## Integrity and recovery

`Lease` enforces exactly one personal/company renter. Company → stable property order → lease is the shared corporate/financial lock order. Employee overlap uses a global person advisory lock in PostgreSQL plus interval validation. Portfolio capture requires every frozen unit/day. Approval, payment, possession, legal end and financial closure remain independent. Late/unknown signatures are retained for reconciliation; session expiry does not permit a second unknown signing operation. A late chargeback reopens the company projection and original budget exposure without creating new rent or inventory.

Current owner cannot become the company's replacement signer, payer or possession coordinator. Current delegate/coordinator succession preserves original signatory, debtor, source history and existing company obligations. Human nonresponse does not become consent. An operator ticket is not a substitute for an authoritative legal, physical or financial result.

## Schema and rollout

Apply feature migrations `0053_company_tenancy`, `0054_company_maintenance_consent`, `0055_company_tenancy_coordinator`. Existing personal leases retain their tenant and data; company is nullable for them. The coordinator migration backfills from the original request only for any previously created company-tenancy rows.

The unrelated identity cutover migration `admin_api/0006_reconcile_legacy_identity.py` is explicitly excluded from this release. Do not apply it by copying an uncommitted worktree into production.

Company new-business activation, recovery scopes and provider configuration are unchanged. Inspected hosting had company business disabled, recovery mode `quarantined`, generation/security epoch `unconfigured`, no open scopes and no configured `RECOVERY_JOURNAL_ADAPTER`; there were zero company/preparation/booking records and ten existing leases. These dated observations do not authorize reopening. Production needs an independently durable journal, evidenced recovery control/coverage and verified background operation. The local drill journal is not a production adapter.

## Verification and exclusions

The app repository's `docs/sokoun-business-flows/COMPANY_TENANCY_CLOSURE_IMPLEMENTATION.md` records final executed tests and deployment hashes. Backend regression evidence includes personal/company leases, funded settlement, combined refunds, PostgreSQL concurrency, reputation and document privacy. Native tests use a separate synthetic local database/API; provider events are explicitly simulated.

Real signing/payment/refund providers, signed-artifact retrieval, exceptional post-execution financial adjustments, corporate commercial renewal/amendments, ownership novation and corporate aggregate reputation are not established by this increment. No new proration, cancellation fee, employee debt redistribution or legal policy approval is introduced.
