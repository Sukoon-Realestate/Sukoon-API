# Feature availability, uploads and legacy aliases (Sprint 00 inventory)

**Date:** 2026-11-09 · **Source:** `main` at `4d2556cf` plus the Sprint 00 working tree. Per-route values come from
[ROUTE_MATRIX.md](ROUTE_MATRIX.md) / [route-matrix.json](evidence/sprint-00/route-matrix.json). Deployed environment
values were **not** inspected (no deployment spec is committed and the root `.env` was deliberately not read), so
"production" below means the code default that applies when the deployment sets nothing. Ops must confirm the
deployed values before any cleanup removes a path listed here.

## 1. Release scope: public, deferred and disabled

`SUKOON_MVP` defaults to `true` (`config/settings/base.py:98`). `core_apps/common/mvp_scope.py` then refuses
deferred routes with `403 {"code": "mvp_feature_deferred"}`, and additionally refuses any `/api/v1/` request carrying
a student/company workspace or company headers. Deferred code stays in source on purpose ("reversible MVP boundary").

| Scope (production default) | API patterns | Notes |
|---|---:|---|
| Reachable | 382 | Auth, profiles, catalog, visits, tours, direct chat, notifications, support, admin |
| Refused for every declared method | 413 | `features/v1/*` except the `FEATURE_ROOTS` allowlist (388), deferred admin review/financial roots (9), advertising (7), named property routes (5: post-visit decision, viewing representatives, revenues/earnings, review create), named profile routes (3: contracts, rates, account summary), Paymob test checkout (1) |
| Refused by context | not countable statically | Group/company/student chat (`chat/services/group_access.py:13`), `?workspace=student|company`, `X-Sukoon-Company-*` headers |

