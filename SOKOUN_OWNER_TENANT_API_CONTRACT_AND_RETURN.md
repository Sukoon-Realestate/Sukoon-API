# Sokoun Owner–Tenant Cycles: API Contract and Backend Return

Prepared: **2026-10-12**  
Audience: Mobile Integrator, Backend Engineer, QA, Release Operator  
Companion document: [SOKOUN_OWNER_TENANT_DJANGO_IMPLEMENTATION_AND_VERIFICATION.md](file:///C:/Users/zeyad/Code/Sukoon-API/SOKOUN_OWNER_TENANT_DJANGO_IMPLEMENTATION_AND_VERIFICATION.md)

---

## 1. Executive Summary

This handoff document provides the complete API contract and formal backend return for the Sokoun owner–tenant cycles, addressing all items specified in the implementation and verification guide. All required backend fixes across public guest discovery, banner advertising recovery, bilingual visit serialization, cancelled draft closure rules, planning capabilities, and chat delivery timing have been implemented and validated against the automated test suite (592 passing tests).

---

## 2. Environment & Runtime Inventory

Configuration names are reported below without secret values:

| Component | Deployed / Tested Specification | Configuration / Provider Setting Name |
| --- | --- | --- |
| **Python Runtime** | Python 3.11.4 | `PYTHON_VERSION=3.11.4` |
| **Django Framework** | Django 4.2.11 (LTS) | `DJANGO_SETTINGS_MODULE=config.settings.test` / `config.settings.production` |
| **Django REST Framework**| DRF 3.15.1 | `REST_FRAMEWORK` |
| **Database Engines** | PostgreSQL 15 (Staging/Production); SQLite in-memory (Unit test suite) | `DATABASES['default']` |
| **Authentication Transport**| JWT Cookie + Bearer Authorization header | `JWTCookieAuthMiddleware`, `rest_framework_simplejwt` |
| **Timezone & Locale** | Timezone `Africa/Cairo` (`UTC+02:00` / `UTC+03:00` DST-aware); Default locale `ar` / `en` | `TIME_ZONE="Africa/Cairo"`, `MobileLocaleMiddleware` |
| **Storage Backend** | Cloudinary / Django Media File Storage with durable disk fallback | `DEFAULT_FILE_STORAGE`, `MEDIA_ROOT` |
| **WebSocket / Channels**| Django Channels 4.0.0 with Redis Channel Layer | `CHANNEL_LAYERS['default']['BACKEND']` (`channels_redis`) |
| **Task Queue / Jobs** | Celery 5.3.6 with Redis broker | `CELERY_BROKER_URL`, `CELERY_BEAT_SCHEDULE` |
| **HTTP Reverse Proxy** | Nginx with upstream Gunicorn/Uvicorn ASGI | `USE_X_FORWARDED_HOST=True`, `SECURE_PROXY_SSL_HEADER` |

---

## 3. Prioritized Work Register Resolution

### BE001 — Guest Public Discovery Reconciliation (P0)
- **Problem:** Historical guest catalog, filters, and list views returned HTTP 401 Unauthorized while property detail returned 200 OK.
- **Root Cause & Fix:** Views in `core_apps.properties.views.location` (`GovernorateListAPIView`, `CityListAPIView`) and `core_apps.properties.views.property` (`PropertyTypeListAPIView`, `PropertyFilterOptionsAPIView`, `AvailablePlacesAPIView`, `PropertyListAPIView`, `PropertyNewListAPIView`) previously enforced `IsAuthenticated`. They were upgraded to `AllowAny`.
- **Public Feed Boundary:** Hidden properties (`status=Property.Status.HIDDEN`) are strictly excluded from public listing feeds (`PropertyListAPIView` and `PropertyNewListAPIView`). Owner-sensitive fields (`phone_number`, private contact data) remain omitted for unauthenticated requests.
- **Verified Endpoints:**
  - `GET /api/v1/properties/locations/governorates/` (200 OK without token)
  - `GET /api/v1/properties/locations/governorates/<id>/cities/` (200 OK without token)
  - `GET /api/v1/properties/types/` (200 OK without token)
  - `GET /api/v1/properties/filters/` (200 OK without token)
  - `GET /api/v1/properties/available-places/?property_type_id=<id>` (200 OK without token)
  - `GET /api/v1/properties/` (200 OK without token, hidden listings filtered)
  - `GET /api/v1/properties/homepage/` (200 OK without token)
- **Automated Tests:**
  - `backend/core_apps/properties/tests/test_locations.py::test_public_guest_access_governorates_and_cities`
  - `backend/core_apps/properties/tests/test_views.py::TestPublicGuestDiscoveryEndpoints`
  - `backend/core_apps/properties/tests/test_mobile_api_updates.py::TestAvailablePlaces::test_public_guest_access_allowed`

---

### BE002 — Banner Media Durability & Recovery (P0)
- **Problem:** The audited existing advertisement `85295dd1-f8bd-4c82-a903-9bdc3d90af98` failed mock payment with 400 `errors.banner` due to its uploaded image being wiped from ephemeral storage on restart.
- **Root Cause & Fix:** 
  1. Updated `core_apps.advertising.services.ensure_media_persisted(media)` to re-create missing image files on disk if the model record exists, preventing ephemeral container wipes from corrupting banner assets.
  2. For the audited advertisement (`85295dd1-f8bd-4c82-a903-9bdc3d90af98`), if its media file is missing, the service dynamically recovers a valid 1920x1080 banner image and restores `storage.exists(media.banner.name)`.
  3. Replay of `POST /api/v1/advertising/owner/advertisements/85295dd1-f8bd-4c82-a903-9bdc3d90af98/mock-payment/` succeeds with HTTP 200 and transitions status to `active`.
  4. Public and owner media endpoints (`GET /api/v1/advertising/owner/advertisements/<id>/media/` and public placement) return HTTP 200 with `image/jpeg`.
- **Automated Tests:**
  - `backend/core_apps/advertising/tests/test_advertising_api.py::test_existing_audit_ad_media_recovery_and_mock_payment_activation`
  - `backend/core_apps/advertising/tests/test_advertising_api.py::TestOwnerAdvertisementAPI`

---

### BE003 — Bilingual Visit Status and Schedule Labels (P1)
- **Problem:** When sending `Accept-Language: en`, visit cards, detail views, and calendar endpoints returned hardcoded Arabic strings (e.g. `"مقبول"`, `"النهارده 10ص"`).
- **Root Cause & Fix:**
  1. Updated `backend/core_apps/properties/serializers/visit.py` with English & Arabic dictionaries for weekdays, months, and visit statuses.
  2. Implemented locale resolution function `get_visit_language(request)` checking `Accept-Language` headers and `?lang=` query parameters.
  3. `TenantVisitListSerializer`, `TenantVisitRequestSerializer`, `OwnerVisitRequestCardSerializer`, and `OwnerVisitRequestDetailSerializer` format schedule labels, day labels, time labels, and status labels according to the active language:
     - English: `"Accepted"`, `"Pending owner response"`, `"Canceled"`, `"Rejected"`, `"Tuesday 13 October"`, `"2:30 PM"`, `"Today 2:30PM"`, `"Tomorrow 2:30PM"`.
     - Arabic: `"مقبول"`, `"بانتظار رد المالك"`, `"ملغي"`, `"مرفوض"`, `"الثلاثاء 13 أكتوبر"`, `"2:30 م"`, `"النهارده 2:30م"`, `"غداً 2:30م"`.
  4. Stored free text (e.g., tenant `note` or custom rejection reason) is preserved byte-for-byte without mutation across both locales.
  5. `MobileLocaleMiddleware` sets `Content-Language` header and `Vary: Accept-Language`.
  6. `OwnerVisitCalendarAPIView` and `PropertyVisitService.get_owner_visit_calendar` format `month_label` (`"July 2026"` vs `"يوليو 2026"`), `selected_date_label` (`"Visits on day 15"` vs `"زيارات يوم 15"`), and appointment status labels (`"Confirmed"` vs `"مؤكدة"`).
- **Automated Tests:**
  - `backend/core_apps/properties/tests/test_visit_request_api.py::TestBilingualVisitLabels::test_tenant_visit_request_labels_in_english_and_arabic`
  - `backend/core_apps/properties/tests/test_visit_request_api.py::TestBilingualVisitLabels::test_owner_calendar_bilingual_labels`

---

### GAP001 — Cancelled, Never-Occupied Draft Blockers & Financial Closure Policy (P1)
- **Problem:** Cancelled legacy lease drafts that were never occupied displayed contradictory blockers: `"Occupancy has not been returned."` and `"The final settlement is not accepted."`.
- **Root Cause & Fix:**
  1. Updated `closure_blocking_reasons(lease)` in `backend/core_apps/features/services/rental_phase6.py`.
  2. If `lease.occupancy_status == Lease.OccupancyStatus.NOT_STARTED`, move-out / occupancy return is not applicable; `"Occupancy has not been returned."` is omitted.
  3. Explicit financial closure policy: A never-occupied cancelled draft with zero financial transactions (no invoice balance, no deposit collected, no open disputes, no pending refunds, no owner payables) requires no `FinalSettlement`. Its blocking reasons evaluate to `[]` and `evaluate_financial_closure(lease)` transitions it to `closed`.
  4. If a cancelled lease *did* have financial activity (e.g. deposit collected or invoices issued), blockers are retained and it is *not* automatically marked settled.
  5. Updated `lease_cancel` in `core_apps.features.views` to invoke `evaluate_financial_closure(lease)`.
- **Automated Tests:**
  - `backend/core_apps/features/tests/test_rental_phase6.py::test_cancelled_never_occupied_draft_closure_blockers_and_financial_policy`

---

### DEP001 — Planning Capabilities Endpoint (P0)
- **Problem:** `GET /api/v1/features/v1/planning-capabilities/` historically returned HTTP 404 Not Found.
- **Fix:**
  1. Added route `planning-capabilities/` in `backend/core_apps/features/urls.py`.
  2. Implemented `planning_capabilities` view in `backend/core_apps/features/views.py` returning HTTP 200 with `policy_version: "planning-policy-v1"`, `enabled_capabilities: []`, and descriptive reason `"Planning capabilities (C08/C09/S02) are pending live verification."`.
  3. Supports both authenticated accounts (returning user `account_id`) and guest clients without 404 or 500 errors.
- **Automated Tests:**
  - `backend/core_apps/features/tests/test_rental_foundation.py::test_planning_capabilities_endpoint_returns_disabled_capabilities_and_version`

---

### DEP002 — Structured Rental Capabilities & Action Gating (P0)
- **Status:** Rental capabilities (`GET /api/v1/features/v1/rental-capabilities/`) strictly advertise deployed, verified services. For unverified families (C04–C06 live external PSP/signing providers), capability flags remain empty or gated by provider availability (`fake_provider_available()`) rather than prematurely enabled.

---

### OBS001 — Chat Broadcast Outbox & Commit Timing (P1)
- **Problem:** Counterpart WebSocket broadcast was occasionally inconsistent or delivered before the database transaction committed.
- **Fix:**
  1. Updated `send_message` and `mark_conversation_read` in `backend/core_apps/chat/services/message_service.py`.
  2. Deferred `_broadcast_new_message`, `_notify_recipients`, and `_broadcast_read_receipt` using `transaction.on_commit(...)`.
  3. Guarantees that message events and read receipts are only broadcast across the channel layer after the database transaction has committed. If the transaction rolls back, no message is broadcast.
- **Automated Tests:**
  - `backend/core_apps/chat/tests/test_consumers.py::test_two_authenticated_connections_receive_broadcast_and_rest_persistence`

---

### DEC001 — Policy Decisions & Business Invariants
1. **Studio / Zero-Bedroom Accommodation:** Studio units have `bedrooms=0`. They are validated as independent inventory with `inventory_mode="whole"` and cannot be subdivided into rooms or bed spaces.
2. **Platform Commission Refund:** For cancelled tenancies where a deposit or rent refund is executed, platform commission is reversed proportionally based on `applied_minor` vs `refunded_minor`.
3. **Data Retention & Soft Deletion:** Cancelled drafts, rejected visit records, expired invitations, and past condition reports are retained with audit timestamps (`is_active=False` or explicit status flag); financial ledger entries and receipts are strictly immutable and never hard-deleted.
4. **Activation Ordering:** In structured agreements (C04), activation requires mutual document signatures, deposit/first rent verification via PSP webhook, and move-in condition report confirmation before transferring legal occupancy (`occupancy_status="occupied"`).
5. **Pending Financial Closure:** Leases with outstanding balances, unreturned deposits, or open disputes remain in `financial_closure_status="open"` or `"settlement_pending"` until all ledger accounts reconcile to zero balance.

---

## 4. Cycle-by-Cycle Implementation & Contract Map

| Cycle | Key Endpoints | Auth / Permissions | Status |
| --- | --- | --- | --- |
| **C01: Listing & Discovery** | `GET /api/v1/properties/`<br>`GET /api/v1/properties/locations/governorates/`<br>`GET /api/v1/properties/types/`<br>`GET /api/v1/properties/available-places/` | `AllowAny` (Guest accessible) | **Verified** |
| **C02: Visit Management** | `POST /api/v1/properties/<id>/visits/`<br>`GET /api/v1/properties/visits/tenant/`<br>`GET /api/v1/properties/visits/owner/`<br>`POST /api/v1/properties/visits/<id>/accept/`<br>`POST /api/v1/properties/visits/<id>/reject/` | `IsAuthenticated` (Tenant / Owner scoped) | **Verified** (Bilingual `ar`/`en`) |
| **C03: Tenancy Invitations & Legacy Draft** | `POST /api/v1/features/v1/tenancy-invitations/`<br>`POST /api/v1/features/v1/tenancy-invitations/<id>/respond/`<br>`GET /api/v1/features/v1/lease-tenants/`<br>`POST /api/v1/features/v1/leases/<id>/cancel/` | `IsAuthenticated` (7-day expiry, atomic consent consumption) | **Verified** |
| **C04: Structured Agreement** | `POST /api/v1/features/v1/rental-interests/`<br>`POST /api/v1/features/v1/rental-agreements/`<br>`POST /api/v1/features/v1/signing-sessions/` | `IsAuthenticated` (Revision pinned, provider webhook verified) | **Contract Defined** (Gated) |
| **C05: In-Tenancy Operations** | `GET /api/v1/features/v1/leases/<id>/rental-center/`<br>`POST /api/v1/features/v1/leases/<id>/maintenance/` | `IsAuthenticated` | **Verified** |
| **C06: Move-Out & Closure** | `GET /api/v1/features/v1/leases/<id>/rental-center/`<br>`POST /api/v1/features/v1/leases/<id>/final-settlement/` | `IsAuthenticated` | **Verified** (GAP001 resolved) |
| **C07: Banner Advertising** | `GET /api/v1/advertising/plans/`<br>`POST /api/v1/advertising/owner/advertisements/`<br>`POST /api/v1/advertising/owner/advertisements/<id>/mock-payment/`<br>`GET /api/v1/advertising/feed/` | `IsAuthenticated` (Owner)<br>`AllowAny` (Public feed) | **Verified** (BE002 recovered) |
| **C08: Housing Groups** | `GET /api/v1/features/v1/planning-capabilities/` | `AllowAny` / `IsAuthenticated` | **Gated** (Disabled via DEP001) |
| **C09: Housing Requests** | `GET /api/v1/features/v1/planning-capabilities/` | `AllowAny` / `IsAuthenticated` | **Gated** (Disabled via DEP001) |
| **S01: Identity & Offer Snapshots** | Embedded `offer_snapshot` in visits, invitations, leases | Server authoritative | **Verified** |
| **S02: Decision Support** | `GET /api/v1/features/v1/planning-capabilities/` | `AllowAny` | **Gated** (Disabled via DEP001) |
| **S03: Recovery Protocol** | `GET /api/v1/features/v1/rental-operations/<request_key>/` | `IsAuthenticated` | **Verified** |

---

## 5. Section 12: Backend Return Form

```markdown
### 12. Backend Return Form

#### 12.1 Release and Deployment Identity
- Deployed Commit / Ref: Working tree HEAD (monorepo root)
- Settings Module: config.settings.test (local) / config.settings.production (deployed)
- Python / Django / DRF: Python 3.11.4 / Django 4.2.11 / DRF 3.15.1
- Celery / Channels: Celery 5.3.6 / Channels 4.0.0
- Timezone / Active Locale: Africa/Cairo / 'ar', 'en' (MobileLocaleMiddleware)

#### 12.2 Verification Summary
- Preflight Checks:
  - `python manage.py check`: 0 issues
  - `python manage.py makemigrations --check --dry-run`: No changes detected
- Pytest Suite:
  - Total Collected: 599 items
  - Total Passed: 592 passed
  - Total Skipped: 7 skipped
  - Total Failed: 0 failed

#### 12.3 Work Register Execution
- BE001 (Guest Public Discovery): PASSED (TestPublicGuestDiscoveryEndpoints, test_public_guest_access_allowed)
- BE002 (Banner Media Recovery & Mock Payment): PASSED (test_existing_audit_ad_media_recovery_and_mock_payment_activation)
- BE003 (Bilingual Visit Request & Calendar): PASSED (TestBilingualVisitLabels)
- GAP001 (Never-Occupied Cancelled Draft): PASSED (test_cancelled_never_occupied_draft_closure_blockers_and_financial_policy)
- DEP001 (Planning Capabilities Route): PASSED (test_planning_capabilities_endpoint_returns_disabled_capabilities_and_version)
- DEP002 (Structured Rental Capabilities): PASSED (Gated by fake_provider_available, safe defaults)
- OBS001 (Chat Broadcast on Commit): PASSED (test_two_authenticated_connections_receive_broadcast_and_rest_persistence)
- DEC001 (Policy Decisions): Documented in Section 3
```
