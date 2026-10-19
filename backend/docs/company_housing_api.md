# Corporate housing and residential portfolio API

Local implementation reference, 2026-10-16. These endpoints implement owner inventory, staff preparation/activation, simultaneous account contexts, company planning/discussion, assigned approval, budget reservation and bounded allocation. Corporate contracting, signing, payment and occupancy are **not yet available**. Do not connect the existing personal lease APIs by using a coordinator as tenant.

## Contract and access

Prefix: `/api/v1/features/v1/`. Use authenticated existing session/JWT transport and `Accept-Language: ar` or `en`. The common controlled response contract is retained:

```json
{
  "message": "A nonempty localized message",
  "data": {
    "resource": {"id": "a UUID", "revision": 1},
    "operation_receipt": {
      "id": "receipt UUID",
      "subject_id": "same resulting resource UUID",
      "request_key": "same submitted operation UUID",
      "revision": 1,
      "status": "confirmed"
    }
  }
}
```

Domain commands require `request_key` (stable UUID) and `expected_revision` (integer ≥0). Token preview and bounded code verification have the separate contracts described below; chat retains its existing client-message/upload identities. New independent resources start from zero; updates use the current subject revision. Selecting an offer uses the **request** revision and the offer revision but returns a new booking item at revision 1. The child's result revision must not be compared with the parent's previous revision.

Command execution uses `rental_lifecycle.common.command`: active verified actor, authorization before receipt replay, actor/root locks, immutable request fingerprints and canonical `IdempotencyRecord`. Same intention/key replays the original receipt. Different content with a used key is a conflict. Recover an uncertain command through the existing `/rental-operations/{request_key}/` contract, then fetch the resulting authorized resource. No command reports a redirect or client flag as payment/signature success.

GET detail responses contain their projection directly in `data`. Paginated lists contain an array in `data`; pagination uses the existing `X-Page`, `X-Per-Page`, `X-Total-Count`, `X-Total-Pages`, `X-Next-Page` and `X-Previous-Page` headers. `page` and `page_size` are supported, default 20, maximum 100. The Flutter transport reconstructs its existing `results` page representation. Do not add a third response-envelope key. Private responses have `Cache-Control: private, no-store`.

Errors preserve the existing status/message/data-null convention and `X-App-Error-Code`. Conflicts do not disclose another tenant's identity. Validation rejects unsupported fields rather than silently accepting client flags such as `approved`, `available` or `paid`.

Batch result messages are localized on detail reads without rewriting the persisted result. Staff authority-review receipts can be recovered by the initiating reviewer while the required staff role remains valid; this does not grant company membership or owner action permissions. Flutter excludes these private exchanges and their recovery responses from debug payload logging.

## Endpoint inventory

| Method | Path | Authorization / behavior |
| --- | --- | --- |
| GET | `company-capabilities/` | Reports new-business flag, portfolio creation, unavailable corporate contracting/payment. |
| GET, POST | `companies/` | List own active memberships / create company plus admin-only membership. |
| GET | `companies/{id}/` | Active membership; sensitive settings only to authorized roles. |
| GET | `companies/{id}/members/` | Company admin. |
| POST | `companies/{id}/members/{membership_id}/` | Admin; revision/last-admin/coordinator-work guards. |
| POST | `companies/{id}/invitations/` | Admin; issue recipient-bound token, no message delivery. |
| GET | `company-invitations/{id}/` | Initiating active admin; recover same token until used/revoked/expired. |
| POST | `company-invitations/accept/` | Exact logged-in recipient, valid unused token. |
| GET | `companies/{id}/occupants/` | Coordinator; minimal active employee identities, no private personal-rental data. |
| POST | `companies/{id}/budget/` | Admin; cannot reduce limits below reserved/committed obligations. |
| GET, POST | `companies/{id}/housing-requests/` | Assigned coordinator/approver read; coordinator creates. |
| GET, POST | `company-housing-requests/{id}/` | Read: assigned coordinator or assigned approver. POST: assigned active coordinator may correct a request before any package exists, with original operation identity and expected revision. |
| POST | `company-housing-requests/{id}/coordinator/` | Admin explicitly reassigns to an active coordinator. |
| POST | `company-housing-requests/{id}/items/` | Coordinator selects exact published offer and receives immutable package. |
| POST | `company-booking-items/{id}/submit/` | Assigned coordinator, fresh quote and configured independent approver. |
| POST | `company-booking-items/{id}/decide/` | Currently assigned independent active expense approver. |
| POST | `company-booking-items/{id}/hold/` | Coordinator; reviewed company, fresh approval/offer/policy/availability, budget and owner readiness. |
| POST | `company-booking-items/{id}/withdraw/` | Coordinator; uncommitted packages only, remains available when new bookings are disabled. |
| GET, POST | `residential-assets/` | Own managed containers / create building or complex. GET requires `kind=building|complex`. |
| GET, PATCH | `residential-assets/{kind}/{id}/` | Exact manager; units, counts, facts/defaults, authority and capacity. PATCH uses the complete typed container body and current revision. |
| POST | `residential-assets/{kind}/{id}/attach-unit/` | Attach original owned standalone unit under version/topology checks. |
| GET | `residential-unit-templates/` | Own existing unit facts, no bookings or verified-evidence cloning. Optional `unparented=true`. |
| POST | `residential-unit-batches/` | Submit/retry up to 100 independently identified rows. |
| GET | `residential-unit-batches/{id}/` | Batch owner; cumulative draft/results/revision. |
| GET, POST | `portfolio-offers/` | Owner creates or reads with `owner=true`; coordinator discovers with `company_id`. |
| POST | `portfolio-offers/{id}/publish/` | Owner; complete exact inventory and authority required. |
| POST | `portfolio-offers/{id}/pause/` | Owner; prevents new progression without erasing snapshots/commitments. |
| POST | `company-authority/{company|building|complex}/{id}/review/` | Independent staff reviewer, evidence reference, reason and current revision. |

