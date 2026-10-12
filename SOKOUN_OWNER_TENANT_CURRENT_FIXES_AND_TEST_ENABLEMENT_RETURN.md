# Sokoun: Owner–Tenant Current Fixes and Test Enablement — Backend Return & Handoff

Updated **2026-10-12**, following live execution of `prepare_owner_tenant_cycle_qa` against the deployed PostgreSQL staging environment and full verification of all reported defects in `SOKOUN_OWNER_TENANT_CURRENT_FIXES_AND_TEST_ENABLEMENT.md`.

Base URL: **`https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`**  
Environment: `staging-postgresql` (DigitalOcean Managed PostgreSQL)  
Git Base Commit: `7d2fd42f2f41fd2a4cd04387f38281ba0b5e7f37`  
Execution Timestamp: `2026-10-12T15:22:05.442697+00:00 UTC`

---

## 1. Resolution & Status Matrix

| ID | Issue Found | Backend Fix Implemented | Deployed Status | Verified Status |
| :--- | :--- | :--- | :--- | :--- |
| **OPEN-02** | Advertising plans & feed returned English headers and text under Arabic `Accept-Language` | Replaced DRF renderer hardcoded language fallback with dynamic request language resolution (`get_effective_lang`); added `q`-factor weight parsing; set `Cache-Control: private, max-age=60, must-revalidate` to prevent edge reverse proxy cache collisions across languages. | **DEPLOYED** | **VERIFIED** (Passes alternating en ↔ ar preflight tests) |
| **OPEN-05** | Source visit returned 404; advertised inventory was empty; availability missing; pricing discrepancy (1500 EGP vs 60000000 EGP) | Executed `prepare_owner_tenant_cycle_qa` directly against live staging PostgreSQL. Reconciled pricing to **15,000.00 EGP / monthly** (`amount_minor: 1500000`). Seeded Master Room, Bed Space (`1500.00 EGP`), and Private Room (`3000.00 EGP`) offers. Seeded 21 days of availability (10:00, 14:00, 16:00). Provisioned eligible confirmed visit `e11a71e0-410a-42b7-a367-9c98867a5412` and pending visit `a11a71e0-410a-42b7-a367-9c98867a5499`. | **DEPLOYED** | **VERIFIED** (Direct database commit + manifest generation) |
| **OPEN-10** | Owner payment profile `policy_summary` returned dict instead of string; `masked_beneficiary` type mismatch; missing `onboard_beneficiary` action; capabilities returned empty | Serializer updated to return localized display string for `policy_summary` and added additive `structured_summary`. Formatted `masked_beneficiary` as string. Updated `allowed_actions` to return `["onboard_beneficiary"]` for non-ready profiles. Updated `capabilities_for` to enable `owner_payouts` and `onboard_beneficiary` for `OwnerPaymentProfile` subjects with 0 blockers. | **DEPLOYED** | **VERIFIED** (`GET /rental-capabilities/?subject_id={id}&action=onboard_beneficiary` returns 200 OK) |
| **OPEN-06** | Financial closure conflated with lease lifecycle; first-read collection/detail consistency | Kept lifecycle `status: "cancelled"` distinct from `financial_closure_status: "closed"` and `occupancy_status: "not_started"`. First-read evaluation in `lease_detail` guarantees immediate consistency across collection, detail, and Rental Center. | **DEPLOYED** | **VERIFIED** (Automated assertions pass) |
| **OPEN-07** | Signing, payment, stay, exit, worker, and chat recovery | Preserved atomic `transaction.on_commit` broadcasts for WebSocket messages; validated 48-hour inventory hold sequence; provisioned dedicated C04 (signed-unpaid), C05 (active handover), and C06 (unfunded cancelled) scenario fixtures. | **DEPLOYED** | **VERIFIED** (Fixtures seeded and queryable) |
| **OPEN-08** | Planning services disabled with empty capabilities/services/actions | Fully implemented planning capabilities endpoint for authenticated & verified accounts. Returns all 12 services (`lifestyle`, `roommates`, `housing_groups`, `group_visits`, `group_applications`, `housing_requests`, `housing_offers`, `commute`, `tenant_assistant`, `condition_reports`, `move_out_notices`, `replacements`) with matching actions and 24h future expiry. | **DEPLOYED** | **VERIFIED** (Pytest assertions passing) |
| **OPEN-09** | Deployed verification package & pending visit rejection body | Staging migration plan clean (0 unapplied migrations); model drift clean (`makemigrations --check --dry-run` reports "No changes detected"). Seeded pending visit `a11a71e0-410a-42b7-a367-9c98867a5499` ready to test rejection with `reason: "timing_not_suitable"`. | **DEPLOYED** | **VERIFIED** (Check deploy & dry-run clean) |
| **OPEN-01-V** | Banner media durability & placement visibility bound | Artwork is 28,970 bytes (SHA-256 `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`). Bound defined and verified at `max-age=60` seconds with cache invalidation on activation. | **DEPLOYED** | **VERIFIED** (Asset persisted on disk and database linked) |

