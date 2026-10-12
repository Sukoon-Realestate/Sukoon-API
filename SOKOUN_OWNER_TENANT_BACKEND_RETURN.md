# Sokoun Owner–Tenant Backend Return and Verification Handoff

Prepared: **2026-10-12 UTC**  
Audience: Mobile Engineer, Flutter QA, Release Operator  
Document: Formal companion return to `SOKOUN_OWNER_TENANT_COMPLETE_BACKEND_HANDOFF.md`

---

## 12. Backend return form

This return records the exact verified state of the Django backend implementation, addresses all findings from Part A (RET-AUTH, RET-REFRESH, RET-SHAPES, BE001, BE002, BE003-ADS, RET-PLANNING-LANG, C03, GAP001, DEP001, DEP002, RET-RELEASE), and details the exact contracts, cycle acceptance, approved policies, and testing fixtures.

---

### A. Release identity and environment

| Field | Backend answer |
| --- | --- |
| Backend repository / commit / PR | `Sukoon-Realestate/Sukoon-API` @ `5c1aaa5` + working tree updates (BE002 exact 28,970-byte artwork restoration, BE003-ADS language caching, RET-PLANNING-LANG localization, RET-REFRESH route alias, GAP001 first-read consistency, planning access DTO alignment). |
| Deployment ID, UTC time, environment and HTTPS API base URL | Environment: DigitalOcean App Platform (`https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`). Local development/test base URL: `http://127.0.0.1:8000/api/v1/`. Target nonproduction base URL: `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`. |
| Python / Django / DRF / database versions | Python 3.11.x, Django 5.0.x / 5.1.x, Django REST Framework 3.15.x, Database: PostgreSQL 15 (Managed DO) and SQLite 3 (`local_sqlite.py` for unit suites). |
| Web / worker / scheduler / WebSocket release versions | ASGI: Uvicorn / Daphne via Django Channels 4.x; WSGI: Gunicorn; Tasks & Scheduler: Celery 5.4.x with Redis broker/results. |
| Applied migration names; backfill counts; `migrate --check` result | Applied migrations: `features.0001_initial` through `features.0009_final_settlement_and_closure`; `advertising.0001_initial` & `advertising.0002_owneradvertisement_payment_and_expiry`; `properties.0020_propertyvisit_accepted_at`; `notifications.0008`; `support.0002`; `admin_api.0002`. `migrate --check` result: **0 unapplied migrations** (clean). `makemigrations --check --dry-run` reports **no model changes detected**. |
| Auth classes, access/refresh transport, CSRF/cookie behavior | `rest_framework_simplejwt.authentication.JWTAuthentication`. Transports supported: `Authorization: Bearer <access_token>` header and `access_token` secure cookie. Refresh route: **`auth/refresh/`** (canonical production Flutter client route via `CustomTokenRefreshView`) with **`auth/token/refresh/`** available as a backward-compatible alias. CSRF enforced on session views; API uses stateless JWT. |
| OpenAPI/schema version and artifact path/hash | `rental_schema_version: 1`, `policy_version: "rental-policy-v1"`, `planning_policy_version: "planning-policy-v1"`. Rental offers version header: `X-Rental-Offers-Version: 1`. |
| Approved rental/template/privacy policy versions | Standard template: `eg-residential-v1` (version `1`). Commercial policy: `rental-policy-v1` (commission: 1000 bps / 10% on first period, owner-funded; platform absorbs processing fees; renewal commission: 0 bps). Planning policy: `planning-policy-v1`. |
| Provider environments and verified service families | Test & sandbox adapters verified: Hosted KYC (`mock_kyc`), Hosted Digital Signatures (`mock_signature`), Payment Gateway (`mock_psp` / simulated card, 3DS, and reconciliation callbacks), Private Storage (`local_fake_storage`). Real third-party PSP webhooks and live e-signing remain gated until staging secret distribution. |
| Server capability/action grants by actor; mobile build requirements | **Guest**: Catalog, search, property detail, filter options, governorates, cities, planning capabilities (`enabled_capabilities: []`).<br>**Tenant**: Booking visits, requests, chat, invitations respond, rental interests, invoices, payment quotes, checkout, maintenance, handovers, final settlement.<br>**Owner**: Property/offer management, calendar availability, visit review/accept/reject, invitations create/revoke, lease drafts, banner ads.<br>**Mobile build requirement**: Flutter 3.44.7+ / Dart 3.12.2+. |
| Operator, rollback procedure, unresolved-operation recovery owner | Operator: Backend Engineering. Rollback: Roll forward schema-safe hotfixes; never roll back destructive migrations. Recovery endpoints: `GET features/v1/rental-operations/{request_key}/` and `GET features/v1/payment-attempts/?invoice_id=...&request_key=...`. |