For date-specific discovery send `company_id` and `request_id`. The backend verifies that both refer to the same authorized company and checks the complete request interval plus configured turnover. `available_for_dates: null` means no date check was made. This is basic scoped discovery; full city/commute/accessibility/budget search is pending.

## Owner bodies

Building creation:

```json
{
  "request_key": "10000000-0000-4000-8000-000000000001",
  "expected_revision": 0,
  "kind": "building",
  "name": "Synthetic Building A",
  "code": "A",
  "address": "Synthetic Cairo address",
  "description": "Synthetic demonstration only",
  "declared_units": 12,
  "floors": 3,
  "facilities": ["elevator", "shared_laundry"]
}
```

Optional `complex_id` must identify the actor's existing authorized container. Name ≤200 characters, code ≤40, address ≤500, description ≤5000, up to 30 facility facts ≤100 characters each, units 1–500, optional floors 1–200. Facilities are factual descriptions, not guaranteed services. No authority status is accepted from the owner.

Complex uses `kind: complex`, `declared_buildings` (0–100) and `declared_standalone_units` (0–500), with at least one child declared. It rejects `floors`, `declared_units` and `complex_id`. It shares identity/address/facility fields with the building body.

Batch body:

```json
{
  "request_key": "10000000-0000-4000-8000-000000000002",
  "expected_revision": 0,
  "batch_key": "10000000-0000-4000-8000-000000000003",
  "template_id": "20000000-0000-4000-8000-000000000001",
  "parent_kind": "building",
  "parent_id": "30000000-0000-4000-8000-000000000001",
  "units": [
    {
      "item_key": "40000000-0000-4000-8000-000000000001",
      "unit_code": "A-101",
      "occupancy_capacity": 4,
      "floor": 1,
      "bedrooms": 2,
      "bathrooms": 1,
      "area": 85,
      "is_furnished": true
    }
  ]
}
```

Omit both parent fields for standalone units. Per-row `occupancy_capacity` is required and may be null (unknown), otherwise 1–1000. Optional title ≤255, bedrooms 0–100, bathrooms 1–100, area 1–100000, floor null or −10 through 200, and furnishing boolean. Every row has a unique UUID and nonempty unit code. Only whitelisted template facts/layout are cloned. Layout room/bed/offer IDs are regenerated; cloned offers are unavailable and verification/media are not copied.

The resource has `id == batch_key`, `revision`, `complete`, `draft` and cumulative `results`. Created rows contain `item_key`, `status: created`, `property_id`, `unit_code`; failed rows contain `item_key`, `status: failed`, `code`, `message`. For a partial retry retain the batch/template/parent identities, use the returned batch revision, a new command key, and the unresolved rows' original item keys. Successful IDs remain present. Changing an already-created row through retry is rejected.

