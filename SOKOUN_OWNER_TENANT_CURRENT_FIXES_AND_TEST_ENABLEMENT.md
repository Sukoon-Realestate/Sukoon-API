# Sokoun: current backend fixes and full-cycle test setup

Prepared: **2026-10-12**. Based on the staging observations recorded **2026-10-12, 12:23–12:29 UTC**, after `SOKOUN_OWNER_TENANT_BACKEND_RETURN (1).md`. This document is a focused work order; preparing it did not run another live audit.

**Backend team: fix the open issues below, deploy them, and directly prepare the accounts, object relationships, permissions, service configuration and fixtures needed to execute the complete owner–tenant cycles.** Account/property setup is part of this work: complete it in staging and return the resulting IDs and evidence instead of handing that configuration back to mobile.

Environment: **`https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`**, the nonproduction environment identified in your reply. All API paths below are relative to this base. Use normal application authorization with test accounts and sandbox providers. An account must receive the rights appropriate to its role and current resource state; making it a superuser or disabling object permissions would invalidate the cycle tests.

## 1. Open work to complete

| ID | Current problem or missing prerequisite | Backend action | Completion evidence |
| --- | --- | --- | --- |
| OPEN-01 | Original banner still serves different image bytes | Restore the original artwork on the existing advertisement and storage reference | Exact length/hash, same-operation mock activation/replay, independent placement/media and redeploy durability |
| OPEN-02 | Advertising Arabic requests receive English responses | Repair effective language selection and cache variation | Same-URL alternating-language tests pass for both plans and public feed |
| OPEN-03 | Arabic planning response contains English blocking reasons | Localize all server-owned reason strings | Arabic reasons and headers agree for guest, owner and tenant |
| OPEN-04 | Promised `auth/token/refresh/` alias returns 404 | Deploy the alias to the canonical refresh implementation, or explicitly withdraw the alias contract | Authenticated POST/identity evidence at the agreed routes |
| OPEN-05 | Working pair has no eligible source visit; secondary actors and advanced fixtures are missing | Perform the account/property/fixture setup in sections 2–4 directly | Actual IDs, relationships, current permissions and successful preflight calls |
| OPEN-06 | Fresh cancellation, funded cancellation and first-read consistency remain unverified | Test new valid fixtures; correct the transition if any invariant fails | Cancellation response, collection/detail/center consistency, replay and financial-obligation tests |
| OPEN-07 | Full signing/payment/stay/exit jobs and chat recovery lack deployed evidence | Configure real sandbox integrations, workers and scenario fixtures; execute the remaining journeys | Provider/job/event/ledger correlations and both actors' results |
| OPEN-08 | C08/C09 and dependent planning services remain undeployed/gated | Implement and deploy those services, configure dependencies, then issue genuine account/action grants | Endpoint scenarios, current service verification, grants and expiry; flags alone do not complete implementation |
| OPEN-09 | Exact deployed release, schema and test outputs are missing; visit rejection enum remains unconfirmed | Return the concrete release/evidence package and confirm client-compatible action bodies | Immutable release identity, migration outputs, schema artifact/hash and exact sanitized request/response examples |

These are the remaining actions. An unverified case is a verification task, not a claim that its implementation is necessarily defective.

## 2. Exact staging records and direct setup instructions

### 2.1 Use these existing identities

The IDs below were resolved from the authenticated staging records. They are resource identifiers, not credentials.

| Record | Actual ID | Required use |
| --- | --- | --- |
| `owner_a` | `3b6d5dd4-2077-4bad-9c59-32717915035e` | Primary owner for the happy path and original banner recovery |
| `tenant_a` | `9eef4201-0ca4-4fc1-b91f-9ef27551c0ea` | Primary tenant for the same property/offer/lease chain |
| Existing owner property | `13954644-cc37-49d9-a772-f1a88be81401` | Prepare for eligible test visits if suitable; otherwise create a dedicated property under the same owner and return its ID |
| Existing ineligible source visit | `ff1b94d2-3255-43a8-9a99-68735c6c7c6c` | Currently `canceled`; retain as the negative fixture and create a new eligible source |
| Original advertisement | `85295dd1-f8bd-4c82-a903-9bdc3d90af98` | Repair in place; retain its owner and operation identities |

