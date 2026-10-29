# Versioned business policy publication

19 October 2026. The product owner delegated selecting suitable supported policies and deferred independent disaster-recovery journal/reopening approval. This supersedes the earlier blanket awaiting-policy treatment only for the implemented pack below. No paid infrastructure or external financial operation is part of this change.

## API

Base: `/api/v1/features/v1/`.

| Method/path | Authority | Result |
| --- | --- | --- |
| GET `business-policies/` | Public | Effective approved public disclosures, with localized presentation and rule values; no internal approval evidence |
| GET `business-policies/{code}/versions/{version}/` | Public | Exact public approved/retired historical version; internal or absent records return 404 |
| GET `operator/business-policies/` | Active staff, not frozen, plus superuser or `features.change_policydecision` | Supported schemas/defaults, current versions and head revisions |
| POST `operator/business-policies/` | Same current authority rechecked under lock | Immutable new version, updated head, audit and original command receipt/201 |

POST fields: `code`, unique slug `version` (up to 80), integer `expected_head_revision`, exact schema `rules`, `reason` (1–4000), `evidence_reference` (1–500), UUID `request_key`. Server time sets effectiveness. Unknown fields, backdating, unsupported modes and stale heads are rejected. Same-key same-input retry returns the original receipt; changed inputs conflict. Competing publishers serialize on `PolicyDecisionHead`; ordinary company administrators cannot publish platform policies.

Admin entry: `/admin/features/policydecision/publish/`. The CSRF-protected form calls the same service and retains invalid input. Approved records are read-only; correction publishes a new prospective version.

Initial pack: `python manage.py publish_business_policies --actor-id UUID --evidence-reference REFERENCE --policy-version VERSION`. Default is dry review. `--apply` uses the same service transactionally and preserves already published families. Migration `features.0059_business_policy_publication` adds a presentation field/head table only; it never fabricates an approver or rewrites contracts.

## Supported contract

| Code | Default | Runtime effect |
| --- | --- | --- |
| D01 | 72h ordinary / 24h urgent case response target | New case deadline snapshot; original hold reconciliation deadline takes precedence |
| D02 | Mutual signed release / operator review on nonresponse | Existing signed-continuation resolution; no forced consent |
| D05 | Whole calendar months, max 120 | New/edited request validation also respects configured reservation-day limit |
| D08 | Platform custody, no automatic deposit forfeiture | Existing nonzero owner-held deposit rejection and canonical custody contract |
| D09 | Additional case after 60 days; independent and required-party review | Additive settlement correction uses the lease's accepted snapshot; distinct case per late correction |
| D17 | 30-minute hold, one extension, three active holds | Canonical personal/company hold engine; existing hold snapshot controls extension |
| D23 | Explicit action consent, generic notice preview | Existing durable inbox/outbox and destination authorization; not delivery proof |
| D25 | 72h reassessment, no silent consent | Revisioned `request_review` case action after expiry/resolution; pending review cannot be duplicated |
| D26 | `private.export` only; first-party email OTP / staff TOTP; 300-second maximum proof lifetime | Existing action-bound verification and rental statement export; current party/role/session authority remains required |
| D29 | Assigned independent `habitability_assessor` | Existing scoped inspected restriction/clearance/reopen authorization |

Numeric bounds and exact supported modes are authoritative in `business_policy_catalog.py`. Fixed modes are disclosures, not a generic executable policy language. New penalties, arbitrary proration, forced legal discharge or cash-custody products cannot be enabled by JSON. Policy publication does not create a provider, operator, physical inspection or cash transfer. Market research informed choices; numerical operational targets are product decisions, not statutory deadlines.

Corporate package snapshots include the exact policy versions before approval. Agreement terms/documents preserve them. A newer publication does not amend an accepted contract, existing hold or case deadline. An absent historical snapshot remains unknown. Public legacy approvals are excluded unless explicitly created with the public presentation contract. Provider availability, current mandates, independent reviews, financial capacity, canonical locks and original receipts remain enforced.

## D26 private export publication — 30 October 2026

The catalog now supports the existing first-party assurance consumer through the normal operator API, Django publication form and policy-pack command. This adds publication support; deploying source does not itself publish a policy, verify an email, send a challenge, create an export or change any financial/contract record. The pack command now includes D26 when explicitly applied; its default remains dry review. Use the single-policy operator flow for a narrowly reviewed D26 publication.

The server fixes scope to `["private.export"]`. The exact rule schema is:

```json
{
  "provider": "core_apps.users.services.assurance.AccountAssuranceProvider",
  "assurance": "email_otp_or_totp",
  "proof_lifetime_seconds": 300
}
```

Only that provider and assurance value are accepted; the lifetime must be an integer from 1 through 300 (booleans are invalid). Arbitrary import paths, other assurance modes, unknown rule keys, client-supplied scopes, backdating and missing governance evidence are rejected by the existing publication path. Head revision, original request identity, immutable versions, current administrator authority, audit and idempotent receipts remain unchanged. The published public disclosure exposes the duration, not internal provider paths or approval evidence.

Compatibility is with the implemented consumer, not an inferred new security flow:

- `users.services.sensitive_actions._adapter` uses the first-party provider when `SECURITY_ASSURANCE_PROVIDER` is empty; any configured value must exactly match the published provider. The first-party provider works with `DEBUG=false`; a test provider or `SECURITY_TEST_BYPASS` is not needed or enabled by this policy.
- `begin` resolves `approved_policy("D26", action)`, requires a positive integer lifetime, and caps expiry at 300 seconds from challenge creation. The returned `expires_at` is authoritative, including a shorter published lifetime. A non-staff actor must already have a verified email; staff/superusers must have a confirmed current TOTP factor. Delivery failure does not verify a challenge.
- First-party action email now identifies the requested action and displays that exact saved expiry in Cairo time with its date and UTC offset (including DST/repeated-hour distinctions). It does not reuse the ordinary verification email's 600-second wording or reset expiry when email is delivered. Ordinary verify-email/resend/contact-verification mail remains unchanged. Neither the email text nor delivery acknowledgment extends the proof deadline.
- `verify` and `consume` retain actor, session, security epoch, exact action/resource/revision/payload, current policy, expiry and single-use checks. The rental statement command independently checks current party/company authority and lease revision. A proof is not a permission grant or a statement.
- `policy_registry.approved_policy` selects the latest effective approved row containing the requested action. A new private-export-only publication therefore does not remove other scopes from older immutable approvals. Existing non-public/legacy D26 rows and their rules are not rewritten or widened; `business_policies.current` separately controls public disclosures. Publishing a newer policy for `private.export` intentionally requires a fresh proof under that version; it does not replay an existing operation.

The catalog deliberately does not expose `refund.execute`, `payout.execute`, company member updates, account changes/recovery/closure, or an arbitrary security scope. Their existing policies and consumers remain independent. Real email delivery/mailbox possession, current payer authority, normal governance publication, statement creation, worker generation and protected download are separate operational acceptance steps. Source and isolated tests do not certify them.

## Recovery deferral

No active application path consults the independent recovery journal or reopening gate. Retained disconnected drill source/tests are historical references. The retired readiness command explicitly reports deferral and does not grant approval. Per-account security epoch, session revocation, compromised-account freeze, private grants and unknown-result reconciliation remain active. Old password-reset links may require reissue after the hash format changes.

Primary-database restore rollback is no longer covered by an independent journal/global restore epoch. That is the explicit deferred product scope, not a claim that restored external facts are reconciled. Future live provider adapters still require authoritative lookup and safe replay design.

## Verification

288 focused PostgreSQL/Django tests passed in the isolated `policy_configuration_settings` environment after all backend changes. They cover the changed policy, company, hold, case, private-document, account/OTP, push/privacy and viewing paths. Five retained tests exercise the deferred drill prototype; they do not prove active recovery coverage. Django checks and migration drift review are separate from production execution. Flutter/native/deployed results are maintained in the application repository's `docs/sokoun-business-flows/POLICY_CONFIGURATION_AND_RECOVERY_DEFERRAL.md` and its verification artifacts. No full-product or real-provider completion claim is made.

## Hosted staging simulation correction

The deployed service selected `config.settings.staging_mock`; its old implicit fake-provider opt-in became visible when the independent recovery gate was removed. The deployment check detected this before any verification invoked a provider action. Staging simulation now independently requires `RENTAL_STAGING_SIMULATION_ENABLED=true`, in addition to selecting the simulation profile and the existing non-production guard. Default is false. Checkout and mock discovery follow this opt-in. Local explicit test settings remain simulated. This does not introduce a new recovery dependency or a real provider.

27 additional focused tests passed for the opt-in, production refusal, mock API contract and recovery-independent company availability. Three overlap the earlier 288-test run. Deployed false availability and unchanged canonical-data hashes must be checked after this correction; the first deployed true observation is retained in the application evidence ledger.