Attachment body: command fields plus `property_id`, `inventory_revision`, `unit_code`, `occupancy_capacity`. The resulting resource is the incremented parent, not a cloned unit. Existing parents, commitments and stale revisions are rejected. Old `entire_property` semantics and historical IDs survive attachment.

Offer body: command fields plus `scope`, the corresponding identity field, `monthly_rent_minor` (1–10^12), `deposit_minor` (0–10^12), optional included/excluded service arrays (up to 50 descriptions of 200 characters), `occupancy_policy` and `publish` (default false).

| Scope | Required identity; all other scope identity fields rejected |
| --- | --- |
| `selected_units` | `unit_ids`: 1–500 exact owned unit UUIDs |
| `entire_building` | `building_id` |
| `selected_buildings` | `building_ids`: 1–100 exact managed building UUIDs |
| `entire_complex` | `complex_id` |

Occupancy policy is `named_occupants_required` or `reserve_capacity_with_notice`. Named-only packages currently require all capacity to have named initial employees. Reserve-enabled packages may contain no initial employees. The UI displays reserve capacity explicitly. This flag is not yet a signed contractual occupant-change policy.

## Company and request bodies

Company creation: command fields, `name` ≤200, `registration_number` ≤100, `contact_email`. Result is a pending company and admin-only membership. No payment/signing authority follows from being admin. Private current-user projection subsequently reports the same human ID with `account_kind: company`; no synthetic company user is created.

Legacy invitation compatibility: command fields, `email`, nonempty `roles` selected from `admin`, `coordinator`, `approver`, `employee`. The response contains `id`, revision 1, recipient email, token and seven-day expiry. Acceptance uses command fields plus `token` (32–200 characters). Tokens are hashed for matching and bound to the exact recipient. The initiating administrator's private operation receipt retains the original issued response for recovery. The new People screen uses staff preparation and server-delivered activation below instead; it never exposes activation secrets to administrators.

Membership update: current membership revision, `roles`, `is_active`, optional `can_execute_payments`, optional `reason` ≤1000. Signing authority is not writable through this endpoint. Rejoining clears old payment/signing grants. Final-admin removal and removal of a coordinator with active work are blocked.

Request creation:

```json
{
  "request_key": "10000000-0000-4000-8000-000000000004",
  "expected_revision": 0,
  "title": "Synthetic project team",
  "purpose": "Synthetic local demonstration",
  "cost_center": "TEST-PROJECT",
  "location": "Cairo",
  "starts_on": "2027-01-01",
  "ends_on_exclusive": "2027-02-01",
  "headcount": 40,
  "commitment_ceiling_minor": 5000000,
  "deposit_limit_minor": 1000000
}
```

Title ≤200, purpose ≤5000, cost center ≤100, location ≤300, headcount 1–10000, ceilings 0–10^12. Creation and correction require 1–120 whole calendar months, using the existing clamped month-end convention, and a server-current/future start. Quote/hold additionally apply the configured maximum-duration policy. A replay of an acknowledged original command remains recoverable after the start date passes. Request facts alone do not allocate accommodation.

Selecting an item: command fields using the current request revision, `offer_id`, `offer_revision` ≥1, `occupant_ids` (0–1000 exact active employee UUIDs), optional `staff_ids` (pending employee-eligible company staff UUIDs). The backend rejects duplicate/foreign/inactive people, resolves all units and capacity, checks the full date interval and current supported policy, then stores a 24-hour immutable package. Unknown capacity blocks approval progression. Offers from multiple owners become separate items.

The private item snapshot additionally includes `company_id`, `company_name`, `requester_id`, `requester_name`, `purpose`, `starts_on`, `ends_on_exclusive`, `occupant_ids`, `occupants` (`user_id` and display `name`), and `reserve_places`. Unit rows retain canonical IDs, unit codes, building/complex IDs and names, topology facts and physical conflict keys. Monthly rent/deposit include `amount_minor`, `currency: EGP` and `exponent: 2`; included/excluded service descriptions remain distinct. Occupant names are planned employees, not acknowledged assignments. These private employee facts are not added to owner/public offer projections.

Submission: command fields, current proposed item revision. Selects the company's current independent default approver and moves the item to `approval_pending`; no decision, inventory hold or charge occurs. Decision: current item revision, `decision: approved|rejected|changes_requested`, `snapshot_digest` (64 lowercase hexadecimal characters), reason required for rejected/changes-requested. Only the assigned eligible approver can decide. Requesters, coordinators and funded occupants cannot be sole approvers, including pending staff matching their work contact. A commercial revision can receive only one decision. The company root serializes aggregate budget checks across requests.