Confirm these relationships in the deployed database before applying setup. A different tenant's confirmed visit cannot authorize `tenant_a`. If the database no longer contains these records, report the environment mismatch and resolve it before creating unrelated substitutes.

### 2.2 Configure accounts and permissions directly

| Actor / object | Backend must prepare | Authorization evidence to return |
| --- | --- | --- |
| `owner_a` | Active account, completed registration, valid test identity/owner eligibility; ownership of test listings/offers; any required sandbox entitlement, KYC and beneficiary setup | Current identity and actual owner-readiness response; owner can manage its property/availability and enter the applicable agreement/onboarding flow |
| `tenant_a` | Active account, completed registration, valid test identity/tenant eligibility; any required test entitlement | Current identity; tenant can book the supplied slot, respond to its invitations, review/sign its agreement and pay its own eligible invoice |
| `owner_b` | Create a separate active, verified owner with its own test property | Successful own-object access, then 403/404 for owner A's private resources |
| `tenant_b` | Create a separate active, verified tenant with its own legitimate test relationship | Successful own-object access, then 403/404 for tenant A's private resources |
| Test property and offers | Correct owner FK/relationship, normal publication/moderation eligibility, active supported rental offers, current revisions, valid pricing/policies, available inventory | Owner/private and tenant/public projections identify the same property and selected accommodation |
| Visits/invitations/leases | Correct participant and parent relationships, current statuses, unexpired source/consent where required | Actions become available to the intended participant at the correct stage; another actor remains denied |
| Invoice/deposit/payment | Correct lease, payer, currency, revision and ledger links; sandbox PSP configuration | Payable tenant invoice grants quote/checkout only when eligible; owner cannot pay or read unrelated tenant resources through a workspace override |
| Private documents/evidence/chat | Participant-bound access, private storage and allowed counterparty relationship | Both intended parties can perform their permitted operations; other actors cannot fetch private content |

Use the actual project models/services; this document does not assume a particular Django group name or a single `can_rent` flag exists. If a subscription/plan gates an operation, provision the appropriate **test entitlement** and return its scope/expiry. If a readiness blocker is missing sandbox configuration or a test-account field, configure it directly. Keep policy acceptance and signing as explicit actor actions in the main journey; expose the required versions and actions instead of silently accepting them for a real account.

Provide working secondary credentials privately. Keep primary account IDs and the original advertisement association intact. For a new Google login exchange, use a legitimate fresh Google sign-in; do not extend or fabricate an expired Google ID token. A valid saved server session can support HTTP recovery tests while it remains valid.

### 2.3 Prepare a usable property and new source visit

1. Configure selectable future visit slots, based on the server clock and `Africa/Cairo`, with dates that remain valid through the scheduled QA run. Confirm agreement between owner availability/calendar and tenant `available_dates/`.
2. For structured accommodation tests, create/prepare real `entire_property`, `room`, `room_group` and `bed` offers as supported by the application. Return stable offer/room/bed IDs, current offer revisions and canonical snapshots. Use separate inventory or non-overlapping scenarios so one test's hold cannot block another inadvertently.
3. Create a **new** source visit connecting owner A's property to tenant A, in a backend-supported eligible `pending` or `confirmed`/`accepted` state. Return the exact stored token. Keep the cancelled visit unchanged as a denial case.
4. Provide a fresh source with no consumed/expired invitation for the C03 positive scenario. Resolve ambiguous competing sources through normal test-data preparation; do not weaken source eligibility.
5. Return current lease configuration, usable template/version, valid future start/end dates and server-approved Money rent. After the tenant accepts the new invitation, the owner picker must include that tenant; after draft creation it must exclude consumed consent.
6. Supply an additional available slot for the main end-to-end booking journey. A pre-created source visit unblocks a focused C03 regression; it does not substitute for testing booking itself.

Acceptance calls include owner `GET properties/owner/properties/{property_id}/availability/`, owner `GET properties/owner/visits/requests/{new_visit_id}/`, `GET features/v1/lease-configuration/`, and the correctly staged `GET features/v1/lease-tenants/?property_id=...`. Capture each actor's authorized response. `source_visit_id` belongs in the QA fixture manifest; it is **not** an extra field in the existing invitation POST body.