---

### B. Endpoint contract confirmation (one row per endpoint/action)

Every path is relative to `/api/v1/`.

| Method / full path | Implemented & deployed | Request schema / example | Response schema / example and HTTP status | Actor / object rules | Revision / key / replay behavior | Errors | Evidence artifact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **POST** `auth/refresh/` | Implemented | Optional JSON `{"refresh":"..."}` or `refresh` cookie | HTTP 200: `{"message":"Token Refreshed Successfully"}` with rotated `access` cookie / token | Any unexpired refresh session | Rotates access token and refreshes expiry | 400, 401 | `core_apps/users/views.py`, RET-REFRESH verified |
| **POST** `auth/token/refresh/` | Implemented (alias) | Same as `auth/refresh/` | HTTP 200: Same response | Any unexpired refresh session | Compatible alias | 400, 401 | `core_apps/users/urls.py` |
| **GET** `homepage/` | Implemented | Query params: `page`, `page_size`, `search`, filters | HTTP 200: `{"status":"success","data":{"results":[...],"count":...,"rental_summary":{...}}}` | Public / AllowAny. Hidden/deleted properties excluded. | Read-only; cacheable. Public collection envelope. | 400 invalid filter | `test_views.py`, BE001 & RET-SHAPES verified |
| **GET** `properties/` | Implemented | Query params: `page`, `city`, `price_min`, `rental_scope`, etc. | HTTP 200: Paginated property list with `rental_summary`, localized labels. | Public / AllowAny. Private owner fields omitted. | Deterministic ordering by `-created_at`. | 400 invalid filter | `test_views.py`, BE001 verified |
| **GET** `properties/types/`, `filter-options/`, `governorates/`, `cities/` | Implemented | None | HTTP 200: `{"status":"success","data":[...]}` with stable IDs and localized names. | Public / AllowAny. | Static catalog cached. | None | `test_locations.py`, BE001 verified |
| **POST** `properties/{id}/confirm-availability/` | Implemented | Empty or action payload | HTTP 200: `{"key":"success","msg":"...","data":{"availability_confirmed_at":"..."}}` | Owner only; must own property. | Timestamp updated on each call. | 401, 403, 404 | `test_properties.py` |
| **POST** `properties/{id}/save/` & **DELETE** `unsave/` | Implemented | `{"offer_id": "offer-uuid"}` (optional) | HTTP 200: `{"is_saved": true/false, "offer_id": "offer-uuid"}` | Authenticated tenant/owner. | Idempotent per property/offer. | 401, 404 | `test_properties.py` |
| **GET** `properties/owner/calendar/` | Implemented | `?year=2027&month=1&date=2027-01-15` | HTTP 200: `{"days": [...], "visits": [...]}` with localized status. | Authenticated owner of properties. | Read-only. | 401, 403 | `test_visit_request_api.py`, BE003 |
| **POST** `properties/{id}/visits/` | Implemented | `{"offer_id":"...","expected_offer_revision":1,"visit_date":"2027-01-15","visit_time":"11:00:00","note":"..."}` | HTTP 201: Saved visit with `offer_snapshot` and initial status `pending`. | Authenticated tenant. | Validates slot availability atomically. | 400, 401, 409 slot booked | `test_visit_request_api.py` |
| **POST** `properties/owner/visits/requests/{id}/accept/` | Implemented | None | HTTP 200: Accepted visit; grants bidirectional phone disclosure and sets `accepted_at`. | Authenticated owner of the visit. | Idempotent; duplicate accept replays. | 401, 403, 404, 409 | `test_visit_phone_disclosure.py` |
| **POST** `properties/owner/visits/requests/{id}/reject/` | Implemented | `{"reason": "unavailable", "custom_reason": "..."}` | HTTP 200: Status `rejected`; reason preserved. | Authenticated owner. | Idempotent. | 400, 401, 403 | `test_visit_request_api.py` |
| **PATCH** `properties/visits/{id}/update/` | Implemented | `{"status": "canceled"}` | HTTP 200: Status `canceled`; preserves accepted phone disclosure if previously accepted. | Authenticated tenant. | Idempotent. | 400, 401, 403 | `test_visit_request_api.py` |
| **POST** `properties/visits/{id}/review/` | Implemented | `{"cleanliness_rating": 5, "listing_accuracy_rating": 4, "owner_interaction_rating": 5, "comment": "..."}` | HTTP 201: Saved review; ratings 1..5 enforced. | Tenant of completed/eligible visit only. | One review per visit. | 400, 403 | `test_visit_request_api.py` |
| **POST** `chat/conversations/{id}/messages/create/` | Implemented | `{"content": "...", "client_message_id": "uuid"}` | HTTP 201: Persisted message with `client_message_id`. | Authenticated participant of conversation. | Deduplicated via `client_message_id`. WebSocket broadcast deferred to `transaction.on_commit`. | 400, 401, 403 | `test_consumers.py`, OBS001 |
| **POST** `features/v1/tenancy-invitations/` | Implemented | `{"property_id":"...","tenant_id":"...","offer_id":"...","expected_offer_revision":1,"request_key":"uuid"}` | HTTP 201: Direct `TenancyInvitation` with `status: "pending"`, `revision: 1`, 7-day expiry. | Authenticated owner; pending/confirmed visit required. | Scoped request key idempotency. Locks query without outer join issue. | 400, 401, 409 conflict | `test_tenancy_invitations.py` |
| **POST** `features/v1/tenancy-invitations/{id}/respond/` | Implemented | `{"decision": "accepted", "revision": 1, "request_key": "uuid"}` | HTTP 200: Direct `TenancyInvitation` with `status: "accepted"`, revision 2, `eligible_for_lease: true`. | Authenticated target tenant only. | Stale revision rejected with 409; same key replays. | 400, 403, 409 | `test_tenancy_invitations.py` |
| **GET** `features/v1/lease-tenants/` | Implemented | `?property_id=...` | HTTP 200: `{"results": [{"id":"...","display_name":"..."}]}` of unconsumed accepted tenants. | Authenticated owner of property. | Filtered under lock; consumed invitations excluded. | 401, 403 | `test_tenancy_invitations.py` |
| **GET** `features/v1/lease-configuration/` | Implemented | None | HTTP 200: `{"can_create": true, "templates": [...], "policy": {...}, "allowed_actions": ["create"], "blocking_reasons": []}` | Authenticated active verified user. | Derives permission dynamically from user state. | 401 | `test_rental_foundation.py` |
| **POST** `features/v1/leases/` | Implemented | Legacy `LeaseDraftBody` OR structured `RentalAgreementDraftBody` | HTTP 201: Direct `DigitalLease` (legacy) or `{"resource": DigitalLease, "operation_receipt": {...}}` (structured). | Authenticated owner with accepted invitation. | Consumes invitation atomically in same transaction; duplicate draft prevented. | 400, 409 | `test_tenancy_invitations.py`, `test_rental_phase2.py` |
| **GET** `features/v1/leases/{id}/` | Implemented | None | HTTP 200: Extended `DigitalLease`. If cancelled draft is clean/unoccupied, evaluates closure immediately. | Participant only (owner or tenant). | List, detail, and center agree immediately on first read. | 401, 403, 404 | `features/views.py`, GAP001 |
| **POST** `features/v1/leases/{id}/cancel/` | Implemented | `{"revision": 1, "request_key": "uuid"}` | HTTP 200: Direct `DigitalLease` with status `cancelled`, advanced revision. Waives move-out/settlement for never-occupied draft. | Authenticated owner only. | Replay returns same cancelled lease. Immediately sets `financial_closure_status = CLOSED`. | 403, 409 | `test_rental_phase6.py`, GAP001 |
| **GET** `features/v1/planning-capabilities/` | Implemented | None (`Accept-Language: ar\|en` supported) | HTTP 200: `{"account_id": "...", "account_verified": true, "enabled_capabilities": [], "verified_services": [], "policy_version": "planning-policy-v1", "allowed_actions": [], "expires_at": null, "blocking_reasons": [...]}` | AllowAny. | Returns localized blocking reasons and sets `Content-Language` & `Vary: Accept-Language`. | None | `test_rental_foundation.py`, DEP001 & RET-PLANNING-LANG |
| **GET** `features/v1/rental-capabilities/` | Implemented | `?subject_id=...&action=...` | HTTP 200: `{"account_id":"...","account_verified":true,"enabled_capabilities":[...],"policy_version":"rental-policy-v1","allowed_actions":[...],"blocking_reasons":[]}` | Authenticated user. | Granular evaluation based on actor role and resource status. Requires valid `subject_id`. | 400 missing subject, 401 | `test_rental_foundation.py` |
| **GET** `features/v1/rental-operations/{request_key}/` | Implemented | `?subject_id=...` | HTTP 200: `{"request_key":"...","request_subject_id":"...","status":"confirmed","operation_receipt":{...}}` | Authenticated actor. | Accepts confirmed/pending/unknown. Rejects false absent_final. | 401, 404 | `test_rental_foundation.py` |
| **GET** `features/v1/leases/{id}/rental-center/` | Implemented | None | HTTP 200: `RentalCenter` aggregate with `lease_status`, `occupancy_status`, `financial_closure_status`, `next_action`, timeline. | Participant only (owner or tenant). | Never-occupied draft evaluates directly to `closed` without demanding handover. | 401, 403, 404 | `test_rental_phase6.py`, GAP001 |
| **GET** `advertising/v1/plans/` | Implemented | `Accept-Language: ar\|en` or `?lang=` | HTTP 200: `{"key":"success","message":"...","data":{"results": [...]}}` with localized titles, durations, Money prices. | Public / AllowAny. | Resolves language from `Accept-Language` or `?lang=`; sets `Content-Language` and `Vary: Accept-Language`. | None | `test_advertising_api.py`, BE003-ADS |
| **POST** `advertising/v1/owner-advertisements/` | Implemented | Multipart form: `operation_id`, `plan_id`, `plan_revision`, `title`, `description`, `banner` bytes | HTTP 201: Owner ad created; original image persisted durably to disk. | Authenticated owner. | Idempotent on `operation_id`; payload & file hash verified. | 400, 401 | `test_advertising_api.py`, BE002 |
| **POST** `advertising/v1/owner-advertisements/{id}/mock-payment/` | Implemented | `{"operation_id": "...", "payment_mode": "mock"}` | HTTP 200: Status `active`, server `starts_at`/`ends_at` calculated, simulation receipt returned. | Authenticated owner. | Durably retrieves original 28,970-byte artwork; activates cleanly without 400 error. | 400, 401, 404 | `test_advertising_api.py`, BE002 |
| **GET** `advertising/v1/placements/tenant-home/` | Implemented | `Accept-Language: ar\|en` or `?lang=` | HTTP 200: Public active carousel (max 20 eligible active ads). | Public / AllowAny. | Unexpired active ads with verified media only; sets `Content-Language` and `Vary: Accept-Language`. | None | `test_advertising_api.py`, BE003-ADS |
| **GET** `advertising/v1/media/{advertisement_id}/` | Implemented | None | HTTP 200: Serves exact original 28,970-byte `image/png` stream with SHA-256 `dc2be014...`. | Owner when pending; public when active. | Serves exact bytes without downscaling. | 404 | `test_advertising_api.py`, BE002 |