Hold: command fields only. Rechecks company review, active independent approver, unchanged offer/inventory/policy, quote/approval expiry, budget reservation, owner beneficiary readiness, every unit's fresh owner availability confirmation, supported dates and hold limit. A canonical `ReservationHold` references all allocated unit/day rows. The aggregate succeeds or fails locally as one transaction. No lease/invoice/payment is created.

Withdraw: command fields only; permitted without new-business flag. Releases uncommitted hold rows and reserved budget; refuses existing invitation/lease links or reconciliation/committed hold state. A withdrawn package cannot later receive a decision.

Budget settings: current company revision, nullable `budget_limit_minor`, nullable `deposit_limit_minor`, required reason. Null disables that shared limit. Request ceilings still apply. Existing reserved/committed obligations cannot be excluded by reducing a limit. The admin projection exposes `permissions.manage_budget`; Flutter uses a protected draft, exact EGP decimal inputs and an explicit review before this command. Reassignment: request revision, exact active `coordinator_id`, required reason; the original requester and approval independence do not change.

Authority review: current subject revision, `status: verified|rejected`, `evidence_reference` ≤200, required reason ≤1000. Company reviews require KYC staff, property scopes require property-review staff; self-review is rejected. Record the actual private review reference. This endpoint does not create evidence or automatically verify legal ownership.

## Staff, activation and work-contact verification

These routes use the same feature prefix, pagination, private response envelope and
command receipts described above. A staff record is company-owned preparation,
not a global login or active membership. Creating one does not change a person's
password, personal/student experience, verification or unrelated memberships.

| Method | Path | Authorization / behavior |
| --- | --- | --- |
| GET | `account-contexts/` | Current human; personal/student/company contexts with company-scoped roles/actions. |
| GET, POST | `companies/{company}/staff/` | Admin; list or prepare staff, no account enumeration. |
| GET, POST | `companies/{company}/staff/{staff}/` | Admin; detail or update unlinked active staff. |
| POST | `companies/{company}/staff/{staff}/activation/` | Admin; explicitly queue recipient-bound activation. |
| POST | `companies/{company}/staff/{staff}/revoke/` | Admin; revoke pending activation, not a personal account. |
| POST | `companies/{company}/staff-batches/` | Admin; at most 50 distinct reviewed rows. |
| GET | `companies/{company}/staff-batches/{batch}/` | Initiating admin; cumulative results and unresolved inputs. |
| GET | `companies/{company}/planning-staff/` | Coordinator; minimal pending employee identities, no work contact details. |
| POST | `company-access/preview/` | Authenticated user; token resolves company, proposed roles and eligibility only. |
| POST | `company-access/accept/` | Verified recipient; explicit acceptance, no automatic payment/signing grant. |
| POST | `company-access/decline/` | Verified recipient; decline this company proposal. |
| POST | `company-access/contact-proof/` | Authenticated existing user; queue proof for a different work email. |
| GET, POST | `company-access/contact-proof/{proof}/` | Same user; status or explicit bounded code verification. |

Staff body:

```json
{
  "request_key": "10000000-0000-4000-8000-000000000010",
  "expected_revision": 0,
  "display_name": "Synthetic employee",
  "employee_code": "TEST-001",
  "work_email": "synthetic@example.invalid",
  "mobile": "",
  "job_title": "",
  "department": "Test project",
  "project_code": "TEST",
  "roles": ["employee"]
}
```

Limits: display name 200, employee code 60, mobile 32, job title 150, department and
project code 100. `work_email` is validated and normalized. Nonblank employee codes
and work email are unique inside the company. Roles are distinct supported presets
(`admin`, `coordinator`, `approver`, `employee`); proposals grant no active access.
`password`, `user_id`, payment/signing flags and unsupported fields are rejected.
Linked staff contact/role changes require a separate supported workflow; this
endpoint does not rewrite the individual's identity.

Batch body: command fields, stable `batch_key`, `rows`, each with stable `row_key`
and the staff fields above (no nested command fields). The result identifies every
created/failed row and retains each successful `staff_id`. Retrying with the same
batch and returned revision cannot duplicate successes. Submitted row content and
identities remain immutable; corrected content uses a new reviewed batch. The
`draft` preserves unresolved inputs for recovery. Batch creation sends no messages.