## 3. Configure the real capability and action grants

Permission setup must satisfy both capability discovery and resource-level authorization. A role name or `workspace=owner|tenant` does not grant access by itself.

### 3.1 Rental services

For the actual subject at each stage, query:

```text
GET features/v1/rental-capabilities/?subject_id={actual_source_or_resource_id}&action={actual_action}
```

Return the authenticated `account_id`, `account_verified:true`, supported nonempty `policy_version`, the required `enabled_capabilities`, and current `allowed_actions`. The resource itself must expose compatible actions/status/revision and remain authorized when the mutation executes. Test each actor separately. A closed lease granting only `rental_center` says nothing about permission on a new invitation, signed agreement or payable invoice.

Create new structured agreement fixtures with the supported writable contract and `legacy_read_only:false` where appropriate. Do not turn a historical read-only lease into a writable agreement by changing that flag alone.

| Needed stage | Capability identifiers used by the app | Examples of actual action names |
| --- | --- | --- |
| Interest and agreement | `rental_interests`, `rental_agreements`, `signed_documents` | `create_rental_interest`, `create_terms_proposal`, `create_lease`, `edit_lease`, `sign`; review/decision tokens depend on the current action |
| Initial and recurring payments | `rent_checkout`, `rental_deposits` | `quote`, `checkout`, `reconcile` on the appropriate invoice/attempt |
| Possession/evidence | `rental_handovers`, `condition_reports` | `create_rental_handover`, `edit_handover`, `upload_evidence`, plus the current review/acknowledgement action |
| Ongoing stay | `rental_maintenance`, `rental_changes` | `create_maintenance_request`, the appropriate change action and participant decision |
| Exit/settlement/dispute | `rental_settlement`, `rental_disputes` | `propose_settlement`, `create_rental_refund`, plus the permitted decision for the current state |
| Owner payout, documents and review | `owner_payouts`, `signed_documents`, `rental_reviews`, `rental_center` | `onboard_beneficiary`, `request_statement`, `review_rental`, plus applicable payout decisions |

This is a list of capabilities needed across stages, **not a request to grant every action to every account**. Configure the prerequisites and derive the proper grants. In particular, signing belongs to the required signer, checkout to the invoice payer, and beneficiary/payout setup to the owner.

For a payable invoice, return a fresh known revision, `invoice_status`, positive server balance, `can_pay:true` and permitted `quote`/`checkout` actions. The quote must cover the full combined amount and use the supported `rental-policy-v1`; checkout remains `invoice_id`, `quote_id`, `expected_revision`, `request_key`. Do not add a client amount or bypass quote validation to make the action available.

### 3.2 Planning and transition services

The remaining planning work needs implementation/deployment as well as permission configuration. After verifying a service, use:

```text
GET features/v1/planning-capabilities/?capability={capability}&action={action}&subject_id={actual_subject_id}
```

Subjectless collection discovery may omit `subject_id`; the resource endpoint must still enforce its parent/account scope. An enabled response needs the correct `account_id`, `account_verified:true`, nonempty `policy_version`, the service in **both** `enabled_capabilities` and `verified_services`, the actual `allowed_actions`, and a real future `expires_at`. Return localized reasons when a legitimate restriction applies.

Prepare these service families for the corresponding cycles: `lifestyle`, `roommates`, `housing_groups`, `group_visits`, `group_applications`, `housing_requests`, `housing_offers`, `commute`, `tenant_assistant`, `condition_reports`, `move_out_notices`, `replacements`. Example action names are `read`, `create` and the resource's declared action; do not reuse rental action names indiscriminately. Condition reports and tenancy transitions use this planning authorization path in the current app.

Do not advertise an unimplemented service merely to unblock the UI. Complete its route/storage/provider/job work, test it, then grant access to the designated test accounts. Return a per-service matrix of **implemented / deployed / verified / granted**, plus any external dependency with an owner and concrete next action.

### 3.3 Coordinate the test build

Backend permissions cannot change Flutter compile-time switches. Return the verified capability matrix so mobile can build with the corresponding `SOKOUN_*` flags. For example, hosted signing also needs `SOKOUN_LEASE_SIGNING`, while agreement/payment/handover flows use their corresponding flags. Full-cycle tests must keep `SOKOUN_BYPASS_VERIFICATION=false` and exercise normal server decisions.

