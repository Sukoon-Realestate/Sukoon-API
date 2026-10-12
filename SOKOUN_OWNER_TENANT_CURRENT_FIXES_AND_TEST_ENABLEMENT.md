# Sokoun: current backend fixes and full-cycle test setup

Updated **2026-10-12**, after live verification of `SOKOUN_OWNER_TENANT_CURRENT_FIXES_HANDOFF.md` against staging at **13:54–14:01 UTC**.

**Backend team: complete the remaining work below in the deployed staging environment, including account, property, permission and provider setup. Return working fixtures and verification evidence so mobile can execute the complete cycles.** This file contains current defects and outstanding verification tasks only. Stable item IDs are retained for your next reply.

Base URL: **`https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`**. Paths below are relative to this base. Use dedicated QA records, ordinary object authorization and sandbox providers. Complete setup directly; do not make the test accounts superusers, bypass verification or grant every action in every state.

## 1. Remaining work

| ID | Current finding | Required result |
| --- | --- | --- |
| OPEN-02 | Arabic advertising plans/feed still return English headers and server text in both alternating request orders | Correct header-only localization and cache variation on the public deployment |
| OPEN-05 | Supplied positive visit returns 404; advertised inventory/availability do not match staging; actor manifest and credentials are incomplete | Repair the actual staging fixture set and return verified IDs, relationships, credentials and valid terms |
| OPEN-10 | Owner payment profile is not ready; its field types and onboarding action do not match the app; subject capability is disabled | Fix the serializer/action contract, enable legitimate scoped onboarding, and complete sandbox prerequisites |
| OPEN-06 | New cancellation, collection-first consistency and funded/uncertain closure cases cannot yet run | Execute new unfunded and funded fixtures with authoritative closure, same-key replay and both actors' readbacks |
| OPEN-07 | Signing/payment/stay/exit, worker and chat recovery claims lack deployed evidence | Supply complete scenario fixtures and actual provider/job/ledger/delivery results |
| OPEN-08 | Planning services remain disabled with no verified services or grants | Implement/deploy/verify the required services, then issue real account/action grants |
| OPEN-09 | Immutable serving release, schema, migrations and actual test outputs are absent | Return the deployment and evidence package in section 8; exercise the stated rejection body using a valid pending visit |
| OPEN-01-V | Media durability across replicas/redeploy is unverified; immediate placement read was stale until cache expiry | Prove durable storage and specify/test the placement visibility bound; this is a remaining verification task |

A missing fixture or evidence package is not proof that every underlying implementation is defective. Do not label those scenarios passed until they execute successfully.

## 2. OPEN-02: advertising localization still fails

At the public base, these exact URLs return `Content-Language: en` for `Accept-Language: ar`:

```text
GET advertising/v1/plans/
GET advertising/v1/placements/tenant-home/
```

Plans still contain `Weekly`, `Monthly`, `Yearly` and `Available plans.`; feed messages remain English. `Vary: Accept-Language` is present. Reproduced with **en → ar → en → ar** and **ar → en → ar → en**, plus the real Flutter transport. A query override is not equivalent to the app's normal header-only request.