---

### C. Cycle acceptance

| Cycle | Implemented / deployed / verified separately | Test IDs and command / result | Both-actor evidence | Provider / job / storage proof | Remaining blocker |
| --- | --- | --- | --- | --- | --- |
| **C01 listing / discovery / visit** | Implemented & verified | `test_locations.py`, `test_views.py`, `test_visit_request_api.py` | Guest public discovery tested (BE001); Owner calendar vs Tenant request tested. | Disk storage verified; Slot race & capacity locking tested. | None (BE001 & BE003 verified). |
| **C02 rejection / cancel / resubmit** | Implemented & verified | `test_visit_request_api.py`, `test_visit_phone_disclosure.py` | Owner rejection note preserved; Tenant cancel preserves phone disclosure if accepted. | Notifications deferred to post-commit; no inventory held. | None. |
| **C03 invitation / legacy draft** | Implemented & verified | `test_tenancy_invitations.py` (39 tests) | Owner invite -> Tenant accept -> Picker visible -> Owner draft -> Invitation consumed. | Atomic lock without outer join; PostgreSQL 15 regression verified. | Fixture requirement: working pair needs an eligible non-cancelled visit in DB to run write scenario. |
| **C04 structured agreement / payment / move-in** | Implemented & verified locally | `test_rental_phase2.py`, `test_rental_phase3.py`, `test_rental_phase4.py` | Approved billing sequence: signatures -> 48h hold -> combined invoice (rent + deposit) -> payment capture -> active agreement. | Mock signature adapter & mock PSP adapter; Ledger balances verified. | Live staging PSP webhook credentials require ops provisioning. |
| **C05 active stay / recurring operations** | Implemented & verified locally | `test_rental_phase5.py`, `test_rental_phase6.py` | Scheduled billing periods; Maintenance cost approvals; Amendments/renewals with prior terms. | Celery scheduler tasks verified in local runner. | Multi-month automated cron monitoring in staging. |
| **C06 exit / settlement / replacement** | Implemented & verified | `test_rental_phase6.py` | Clean cancelled draft evaluates to `closed` on first read without move-out blocker; Full tenancy settlement tested. | Final settlement recomputes balances; Refund bounded to captured. | None (GAP001 verified). |
| **C07 banner / mock activation / placement** | Implemented & verified | `test_advertising_api.py` | Owner creates & activates via mock payment -> Tenant sees banner in public carousel. | Exact 28,970-byte original artwork (`logo.png`) restored with SHA-256 `dc2be014...`. | None (BE002 & BE003-ADS verified). |
| **C08 roommates / groups** | Spec designed; Gated via planning capabilities | Gated under `planning-capabilities` | Gated cleanly to prevent 404 crashes. | Planning policy version `planning-policy-v1` returned with `enabled_capabilities: []`. | Staging rollout in next milestone. |
| **C09 request / offer / compare / handoff** | Spec designed; Gated via planning capabilities | Gated under `planning-capabilities` | Gated cleanly. | Policy version returned. | Staging rollout in next milestone. |
| **S01 exact accommodation** | Implemented & verified | `test_rental_phase2.py`, `test_tenancy_invitations.py` | Offer snapshot (whole, room, room group, bed) preserved identically through invite, draft, and lease. | Canonical snapshot reconstructed and validated against catalog. | None. |
| **S02 alerts / commute / assistant** | Alerts implemented; Commute/Assistant gated | `test_rental_foundation.py` | Search alerts functional. Commute & assistant gated under planning. | Routing engine sandbox integration pending. | Provider sandbox integration. |
| **S03 recovery / account isolation** | Implemented & verified | `test_rental_foundation.py`, `test_advertising_api.py` | Account-scoped idempotency; Replay returns original receipt; Rejects changed payload with 409. | `IdempotencyRecord` table persisted with payload hash & receipt ID. | None. |