## 4. Supply distinct fixtures for the remaining journeys

Prepare one untouched starting fixture for the full happy path, plus separate fixtures for destructive/negative branches. Seeded intermediate states are setup data; label them as such and do not report them as completed API transitions.

| Scenario | Required preparation |
| --- | --- |
| C01 listing/visit/chat/review | Owner can create/manage a test listing; exact offers; future slots; bookable starting state; allowed conversation; a separate review-eligible visit |
| C02 reject/cancel/resubmit | Separate pending and accepted visits; rejection reason compatibility; fresh resubmission slot; retained accepted-contact history |
| C03 invite/legacy draft | New eligible source for the exact primary pair, current template/terms and unconsumed consent; unrelated B actors |
| C04 agreement/sign/payment/move-in | Fresh interest/accepted invitation as required, server terms/policy, signer readiness, available inventory, hosted sandbox signing and checkout; separate signed-unpaid combined-invoice fixture for recovery tests |
| C05 active stay | Active lease with paid initial invoice and move-in state, recurring billing schedule, maintenance evidence/costs and independent amendment/renewal/extension cases |
| C06 exit/settlement | Separate clean unfunded cancellation, funded cancellation/refund, notice/move-out, settlement/deposit/dispute/payout and replacement cases; keep amounts and ledger links consistent |
| C07 original advertisement | Existing ad and original operations, exact original artwork and owner authorization; no replacement record |
| C08 group/roommate | Distinct discoverable test tenants, consent-controlled connection/chat, group administrator/member/invite and roster revisions, group visit/application fixtures |
| C09 request/offer/compare | Tenant request, owner responses from correctly owned properties, two/three comparable offers, and selection handoff retaining exact offer identity; separate unrelated owner |
| S01 exact accommodation | Coverage for the supported accommodation scopes with the same snapshot through booking, consent, agreement and occupancy |
| S02 alerts/commute/assistant | Saved-search event/job fixture, routing sandbox and assistant configuration; verified account/service grants |
| S03 recovery/isolation | Stable operation keys, durable lookup/receipt records, duplicate and lost-response tests, revoked/expired sessions and independent account-switch checks |

Prefer an idempotent, additive Django management command using the existing domain services. Implement one if none exists; proposed command name: **`prepare_owner_tenant_cycle_qa`**. This is a requested backend utility, not a claim that the command already exists. Bind its fixture-set identity to this environment and primary pair; return created/reused IDs, revisions, validity windows and cleanup scope. Rerunning setup must not regenerate an unresolved operation key or erase financial/history records. Scope cleanup to dedicated disposable test fixtures; do not reset the shared database.

Return a populated `fixtures.json` compatible with the current runner. The following is a **QA manifest template, not an API request**. Replace every `BACKEND_MUST_RETURN_...` value with the actual deployed value; money must contain real integer minor units. For an offer-aware C03 fixture add current `offer_id` and `expected_offer_revision`; omit both in legacy property mode.

```json
{
  "legacy": {
    "property_id": "13954644-cc37-49d9-a772-f1a88be81401",
    "source_visit_id": "BACKEND_MUST_RETURN_NEW_ELIGIBLE_VISIT_ID",
    "draft": {
      "template_id": "BACKEND_MUST_RETURN_CURRENT_TEMPLATE_ID",
      "template_version": "BACKEND_MUST_RETURN_CURRENT_TEMPLATE_VERSION",
      "start_date": "BACKEND_MUST_RETURN_VALID_YYYY_MM_DD",
      "end_date": "BACKEND_MUST_RETURN_VALID_YYYY_MM_DD",
      "rent": "BACKEND_MUST_REPLACE_WITH_MONEY_OBJECT"
    }
  },
  "banner": {
    "advertisement_id": "85295dd1-f8bd-4c82-a903-9bdc3d90af98",
    "operation_id": "74682688-4428-413c-a1ae-c4b87222c687",
    "mock_operation_id": "74682688-4428-413c-a1ae-c4b87222c687-payment",
    "artwork_sha256": "dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b"
  }
}
```