Resolve the effective locale before producing or caching server text. Review custom language helpers, Django middleware order, application cache keys and edge cache behavior in the actual serving release. Vary cached representations by the effective language and invalidate only affected stale entries. Django describes language-aware caching and header variation in its [cache documentation](https://docs.djangoproject.com/en/5.1/topics/cache/#the-per-site-cache).

Acceptance: same-URL alternating requests, warm and cold cache, both languages and serving replicas. Assert headers, localized plan titles/messages and cache metadata. Preserve machine identifiers and user-written ad content.

## 3. OPEN-05: prepare the actual accounts, property and source visit

### 3.1 Bind setup to these records

| Record | ID | Current finding / required action |
| --- | --- | --- |
| Owner A | `3b6d5dd4-2077-4bad-9c59-32717915035e` | Authenticated ID is correct; the reply's email does not match current-user data. Keep this identity and return its actual login mapping privately |
| Tenant A | `9eef4201-0ca4-4fc1-b91f-9ef27551c0ea` | Same email mismatch; current authenticated ID is correct |
| Owner B, claimed | `4c7e6ee5-3188-5cbe-815a-43828a26146f` | Supply working private credentials and prove distinct identity and appropriate ownership |
| Tenant B, claimed | `af0a5312-1db5-502a-9f20-800a688221fb` | Supply working private credentials and prove distinct identity |
| Property A | `13954644-cc37-49d9-a772-f1a88be81401` | Owner A relationship is confirmed; inventory and availability differ from the reply |
| Positive visit, claimed | `e11a71e0-410a-42b7-a367-9c98867a5412` | Owner A detail returns **404**, `No PropertyVisit matches the given query.` |
| Existing negative visit | `ff1b94d2-3255-43a8-9a99-68735c6c7c6c` | Remains cancelled; retain as a negative fixture |
| Property B, claimed | `24b94f65-5122-4a0b-99d7-82a87401c102` | Public detail returns 404. Verify existence/publication and Owner B access; Owner A's 404 alone does not prove the isolation scenario |

A 404 establishes that the record is unavailable through the tested actor/endpoint; backend must distinguish absent data, wrong database/environment, hidden state and incorrect ownership. The owner's visit list contains the cancelled primary-tenant visit and a confirmed visit for a different tenant. That other tenant's visit cannot authorize Tenant A.

Both primary sessions remain usable. Fresh owner Google authentication needs a current authorized login credential; the earlier ID token is expired. Secondary actor emails alone are not credentials. Deliver authentication inputs privately, outside the repository, and verify each through current-user identity after login/refresh. Do not overwrite established primary identities to match example emails.

### 3.2 Repair fixtures and verify their projections

Run your supplied command against the **same deployed database and settings as this public URL**:

```bash
python manage.py prepare_owner_tenant_cycle_qa --output=fixtures.json --print-extended
```

Return sanitized command output, UTC execution time, serving release/environment identity and a generated manifest from persisted records. Keep the operation journal, financial history and consumed consent intact. The command must be additive and repeatable; do not reset the database. Return attachable JSON artifacts rather than a developer-local `file:///...` link.

Complete these steps:

1. Prepare an eligible, unconsumed source visit for the exact Owner A / Tenant A / Property A relationship. Return its real ID and status, then prove owner detail **200** and matching tenant/property IDs. Repair the claimed ID if it is the intended record, or clearly document its replacement in the manifest.
2. Prepare selectable future availability. Observed week `2026-10-12` has `days:[]`; week `2026-10-19` has only Monday `12:00`; week `2026-10-26` has `days:[]`. The claimed 14 days at `10:00`, `14:00`, `16:00` are not present. Include actual slots, timezone and validity window for both the isolated C03 fixture and a fresh booking journey.
3. Prepare structured room/bed/offer inventory with current revisions. `GET properties/{property_a}/` currently returns `rental_inventory.offers:[]`; the reply's room/bed/offer identifiers are not exposed. Verify the real IDs in the property response before declaring S01 or offer-aware flows ready. For legacy property mode, omit `offer_id` and `expected_offer_revision` together.
4. Reconcile pricing and dates. The manifest states monthly `15000.00`; its lease Money `amount_minor:150000`, EGP exponent 2 means **1500.00 EGP**; the live property reports `price:"60000000.00"`, `price_period:"weekly"`. Return intended listing/offer/negotiated rent and billing period explicitly. If differences are intentional, identify the approved terms; mobile must not infer a conversion or charge an example amount. Refresh the supplied `2026-10-14` start date when necessary.
5. Return current template/version and policy. The observed `eg-residential-v1`, version `1`, configuration permits creation, but that alone does not authorize an arbitrary tenant. After valid invitation acceptance, the picker must include Tenant A; after draft consumption, it must exclude consumed consent.
6. Verify Property B under Owner B and test unrelated-object denial only after the target's authorized owner proves it exists. Prepare published competing properties/offers separately where C09 requires them.

Required preflight paths:

```text
GET auth/users/me/
GET properties/{property_id}/
GET properties/owner/properties/{property_id}/availability/?week_start={YYYY-MM-DD}
GET properties/owner/visits/requests/{source_visit_id}/
GET features/v1/lease-configuration/
GET features/v1/lease-tenants/?property_id={property_id}
```

Keep `source_visit_id` in the QA manifest. The existing invitation POST uses `property_id`, `tenant_id`, `request_key` and, in offer mode, `offer_id` plus `expected_offer_revision`; it does not add a `source_visit_id` wire field. The server must validate the eligible relationship.

## 4. OPEN-10: owner onboarding cannot proceed with the current response

Owner A's `GET features/v1/owner-payment-profile/` returns:

```json
{
  "status": "not_started",
  "revision": 1,
  "provider": "",
  "masked_beneficiary": {},
  "policy_summary": {
    "commission": "10% of first-period base rent, paid by owner",
    "renewal_commission": "0%",
    "tenant_service_fee": "0 EGP",
    "processing_fee_payer": "platform"
  },
  "required_policy_versions": ["rental-policy-v1"],
  "accepted_policy_versions": [],
  "allowed_actions": ["onboard"]
}
```

This is an **observed subset**, not the full response. The reply's `payment_profile_ready:true` and `payout_ready:true` do not match it. Arabic profile requests have an Arabic header but English policy/blocking text.

The current `OwnerPaymentProfile` model expects **strings** for `policy_summary` and `masked_beneficiary`. An object-valued policy becomes empty. `OwnerPaymentData.onboarding` requires a nonempty policy summary, required policy acceptance, matching revision and the exact action **`onboard_beneficiary`**. The UI uses that same action to expose onboarding. Consequently, this response prevents the legitimate owner from beginning onboarding.

Repair the deployed serializer to return localized display strings for those fields; any structured breakdown can be an additive separate field. For an eligible not-started profile, expose `onboard_beneficiary` consistently on the resource and capability response. Keep legitimate blockers/state restrictions. Return the real provider and masked beneficiary once available; do not fabricate readiness.

This subject-specific probe currently returns HTTP 200 with **empty capabilities/actions** and `The requested rental action is not available yet.`:

```text
GET features/v1/rental-capabilities/?subject_id={owner_payment_profile_id}&action=onboard_beneficiary
```

Configure the verified owner, sandbox provider and policy prerequisites directly, then authorize `owner_payouts` / `onboard_beneficiary` for the correct profile. Complete the sandbox beneficiary/KYC flow using approved test identities and recorded policy acceptance. Setting a `payout_ready` flag alone is insufficient.

The app's existing session request is:

```text
POST features/v1/owner-payment-profile/onboarding-session/
```

```json
{
  "expected_revision": 1,
  "request_key": "REUSE_THE_SAVED_ONBOARDING_REQUEST_KEY",
  "accepted_policy_versions": ["rental-policy-v1"]
}
```

This is a body template: use the fresh revision, versions actually presented/accepted, and a durable operation key created once for that intention. Return the established mutation resource/receipt, matching subject/key/revision, HTTPS hosted URL and future expiry. Verify exact replay, stale revision, wrong owner and expired session. Return a separate ready profile fixture for downstream payout tests while retaining an onboarding-start fixture for this journey.

## 5. Complete capabilities and scenario fixtures directly

### Rental capabilities

For each real resource and actor, query `features/v1/rental-capabilities/?subject_id={id}&action={action}`. Require matching `account_id`, `account_verified:true`, supported nonempty `policy_version`, the needed `enabled_capabilities` and current `allowed_actions`. The resource and mutation must enforce the same role, parent scope, state and revision. The currently observed closed lease grants only `rental_center`; that does not establish grants on a new lease or invoice.

| Stage | Capability identifiers | Required actions / setup |
| --- | --- | --- |
| Interest/agreement | `rental_interests`, `rental_agreements`, `signed_documents` | `create_rental_interest`, `create_terms_proposal`, `create_lease`, `edit_lease`, `sign`, with exact parties/offer/terms |
| Billing | `rent_checkout`, `rental_deposits` | `quote`, `checkout`, `reconcile`; payable invoice with known revision, positive balance, `can_pay:true` and correct payer |
| Possession/stay | `rental_handovers`, `rental_maintenance`, `rental_changes` | `create_rental_handover`, `edit_handover`, `upload_evidence`, `create_maintenance_request`, and state-specific participant decisions |
| Exit/finance | `rental_settlement`, `rental_disputes`, `owner_payouts` | `propose_settlement`, `create_rental_refund`, `onboard_beneficiary`, and appropriate decisions |
| Statements/reviews | `signed_documents`, `rental_reviews`, `rental_center` | `request_statement`, `review_rental`, eligible tenancy history |

Grant only the actions legitimate at that stage. Use new writable structured agreements where appropriate; changing a historical lease's `legacy_read_only` flag is not a migration. Checkout remains `invoice_id`, `quote_id`, `expected_revision`, `request_key`, with the full server balance under the supported rental policy.

### OPEN-08: planning implementation and grants

Guest and both primary actors still receive empty `enabled_capabilities`, `verified_services`, `allowed_actions`, and null `expires_at`. That is a disabled discovery contract; it does not implement C08/C09/S02.

Complete required services and dependencies for `lifestyle`, `roommates`, `housing_groups`, `group_visits`, `group_applications`, `housing_requests`, `housing_offers`, `commute`, `tenant_assistant`, `condition_reports`, `move_out_notices` and `replacements`. Condition reports and transitions use planning authorization in the current app.

Then verify `features/v1/planning-capabilities/?capability={service}&action={action}&subject_id={id}`. An enabled grant needs the matching verified account, policy, service in **both** enabled and verified lists, proper actions and future expiry. Subjectless collection discovery may omit the subject; reads/writes still enforce their parent/account scope. Return a per-service **implemented / deployed / verified / granted** matrix and exact remaining dependency owners.

### Fixtures still absent from the extended manifest

| Journey | Prepare distinct starting records and return IDs/revisions |
| --- | --- |
| C01/C02 | Bookable listing/offer/slot; pending and accepted visits; exact `timing_not_suitable` rejection body with optional `custom_reason`; resubmission slot; counterpart chat and review-eligible case |
| C03 | Eligible primary-pair source, unconsumed consent, valid template/terms; unrelated B actors |
| C04 | Untouched interest/consent start, hosted signing sandbox; separate signed-unpaid lease with one combined initial invoice |
| C05 | Active lease, initial payment/move-in, recurring job period, maintenance/evidence/cost and independent amendment/renewal/extension cases |
| C06 | Separate clean unfunded cancellation, unpaid invoice, captured funds/refund due, uncertain payment, notice/move-out, settlement/deposit/dispute/payout and replacement fixtures |
| C08/C09 | Distinct tenants/consents/group administrator/members/roster revisions, group visit/application; tenant request plus two/three comparable offers from correctly owned properties |
| S01/S02/S03 | Exact accommodation snapshots; saved-search event/job; routing/assistant providers; stable keys, receipts and controlled lost-response/restart/account-switch cases |

The reply's extended JSON contains none of the required signed/active lease, invoice, attempt, deposit, handover, settlement, group or request IDs. Seeded intermediate states are setup data, not proof that API transitions ran.

Return `fixtures.json` with verified `legacy` and unchanged `banner` sections plus an extended manifest for these cases. Preserve the existing private journal; never regenerate an unresolved key. Include fixture-set ID, actor/parent relationships, expected states, revisions, expiry and scoped cleanup rules. Supply a repeatable billing-period/job trigger for dedicated QA fixtures so recurring tests do not require waiting a calendar month.

## 6. OPEN-06 / OPEN-07: prove transitions and external effects

Run invitation → acceptance/replay → eligible picker → draft → consumed invitation → cancellation/replay on the newly provisioned source. Read **collections first**, then detail/center for both parties; repeat in another order on a separate untouched fixture. All projections and the mutation must agree immediately, with no GET required to finish a transition or increment revision.

Clarify the reply's `status:"closed"` wording. Keep lifecycle status `cancelled`/`canceled` distinct from **`financial_closure_status:"closed"`** and `occupancy_status:"not_started"`. Do not replace lease lifecycle status with financial closure or grant new permissions from that conflation.

Evaluate authoritative obligations during transitions. No occupancy can waive handover, but it does not settle an invoice, captured deposit, pending/unknown payment, failed refund or dispute. Test late capture racing cancellation, bounded refunds, ledger conservation, duplicate callbacks and no restoration of consumed consent. Run concurrency cases on PostgreSQL using independent transactions; Django documents the relevant [locking/test behavior](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update).

Verify the agreed order: **final signatures → 48-hour inventory hold and one initial rent/deposit invoice → required successful capture → active agreement → move-in**. Return actual signing/PSP/KYC/refund/payout sandbox correlations, invoice/deposit/ledger readbacks, callback signature checks and worker/job IDs. Mock payment evidence must stay labeled mock.

For chat, return both-party persistence/delivery, rollback suppression, reconnect/history catch-up, duplicate message-key handling and process/broker restart recovery. `transaction.on_commit` runs after commit; it does not itself establish durable delivery after process loss. A source claim of an outbox needs records and recovery-test evidence. [Django transaction callbacks](https://docs.djangoproject.com/en/5.1/topics/db/transactions/#performing-actions-after-commit).

Coordinate verified backend capabilities with the appropriate Flutter build flags. `SOKOUN_LEASE_SIGNING=true` alone cannot enable all journeys; keep `SOKOUN_BYPASS_VERIFICATION=false` and enable only capabilities backed by verified services.

## 7. OPEN-01-V: remaining storage and placement verification

For the existing advertisement `85295dd1-f8bd-4c82-a903-9bdc3d90af98`, prove the same **28,970 bytes**, SHA-256 `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`, survive replica change, process restart and redeploy. Return storage adapter/object identity and before/after evidence without storage secrets. A source-embedded audit asset or disk restoration helper alone does not prove deployment durability or general uploaded-media persistence.

The immediate placement read at **13:57:47 UTC** was an empty cached response (`Age:12`, `max-age=60`, response `server_now` before activation). It was still empty at **13:58:31**, and the original ad was visible at **13:59:02**, after that cache entry's lifetime. This is observed cache delay, not an ongoing missing-banner claim. Specify the permitted publication visibility bound and test it. If publication must be immediately visible, invalidate the relevant placement cache after committed activation; otherwise document and verify the bounded delay, including edge caches.

Retain the original create operation `74682688-4428-413c-a1ae-c4b87222c687` and mock operation `74682688-4428-413c-a1ae-c4b87222c687-payment`, receipt and activation dates during these tests. Do not reset or re-create this advertisement or operation.

## 8. OPEN-09: return deployment proof and runnable inputs

Return a completed response with:

1. Full commit SHA/image digest, deployment ID and UTC time for API, worker, scheduler and WebSocket; installed Python/Django/DRF/PostgreSQL versions and schema artifact/hash.
2. Sanitized deployed-settings outputs and exit statuses for the commands below; applied migrations/backfills and any unresolved result. Model drift and unapplied migrations are separate checks. Use the appropriate commands for the installed Django version; reference: [Django management commands](https://docs.djangoproject.com/en/5.1/ref/django-admin/).
3. Actual fixture command output, runner/extended JSON, current actor IDs/private login inputs and real subject/action grants. Verify every manifest record through the intended account before returning it.
4. Per-item implementation commit, public-URL verification command, UTC time, status, sanitized request/response and artifact. Report implemented, deployed and verified separately.
5. Provider/job/ledger/event evidence, both participants' readbacks, unrelated-actor denials and remaining dependency owner/next action. Include a compatible rollback/recovery procedure that preserves operation identities.

```bash
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
python manage.py migrate --check
```

Prove rejected visits accept `reason:"timing_not_suitable"` and the optional `custom_reason` on a real pending fixture. This is runtime verification of your confirmation, not a request to invent a new enum. Preserve invitation `revision`, structured rental `expected_revision`, and advertising `operation_id` as their separate contracts.

After setup, mobile/QA can run from `apps/sokoun_app` with fresh evidence paths:

```bash
make ownerTenantCyclesApiLive CYCLES_REUSE_SESSIONS=true SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory CYCLES_EVIDENCE_DIR=/fresh/http-evidence
make ownerTenantCyclesLive FLUTTER=/path/to/flutter SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory CYCLES_EVIDENCE_DIR=/fresh/combined-evidence
```

Saved-session reuse applies to the HTTP runner; fresh Flutter authentication still needs current login inputs. These targets automate reads and conditional C03/C07 regressions, not every full-cycle provider/job/device journey. Keep blocked cases visible and complete the remaining scenarios above before declaring full-cycle readiness.

Supporting evidence in the mobile repository: [latest HTTP report](../qa/evidence/owner-tenant-current-fixes-reply-2026-10-12/scenarios-resumed/cycle-report.json), [Flutter checks](../qa/evidence/owner-tenant-current-fixes-reply-2026-10-12/flutter-live-read.json), [fixture/locale preflight](../qa/evidence/owner-tenant-current-fixes-reply-2026-10-12/preflight/), [fixture/payment follow-up](../qa/evidence/owner-tenant-current-fixes-reply-2026-10-12/followup/), [onboarding subject grant](../qa/evidence/owner-tenant-current-fixes-reply-2026-10-12/payment-profile-scope/), [placement after cache expiry](../qa/evidence/owner-tenant-current-fixes-reply-2026-10-12/placement-after-ttl/). The concrete instructions and identifiers are included here so this file can be sent alone.