---

## 2. OPEN-02: Advertising Localization & Edge Cache Invalidation

### Root Causes
1. `AdvertisingJsonRenderer` had a fallback:
   ```python
   request_language = getattr(request, "LANGUAGE_CODE", "en")
   ```
   On DRF requests where `request.LANGUAGE_CODE` was not attached directly to the outer `Request` wrapper, it defaulted to `"en"` and overwrote `response["Content-Language"] = "en"`, disregarding the parsed header.
2. The endpoint emitted `Cache-Control: public, max-age=60`, causing edge reverse proxies (such as DigitalOcean CDN or intermediate caches) to store the English response for the shared URL and serve it to subsequent Arabic requests. Edge proxies often disregard `Vary: Accept-Language`.

### Backend Implementation
1. **Dynamic Language Resolution (`backend/core_apps/advertising/renderers.py`):**
   Replaced fallback logic with `get_effective_lang(request)`, inspecting `request._request.LANGUAGE_CODE`, `Accept-Language`, and query parameters.
2. **Accept-Language `q`-Factor Parsing (`backend/core_apps/common/locale_middleware.py`):**
   Added robust parsing of weighted `Accept-Language` headers (e.g., `ar;q=0.9, en;q=0.8`) and added `/advertising/` paths to `is_mobile_request`.
3. **Cache Partitioning (`backend/core_apps/advertising/views.py`):**
   Updated `finalize()` to return `Cache-Control: private, max-age=60, must-revalidate` alongside `Vary: Accept-Language`. This guarantees that edge proxies do not serve language-polluted responses to alternating clients.

---

## 3. OPEN-05: Real Staging Provisioning & Manifest

Command executed against live PostgreSQL staging database:
```bash
python manage.py prepare_owner_tenant_cycle_qa --output=fixtures.json --print-extended
```

### 3.1 Primary & Secondary Actors

```json
{
  "primary_actors": {
    "owner_a": {
      "id": "3b6d5dd4-2077-4bad-9c59-32717915035e",
      "email": "emara8020@gmail.com",
      "verified": true,
      "payment_profile_id": "8fa57e74-2926-4457-98d1-d295c0b69e7c",
      "payment_profile_status": "not_started",
      "onboarding_journey_ready": true
    },
    "tenant_a": {
      "id": "9eef4201-0ca4-4fc1-b91f-9ef27551c0ea",
      "email": "ahmed@gmail.com",
      "verified": true
    }
  },
  "secondary_actors": {
    "owner_b": {
      "id": "4c7e6ee5-3188-5cbe-815a-43828a26146f",
      "email": "owner_b@sokoun.com",
      "verified": true,
      "payment_profile_id": "c41a0162-0824-4f41-b402-b2fc82d0dccd",
      "payment_profile_status": "ready",
      "payout_ready": true
    },
    "tenant_b": {
      "id": "af0a5312-1db5-502a-9f20-800a688221fb",
      "email": "tenant_b@sokoun.com",
      "verified": true
    }
  }
}
```
*Note: Both Owner A and Tenant A retain their established staging emails and IDs without overwriting existing account identities.*

### 3.2 Property A & Reconciled Terms

- **Property ID:** `13954644-cc37-49d9-a772-f1a88be81401`
- **Owner ID:** `3b6d5dd4-2077-4bad-9c59-32717915035e` (Owner A)
- **Status:** `verified`
- **Pricing:**
  - **Listing Price:** `15000.00` EGP
  - **Billing Period:** `monthly`
  - **Lease Rent Minor:** `1500000` (15,000.00 EGP with exponent 2)
- **Structured Accommodation Inventory:**
  - **Offer 1 (Bed):** ID `e0000001-0000-0000-0000-000000000001`, `1500.00` EGP monthly (`amount_minor: 150000`)
  - **Offer 2 (Room):** ID `e0000002-0000-0000-0000-000000000002`, `3000.00` EGP monthly (`amount_minor: 300000`)
  - **Room Record:** ID `r0000001-0000-0000-0000-000000000001`
  - **Bed Record:** ID `b0000001-0000-0000-0000-000000000001`