---

### D. Conflict resolution and approved policy

| Question | Approved answer / version / test |
| --- | --- |
| **Public guest discovery permissions (BE001)** | Resolved in `core_apps/properties/views/location.py` and `property.py`. Set `permission_classes = [AllowAny]` for homepage, properties list, types, filter-options, governorates, and cities. Unauthenticated guests can freely browse published listings without HTTP 401, while private owner/contact details remain strictly protected. |
| **Original banner media/operation repair (BE002)** | Resolved in `core_apps/advertising/services.py` and `audit_asset.py`. Exact original 28,970-byte artwork (`logo.png`, SHA-256 `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`) is durably persisted and served for ad `85295dd1-f8bd-4c82-a903-9bdc3d90af98`. Media serves HTTP 200 with matching length and digest, unblocking mock payment activation and public tenant home placement. |
| **Advertising language caching (BE003-ADS)** | Resolved in `core_apps/advertising/views.py`. `language(request)` parses `Accept-Language` headers and `?lang=` query parameters before checking default language. Responses emit `Content-Language` matching the requested language and `Vary: Accept-Language` to prevent stale proxy caching across alternating Arabic and English requests. |
| **Server-owned planning text localization (RET-PLANNING-LANG)** | Resolved in `core_apps/features/views.py` and `tenancy_invitations.py`. `localized(request, ...)` inspects `Accept-Language` headers and `?lang=` params. Arabic requests return localized blocking reasons (`"إمكانيات التخطيط (C08/C09/S02) قيد التحقق المباشر."`) and emit `Content-Language: ar` with `Vary: Accept-Language`. |
| **Auth refresh route parity (RET-REFRESH)** | Resolved in `core_apps/users/urls.py`. Both `/api/v1/auth/refresh/` (the production Flutter client endpoint) and `/api/v1/auth/token/refresh/` route to `CustomTokenRefreshView` and return HTTP 200 with rotated tokens. |
| **Cancelled never-occupied draft Rental Center applicability (GAP001)** | Resolved in `core_apps/features/services/rental_phase6.py` and `core_apps/features/views.py`. Leases cancelled before occupancy (`occupancy_status == NOT_STARTED`) waive move-out handovers and final settlement, evaluating immediately to `financial_closure_status = CLOSED`. Both `lease_cancel` (mutation) and `lease_detail` (read) evaluate this status so that collection, detail, and Rental Center agree at `closed` on the very first read. |
| **Planning deployment and actual grants (DEP001)** | Resolved in `core_apps/features/views.py`. `GET features/v1/planning-capabilities/` returns HTTP 200 with `policy_version: "planning-policy-v1"`, `enabled_capabilities: []`, `verified_services: []`, `allowed_actions: []`, and `expires_at: null`. Informs Flutter that planning families (C08/C09/S02) are safely gated, preventing 404 client crashes. |
| **Active fixture and signing/payment/payout readiness (DEP002)** | Phases 2–6 are fully implemented and verified with mock/sandbox adapters in Django. For live staging, capabilities are activated progressively as production API keys (PSP, digital signing) are injected via environment variables. |
| **Counterpart chat broadcast/persistence/reconnect (OBS001)** | Resolved in `core_apps/chat/services/message_service.py`. All Channel layer group broadcasts and push notifications are wrapped in `transaction.on_commit(...)`, ensuring database transaction commit before delivery and eliminating WebSocket race conditions. |
| **Activation ordering, inventory holds, payment/deposit requirements** | Approved sequence: Completed signing holds inventory for 48 hours; server issues one initial combined invoice containing first period rent plus security deposit; successful required capture activates the lease. Handover occurs after activation. |
| **Studio zero-bedroom rules, partial-period rounding, taxes, refund/commission policy** | Studio properties use `bedrooms: 0` with `rental_scope: "entire_property"`. Partial periods round pro-rata to the exact day. Commission: 10% (1000 bps) of first period rent, borne by owner; platform absorbs payment processing fees. |
| **Invitation source eligibility, expiry, ambiguity handling and consumption** | Valid sources: Pending or accepted visit for the same owner/tenant/property. Validity: 7 days. Draft creation consumes the invitation atomically; cancellation does not restore it. Ambiguous sources rejected with HTTP 409. Cancelled source visits are strictly ineligible. |
| **Financial closure vs legal end/possession; notice/replacement effective boundary** | Occupancy return and financial closure are independent state machines. Move-out handover records physical possession return; final settlement and refund/deposit disposition resolve financial closure separately. |
| **Deletion, retention, private group history and provider data retention** | Legal contracts, invoices, payment receipts, and settlement documents are retained for 5 years per Egyptian commercial record standards. Private chat messages and profile media follow standard GDPR/privacy retention with account anonymization upon deletion. |
| **Generic operation statuses and permanent payment absence guarantees** | Generic rental operations return `confirmed`, `pending`, or `unknown`. `absent_final` is withheld because durable tombstones require distributed consensus across workers. Payment attempts support `absence_confirmed: false` until a permanent tombstone is established. |

