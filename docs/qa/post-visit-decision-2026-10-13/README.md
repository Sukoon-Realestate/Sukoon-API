# Post-visit decision backend implementation and local evidence

Date: 2026-10-13. Companion specification: `darak-app/SOKOUN_POST_VISIT_DECISION_CODEX_IMPLEMENTATION.md`.

Implemented in this backend checkout. No commit, push, deployment, shared-server request, real payment/signature, or customer notification was performed. The user owns release. Mobile implementation and device evidence are recorded separately in the companion app.

## HTTP contract

All routes require the existing authenticated account. IDs in the examples below stand for actual authorized UUIDs.

`POST /api/v1/properties/visits/{visit_id}/post-visit-decision/`

```json
{
  "decision": "proceed",
  "attended": true,
  "expected_revision": 1,
  "request_key": "operation-uuid"
}
```

For `decline`, add a required `reason`. Leading/trailing whitespace is trimmed; interior Arabic/English text, punctuation, newlines and emoji are preserved. The maximum is 1,000 **Unicode code points**: Python `len(str)` and Dart `runes.length`, not UTF-16 units or grapheme clusters. Proceed rejects a supplied reason, even an empty one. The request requires JSON boolean `true`, not a truthy string.

The successful initial submission and authorized replay both return HTTP 200 in the existing `{status, message, data}` envelope. `data` contains the full tenant visit detail plus:

```json
{
  "revision": 2,
  "offer_id": "offer-uuid",
  "offer_snapshot": {},
  "post_visit_decision": {
    "id": "decision-uuid",
    "visit_id": "visit-uuid",
    "value": "proceed",
    "attended": true,
    "attendance_source": "tenant_attestation",
    "attested_at": "server-timestamp",
    "created_at": "server-timestamp",
    "visit_revision": 1
  },
  "post_visit_actions": {
    "can_submit": false,
    "eligible_at": "scheduled-start-with-Cairo-offset",
    "blocked_reason": "decision_already_recorded"
  },
  "rental_continuation": {
    "status": "awaiting_owner_invitation",
    "next_actor": "owner",
    "next_action": null,
    "blocked_reason": null,
    "source_visit_id": "visit-uuid",
    "source_decision_id": "decision-uuid",
    "invitation_id": null,
    "agreement_id": null,
    "invoice_id": null,
    "compatibility_version": "visit_decision_v1"
  },
  "operation": {"request_key": "operation-uuid", "status": "recorded"}
}
```

This example is the tenant projection. The authorized owner instead receives `next_action: create_rental_invitation` when contracting is available. The ordinary tenant visit detail/list, owner visit request detail/list, and generic authorized visit responses include the same additive context. Owner detail is `/api/v1/properties/owner/visits/requests/{visit_id}/`.

`GET /api/v1/properties/visits/{visit_id}/post-visit-decision/?request_key={uuid}` is read-only recovery. It serializes with any transaction already holding the visit lock and returns current canonical state plus `operation.status: recorded|absent`, scoped to account and visit. GET does not submit, expire, revoke or create anything. Both methods set `Cache-Control: private, no-store`.

Operation semantics:

- Same key and normalized original payload returns the current canonical decision without a duplicate event.
- Same immutable value/reason with another key returns the existing decision and stores an alias operation receipt. No second decision or notification is created, even with the older accepted visit revision.
- Same key with different payload/visit is HTTP 409 `idempotency_conflict`. Opposite choice or changed reason is HTTP 409 `decision_conflict`.
- The immutable decision retains its original key and accepted revision. Original-key recovery/replay still works if auxiliary idempotency records are later removed. Aliases follow existing idempotency retention.
- After an uncertain transport or 5xx result, keep the original request identity and reconcile before another choice. The server returns `decision_request_failed` for unexpected errors without exposing private request/exception content.

## Eligibility, privacy and provenance

Server eligibility requires the visit's tenant, confirmed current appointment, current scheduled time reached, no saved decision, and no progressed/grandfathered journey to resume. Eligibility uses `Africa/Cairo` and server time. Revision changes cover appointment status/date/time, participants, property, offer and offer snapshot. Decision and appointment mutations lock the same row; stale edits, cancellation/rescheduling races, and contradictory decisions cannot overwrite an accepted decision.