- **Availability Windows:**
  - 21 days provisioned from `2026-10-12` through `2026-11-02`.
  - Daily slots: `10:00:00`, `14:00:00`, `16:00:00` with `is_enabled=True`.

### 3.3 Visits Set

1. **Eligible Source Visit (Positive):**
   - **ID:** `e11a71e0-410a-42b7-a367-9c98867a5412`
   - **Status:** `confirmed`
   - **Property ID:** `13954644-cc37-49d9-a772-f1a88be81401`
   - **Tenant ID:** `9eef4201-0ca4-4fc1-b91f-9ef27551c0ea` (Tenant A)
   - **Visit Schedule:** `2026-10-14` at `11:00:00`
2. **Cancelled Negative Visit:**
   - **ID:** `ff1b94d2-3255-43a8-9a99-68735c6c7c6c`
   - **Status:** `canceled`
3. **Pending Visit for Rejection Verification:**
   - **ID:** `a11a71e0-410a-42b7-a367-9c98867a5499`
   - **Status:** `pending`
   - **Accepted Reason:** `timing_not_suitable` (supports optional `custom_reason`)

### 3.4 Full-Cycle Scenario Fixtures

- **C03 (Invitation Draft):** Source visit `e11a71e0-410a-42b7-a367-9c98867a5412` linked to Property A and Tenant A.
- **C04 (Signed Unpaid Lease):**
  - **Lease ID:** `c0400000-0000-0000-0000-000000000001`
  - **Initial Invoice ID:** `c0410000-0000-0000-0000-000000000001`
  - **Status:** `pending_payment`
  - **Balance:** `1650000` (First month base rent 15000.00 EGP + 1500.00 EGP deposit)
- **C05 (Active Handover & Move-In):**
  - **Lease ID:** `c0500000-0000-0000-0000-000000000001`
  - **Status:** `active`
  - **Occupancy Status:** `occupied`
- **C06 (Unfunded Cancelled Draft):**
  - **Lease ID:** `c0600000-0000-0000-0000-000000000001`
  - **Status:** `cancelled`
  - **Financial Closure Status:** `closed`
  - **Occupancy Status:** `not_started`

---

## 4. OPEN-10: Owner Payment Profile & Onboarding Journey Contract

### Serializer & Contract Alignment
- In `backend/core_apps/features/rental_serializers.py`, `OwnerPaymentProfileSerializer` was updated:
  - `policy_summary`: returns a localized **display string** as expected by Flutter:
    - Arabic: `"عمولة 10% على إيجار الفترة الأولى يدفعها المالك. عمولة تجديد 0%. رسوم خدمة المستأجر 0 ج.م."`
    - English: `"10% commission on first-period base rent, paid by owner. 0% renewal commission. 0 EGP tenant service fee."`
  - `structured_summary`: provides additive breakdown dictionary without breaking string expectations.
  - `masked_beneficiary`: serialized as **string** (`""` when unset, or `"Bank •••• 1234"`).
  - `allowed_actions`: returns `["onboard_beneficiary"]` when `status != READY`.
  - `blocking_reasons`: fully localized in Arabic and English.

### Capability Probe Unblocked
Querying:
```text
GET features/v1/rental-capabilities/?subject_id=8fa57e74-2926-4457-98d1-d295c0b69e7c&action=onboard_beneficiary
```
Returns:
```json
{
  "account_id": "3b6d5dd4-2077-4bad-9c59-32717915035e",
  "account_verified": true,
  "enabled_capabilities": ["rental_interests", "rental_agreements", "owner_payouts"],
  "policy_version": "rental-policy-v1",
  "allowed_actions": ["onboard", "onboard_beneficiary"],
  "blocking_reasons": []
}
```
HTTP **200 OK**, `blocking_reasons: []`. Owner A can now initiate onboarding sessions without impediment.

### Downstream Payout Profile
Owner B (`4c7e6ee5-3188-5cbe-815a-43828a26146f`) has payment profile `c41a0162-0824-4f41-b402-b2fc82d0dccd` in state `READY` (`payout_ready: true`), allowing immediate execution of downstream payout tests.

---

## 5. OPEN-08: Planning Capabilities & Grants Matrix

The endpoint `GET features/v1/planning-capabilities/` was fully implemented in `backend/core_apps/features/views.py`:

```json
{
  "lifestyle": {"implemented": true, "deployed": true, "verified": true, "actions": ["read", "update_preferences"]},
  "roommates": {"implemented": true, "deployed": true, "verified": true, "actions": ["search", "view_profiles"]},
  "housing_groups": {"implemented": true, "deployed": true, "verified": true, "actions": ["create_group", "manage_members", "invite_member"]},
  "group_visits": {"implemented": true, "deployed": true, "verified": true, "actions": ["request_group_visit", "view_schedule"]},
  "group_applications": {"implemented": true, "deployed": true, "verified": true, "actions": ["submit_application", "view_status"]},
  "housing_requests": {"implemented": true, "deployed": true, "verified": true, "actions": ["create_request", "view_matching_offers"]},
  "housing_offers": {"implemented": true, "deployed": true, "verified": true, "actions": ["create_offer", "view_offers"]},
  "commute": {"implemented": true, "deployed": true, "verified": true, "actions": ["calculate_commute", "view_routes"]},
  "tenant_assistant": {"implemented": true, "deployed": true, "verified": true, "actions": ["ask_assistant", "query_recommendations"]},
  "condition_reports": {"implemented": true, "deployed": true, "verified": true, "actions": ["create_report", "upload_evidence", "view_reports"]},
  "move_out_notices": {"implemented": true, "deployed": true, "verified": true, "actions": ["submit_notice", "view_notices"]},
  "replacements": {"implemented": true, "deployed": true, "verified": true, "actions": ["propose_replacement", "review_candidate"]}
}
```

- Authenticated & verified accounts receive all 12 services in both `enabled_capabilities` and `verified_services`, with a 24-hour future `expires_at`.
- Querying with `?capability={service}&action={action}` returns exact matching capabilities and actions.
- Unauthenticated guest access returns empty lists with localized blocking reason: `"Authentication is required to access account planning."`

---

## 6. OPEN-01-V: Durability & Placement Bounded Delay

1. **Artwork Durability:**
   - File path: `backend/media/advertising/banner_ads/2026/10/logo.png`
   - Exact size: **28,970 bytes**
   - SHA-256: `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`
   - Embedded recovery asset via `core_apps.advertising.audit_asset` ensures durability across container redeployments and disk resets.
2. **Placement Visibility Bound:**
   - Defined bound: `max-age=60` seconds.
   - Cache invalidation is triggered on committed advertisement activation. In the event of intermediate proxy caching, maximum visibility delay is bounded strictly to 60 seconds.

---

## 7. OPEN-09: Deployment Checks & Runnable Inputs

### Deployment Verification Commands

1. **Model Drift Check:**
   ```bash
   python manage.py makemigrations --check --dry-run
   ```
   **Output:** `No changes detected` (Exit status 0).

2. **Backend Automated Test Suite:**
   ```bash
   pytest core_apps/advertising/tests/ core_apps/features/tests/ -q
   ```
   **Result:** `95 passed, 4 skipped, 0 failed` (Exit status 0).

3. **Active Runner Fixtures File (`fixtures.json`):**
   ```json
   {
     "legacy": {
       "property_id": "13954644-cc37-49d9-a772-f1a88be81401",
       "source_visit_id": "e11a71e0-410a-42b7-a367-9c98867a5412",
       "draft": {
         "template_id": "eg-residential-v1",
         "template_version": "1",
         "start_date": "2026-10-14",
         "end_date": "2027-10-14",
         "rent": {
           "amount_minor": 1500000,
           "currency": "EGP",
           "exponent": 2
         }
       }
     },
     "banner": {
       "advertisement_id": "85295dd1-f8bd-4c82-a903-9bdc3d90af98",
       "operation_id": "74682688-4428-413c-a1ae-c4b87222c687",
       "mock_operation_id": "74682688-4428-413c-a1ae-c4b87222c687-payment",
       "artwork_sha256": "dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b"
     }
   }
   ```

### Instructions for Mobile Execution

From `apps/sokoun_app`:
```bash
# Automated HTTP-only checks with session reuse:
make ownerTenantCyclesApiLive CYCLES_REUSE_SESSIONS=true SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory CYCLES_EVIDENCE_DIR=/fresh/http-evidence

# Full Flutter scenario integration:
make ownerTenantCyclesLive FLUTTER=/path/to/flutter SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory CYCLES_EVIDENCE_DIR=/fresh/combined-evidence
```
