# Sprint 01 — Close security and data-preservation gaps

**Outcome:** legacy aliases, account/media lifecycles and communication revisions cannot bypass canonical policies.
**Owners:** identity, property/tour, communication and admin maintainers; security reviewer.
**Evidence:** A1-01…A1-05, A1-08; A2-01/A2-02; A3-01; A4-02; A5-01/A5-02/A5-03; A6-01/A6-10.

## Stories

1. **Media provenance and erasure:** prevent arbitrary avatar references from becoming owned assets or deletion intents.
   Audit existing references non-destructively. Protect all live portfolio blob owners in local/remote cleanup; define
   retention for removed and historical evidence. Compensate losing concurrent upload writes without retaining all orphans.
2. **Account identity:** close all inherited Djoser deletion aliases; route deletion through reviewed closure. Prevent social
   preregistration/adoption from preserving attacker-controlled passwords/sessions. Make OTP attempts/consumption/cooldown
   atomic. Revalidate original session epoch after locked identity submission.
3. **One publication/moderation policy:** enforce it under visit-creation locks and on tour availability/session/manifest/
   byte paths. Preserve separately authorized historical/reviewer/owner previews. Route legacy moderation through the
   canonical independent-review, revision, receipt and event service.
4. **Financial privacy:** agree on retained-record rights after personal access revocation; apply one policy to invoice,
   payment and new checkout commands without blocking necessary original-operation reconciliation.
5. **Communication:** enqueue moderation for the actual edited event/revision; apply typed text/quota checks to legacy and
   rich REST/WS sends. Replace unnecessary participant email projection with the approved public identity contract.
6. **Runtime hardening:** assess cookie-origin/CSRF threat conditions and coordinate required browser proof with clients;
   preserve bearer clients and signed provider callbacks. Select a supported Django/dependency stack and audit the lock.
   Verify deployment HTTPS/HSTS/session/CSRF/origin settings rather than applying synthetic warnings blindly.

## Acceptance

- Borrowed-media closure with mocked providers cannot destroy another asset. Cleanup retains active portfolio assets
  older than seven days locally and remotely while still reclaiming true orphans.
- Every self/staff deletion alias, including router/format variants, preserves closure obligations. Social adoption revokes
  untrusted prior credentials. Parallel OTP and in-flight revoked identity submissions fail correctly.
- Hidden/retired/blocked/closure-pending properties cannot start visits or expose public tour bytes; existing grants are
  denied immediately. Withdrawing closure restores only otherwise eligible publication.
- All moderation aliases reject self-review/stale/conflicting commands and emit one canonical decision/event.
- Edited messages receive exactly one input per eligible revision; bad legacy socket inputs do not kill the connection or
  bypass quotas. Chat projections follow the agreed contact-disclosure policy.
- Financial revocation tests cover lists/details/new commands and necessary reconciliation separately.
- Supported framework/runtime audit and focused security tests pass; unresolved provider/deployed checks remain explicit.

**Delivery:** split independent fixes into small PRs with source-triggered regression cases. Do not combine the entire
dependency upgrade and mechanical CBV migration with these behavior changes.

## Results (2026-11-09)

Implemented on branch `sprint-01/security-and-data-preservation` (based on `d46cc2bf`); changes are uncommitted for
review. Evidence: [evidence/sprint-01](evidence/sprint-01/README.md). No existing database, media, secret or
production system was altered (hashes verified before/after); `Pipfile.lock` is unchanged.

### Stories

| Story | Status | What changed |
|---|---|---|
| 1. Media provenance and erasure | Done; legacy treatment needs ops review | Avatar inputs (`avatar`/`profile_image`/`image` on both profile routes) accept uploads/data URIs only; a string is accepted only when it names the stored avatar (no-op). New `ProfileMediaUpload` receipt recorded by the profile and identity upload services. Closure queues erasure only for receipted assets and the worker rechecks provenance before `destroy`; unproven/legacy references are **held** (`held_reason`), never destroyed. Read-only `audit_profile_media_provenance` command reports unproven/shared references. Tour-storage cleanup uses one `referenced_blobs()` graph that includes `ResidentialMedia` (ready and removed — removed media is retained as private evidence, matching `portfolio_media.remove`); losing concurrent portfolio writes drop their local copy, remote copies are reclaimed by the sweep |
| 2. Account identity | Done | Djoser `destroy` (users/me, users/<id>, format suffixes, self and staff) answers the retired-route 409. Social adoption: email-verified accounts link and keep credentials; unverified local accounts have their password retired and all sessions/devices revoked; closed/suspended accounts are refused; concurrent links resolve to one identity. OTP verify/consume/attempts run under the account row lock; challenge issue is under the same lock; resend cooldown is claimed atomically. Identity submission compares the authenticated epoch and session claims after taking its lock, before any profile/provider change |
| 3. Publication/moderation policy | Done; stale check on the legacy route needs the client | Visit creation rechecks `public_properties` under the property lock (404 like the catalog). Public reviews and places use the same predicate; owner/staff/visit participants keep historical review reads. Tour availability, sessions, exchange, manifests and byte grants use the canonical predicate (closure-pending and closed owners, moderation blocks, restrictions); owner/reviewer previews unchanged. The legacy moderation route delegates to canonical `decide(action="block")` |
| 4. Financial privacy | Done as a default policy; needs product sign-off | A personal participant with `PrivateAccessRevocation` loses `financial_read`/`can_pay` (invoice/payment list, detail, quote, checkout, resume, billing list), the same rule company roles already follow. The original payer can still reconcile their own attempt; provider/server reconciliation is not user-gated |
| 5. Communication | Done; contact policy needs product sign-off | Moderation enqueues `MODERATED_MESSAGE_EVENTS = {message.new, message.edited}` (one input per revision, retries deduplicated). One `validate_text` policy (4,000 code points, no NUL, string only, normalized newlines) for legacy REST/socket; legacy transports consume the shared `send` quota; bad socket frames get a stable error and the socket stays open. Chat participant projections return `email: ""` for everyone but the viewer |
| 6. Runtime hardening | Partly done | Cookie-authenticated unsafe requests (and cookie refresh) with a foreign `Origin` get 403; bearer clients and Origin-less requests are unaffected (`COOKIE_TRUSTED_ORIGINS`, `COOKIE_ORIGIN_ENFORCEMENT`). Dependency audit and a Django 5.2.19 LTS trial completed; **the lock was not upgraded** (sprint rule: separate PR). Deployed HTTPS/HSTS/session/CSRF/origin values were not inspected |