Consequence for testing: 680 tests are deselected in MVP mode by `tools/qa/mvp_collection.py`, and ~1,086 more fail
only because the gate refuses them (they pass with `SUKOON_MVP=false`). Deferred features are therefore tested only
in restoration mode. See [evidence README](evidence/sprint-00/README.md#test-results).

### Feature switches (code defaults)

| Switch | Default | Effect when default applies |
|---|---|---|
| `SUKOON_MVP` | true | Deferred scope above |
| `RENTAL_PROVIDER_BACKEND` | `disabled` | Rental payment provider off; `fake` allowed only when `RENTAL_FAKE_PROVIDER_ALLOWED` (false in base, true in test/mock settings) |
| `RENTAL_CHECKOUT_ENABLED`, `PAYMOB_INVOICE_CHECKOUT_ENABLED`, `PAYMOB_REFUNDS_ENABLED`, `PAYMOB_PAYOUTS_ENABLED` | false | Money movement paths off unless enabled per environment |
| `PAYMOB_TEST_CHECKOUT_ENABLED` | false | `POST /api/v1/payments/paymob/test-checkout/` (AllowAny) is also MVP-deferred |
| `COMMERCE_STORE_PURCHASES_ENABLED`, `COMMERCE_ENTITLEMENTS_ENABLED` | false (hard-coded) | Store purchase/entitlement paths off |
| `COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED`, `COMMERCE_HOSTED_SANDBOX_ENABLED` | false | Sandbox flows; allowlisted user IDs only when enabled |
| `EVIDENCE_STORAGE_PROVIDER`, `EVIDENCE_SCANNER_BACKEND` | `disabled` | Private evidence uploads fail closed |
| `OWNER_TENANT_QA_ENABLED`, `PLANNING_MOCK_DISCOVERY` | false (hard-coded) | QA/mock helpers off; true only in `config.settings.test` |
| `COMPANY_HOUSING_ENABLED`, `SHARED_HOUSING_ENABLED`, `REVIEWS_ENABLED`, `ADMIN_CAMPAIGNS_ENABLED` | false | Feature off (and mostly MVP-deferred too) |
| `PROPERTY_CAPTURE_ENABLED`, `CAPTURE_RECONSTRUCTION_ENABLED` | false | Capture/reconstruction off; `CAPTURE_COACH_ENABLED` defaults true |
| `CHAT_TRANSCRIPTION_ENABLED`, `SIGNWELL_TEST_ENABLED`, `RUNTIME_EVIDENCE_ENABLED` | false | Off |

### Non-production settings modules (never deploy)

`test`, `postgres_test`, `mvp_http_test` (test harnesses); `staging_mock`, `advanced_mock` (hosted provider
simulation on separate databases); `demo`, `commerce_sandbox`, `capture_dev` (isolated local SQLite);
`background_probe` (connectivity scheduling). Each module's docstring states its isolation rule. Fake providers
and QA switches are enabled only in these modules.

### Fake, fixture and staging code reachable from serving paths

From the audit (not re-verified line by line in Sprint 00): advertising banner fixture repair and fabricated artwork in
GET handling ([UPLOADS.md](UPLOADS.md), Sprint 11); the Paymob test checkout route above;
`settings_service.get_platform_settings()` returns an empty compatibility result by design (A6 non-finding).
Cleanup (Sprint 11) must re-check routes, imports, tasks, signals, admin, migrations and clients first.

## 2. Upload entry points

[UPLOADS.md](UPLOADS.md) holds the per-resource policy. Sprint 00 maps it to the modules that read request bytes or
file fields (static scan, tests/migrations excluded):

| Surface | HTTP entry modules | Storage/model fields |
|---|---|---|
| Avatar / profile images, identity media | `profiles/views.py`, `profiles/views_parts/profile_edit_apiview.py`, `users/views.py`, `users/views_parts/verify_email_apiview.py` | `profiles/models.py` (4), `profiles/identity_media.py` (2), base64 in `profiles/serializers_parts/update_profile_serializer.py`, `users/serializers_parts/create_user_serializer.py` (3) |
| Listing images/video | property image routes (`property-image-upload`, `images/order`) | `properties/models/property.py` (4), `property_serializer.py`, `property_list_serializer.py` |
| Portfolio media | `features/portfolio_views.py` | features private storage |
| Tours/capture parts | `virtual_tours/views.py` (revision uploads, capture sessions) | `VIRTUAL_TOUR_PRIVATE_ROOT` / S3/Cloudinary provider |
| Rental/student evidence | `features/rental_phase4_views.py`, `rental_phase4_views_parts/rental_evidence_upload.py`, `features/student_verification_views.py` | `EVIDENCE_*` provider (disabled by default) |
| Chat attachments | `chat/views/group_attachments.py` (+ direct media services) | `CHAT_PRIVATE_MEDIA_ROOT` / provider |
| Support evidence | `support/views/ticket.py`, `support/views/uploads.py` | `support/models/attachment.py` (2), `SUPPORT_PRIVATE_MEDIA_ROOT` |
| Advertising banners | `advertising/views.py`, `advertising/views_parts/owner_advertisement_collection.py` | `advertising/models.py`, `advertising/serializers.py`, `audit_asset.py` (MVP-deferred) |
| Commerce | `features/commerce_views.py` | — |
| Provider callbacks (raw body, not uploads) | `common/paymob_views.py` | HMAC over raw body; keep Django `View` semantics |

Account closure (`users/services/account_closure.py`) references stored media for erasure; A1-01 requires that it only
erases owned, server-recorded assets.

## 3. Legacy aliases and deprecation requirements

61 handlers serve more than one non-format path (180 paths), plus 12 DRF format-suffix variants. Client usage below is a
string scan of `Sukoon-API/frontend/src` (web) and `sokoun/apps`, `sokoun/packages` (Flutter) on 2026-11-09.
A zero is not proof of no caller (dynamic URLs, old app versions in the field).

| Alias group (same handler) | Web | Flutter | Requirement |
|---|---:|---:|---|
| `auth/verify/` · `auth/verify-email/` · `auth/verify-otp/` | 0 · 1 · 0 | 3 · 0 · 0 | Keep all three; any removal needs app-version telemetry |
| `auth/refresh/` · `auth/token/refresh/` | 0 · 0 | 9 · 0 | Keep both; `token/refresh` is the conventional SimpleJWT path |
| `auth/delete-account/` · `profiles/delete-account/` | 0 · 0 | 1 · 0 | Keep; both must route to reviewed closure (Sprint 01) |
| Djoser router `auth/^users/...` incl. `me/` | — | 5 (`users/me/`) | Mobile reads `users/me/`; Sprint 01 must block destructive inherited actions (A1-02) without breaking GET |
| `properties/owner/revenues/` · `owner/earnings/` | 0 · 0 | 1 · 0 | MVP-deferred; keep both until restoration |
| `homepage/` (catalog view) | 0 | 1 | Keep |
| Tour routes under `properties/`, `residential-assets/building/`, `residential-assets/complex/` (+ admin) | — | 1 · 1 | Keep all three prefixes; same authorization per prefix |
| `rental-cases/` · `move-in-cases/` · `operations/rental-cases/` | 0 | 0 | MVP-deferred; decide canonical path before Sprint 07 |
| DRF format-suffix variants (`.json` etc., 12) | — | — | Keep through CBV conversion (router-generated) |

Removal of any alias requires: route-matrix diff, client scan, product/client-owner approval, a deprecation window with
a documented error contract, and a contract test for the surviving path.