Activation/revocation use command fields with the current staff revision. Activation
requires the new-business flag, an active issuing administrator and a delivery
cooldown. Tokens are valid for seven days, recipient/company/staff/proposal bound,
single use, and stored only as digests. Resend or recipient/role changes revoke old
proposals. Worker delivery derives the scoped secret with the server key. Rotating
that key requires an explicit resend. Administrator responses and receipts never
include the token or an indication of an unrelated existing personal account.

Preview sends `{ "token": "the received activation secret" }`; it is not cached or
stored as a command. Acceptance/decline adds `request_key`, `expected_revision` and
the reviewed `proposal_revision`. A matching verified login email or a verified
work-contact proof for this same logged-in user is required. Accepting twice does
not create two memberships or reactivate a subsequently offboarded member.

For work-contact proof, send command fields and `token` to the proof collection.
Read the returned proof by ID; post `{ "code": "12345678" }` to verify. The code is
valid at most ten minutes, limited to five attempts, and bound to user/provisioning.
Invalid attempts commit before the validation response. Successful repeated
verification does not consume another attempt. Verification returns a direct proof
projection (no operation receipt) and does not accept membership. Explicit
activation acceptance still follows. The app never stores or automatically replays
verification codes. These endpoints share an authenticated 20/hour throttle;
work-contact resends also use a recipient-scoped cooldown across accounts.

`COMPANY_ACTIVATION_EMAIL_ENABLED` defaults false. The existing planning worker
drains durable activation/proof intentions with provider I/O outside database locks.
Delivery `queued`, `sending`, `sent`, `failed`, `unknown`, `cancelled` is separate
from membership acceptance. Stalled sending becomes unknown; unknown delivery is
not blindly retried. Tests use the in-memory email backend. Production transport,
worker execution and hosted activation links have not been verified; current
Flutter entry accepts the received code under Companies → Activate company access.

## Assigned approval, work and case discussions

| Method | Path | Authorization / behavior |
| --- | --- | --- |
| POST | `companies/{company}/approval-route/` | Admin; current company revision, default/backup active approver and reason. |
| GET | `companies/{company}/work-items/` | Membership; only the actor's current domain tasks. |
| POST | `company-booking-items/{item}/reassign/` | Admin; current item revision, explicit eligible approver, reason. |
| GET | `companies/{company}/housing-requests/{request}/discussion/` | Assigned case coordinator/approver; existing canonical conversation summary. |

Route configuration adds nullable `default_approver_id` and `backup_approver_id`
(membership IDs) and a required reason. Backup must differ from default. Admin
projections include their display names; these settings are not added to employee
projections. Reassignment adds `approver_id` (membership ID), required reason and
current item revision. It changes assignment explicitly, with audit/event records;
it is not an automatic fallback after a rejection or absence.

My Work is derived from current booking state. An ordinary admin may receive a
metadata-only reassign task, without private commercial totals/snapshot. An eligible
assigned approver receives the decision action; stale/revoked assignments cannot
decide. `due_at` reflects quote expiry. No task-complete flag can replace approval,
signing or payment. Notification intentions use the existing durable `PlanningEvent`
service and recheck assignee/version before delivery.

Housing request creation provisions `Conversation(kind=company_request)` with a
one-to-one request relationship. Participants reference `CompanyMembership`, not
housing-group memberships. Only the current coordinator and assigned approvers
receive case access. Owners, employees and unassigned admins do not automatically
join. Membership/assignment changes revoke old access and synchronize current
participants transactionally; an authorized successor receives retained case history.

The summary identifies `id`, `conversation_type`, `company_id`, `company_name`,
`request_id`, current participant revision and the normal chat cursor/permission
fields. Sending, uploads, read cursors, muting, replies, deletion, event catch-up,
private media and sockets reuse the canonical chat endpoints and client identities.
The existing group-summary endpoint does not substitute for the company summary.
Company threads are excluded from the personal/group inbox. Every read, write,
media grant, socket event and delayed notification checks current case membership.

Submission, reassignment and decisions append system cards containing canonical
company/request/item IDs and the relevant revision in the same domain transaction.
Cards are references, not mutable financial documents; open them by fetching the
current authorized request. Chat text such as "Approved" cannot record a decision.
Company discussion notifications carry `action_type: open_company_discussion`,
company/request/conversation/message identities and no private message or price
preview. Employee-HR, owner-commercial and private stay channels remain pending.