### Acceptance

| Criterion | Met? | Notes |
|---|---|---|
| Borrowed-media closure with mocked providers cannot destroy another asset; cleanup retains active portfolio assets older than seven days locally and remotely while reclaiming true orphans | **Yes** | Remote side verified by asserting the reference set passed to the sweep (mocked provider); no real S3/Cloudinary sweep was run |
| Every self/staff deletion alias, incl. router/format variants, preserves closure obligations | **Yes** | Admin deletion was already disabled. Non-owner DELETE keeps Djoser's existing 403 |
| Social adoption revokes untrusted prior credentials | **Yes** | |
| Parallel OTP and in-flight revoked identity submissions fail correctly | **Yes (PostgreSQL)** | Thread/barrier tests on disposable PostgreSQL |
| Hidden/retired/blocked/closure-pending properties cannot start visits or expose public tour bytes; existing grants denied immediately; withdrawing closure restores only otherwise eligible publication | **Yes** | Restricted-owner state relies on the existing `visible_properties` tests (fixture needs a moderation case) |
| All moderation aliases reject self-review/stale/conflicting commands and emit one canonical decision/event | **Partly** | Self-review, conflicting key, retired/blocked and single emission hold on every alias. **Stale-version rejection on the legacy route only works when the client sends `expected_version`**; the admin web client sends no body, so it gets the version observed under the lock. Needs a frontend change |
| Edited messages receive exactly one input per eligible revision; bad legacy socket inputs do not kill the connection or bypass quotas; chat projections follow the agreed contact-disclosure policy | **Yes, policy pending** | Disclosure follows a *default* policy (never disclose counterpart email); product has not approved a disclosure policy |
| Financial revocation tests cover lists/details/new commands and necessary reconciliation separately | **Yes, policy pending** | Retained-record rights after revocation are not agreed; implemented default denies general reads |
| Supported framework/runtime audit and focused security tests pass; unresolved provider/deployed checks remain explicit | **No** | Audit done (124 advisories). Django 5.2.19 trial passes everything except one test using a removed API. Clean audit is blocked by djoser ↔ social-auth-core and dev tools in the default lock section. Runtime still Django 4.2.11 (unsupported) |

### Behavior changes clients should know about

- `DELETE /api/v1/auth/users/me/` (and `users/<id>/`) now returns 409 `account_closure_review_required` instead of deleting.
- Profile avatar fields reject URL/public-ID strings other than the current avatar (400). Flutter sends files only.
- Legacy REST chat send limit is 4,000 code points (was 5,000) and is rate-limited like rich sends.
- Chat `other_participant.email` / `sender.email` are `""` except for the viewer. Flutter parses but never reads it.
- Second legacy moderation "delete" of an already-blocked listing returns 409 (previously recorded a duplicate decision).
- Cookie-only writes from a foreign `Origin` return 403.

### Open items handed to the owners

1. Product: approve the chat contact-disclosure policy (A5-03) and retained-record rights after private-access revocation (A4-02).
2. Frontend: send `expected_version` and `Idempotency-Key` on `POST /admin/moderation/<id>/delete/` (or move to the canonical block route).
3. Ops: run `manage.py audit_profile_media_provenance` against production read-only; decide per held erasure. Set
   `COOKIE_TRUSTED_ORIGINS` if any browser client writes with cookies only from another origin. Confirm deployed
   HTTPS/HSTS/session/CSRF settings.
4. Backend lead: dependency PR — Django 5.2.19 LTS + DRF 3.18.2 + djoser 2.3.3 + listed fixes; fix the one
   `timezone.utc` test; decide djoser social vs social-auth-core ≥ 5; move black/pytest to dev packages.
5. Merge coordination: the shared checkout's `feature/admin-portal-backend` work also edits
   `admin_api/services/moderation_service.py`; expect a conflict with the A6-01 change.
