# Rating domain operations

The rating domain extends the existing features, visit-attendance, lease/handover, idempotency and notification systems. It does not replace those business cycles.

- API contract: [rating_api.md](rating_api.md).
- Policy and schemas: `core_apps/features/services/reputation/policy.py`.
- Models: `core_apps/features/model_parts/reputation.py`.
- Source eligibility and generation: `core_apps/features/services/reputation/`.
- API routes: `core_apps/features/reputation_urls.py` and `core_apps/admin_api/urls.py`.
- Migrations: features `0035_reviewcase_reviewopportunity_reviewsubmission_and_more`, `0036_reviewdecisionnotice_and_more`, `0039_rating_experience_integrations`.
- Tests: `core_apps/features/tests/test_reputation.py` and `test_reputation_integrations.py`.

`REVIEWS_ENABLED` defaults to `false`. This stops new submissions, grants, opportunity generation and reminders. Historical authorized reads, receipt lookup, withdrawal, appeals and moderation remain available. Corporate review generation follows the same flag and requires an accepted signed-lease binding, actual occupancy evidence and explicit company review authority.

Apply migrations with the normal release process, inspect and run `python manage.py migrate_legacy_reviews`, and deploy the app containing the immutable final-confirmation flow before enabling writes. The legacy importer is repeatable, preserves source rows and marks old content `legacy_unverified`; it does not turn viewing stars into verified stay or landlord scores. Old write clients receive `client_update_required`.

The existing Celery worker/beat invokes `core_apps.features.tasks.reconcile_reviews` every 300 seconds. Manual reconciliation uses `python manage.py reconcile_reviews`. The existing planning notification outbox handles delivery; new review notifications contain no score, private text or counterparty identity. Permission and source checks occur again during commands and reads.

Staff require explicit `features.moderate_reviews` or `features.review_eligibility` permissions. Decisions and access reasons are audited, parties cannot moderate their own content, and appeals require an independent reviewer. Scores cannot be edited. Keep operator coverage in place before enabling creation.

For rollback, disable the flag and retain review tables, receipts and source history. Do not reverse populated migrations, delete submissions or restore the old unconfirmed write endpoints.

`python manage.py seed_review_demo --confirm-local` is for a disposable local database with `DEBUG=true`. It creates synthetic `.test` accounts with unusable passwords, personal occupancy fixtures, company representatives and an employee with a personal tenancy. It deliberately creates no corporate review opportunity and must not run against production.

## Local verification and boundaries

The earlier rating-only overlay on backend commit `31d382dee04eea1a025f6d4ce4c64f8f512cf00d` passed Django checks, migration consistency and 132 PostgreSQL tests (48 rating plus 84 related regression cases). Concurrent unrelated backend work was excluded from this overlay; the later combined-workspace Django system check also passed. No deployment or production migration was performed.

Migration `0039_rating_experience_integrations` implements confirmed company lease bindings, explicit per-binding review permissions, bilateral employee occupancy confirmations and ownership responsibility boundaries. Corporate ballots and employee property ballots are separate; employee release is deadline-only. Contract/move-in snapshots retain historical parent IDs; building/complex rollups count visible sections and distinct units directly. `backfill_review_ancestry` copies only known original snapshots. Audited `review-recovery/` and `review-windows/{id}/extend/` operator routes handle older outages and pre-disclosure pair extensions. Company membership, booking holds and planned assignment labels alone remain insufficient evidence.

The sibling Flutter checkout contains the complete [implementation](../../../darak-app/SOKOUN_RATING_IMPLEMENTATION.md), [verification](../../../darak-app/SOKOUN_RATING_VERIFICATION.md) and [integration status](../../../darak-app/SOKOUN_RATING_BACKEND_REQUIREMENTS.md). These relative links assume the two repositories are sibling directories. Staging must verify actual migrations, worker execution, push delivery, permissions, native process-death recovery and accessibility before production enablement.


Local extension verification: 112 PostgreSQL rating/rental/company cases passed in a verification copy with unchanged non-rating baseline models. The current shared checkout has concurrent advanced-housing model additions without matching migrations; these were preserved and excluded from that copy. All overlaid rating sources matched the workspace at the end of that run. No deployment or provider operation was performed.