The current model has **no scheduled end, trusted completion, no-show, or superseded status**. V04 is therefore a documented schema limitation, not a tested existing no-show rule. The start time is the earliest eligibility time and `tenant_attestation` is the explicit tenant statement; it is not independent attendance evidence. A future completion/no-show feature must be integrated into this eligibility service.

The reason exists only on the immutable decision. It is visible to the submitting tenant and active existing `StaffProfile` roles `support`/`system_owner`. Property ownership never grants the reason; `is_staff` alone does not grant it. Support GET omits invitation/agreement/invoice IDs and actor actions. No new admin feedback product or general staff permission was added.

Owner detail/list/received/generic projections, notification content/payloads and idempotency response storage omit the reason. Existing configured middleware and DRF exception handling do not log request bodies. The new endpoint catches unexpected failures before generic Django crash reporting and logs only visit ID, actor ID and exception class. Failure-injection tests verify rollback, recoverable absent status, and absence of the private text from response/logs. The decision is not registered in Django admin; existing admin property/report queries do not project it.

New direct `POST /api/v1/features/v1/tenancy-invitations/` requests must include `source_visit_id` and `source_decision_id`. The server checks exact visit, tenant, property, current owner, saved `proceed`, and visited offer. Existing account/property/availability checks remain enforced. Positive feedback creates no invitation, interest, lease, inventory reservation, payment or signature automatically.

Offer-aware visits cannot change the offer or physical room/bed/scope under the same offer ID. Property-only visits require explicit valid selection when the property's current inventory requires one. Structured draft creation validates source provenance and the accepted invitation's exact offer revision/snapshot, then uses the existing inventory hold and both-party review/signing workflow. Draft edits cannot change the physical accommodation. A new-key submit-for-signature cannot regenerate a document after signing has started; original-key replay remains available.

Independent interest-origin invitations remain valid with `independent_interest_v1`. Existing invitations are explicitly grandfathered as `historical_v0` without fabricating positive decisions. A unique matching historical invitation/agreement can be resumed; ambiguous historical contexts block new visit feedback without guessing a resource link. Later property ownership does not confer access to a previous owner's invitation/agreement.

## Continuation and notification contract

Exact `next_action` values are `submit_post_visit_decision`, `create_rental_invitation`, `open_invitation`, `open_agreement`, `open_invoice`, `setup_owner_payments`, or null. `next_actor` is `tenant`, `owner`, `both`, or null. Actions are actor-specific; resource links continue to require their original participant authorization.

Statuses are `visit_not_eligible`, `awaiting_tenant_decision`, `awaiting_owner_invitation`, `contracting_blocked`, `declined`, `invitation_pending`, `invitation_accepted`, `invitation_rejected`, `invitation_expired`, `invitation_revoked`, and `agreement_{actual_lease_status}`. Agreement states include draft, pending_signatures, signed, active, ended, cancelled and expired; legacy pending/termination_pending remain represented by their actual lease state. Due/overdue invoices become the tenant action after signing/activation. Terminal invitation and agreement states never revert to a misleading waiting-for-owner message.

Validation codes include `invalid_decision`, `attendance_required`, `reason_required`, `reason_too_long`, `reason_not_allowed`, `invalid_request_key`, `source_visit_required`, `source_decision_required`. Conflict/blocking codes include `stale_revision`, `decision_already_recorded`, `decision_conflict`, `idempotency_conflict`, `visit_not_confirmed`, `visit_not_started`, `continuation_exists`, `source_mismatch`, `offer_mismatch`, `ownership_changed`, `property_unavailable`, `offer_unavailable`, `owner_access_changed`, `tenant_access_changed`, `accommodation_changed`, `allocation_conflict`, and signing's existing `invalid_state`. Wrong actors receive the existing privacy-preserving 404/401 conventions. Existing downstream errors/messages remain supported.

Each committed decision atomically creates one durable `PlanningEvent` and one in-app notification. Event payload: `event_kind=visit_post_decision`, `action_type=view_visit`, `workspace=owner`, `target_id=visit_id`, plus `property_id`, `source_decision_id`, `schema_version=1`, `event_id`. No free-text reason. Existing invitation/agreement notifications also carry `source_visit_id`/`source_decision_id` when linked, so clients can refresh the relevant visit.

