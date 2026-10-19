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
| D29 | Assigned independent `habitability_assessor` | Existing scoped inspected restriction/clearance/reopen authorization |

Numeric bounds and exact supported modes are authoritative in `business_policy_catalog.py`. Fixed modes are disclosures, not a generic executable policy language. New penalties, arbitrary proration, forced legal discharge or cash-custody products cannot be enabled by JSON. Policy publication does not create a provider, operator, physical inspection or cash transfer. Market research informed choices; numerical operational targets are product decisions, not statutory deadlines.

Corporate package snapshots include the exact policy versions before approval. Agreement terms/documents preserve them. A newer publication does not amend an accepted contract, existing hold or case deadline. An absent historical snapshot remains unknown. Public legacy approvals are excluded unless explicitly created with the public presentation contract. Provider availability, current mandates, independent reviews, financial capacity, canonical locks and original receipts remain enforced.

## Recovery deferral

No active application path consults the independent recovery journal or reopening gate. Retained disconnected drill source/tests are historical references. The retired readiness command explicitly reports deferral and does not grant approval. Per-account security epoch, session revocation, compromised-account freeze, private grants and unknown-result reconciliation remain active. Old password-reset links may require reissue after the hash format changes.

Primary-database restore rollback is no longer covered by an independent journal/global restore epoch. That is the explicit deferred product scope, not a claim that restored external facts are reconciled. Future live provider adapters still require authoritative lookup and safe replay design.

## Verification

288 focused PostgreSQL/Django tests passed in the isolated `policy_configuration_settings` environment after all backend changes. They cover the changed policy, company, hold, case, private-document, account/OTP, push/privacy and viewing paths. Five retained tests exercise the deferred drill prototype; they do not prove active recovery coverage. Django checks and migration drift review are separate from production execution. Flutter/native/deployed results are maintained in the application repository's `docs/sokoun-business-flows/POLICY_CONFIGURATION_AND_RECOVERY_DEFERRAL.md` and its verification artifacts. No full-product or real-provider completion claim is made.

## Hosted staging simulation correction

The deployed service selected `config.settings.staging_mock`; its old implicit fake-provider opt-in became visible when the independent recovery gate was removed. The deployment check detected this before any verification invoked a provider action. Staging simulation now independently requires `RENTAL_STAGING_SIMULATION_ENABLED=true`, in addition to selecting the simulation profile and the existing non-production guard. Default is false. Checkout and mock discovery follow this opt-in. Local explicit test settings remain simulated. This does not introduce a new recovery dependency or a real provider.

27 additional focused tests passed for the opt-in, production refusal, mock API contract and recovery-independent company availability. Three overlap the earlier 288-test run. Deployed false availability and unchanged canonical-data hashes must be checked after this correction; the first deployed true observation is retained in the application evidence ledger.
