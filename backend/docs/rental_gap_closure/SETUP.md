# Migration, policy, workers and provider setup

No remote deployment or migration was executed for this task. Run these steps against an authorized environment after backup and compatibility review. Commands below are relative to `Sukoon-API/backend`; use that environment's explicit Django settings.

## Safe rollout order

1. Keep `RENTAL_PROVIDER_BACKEND=disabled` in production and leave `RENTAL_LIFECYCLE_POLICY_VERSION` empty. Disable new commercial actions while auditing legacy allocations. Reads and existing recovery records remain available according to current permissions.
2. Back up the database and take an inventory/conflict report before accepting new allocations. Drain older allocation writers/workers for the schema cutover; they do not populate the new unit column.
3. Run `python manage.py check`, `python manage.py migrate --plan`, and apply migrations through `features.0023_rentalpayout_beneficiary_account_id_and_more`. `0021` adds lifecycle records and mapped-unit constraints; `0022` adds appointment/access consent versions and participant terms; `0023` adds beneficiary snapshots. Existing IDs and financial rows remain intact. Nullable unit and beneficiary-history fields preserve old records without inventing verification.
4. Run `python manage.py reconcile_rental_inventory` (dry-run). Review `review_required` property IDs against actual room/bed selections and overlapping dates. Unknown/conflicting rows stay in place. For proven maps run `python manage.py reconcile_rental_inventory --property-id UUID --apply`. Re-run the report. `--apply` opens an inventory case for conflicts and converts only unambiguous properties. Never solve conflicts by deleting financial/tenancy history.
5. Deploy the matching API plus worker image. Old writers must not keep creating unmapped rows after cutover. Restart workers from the new image; verify actual runtime revision, schema and feature routes. A server restart alone is not evidence of a new build.
6. Install a new reviewed policy version using the command below. Run local/staging read, race, restart and owner/tenant journey checks. Assign operations roles and case ownership before enabling time-sensitive commitments.
7. Enable only approved lifecycle capabilities by setting `RENTAL_LIFECYCLE_POLICY_VERSION` to that installed version and deploying the matching Flutter build. Keep payment/signing/settlement-dependent capabilities disabled until the actual provider integrations are implemented and tested.

Rolling back the app does not justify dropping these tables or unique constraints. Disable new actions, retain receipts, reconcile unknown operations, and preserve allocations/history. A pre-migration writer is not a safe rollback target after mapped units are in use.

## Policy installation

`python manage.py configure_rental_lifecycle_policy --input /private/reviewed-policy.json` validates without keeping a record. Add `--apply` to install a new immutable version. The named active base policy must already exist. Fees, currency, commission payer/basis and renewal commission are copied from that base; the command does not choose new commercial policy. Existing versions cannot be overwritten, and policy records are read-only in Django admin.

Input shape:

```json
{
  "version": "APPROVED-NEW-VERSION",
  "base_policy_version": "EXISTING-COMMERCIAL-VERSION",
  "lifecycle_rules": {
    "approved": true,
    "approval_reference": "ACTUAL-REVIEW-REFERENCE",
    "application_sharing": false,
    "reservations": false,
    "independent_group_booking": false,
    "hold_minutes": null,
    "max_extensions": null,
    "max_active_holds": null,
    "availability_hours": null,
    "turnover_days": null,
    "reconciliation_minutes": null,
    "max_booking_days": null,
    "share_days": null,
    "case_hours": null
  }
}
```

This deliberately incomplete template cannot enable a capability. Replace nulls only with reviewed values. `approved: true` describes the expected input shape; this file does not supply approval.

| Rule | Accepted bounds | Meaning |
|---|---|---|
| hold_minutes | 1–1440 | Initial free hold and bounded extension interval |
| max_extensions | 0–3 | Extension count for an unconsumed free hold |
| max_active_holds | 1–10 | Active/reconciliation reservations per actor |
| availability_hours | 1–168 | Maximum age of owner availability confirmation |
| turnover_days | 0–7 | Additional blocked dates after the contractual exclusive end |
| reconciliation_minutes | 1–1440 | Unknown-payment hold case deadline, never automatic refund/release |
| max_booking_days | 1–1096 | New free hold/group booking date span |
| share_days | 1–90 | Maximum application-grant lifetime; Flutter currently requests one day |
| case_hours | 1–168 | Operational case due time; existing incidents use a 24-hour fallback when policy is absent |

Interest follow-up reminders currently use the existing local 48-hour response interval. Group proposal deadlines are explicit server-validated instants within seven days; the initial Flutter form uses one day. These are engineering defaults requiring operations review before launch. Converted agreement signing/activation retains the existing agreement hold policy; the free-hold extension limit applies before consumption.

## Environment variables and runtime gates

- `RENTAL_LIFECYCLE_POLICY_VERSION`: reviewed active database policy version; empty disables new sharing/holds/group commitments.
- `RENTAL_PROVIDER_BACKEND`: existing provider selector; production defaults disabled. Current code supports only fake in explicitly allowed development/test/staging settings.
- `RENTAL_RUNTIME_ENVIRONMENT`, `RENTAL_FAKE_PROVIDER_ALLOWED`: production settings force production/false. Never relax them to advertise live functionality.
- Existing `RENTAL_HOLD_TTL_MINUTES`, `RENTAL_SIGNING_TTL_MINUTES`, `RENTAL_CHECKOUT_TTL_MINUTES`, `RENTAL_QUOTE_TTL_MINUTES`, onboarding TTL and provider webhook secret remain in the backend settings. No secrets belong in Flutter defines or evidence artifacts.
- Flutter `SOKOUN_RENTAL_LIFECYCLE=false` disables client writes through the existing build-readiness gate. Server permissions remain authoritative.
- Tests use `TEST_POSTGRES_DB`, `TEST_POSTGRES_USER`, optional HOST/PORT/PASSWORD and `config.settings.postgres_test`. The test database explicitly uses UTF-8/template0 and never inherits production DB credentials.

## Workers and provider dependencies

The existing Celery beat runs source/hold expiry, ambiguous-payment reconciliation, approved payouts and rental changes every five minutes; planning jobs deliver the durable outbox and run lifecycle deadlines. Confirm actual beat/worker processes and delivery monitoring after deployment. Unit tests invoking task functions are not worker deployment evidence.

A production integration still needs adapter code for provider onboarding, document generation/signature verification, checkout creation and original-reference lookup, authenticated payment events with merchant/account checks, refund/payout submission and lookup, private evidence storage/download and malware scanning. Commit durable instructions before network calls; unknown requests must be looked up by their original reference before retry. Actual escrow, delayed release, guarantees, third-party payment and all-or-nothing group compensation remain unsupported.

Historical payouts with no beneficiary snapshot cannot be newly dispatched by guessing an account. Changed/restricted beneficiaries require an operations case and an explicit reviewed remedy; no auto-redirection or automatic reapproval is implemented.