Migrations in this increment: features `0032_company_staff_access_and_approval_routing`,
`0033_company_staff_batch_recovery`, `0034_company_work_contact_proof`; chat
`0007_company_request_discussions`, `0008_backfill_company_discussions`. The backfill
uses historical models and current assigned case grants. It is deliberately
irreversible: rollback must not silently erase retained business conversations.

## Inventory, revisions, fees and recovery

Models and services: `properties/models/portfolio.py`, `features/company_models.py`, `features/services/company/`, and canonical `rental_lifecycle/inventory.py`. Migrations: properties `0022_company_portfolio_foundations`, `0023_portfolio_batch_recovery`; features `0030_company_portfolio_foundations`, `0031_company_authority_review`.

Root locks precede descendant enumeration. Whole scopes require exact declared completeness and consistent reviewed contracting authority. All modes allocate the same physical day rows. Conflicting personal rooms/beds/units reject a parent hold; selected scopes leave unrelated resources free. Dates use exclusive ends. No topology edit or added child may bypass an active aggregate hold. Parent identities and historic scope are retained; previewed uncommitted moves/splits/merges are supported, with unsafe changes under allocations/leases blocked. Retired split/merge predecessors remain hidden historical identities with successor links.

Monthly EGP/exponent-2 policy remains owner commission 1000 bps on first-period base rent, platform processing and zero renewal commission. Parent offer prices are explicit bundle prices. Deposit is counted once per bundle. Known full-term rent, reserved budget, committed budget, cash, deposit liability and refunds must remain distinct. This increment implements reservations and projection scaffolding; it does not implement corporate cash movement or committed-budget transfer on signing.

`GET company-capabilities/` reports corporate contracting and payment false. `CompanyBookingItem` has nullable canonical hold/invitation/lease relationships; only the hold link is populated by this implementation. `EmployeeAssignment` is a foundation model without exposed workflow. Do not create these downstream records through admin to simulate completion.

## Local verification and rollout limits

Use the existing `config.settings.postgres_test` with an isolated local database via `TEST_POSTGRES_DB`, `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD` if required, `TEST_POSTGRES_HOST`, `TEST_POSTGRES_PORT`. Never point these tests at production. The tests override the new-business flag and seed clearly synthetic reviewed/readiness records.