If using a new dedicated property, replace the manifest property ID with the returned property owned by owner A. Keep a separate extended manifest for the other scenarios: actor aliases/IDs, property/offer/revision, source visit, invitation, lease, invoice, payment attempt, deposit, handover, settlement, group/request IDs, expected starting states and expiry. The current runner directly consumes the `legacy` and `banner` sections; the extended manifest supports the additional integration scenarios, not automatic coverage it does not yet have.

## 5. Implement and verify the current defects

### OPEN-01 — exact original banner recovery

Original asset: `packages/core/assets/png/logo.png` in the mobile repository. Expected **28,970 bytes**, SHA-256 **`dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`**. Last observed remote response: **1,213 bytes**, SHA-256 `303a95728f601403f468dd9abe1cd8618d1f9fee2ef68e7cb57a257337b5b370`; status `pending_payment`.

Restore that exact original object in durable shared storage and repair the existing ad's reference. Owner-authenticated `GET advertising/v1/media/85295dd1-f8bd-4c82-a903-9bdc3d90af98/` must match the original digest, with `Accept: image/jpeg, image/png, image/webp, application/json`. Verify stored and served bytes after restart/replica change/redeploy.

Only after the image/current-operation checks pass, replay the existing intention at:

```text
POST advertising/v1/owner-advertisements/85295dd1-f8bd-4c82-a903-9bdc3d90af98/mock-payment/
```

```json
{"operation_id":"74682688-4428-413c-a1ae-c4b87222c687-payment","payment_mode":"mock"}
```

The response and fresh owner read must identify the same ad, `status=active`, the server mock receipt and activation dates. Exact replay must preserve receipt/dates and create no duplicate charge/effect. Tenant and guest must independently see the same ad/media in placement. Do not publish a substitute image to pass this test.

### OPEN-02 / OPEN-03 — language and caching

Affected paths: `advertising/v1/plans/`, `advertising/v1/placements/tenant-home/`, `features/v1/planning-capabilities/`.

Resolve one effective language for server-owned payload strings and `Content-Language`. Review custom serializer helpers, active request locale and application/CDN cache keys. Emit appropriate `Vary: Accept-Language`; its presence alone is insufficient. Preserve normal header-only mobile requests.

Test identical URLs with `Accept-Language` in **en → ar → en → ar**, then **ar → en → ar → en** order, on warm cache and after targeted invalidation, and across replicas. Check plan titles/server messages, language headers and cache metadata. User-authored advertisement text does not need automatic translation. Arabic planning must localize both the service-readiness reason and the guest-authentication reason, plus any applicable account reasons.

### OPEN-04 / OPEN-09 — refresh alias and remaining contract confirmation

Route the promised `auth/token/refresh/` alias to the same refresh implementation as `auth/refresh/`, or explicitly state that the alias is withdrawn from the backend contract. Preserve the canonical mobile route. Verify valid-session POST followed by the same current-user identity, then expired/revoked-session and concurrency cases. Return statuses/cookie metadata without secrets.

Confirm that visit rejection accepts the current mobile `reason=timing_not_suitable` plus `custom_reason`, or supply a coordinated, versioned enum migration. Return actual request/response JSON for the tested actions. Keep invitation `revision`, structured rental `expected_revision`, and advertising `operation_id` as their distinct existing dialects.

### OPEN-06 — fresh closure and funded cancellation

Run new cancellation fixtures after provisioning C03. The cancellation response, **first collection read**, detail and Rental Center must agree for both parties without relying on a GET to finish a transition or increment revision. Test another read order and exact cancellation replay.

Derive closure from authoritative obligations during the transition. Never-occupied status can waive an inapplicable handover; it does not settle an invoice, captured deposit or uncertain payment. Test clean unfunded cancellation separately from unpaid-invoice cancellation, captured funds/refund due, pending/unknown payment, failed refund, dispute and late capture racing cancellation. Keep financial closure unresolved while obligations remain. Verify ledger totals, bounded refunds and no restored consumed consent.

Run transaction/race tests against PostgreSQL with independent transactions. Return test outputs and correlated state/ledger records, rather than only serializer snapshots.

### OPEN-07 / OPEN-08 — configure external dependencies and finish implementation

