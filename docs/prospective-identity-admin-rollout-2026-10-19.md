# Prospective identity and administrative authority rollout

The approved repair scope can stop new email-verification events from granting identity approval without automatically revoking existing users. This rollout preserves that separation.

## Additive schema before runtime code

Publish and explicitly apply only `users.0005_user_is_email_verified`, `admin_api.0004_staffauthorityaudit` and `admin_api.0005_kycsubmission_evidence_digest_and_more`. Existing `User.is_verified` values remain unchanged. A false initial `is_email_verified` value means email possession has not been separately recorded; it does not log a user out or rewrite an existing identity decision.

The three migrations add a separate email flag, an immutable staff-authority audit table and version-bound KYC evidence fields. Take a private encrypted backup of the existing user/KYC tables first. Inspect the exact migration plan, apply only these targets, and verify user/verification/KYC counts afterward. Do not run the pending `admin_api.0006_reconcile_legacy_identity` historical cutover.

## Following runtime release

- Email OTP and independently verified social email establish email possession only. SMTP refusal/unknown delivery does not acknowledge successful delivery. Existing security-epoch and resend limits remain.
- Complete identity evidence enters a versioned review queue. Replacing evidence creates a new version and cannot inherit an earlier approval. Only a current independent authorized reviewer can approve or reject the current pending snapshot.
- Administrative requests use current server authority and exact UUID targets. Staff changes retain an immutable audit. Ordinary users and inactive/revoked roles are denied independently of UI controls.
- Finance and monitoring summaries use available canonical records; missing telemetry remains unknown. Deposits are not silently counted as revenue. Broadcast delivery remains explicitly unavailable without an implemented dispatch path.

The exact isolated candidate passed 246 PostgreSQL tests covering users, OTP, recovery, profiles, identity review, administrative roles/projections and selected concurrent authorization/private-document cases. The historical migration and its specific test were excluded from that deployable snapshot. Their original local files remain pending a separate existing-account decision.

## Historical boundary

The read-only preflight found 31 accounts, 13 boolean-verified accounts and no KYC submissions. The user has been asked to approve or defer historical re-verification. No such approval is inferred from deploying these prospective fixes. Existing leases, money and occupancy are not rewritten. Preserved legacy booleans remain an explicit assurance gap until that review is resolved; this release is not full closure of legacy identity assurance.

The runtime App Platform component serves the Django API/admin. Next.js administrative interfaces require their own build/hosting evidence; publishing their source alongside this API does not prove a deployed React portal.
