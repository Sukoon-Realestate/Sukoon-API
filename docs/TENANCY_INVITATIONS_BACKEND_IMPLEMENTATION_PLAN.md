# Tenancy Invitations Backend Implementation Plan

Date: 2026-10-08  
Repository: `Sukoon-API`  
Backend: Django REST Framework, `backend/core_apps/features/`

## Goal

Implement an auditable invitation workflow in which an owner invites a verified tenant for one owned property and, for rental-inventory properties, one exact offer. Only an accepted, still-valid invitation may populate the lease tenant picker or authorize creation of a lease draft.

This replaces the current broad `LeaseEligibleTenant` authorization path. A visit, conversation, favorite, or property view must never grant lease eligibility by itself.

## Confirmed product policies

- Invitation lifetime is seven days from server creation.
- Both participants must be active and verified. The authenticated creator must still own the property.
- The first release accepts invitation sources only when the tenant has an existing `PropertyVisit` for the exact property whose status is `pending` or `confirmed`. Chat-only sourcing is deferred because conversations currently have no property association.
- Rental inventory schema version 1 requires `offer_id` and `expected_offer_revision`. Legacy properties without rental inventory require both fields to be absent.
- A live duplicate is a `pending` or unconsumed `accepted` invitation for the same owner, property, tenant, and accommodation. Same-key/same-body retries replay; a new key conflicts.
- Pending invitations may become rejected, revoked, or expired. Accepted but unconsumed invitations may be revoked or expire. Linked invitations retain `accepted` as audit history but are no longer eligible.
- Automatic invalidation occurs when ownership changes, either account becomes inactive/unverified, the approved offer changes revision/terms, is archived/unavailable, or a conflicting live lease/allocation exists. Reads compute effective state even before cleanup persists it.
- A cancelled draft does not reactivate its consumed invitation. It permits a new invitation and a new draft after current eligibility and availability checks.
- Invitation acceptance creates willingness only. Inventory is allocated and financial obligations begin only in later documented lease transitions, never at invitation acceptance or draft creation.

## Phase 1 — Persistence and constraints

Add models in `backend/core_apps/features/models.py` and a migration:

1. `TenancyInvitation`
   - UUID identity from the shared timestamped model.
   - Foreign keys: `property`, `owner`, `tenant`, nullable one-to-one `lease`.
   - `offer_id` as a blank string for legacy property-level invitations.
   - immutable `offer_snapshot` JSON.
   - status choices: `pending`, `accepted`, `rejected`, `revoked`, `expired`.
   - positive `revision`, `expires_at`, transition timestamps, creator/responder actor fields.
   - indexes for participant lists and eligibility lookup.
   - check constraint preventing `owner_id == tenant_id`.
   - conditional uniqueness for one live, unconsumed invitation per owner/property/tenant/offer.
2. Reuse `IdempotencyRecord`, with operations `tenancy_invitation.create` and `tenancy_invitation.respond`. Store the complete rendered data payload and status.
3. Add a notification-event record or equivalent unique event key so create/response in-app notifications are inserted once per logical transition; dispatch push only with `transaction.on_commit`.
4. Add a conditional uniqueness constraint for live leases per property/accommodation (`draft`, `pending`, `signed`, `active`). Treat a blank offer as the legacy whole-property allocation key.

Do not manufacture invitations from existing `LeaseEligibleTenant` rows: those rows have no tenant consent, source, expiry, offer, or terms snapshot. Deprecate the model and remove it only after the invitation-backed picker is deployed and verified.

## Phase 2 — Domain service

Create `backend/core_apps/features/services/tenancy_invitations.py` with small reusable operations:

- Resolve and lock an owned property.
- Validate active/verified owner and tenant, prevent self-invitation, and validate the exact visit source relationship.
- Resolve schema-v1 offers and build a complete immutable snapshot, including room/bed names, capacity, bathroom access, terms, availability, archive flag, offer link, and revisions.
- Compare the current offer with the approved snapshot using canonical fields, not JSON key order.
- Compute effective status and `eligible_for_lease` from current server truth.
- Perform create/respond transitions under `transaction.atomic()` and `select_for_update()`.
- Authorize the actor before idempotency replay.
- Use a database uniqueness conflict as the final duplicate/concurrency guard and translate it to HTTP 409.
- Create localized notification records in the transaction and enqueue FCM only after commit.

The expiry cleanup job may persist expired records in batches, but every read and mutation must enforce expiry synchronously.

## Phase 3 — API contract

Add serializers and views under the existing feature app and register these unchanged routes in `backend/core_apps/features/urls.py`:

| Method | Route |
| --- | --- |
| POST | `/api/v1/features/v1/tenancy-invitations/` |
| GET | `/api/v1/features/v1/tenancy-invitations/` |
| GET | `/api/v1/features/v1/tenancy-invitations/{id}/` |
| POST | `/api/v1/features/v1/tenancy-invitations/{id}/respond/` |

Requirements:

- Preserve `FeatureJsonRenderer`: successful payloads use `key/msg/data`; failures use the existing localized `message` envelope.
- Lists require `workspace=owner|tenant`, filter by participant and authorized optional property before pagination, and order by `-created_at`, then `-id`.
- Empty pages return `count: 0`, `total_pages: 1`, and `results: []`.
- Detail access returns 404 to non-participants.
- Response accepts only `accepted` or `rejected`, exact current revision, and a stable request key.
- Return all audit timestamps, including `rejected_at` and `revoked_at`, even though the supplied example omitted them.

## Phase 4 — Picker and lease integration

Update `lease_tenants`:

- Require an owned `property_id`; accept optional `offer_id`.
- Select only distinct tenants backed by accepted, unexpired, unrevoked, unconsumed invitations that still match owner, account verification, current offer revision/terms, availability, and lease allocation state.
- With `offer_id`, require the exact accommodation. Without it, return the union for backward-compatible property-level display only.
- Filter and deduplicate before pagination. Order deterministically by the newest qualifying invitation and tenant ID.

Update lease creation:

1. Resolve request idempotency safely.
2. Start one database transaction.
3. Lock the property, matching invitation, and conflicting lease/allocation rows.
4. Recheck ownership, accounts, invitation state/expiry, exact offer snapshot/revision, and availability.
5. Enforce the template and rent validations already present.
6. Create one `draft` lease and link its invitation in the same transaction.
7. Store the independent lease offer snapshot and idempotency receipt.
8. Return 409 if eligibility was consumed or changed after picker display.

Update draft cancellation so the invitation remains linked/consumed. A fresh invitation is required for a later draft.

## Phase 5 — Notifications and localization

- Add `tenancy_invitation` and `tenancy_invitation_response` notification types.
- Store flat `action_label`, `action_type`, `target_id`, and `workspace` fields in `Notification.data`, matching the current notification serializer/FCM pipeline. The detail serializer projects those fields into the normal notification-center `actions.primary` object.
- Tenant create event: `action_type=open_tenancy_invitation`, invitation `target_id`, `workspace=tenant`.
- Owner response event: the same action and target with `workspace=owner`.
- Send FCM data as strings: `notification_type`, `action_type`, `target_id`, `workspace`, `title`, `body`, and `action_label`.
- Add English and Arabic server strings selected through the existing `Accept-Language` middleware. IDs and machine values remain unchanged.

Lease lifecycle remains explicit: invitation acceptance and `draft`/`pending` lease states do not allocate inventory or create financial entries. The later fully-authorized transition to `active` must atomically lock the allocation, mark the exact offer rented/unavailable, and generate the initial invoice schedule. The current feature module has no production activation/provider-webhook implementation, so that remains a separate rollout blocker for end-to-end leasing even though invitation and draft creation can be delivered independently.

## Phase 6 — Tests

Add focused API/service/model tests covering:

- Legacy plus all four offer scopes.
- Ownership, account verification, self-invitation, visit-source authorization, foreign offer, stale revision, archive, and availability failures.
- Participant-only list/detail/respond privacy.
- Accept/reject, expiry, revocation, changed terms, revision conflicts, and effective read-time expiry.
- Duplicate live records, identical retries, mismatched retry bodies, and exactly one logical notification.
- Picker filtering/deduplication/pagination for every state and offer.
- Atomic draft creation, invitation linking, cancelled-draft policy, stale picker races, and conflicting allocations.
- Concurrent responses and concurrent draft creation. Run these tests against PostgreSQL because SQLite does not provide representative row-lock behavior.
- Arabic/English success and error messages and notification payloads.

Suggested verification:

```sh
cd backend
pipenv run python manage.py makemigrations --check --dry-run
pipenv run python manage.py check
pipenv run pytest core_apps/features/tests -q
pipenv run pytest core_apps/notifications/tests -q
pipenv run flake8 core_apps/features core_apps/notifications
```

## Phase 7 — Staging and rollout

1. Apply the migration in staging and keep `SOKOUN_TENANCY_INVITATIONS` disabled on mobile.
2. Seed two verified accounts, owned legacy/rental properties, all four offer scopes, and valid visit relationships.
3. Return real fixture IDs and request/response evidence for the six scenarios in the mobile handoff.
4. Test concurrent response/draft requests against staging PostgreSQL and verify one notification event.
5. Test notification navigation for tenant and owner workspaces in Arabic and English.
6. Have mobile reconcile any documented contract deviations.
7. Enable the Dart capability only after both-role staging round trips pass.

## Completion criteria

The feature is complete only when migrations are deployed, the invitation endpoints and invitation-backed lease flow pass automated and staging concurrency tests, fixture evidence is returned, notification navigation works for both roles, and the mobile team confirms the adapter before enabling the capability.

## Local implementation result — 2026-10-08

Phases 1–6 are implemented in the working tree and pass local Django checks, migration-drift checks, focused lint, focused invitation tests, and the complete backend regression suite. Phase 7 remains: deploy the generated migrations, create authorized staging fixtures, exercise PostgreSQL concurrency and real FCM navigation, return the evidence, and only then enable the mobile capability.
