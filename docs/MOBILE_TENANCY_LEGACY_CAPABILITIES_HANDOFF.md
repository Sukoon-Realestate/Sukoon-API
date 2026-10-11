# Mobile handoff: invitation draft capabilities and permissions

Date: 2026-10-11 (Africa/Cairo). Source: [live verification follow-up](../TENANCY_INVITATIONS_LIVE_VERIFICATION_FOLLOWUP.md).
Baseline: `82fe579`; delivery is a working-tree patch, not a deployed revision.

The two current release blockers are fixed locally. No mobile flag, provider setting, production data, or deployment was changed. No migration is required. The historical PostgreSQL failure in the source report is separate from this patch.

## Configuration contract

`GET /api/v1/features/v1/lease-configuration/` configures the existing template/invitation draft form. For an active, verified account it returns:

```json
{
  "can_create": true,
  "allowed_actions": ["create"],
  "blocking_reasons": [],
  "templates": [{"id": "eg-residential-v1", "version": "1"}]
}
```

The template above is abbreviated; full template metadata and the existing rental policy remain in the response. Provider onboarding is not required to prepare this kind of draft. No new client fields are needed. `can_create` permits opening the form; POST still checks property ownership/availability, both participants, accepted unconsumed invitation eligibility, accommodation conflicts, dates, rent, and template validity. An unverified account gets `can_create=false`, no actions, a localized reason, and HTTP 403 from POST.

This capability does not authorize the separate structured agreement body (`invitation_id` plus `terms`). Structured creation retains its existing onboarding, policy, payout, provider, and inventory checks. Signing, activation and payments are not enabled by this configuration response.

## Draft permissions

The existing template POST body and routes are unchanged. A supported invitation-backed template draft has this owner projection in POST, detail, and list responses:

```json
{
  "status": "draft",
  "lease_status": "draft",
  "revision": 1,
  "offer_id": "",
  "offer_snapshot": null,
  "legacy_read_only": false,
  "can_sign": false,
  "can_cancel": true,
  "allowed_actions": ["cancel_draft"],
  "blocking_reasons": []
}
```

The real receipt also includes its IDs, invitation link, dates, rent, and other existing fields. The tenant sees `can_cancel=false` and `allowed_actions=[]`; both participants see `can_sign=false`. Offer-backed template drafts keep their actual offer ID/snapshot and the same permission policy.

The narrow exception applies only to a draft with a linked tenancy invitation and no structured terms. Historical legacy records without that provenance remain `legacy_read_only=true`, with both mutation booleans false and no actions. Existing invitation-backed template drafts also receive the corrected projection when fetched; no data backfill is needed.

Backend implementation detail: the persisted `Lease.legacy_read_only` remains true for template leases to preserve structured-workflow exclusion and the existing database uniqueness constraint. The public field is an effective read-only projection for this API. Its false value permits only explicitly advertised actions; it is not authorization for structured editing, review, signing, activation, or money movement.

## Cancellation and signing

`POST /api/v1/features/v1/leases/{id}/cancel/` still takes `revision` and a stable `request_key`. An active, verified owner can cancel a supported draft. The response remains the cancellation receipt with status `cancelled` and revision incremented once. An identical retry returns the original receipt. Cancellation now locks the lease before checking revision and permissions. Tenants/non-owners receive 404; a historical read-only agreement or otherwise unsupported owner cancellation receives JSON 409.

After cancellation, refreshed template lease projections are read-only with no actions and both booleans false. The accepted invitation stays linked and consumed. Fresh consent is required for another draft. No invoices or inventory allocation result from draft creation/cancellation.

Template signing now returns localized JSON 409, including when a caller supplies `document_id`. It creates no signing session and does not move the draft to pending. The old placeholder hosted-signing URL is removed. Structured signing still uses its document-bound provider flow and existing readiness checks.

## Mobile integration and rollout

Keep the existing client `legacy_read_only` safeguard and nullable-snapshot parser. Keep using `can_create` for form access and the returned per-actor permissions for controls. No client bypass or new-field inference is needed. Refetch lease detail after cancellation or an authorization/conflict response.

Pre-deployment idempotency receipts remain stored as originally returned. A retry of an old creation request can replay its old permission snapshot; fetch current lease detail to refresh permissions. Use fresh request keys for new verification operations.

Before enabling the mobile capability:

1. Deploy this patch, record the deployed revision, and confirm migration state. This patch adds no schema changes.
2. Reread configuration as the report's authorized owner in English and Arabic; open the actual Create lease screen with the test-build capability enabled.
3. Create/accept a fresh invitation, create the draft, and compare owner/tenant POST, detail and list permissions. Confirm provider-disabled drafting works while signing remains unavailable.
4. Cancel as owner, retry the same request, and confirm revision changes once, the invitation stays consumed, and refreshed permissions disable mutations. Confirm the tenant cannot cancel and historical records remain read-only.
5. Finish the source report's deployed offer-scope, expiry/revocation, changed-terms, privacy, pagination, concurrency, notification delivery/navigation and device checks. This local patch does not establish those live results.

## Local verification

Tests exercise English/Arabic responses, disabled/fake provider modes, missing acceptance, both participants' projections, signing rejection (including a structured-shaped request), owner-only cancellation/retry, continued consumption, historical read-only records, and unverified accounts.

- Focused invitation and structured agreement suite on the final patch: **48 passed, 3 skipped**. The skips require PostgreSQL; this run used SQLite and does not prove row-lock concurrency behavior.
- Full backend suite: **574 passed, 6 skipped, 1 failed**. The failure is `core_apps/properties/tests/test_visit_request_api.py::TestPropertyReviewListAPI::test_list_reviews_happy_path_with_summary`, which expects the second review first but receives the first review. It also failed in isolation. No property-review implementation or tests were changed. This full run preceded the final additional guard rejecting template leases with a structured-shaped signing body; the focused suite was rerun afterward.
- Django system check passed; migration drift check reported no changes; focused flake8 and diff whitespace checks passed.
- No PostgreSQL, deployed API, Flutter, push transport, or device checks were performed for this patch.

Commands from `backend/`:

```powershell
../.venv/Scripts/python.exe -m pytest core_apps/features/tests/test_tenancy_invitations.py core_apps/features/tests/test_rental_phase2.py -q --tb=short
../.venv/Scripts/python.exe -m pytest -q --tb=short
../.venv/Scripts/python.exe manage.py check --settings=config.settings.test
../.venv/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test
../.venv/Scripts/python.exe -m flake8 core_apps/features/views.py core_apps/features/serializers.py core_apps/features/services/lease_permissions.py core_apps/features/tests/test_tenancy_invitations.py
```

Changed implementation: `backend/core_apps/features/services/lease_permissions.py`, `serializers.py`, and `views.py`. Regression coverage: `backend/core_apps/features/tests/test_tenancy_invitations.py`.