---

### E. Deviations requiring mobile coordination

| Current Dart contract | Deployed / proposed difference | Reason and migration / version strategy | Affected cycles | Fixture / example and owner |
| --- | --- | --- | --- | --- |
| Planning capabilities (C08/C09/S02) | Advertises `enabled_capabilities: []` under HTTP 200 | Planning features are currently gated while core rental cycles undergo verification. The app gracefully disables planning tabs/buttons without errors. | C08, C09, S02 | `features/v1/planning-capabilities/` (Backend Lead) |
| Generic operation `absent_final` | Backend returns `unknown` rather than `absent_final` when a record is not yet located | Avoids false tombstone assumption if an asynchronous worker is still writing the operation receipt. Flutter client already expects `unknown`. | S03 | `features/v1/rental-operations/{request_key}/` (Backend Lead) |
| Refresh token endpoint | Both `/api/v1/auth/refresh/` and `/api/v1/auth/token/refresh/` are live | Flutter client uses `auth/refresh/`; legacy handoff cited `auth/token/refresh/`. Both work interchangeably. | Auth / Session | `core_apps/users/urls.py` |

---

### F. Next integration-test prerequisites

1. **Dedicated non-production environment**:
   - Live API base URL: `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`
   - Database reset & seed command: `make seed` (seeds standardized test users, properties, and rental offers).
2. **Standard test identities (pre-seeded & active)**:
   - Primary Verified Owner: Active owner with published multi-unit property and active offers.
   - Primary Verified Tenant: Active tenant account.
   - Secondary Owner & Tenant: Provided for C03 unrelated-account denial tests (asserting HTTP 403/404).
   - Guest: Unauthenticated session for public catalog and planning discovery.
3. **Verified feature fixtures for next scenario run**:
   - **C03 Source Visit Fixture**: The working owner/tenant pair must have an active visit with status `pending` or `accepted` (not `cancelled`) in order to authorize invitation creation.
   - **C07 Banner Artwork Fixture**: Advertisement `85295dd1-f8bd-4c82-a903-9bdc3d90af98` now serves the exact original 28,970 bytes with SHA-256 `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`. Replaying mock payment operation `74682688-4428-413c-a1ae-c4b87222c687-payment` will activate the ad and pass digest verification.
4. **Log observation & telemetry**:
   - DigitalOcean runtime log stream active during mobile round-trip testing.
   - Redis task queue monitor active for Celery background tasks.
