# Corporate housing and residential portfolio API

Local implementation reference, 2026-10-16. These endpoints implement owner inventory, company planning, approval, budget reservation and bounded allocation. Corporate contracting, signing, payment and occupancy are **not yet available**. Do not connect the existing personal lease APIs by using a coordinator as tenant.

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

All commands require `request_key` (stable UUID) and `expected_revision` (integer ≥0). New independent resources start from zero; updates use the current subject revision. Selecting an offer uses the **request** revision and the offer revision but returns a new booking item at revision 1. The child's result revision must not be compared with the parent's previous revision.

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
| GET, POST | `companies/{id}/housing-requests/` | Coordinator/approver read; coordinator creates. |
| GET | `company-housing-requests/{id}/` | Coordinator/approver of the same company. |
| POST | `company-housing-requests/{id}/coordinator/` | Admin explicitly reassigns to an active coordinator. |
| POST | `company-housing-requests/{id}/items/` | Coordinator selects exact published offer and receives immutable package. |
| POST | `company-booking-items/{id}/decide/` | Independent active expense approver. |
| POST | `company-booking-items/{id}/hold/` | Coordinator; reviewed company, fresh approval/offer/policy/availability, budget and owner readiness. |
| POST | `company-booking-items/{id}/withdraw/` | Coordinator; uncommitted packages only, remains available when new bookings are disabled. |
| GET, POST | `residential-assets/` | Own managed containers / create building or complex. GET requires `kind=building|complex`. |
| GET | `residential-assets/{kind}/{id}/` | Exact manager; units, counts, authority and known/unknown capacity. |
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

Invitation: command fields, `email`, nonempty `roles` selected from `admin`, `coordinator`, `approver`, `employee`. The response contains `id`, revision 1, recipient email, token and seven-day expiry. Acceptance uses command fields plus `token` (32–200 characters). Tokens are hashed for matching and bound to the exact recipient. The initiating administrator's private operation receipt retains the original issued response for recovery.

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

Title ≤200, purpose ≤5000, cost center ≤100, location ≤300, headcount 1–10000, ceilings 0–10^12. End must follow start. Quote/hold additionally apply the configured future-date/maximum-duration policy and whole monthly periods. Request facts alone do not allocate accommodation.

Selecting an item: command fields using the current request revision, `offer_id`, `offer_revision` ≥1, `occupant_ids` (0–1000 exact active employee UUIDs). The backend resolves all units and capacity, checks the full date interval and current supported policy, then stores a 24-hour immutable package. Unknown capacity blocks approval progression. Offers from multiple owners become separate items.

The private item snapshot additionally includes `company_id`, `company_name`, `requester_id`, `requester_name`, `purpose`, `starts_on`, `ends_on_exclusive`, `occupant_ids`, `occupants` (`user_id` and display `name`), and `reserve_places`. Unit rows retain canonical IDs, unit codes, building/complex IDs and names, topology facts and physical conflict keys. Monthly rent/deposit include `amount_minor`, `currency: EGP` and `exponent: 2`; included/excluded service descriptions remain distinct. Occupant names are planned employees, not acknowledged assignments. These private employee facts are not added to owner/public offer projections.

Decision: current item revision, `decision: approved|rejected`, `snapshot_digest` (64 lowercase hexadecimal characters), optional reason. Requesters and funded occupants cannot be sole approvers, regardless of multiple role assignments. A commercial revision can receive only one decision. The company root serializes aggregate budget checks across requests.

Hold: command fields only. Rechecks company review, active independent approver, unchanged offer/inventory/policy, quote/approval expiry, budget reservation, owner beneficiary readiness, every unit's fresh owner availability confirmation, supported dates and hold limit. A canonical `ReservationHold` references all allocated unit/day rows. The aggregate succeeds or fails locally as one transaction. No lease/invoice/payment is created.

Withdraw: command fields only; permitted without new-business flag. Releases uncommitted hold rows and reserved budget; refuses existing invitation/lease links or reconciliation/committed hold state. A withdrawn package cannot later receive a decision.

Budget settings: current company revision, nullable `budget_limit_minor`, nullable `deposit_limit_minor`, required reason. Null disables that shared limit. Request ceilings still apply. Existing reserved/committed obligations cannot be excluded by reducing a limit. Reassignment: request revision, exact active `coordinator_id`, required reason; the original requester and approval independence do not change.

Authority review: current subject revision, `status: verified|rejected`, `evidence_reference` ≤200, required reason ≤1000. Company reviews require KYC staff, property scopes require property-review staff; self-review is rejected. Record the actual private review reference. This endpoint does not create evidence or automatically verify legal ownership.

## Inventory, revisions, fees and recovery

Models and services: `properties/models/portfolio.py`, `features/company_models.py`, `features/services/company/`, and canonical `rental_lifecycle/inventory.py`. Migrations: properties `0022_company_portfolio_foundations`, `0023_portfolio_batch_recovery`; features `0030_company_portfolio_foundations`, `0031_company_authority_review`.

Root locks precede descendant enumeration. Whole scopes require exact declared completeness and consistent reviewed contracting authority. All modes allocate the same physical day rows. Conflicting personal rooms/beds/units reject a parent hold; selected scopes leave unrelated resources free. Dates use exclusive ends. No topology edit or added child may bypass an active aggregate hold. Parent identities and historic scope are retained; unsupported reparenting/splitting/merging is blocked.

Monthly EGP/exponent-2 policy remains owner commission 1000 bps on first-period base rent, platform processing and zero renewal commission. Parent offer prices are explicit bundle prices. Deposit is counted once per bundle. Known full-term rent, reserved budget, committed budget, cash, deposit liability and refunds must remain distinct. This increment implements reservations and projection scaffolding; it does not implement corporate cash movement or committed-budget transfer on signing.

`GET company-capabilities/` reports corporate contracting and payment false. `CompanyBookingItem` has nullable canonical hold/invitation/lease relationships; only the hold link is populated by this implementation. `EmployeeAssignment` is a foundation model without exposed workflow. Do not create these downstream records through admin to simulate completion.

## Local verification and rollout limits

Use the existing `config.settings.postgres_test` with an isolated local database via `TEST_POSTGRES_DB`, `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD` if required, `TEST_POSTGRES_HOST`, `TEST_POSTGRES_PORT`. Never point these tests at production. The tests override the new-business flag and seed clearly synthetic reviewed/readiness records.

```sh
.venv/bin/python -m pytest --ds=config.settings.postgres_test core_apps/features/tests/test_company_housing.py
.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

The final company suite passed 34 tests. Real PostgreSQL tests cover shared-budget, parent/child allocation and topology-growth races. The synthetic 12-unit scenario proves a 48-place bounded hold for 40 initial employees and eight reserve places, without creating a lease, signature, payment or assignment. Another run passed 38 existing personal/student/lifecycle regressions, and 86 shared response-contract tests passed. Test providers/fixtures are not deployed or production evidence. The full readiness and missing-implementation record is in the Flutter repository's `docs/COMPANY_HOUSING_IMPLEMENTATION.md`.