```sh
.venv/bin/python -m pytest --ds=config.settings.postgres_test core_apps/features/tests/test_company_housing.py
.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

The earlier portfolio foundation passed 34 company tests. The current combined run passed **230 tests**, including 62 company tests plus personal/student lifecycle, OTP and response-contract regressions. The existing chat suite passed **87 tests**, with two actual-device recording cases skipped pending Android/iOS clip inputs. Real PostgreSQL tests cover shared-budget, parent/child allocation, topology growth, activation, approval and duplicate-message races. The synthetic 12-unit scenario proves a 48-place bounded hold for 40 initial employees and eight reserve places, without creating a lease, signature, payment or assignment. Django system checks, migration drift checks and a complete fresh migration apply passed on isolated PostgreSQL. Test providers/fixtures are not deployed or production evidence. The full readiness and missing-implementation record is in the Flutter repository's `docs/COMPANY_HOUSING_IMPLEMENTATION.md`.


## Owner editing, inheritance, physical changes and media

Added locally on 2026-10-16. These routes use the existing `/api/v1/features/v1/` prefix, session authentication, localized envelope, request-key receipts and fresh authorization described above. Container edits do not create new canonical units or rental commitments.

| Method | Path | Contract |
| --- | --- | --- |
| PATCH | `residential-assets/{kind}/{id}/` | Same discriminated body as creation with current `expected_revision`; existing kind/parent cannot be changed here. |
| POST | `residential-assets/{kind}/{id}/bulk-edit/preview/` | Save immutable exact-unit preview; per-row versions and selected fields required. |
| POST | `residential-assets/{kind}/{id}/topology/preview/` | Save move/split/merge scope and blockers; no inventory mutation yet. |
| GET | `residential-assets/{kind}/{id}/changes/` | Owner-scoped paginated previews/results, newest first; recover after restart. |
| GET, POST | `residential-changes/{id}/` | Read saved preview/result, or apply with current change revision and a stable request key. |
| GET, POST | `residential-assets/{kind}/{id}/media/` | List up to 60 active intentions/items, or create a private durable upload intention. |
| GET, PUT, DELETE | `residential-media/{id}/` | Owner metadata/reconciliation; PUT multipart `file`; DELETE uses the canonical command body. |
| GET | `residential-media/{id}/bytes/` | Authenticated no-store PNG bytes; current media and parent policy required. |
| POST | `residential-media/{id}/review/` | Independent property reviewer, current revision, approved/rejected status and reason. |

### Typed facts and revisions

Container create/edit accepts optional `facts`:

```json
{
  "latitude": "30.044400",
  "longitude": "31.235700",
  "elevators": 2,
  "parking_spaces": 12,
  "accessibility": "Synthetic step-free shared entrance",
  "utilities": {"water": "Metered", "electricity": "Metered", "internet": "Shared connection", "laundry": "Shared room"},
  "included_services": ["Synthetic common-area cleaning"],
  "public_access": "Reception entrance",
  "private_access": "Private instructions for authorized operations only",
  "contact_name": "Synthetic operator",
  "contact_phone": "",
  "unit_defaults": {"is_furnished": true, "has_wifi": true}
}
```

Coordinates must be paired or both null, latitude within ±90 and longitude ±180, six decimal places. Counts may be unknown (`null`), elevators 0–100 and parking 0–10000. Access/accessibility text ≤2000, each utility arrangement ≤500, up to 30 included-service descriptions ≤300 each, contact name ≤200 and phone ≤40. These describe factual arrangements, not guaranteed response times or implicit extra charges.

Private access and operational contacts stay in owner projections, outside commercial snapshots. `revision` protects ordinary edits, `topology_revision` protects physical scope, and `commercial_revision` protects changed public quote facts. Private contact/access/default edits do not invalidate an otherwise unchanged commercial package. Identity/structure changes reset parent authority; declared counts cannot exclude registered inventory.

### Exact bulk previews

```json
{
  "request_key": "10000000-0000-4000-8000-000000000010",
  "expected_revision": 4,
  "units": [{"id": "10000000-0000-4000-8000-000000000011", "version": "2026-10-16T12:00:00+00:00"}],
  "changes": {"is_furnished": true},
  "inherit_fields": ["has_wifi"],
  "reset_overrides": false,
  "reason": "Synthetic reviewed defaults update"
}
```

Use the exact `version` supplied by each asset unit row; do not generate a client timestamp. Up to 100 distinct units are allowed. Override and inherit sets cannot overlap. `unit_defaults`/inheritance accepts furnishing, nullable smoking rule, Wi-Fi/elevator/garage/security/air-conditioning/gas/electricity-meter/water-meter booleans, district/street/country. Bulk changes additionally accept bedrooms/bathrooms 0–100, area 1–100000, floor null or −20–200 and capacity null or 1–1000. Money, authority and booking fields are rejected.

The returned change has `id`, `revision`, `operation: bulk_edit`, `applied`, immutable `preview` and `results`. Preview rows identify canonical ID/code/version, before/after/source, skipped fields and `ready|blocked|unchanged`. Apply rechecks exact membership/ownership, current defaults and all revisions/commitments. Results preserve `updated|failed|blocked|unchanged` per unit and a machine `code_reason` when appropriate. An applied change can contain failures; unresolved rows require a fresh preview. Receipt replay never repeats successful updates.

Complex defaults are overridden by building defaults. A unit's recorded explicit value is preserved unless `reset_overrides` is selected. Canonical ordinary unit edits mark explicit overrides too. Parent changes never silently propagate to children or rewrite an approval/agreement. Each inherited value records source ID/name/revision/value.

### Move, split and merge previews

Body: canonical `request_key`/`expected_revision`, `operation`, `units` with exact ID/version, `replacements`, and a nonempty `reason` ≤1000.

- `move_units`: one to 100 source units and `target_kind`, `target_id`, `target_revision`; no replacements. Target is a managed building or complex.
- `move_building`: building source, complex target and target revision; empty units/replacements. The server resolves every contained unit.
- `split_unit`: exactly one source, two to 20 replacement rows, no target fields.
- `merge_units`: two to 100 units with the same direct parent, one replacement row, no target fields.

Every replacement needs unique nonempty `unit_code` ≤40, title ≤255 and explicit/unknown capacity; optional safe unit facts use the bulk-field contract. Preview includes resolved unit versions, target label, `allowed`, `blocked_reasons` and identity-retention facts. Apply uses only the stored scope and current change revision; it does not accept revised target/units.

Complex roots, buildings and properties are locked in order. Parent changes are rechecked after locking, including stale parent relationships resolved before a concurrent move. Moves retain identities; splits/merges retain hidden predecessors and create fresh canonical units with `replaces` lineage, no room/bed IDs, copied media or verified authority. Replaced IDs cannot be publicly retrieved, reactivated or allocated. Ordinary historical lease/document access remains canonical. A database constraint keeps retired rows hidden.

The entire topology apply succeeds or rolls back. Source/destination declarations do not silently expand; affected authority/topology revisions require review. Existing allocations, relevant leases and live parent holds block unsafe changes, including commitments acquired after preview. No active-contract amendment is simulated.

### Upload and review recovery

An intention body contains parent `expected_revision`, stable `request_key`, `purpose: photo|authority`, caption ≤300, `representative`, lowercase SHA-256, `byte_size` and `content_type: image/png|image/jpeg`. Authority evidence cannot be representative. Files are limited to 5 MiB and 24 million pixels. The server validates the original digest/size/format and strips embedded metadata through PNG re-encoding.

POST intention returns a recoverable media resource/receipt before bytes are sent. PUT sends multipart field `file` and returns current media metadata directly in `data`; read GET first after an uncertain response. Ready intentions return without another write. A pending intention requires the exact original file. Local drafts retain digest/identity metadata, not evidence bytes or local paths. Storage I/O runs outside locks; concurrent retries can leave an unreferenced private storage blob but cannot create multiple media records or publish an unreviewed file.

Review requires `status: approved|rejected`, a reason and current revision. Self-review is forbidden. The initiating reviewer's receipt is recoverable only while the staff role remains authorized. Review is independent of whole-building/complex authority. Ready private evidence is readable only by its owner or reviewer. Approved photos become eligible to other authenticated readers only for nonarchived parents with verified authority. DELETE revokes byte access while retaining review history; authorized staff inspection can retain historical evidence.

The Django `ResidentialMedia` review console and read-only `PortfolioChangeSet` inspection expose pending reviews and partial failures without arbitrary confirmation/payment controls. Production evidence retention/scan policy, private storage and staff operations require deployment validation. This endpoint accepts image evidence, not PDF/video dossiers.

### Canonical parent tours

Use `/api/v1/residential-assets/{building|complex}/{id}/virtual-tours/` and its canonical tour/revision/viewer suffixes. These deliberately use the existing tour API prefix rather than `features/v1`. Owner authorization, idempotency headers, ETags, resumable upload sessions, processing, staff review and short-lived viewer grants remain canonical.

Responses include `asset_id`, `asset_kind: property|building|complex` and nullable legacy `property_id`. The exported tour OpenAPI document includes both parent route families. A parent needs uploaded ordinary photos before tour authoring. Only common-area overview spaces are permitted; child bedrooms/room IDs/bed IDs and child offer scopes are rejected. Unit interior tours retain original property endpoints. Parent topology revisions bind the scope fingerprint and invalidate stale viewer sessions.

Migrations: `properties` 0024, 0025, 0026; `virtual_tours` 0002. They preserve legacy units/tour targets and do not reinterpret historical apartment `entire_property` selections. No deployment or production configuration change is included.


Owner-increment evidence: 252 distinct selected backend cases verified across the combined regression and corrected owner runs; the 20 owner cases include real PostgreSQL concurrency and staff review-console authorization. The only initial failure was a new test URL, corrected and rerun successfully. Django checks, migration drift checks and all migrations on a fresh isolated PostgreSQL database passed. No deployment/provider or native-device verification is implied.

## Planning request correction (19 October 2026)

POST `company-housing-requests/{id}/` accepts the same full fields as request creation, plus the current `expected_revision` and a stable `request_key`. It returns the canonical request with an operation receipt. Only the currently assigned active coordinator can write; another coordinator or approver cannot inherit the assignment. The company and request are locked in the existing order before revision checks.

`can_edit` is a current server projection and defaults to false in older clients. Correction requires new-business capability and no package records at all. Even a withdrawn package retains immutable history, so its request cannot be rewritten; create a new request instead. The request's conversation identity stays the same, and correction creates no hold, invoice, signature or approval. Lost-response retry must retain the original key/payload; a new command with a stale revision returns conflict.

The Flutter editor preserves EGP minor units, offers exact decimal inputs, retains account/environment-scoped drafts and returns to a refreshed request after acknowledgment. Whole-month validation appears before submission, while server time and current policy remain authoritative.