The existing `process_planning_jobs` task drains the shared outbox every 30 seconds. Retry uses the same event/notification, at least two minutes between attempts and at most five attempts. Before sending, delivery rechecks recipient/current owner, exact decision/visit and matching target ID. Failed pushes leave committed feedback visible. FCM failure with an active eligible device remains pending; no device or disabled push preference requires no send. This establishes durable local state and retry behavior, not real-device receipt or provider exactly-once delivery.

## Migrations and release order

The workspace already contained planning work. Its generated migration names are preserved because they may have been applied elsewhere. Deploy the complete migration graph; do not rename, split, omit or fake these dependencies:

1. `properties.0021_planning_report_integrity` depends on `properties.0020_propertyvisit_accepted_at`. Adds visit revision (existing rows start at 1), the decision table, unique tenant/key constraint, one decision per visit, attended and value/reason-shape constraints.
2. `features.0013_planning_completion` depends on `features.0012_planning_cycles` and `notifications.0008_alter_notification_notification_type`. Existing concurrent planning migration supplies the durable `PlanningEvent` table and its recipient/event uniqueness, plus its other planning changes.
3. `features.0014_planning_report_integrity` depends on **both** the migrations above. Adds invitation source visit/decision foreign keys, provenance version, and at most one live unconsumed invitation per visit. It also includes the existing condition-report/deposit changes; preserve them.
4. `features.0015_post_visit_invitation_compatibility` depends on 0014. Tags every existing invitation with both source links null as `historical_v0`; it preserves status, revision, lease, receipts, amounts and participant data. Rows with explicit new source links are unchanged. The reverse is a no-op because reverting would misrepresent historical provenance. No decision or attendance is backfilled.

Run the normal reviewed backend release with all these files. Before serving the new API/mobile flow, run `python manage.py migrate --noinput` using the deployment's existing configured settings and database, then `python manage.py check`. Restart API and existing worker/beat processes on the same code/schema. Preserve existing provider/runtime configuration; this feature does not enable mock providers in production. Ensure the deployed worker/beat includes `process-planning-jobs`, then rebuild/release the companion app. Older direct-invitation clients that omit provenance will receive the explicit validation failure; historical existing journeys continue.

Post-deployment acceptance should use controlled test accounts: eligible visit -> tenant decision -> owner invitation -> tenant acceptance -> owner readiness -> structured draft -> both reviews -> separate signatures -> initial invoice. Also verify declined reason privacy, interrupted save recovery, forbidden actors, owner notification refresh and current-provider/device behavior. Local evidence below does not establish any deployment outcome.

## Local verification

Python 3.11.17, Django 4.2.11, PostgreSQL 16.15; disposable UTF-8 loopback cluster, explicit `config.settings.postgres_test`, test-owned accounts and existing fake rental provider. No production database or credentials were used.

Final command from `backend/` (artifact input is the already exported real Flutter request bodies):

```bash
SOKOUN_POST_VISIT_ARTIFACT_DIR=../docs/qa/post-visit-decision-2026-10-13 \
SOKOUN_PLANNING_ARTIFACT_DIR=/private/tmp/sokoun-post-visit-contracts \
SOKOUN_CONTRACT_ARTIFACT_DIR=/private/tmp/sokoun-post-visit-contracts \
SOKOUN_FLUTTER_REQUEST_BODIES=/private/tmp/sokoun-cycle-contracts-20261013/flutter-request-bodies.json \
TEST_POSTGRES_DB=postvisit TEST_POSTGRES_USER=postvisit \
TEST_POSTGRES_HOST=127.0.0.1 TEST_POSTGRES_PORT=55441 \
.venv/bin/python -m pytest core_apps --ds=config.settings.postgres_test \
  -q --tb=short \
  --junitxml=../docs/qa/post-visit-decision-2026-10-13/backend-postgres.xml
```