Provision actual sandbox signing/PSP/KYC/beneficiary credentials, callback URLs/signature verification, private document storage, queue workers, scheduler and WebSocket/notification infrastructure. Record API/worker compatibility. Verify the agreed sequence: **signatures → 48-hour hold and one rent/deposit invoice → required successful capture → active agreement → move-in**. Settlement/refund and owner payout need their own evidence.

Exercise duplicate/out-of-order callbacks, lost responses, hold expiry/late capture, recurring invoice execution, refund/payout outcomes and restart recovery. A mock adapter result must be labeled mock; environment variables alone do not prove an integration works.

Provide a controlled way to advance the dedicated fixture's billing period or invoke the real scheduled job in QA, so recurring-operation tests do not depend on waiting a calendar month. Keep the normal period uniqueness/locking rules and return actual job and invoice IDs.

For chat, verify persistence and independent counterpart receipt, reconnect/history catch-up, message-key deduplication and rollback/process/broker failure behavior. `transaction.on_commit` does not itself guarantee durable delivery. Complete any missing recovery/outbox work required by these cases.

Deploy missing planning routes/providers before advertising those capabilities. If an external prerequisite cannot be supplied, return its exact missing item, responsible owner and delivery date; do not mark the affected cycle complete.

## 6. Deployment proof and backend return

Return one completed response to this work order containing:

1. **Release:** full committed SHA/image digest, deployment ID and UTC time for API/worker/scheduler/WebSocket, exact installed Python/Django/DRF/PostgreSQL versions, and schema artifact/hash.
2. **Deployment checks:** sanitized deployed-settings outputs from `check --deploy`, `makemigrations --check --dry-run`, `showmigrations --plan`, and `migrate --check`. State applied migrations/backfills and any unresolved result; model drift and unapplied migrations are different checks.
3. **Setup completed:** exact account/property/offer/source IDs, private secondary credentials, completed sandbox prerequisites, current actor/subject/action grant matrix and capability expiry where applicable. Include the populated runner fixture file and extended scenario manifest.
4. **Each open item:** implementation commit, public-environment verification command, UTC time, exit status, request/response or provider/job correlation, expected/actual outcome and artifact reference. Use implemented/deployed/verified as separate fields.
5. **Cycle results:** both participants' readbacks, negative-actor denial evidence, financial/provider/job assertions and outstanding dependencies. Prepared fixtures are not completed journeys.

Verify through the public staging URL after deploy and applicable cache invalidation. If deployed results contradict local tests, resolve the serving release/configuration/storage mismatch before returning “fixed.” Include recovery ownership and a compatible rollback/roll-forward procedure.

## 7. Handoff to integration testing

Backend should finish provisioning and return the ready fixtures directly. Mobile/QA can then run, from `apps/sokoun_app`:

```bash
make ownerTenantCyclesLiveRead FLUTTER=/path/to/flutter SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory CYCLES_EVIDENCE_DIR=/fresh/read-evidence
make ownerTenantCyclesLive FLUTTER=/path/to/flutter SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory CYCLES_EVIDENCE_DIR=/fresh/scenario-evidence
```

For HTTP-only checks with valid saved sessions, `ownerTenantCyclesApiRead` / `ownerTenantCyclesApiLive` accept `CYCLES_REUSE_SESSIONS=true`. Flutter fresh-login tests still need current login inputs. Preserve the same private operation journal between runs and use fresh evidence directories. Resolve an uncertain operation before retrying it under the same identity.

These targets cover public/account reads and the current C03/C07 regressions. Full acceptance additionally requires the other scenarios in section 4, provider/job evidence and Android/iOS user journeys with the verified test-build flags. Do not label a blocked or unimplemented scenario as passed.

Supporting evidence, if the mobile repository is available: [current HTTP failures and blocked checks](../qa/evidence/owner-tenant-reply-2-2026-10-12/scenarios/cycle-report.json), [current Flutter assertions](../qa/evidence/owner-tenant-reply-2-2026-10-12/flutter-live-read.json), [visit/alias follow-up](../qa/evidence/owner-tenant-reply-2-2026-10-12/followup/followup-summary.json). The actions and known IDs needed to start are included in this file.