Final full suite: **812 passed, 0 failed/errors, 0 skipped**, in 63.057 seconds, including 41 post-visit tests and all eight actual Flutter request-body roundtrips. The earlier focused integration regression passed 96 tests. The final suite includes actual JWT/loopback HTTP, PostgreSQL races, existing independent interest/planning/rental cycles, the new direct visit-to-invoice journey, private failure logging and compatibility data migration. Existing dependency/staticfiles/date-fixture warnings remain non-failing.

Additional checks: `manage.py check --settings=config.settings.test`; `manage.py makemigrations --check --dry-run --settings=config.settings.test`; critical Python lint (`flake8 --select=E9,F63,F7,F82` on changed services/views/models); formatting of new files; `git diff --check`. Fresh complete migrations were also applied to the owned loopback database, with output in [migrations.log](migrations.log).

Evidence:

- [backend-postgres.xml](backend-postgres.xml): final full-suite machine-readable result.
- [backend-postgres.log](backend-postgres.log) and [verification-summary.json](verification-summary.json): exact final count, runtime and selected coverage counts.
- [django-visit-context.json](django-visit-context.json): eight actual local Django response scenarios for Flutter parsing (eligible, proceed tenant/owner, invitation/context, decline tenant/owner, historical). UUIDs and fixture identities are test-owned; no auth tokens or passwords.
- `backend/core_apps/properties/tests/test_post_visit_decision.py`: persisted decision/privacy/recovery/race/provenance/compatibility and full both-party HTTP signature-to-invoice tests.

The final suite also regenerated `/private/tmp/sokoun-post-visit-contracts/django-cycle-contract.json` with active lease, initial invoice, capabilities, onboarding, signing sessions/completions, payment attempt, deposit and checkout responses for the existing optional Flutter contract test. Planning and complete HTTP-cycle artifacts are alongside it. The eight-scenario visit artifact above is retained in this repository for the new feature's client parser tests.

Concrete shared journey repairs discovered during integration: misplaced renewal-only guards were moved out of maintenance creation to the proper locked renewal creation path; maintenance's own revision check remains. Renewal tests now use continuous periods. The existing group HTTP fixture now explicitly creates the tenant's independent rental interest after group approval, matching the current consent contract.

The QA seed command intentionally still creates future confirmed visits without attendance claims. Its `legacy.source_visit_id` is not proof of eligibility. A controlled QA run must reach the scheduled time, attest as the tenant, and record `proceed` before the direct invitation runner can run. Do not bypass this rule for old pending-only fixtures. The isolated seed-execution test adjusts only its own test appointment to the past and calls the authenticated tenant POST. Seeded statuses and local provider responses are not external execution evidence.

Provider/device boundaries: documents and each signer's completion use the existing explicit fake provider; both actual local server state transitions and invoice creation are checked, with no premature activation. Real e-signature/KYC/payout/payment providers, shared-server deployment, FCM device delivery and native UI are outside this backend run.

## Changed backend files and local cleanup

Post-visit implementation: `properties/models/visit.py`, `models/__init__.py`, `services/post_visit_decision.py`, `views/post_visit_decision.py`, `serializers/visit.py`, `urls.py`; `features/models.py`, `serializers.py`, `views.py`, `rental_phase2_views.py`, `services/tenancy_invitations.py`, `services/planning_notifications.py`; the preserved mixed migrations and compatibility migration described above. Shared journey repair: `features/rental_phase5_views.py`.

Tests/fixtures updated: `properties/tests/test_post_visit_decision.py`, `test_views.py`, `test_visit_request_api.py`; `features/tests/test_tenancy_invitations.py`, `test_cycle_qa_setup.py`, `test_change_recovery.py`, `cycle_http_sources.py`. `WORKLOG.md` records completion. Other existing planning/revocation work remains in this dirty checkout and is included in the full regression without being reset.

The owned temporary cluster is identified by `/private/tmp/sokoun-post-visit-pg.json` (directory and loopback port 55441). Shutdown command, using its exact `root` value:

```bash
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D '<root>/data' -m fast -w stop
```

Only that cluster is owned by this verification. It was stopped successfully after all tests/artifacts completed; [local-cleanup.json](local-cleanup.json) records exit code 0. Its directory/metadata and saved artifacts are retained for reproducibility; no other PostgreSQL server or shared database was stopped or deleted.
