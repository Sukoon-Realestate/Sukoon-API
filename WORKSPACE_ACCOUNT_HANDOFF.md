# Backend Workspace Account Handoff & Contract Confirmation

## 1. Overview & Architecture Alignment

The backend has implemented and verified the **"One account, tenant and owner workspaces"** model. A single authenticated user session now has full authorization to access both tenant and owner APIs without requiring separate accounts or server-side role switching.

---

## 2. What Has Changed / Implemented on the Backend

### 🔐 1. Unified Registration & Identity
- **Registration (`POST /api/v1/auth/users/` & `POST /api/v1/auth/register/`):**
  - Accepts registration payloads without requiring an exclusive `type` / role.
  - Generates the unified `User` account and linked `Profile`.
- **Identity Retrieval (`GET /api/v1/auth/users/me/`):**
  - Returns `id`, `email`, `first_name`, `last_name`, `full_name`, `gender`, `birth_date`, `is_verified`, and legacy metadata `type: "user"`.
  - Works with standard cookie session or Bearer token.

### 🔑 2. Unified Session & Workspace Authorization
- A single authenticated session (`access` token cookie or Authorization header) grants access to all tenant and owner endpoints.
- No `switch-role` endpoint is needed or required. Switching workspaces in Flutter is purely client-side UI routing.

### 📊 3. Graceful Owner Endpoint Empty States (Zero-Listing Accounts)
All owner endpoints return standard empty data structures (rather than `403 Forbidden` or errors) when accessed by an account with no property listings:
- **`GET /api/v1/properties/owned/` (`/my-properties/`):**
  Returns `{ "count": 0, "next": null, "previous": null, "results": [] }`.
- **`GET /api/v1/properties/owner/dashboard/`:**
  Returns `{ "visits_this_week": 0, "active_properties": 0, "overall_rating": 0.0, "pending_requests": 0, "pending_visits": [] }`.
- **`GET /api/v1/properties/owner/profile/`:**
  Returns user identity, `stats.properties_count = 0`, `reviews_count = 0`, `average_rating = 0.0`, `recent_reviews = []`.
- **`GET /api/v1/properties/owner/calendar/?year=YYYY&month=M`:**
  Returns `{ "days": [], "visits": [], "month_label": "...", "selected_date": null }`.
- **`GET /api/v1/properties/owner/visits/requests/`:**
  Returns `{ "tabs": { "new": 0, "pending": 0, "confirmed": 0, "rejected": 0, "all": 0 }, "results": [] }`.

### 🛡️ 4. Resource-Level Permission Enforcement
- Permissions are strictly evaluated against the **target resource** (e.g. "is this user the owner of property X?" or "is this user the tenant/owner of visit Y?"), combined with KYC verification and moderation status.
- Listing mutations (`PUT/PATCH/DELETE /api/v1/properties/<id>/`) enforce `IsOwner` (`obj.owner == request.user`).
- Visit actions (`accept`/`reject`) enforce `visit.property.owner == request.user`.
- Visit cancellation and reviews enforce `visit.tenant == request.user`.

### 👤 5. Shared Profile Synchronization
- **`PATCH /api/v1/profiles/edit/`** atomically updates shared identity (`full_name`, `first_name`, `last_name`, `phone_number`, `avatar`, `birth_date`, `gender`).
- Updates immediately reflect across both:
  - `GET /api/v1/profiles/my-account/` (Tenant view)
  - `GET /api/v1/properties/owner/profile/` (Owner view)

### 📬 6. Universal Inboxes (Chat & Notifications)
- **Notifications (`GET /api/v1/notifications/`):**
  - Attached to the unified `User` account across all workspaces.
  - Unread counts (`/unread-count/`) and mark-all-read (`/mark-all-read/`) apply account-wide.
  - Preserves explicit `notification_type` values and payload IDs:
    - `visit_request`: Sent to property owner (includes `visit_id`, `property_id`, `visit_date`, `visit_time`).
    - `visit_accepted`: Sent to tenant upon owner confirmation (includes `visit_id`, `property_id`, `appointment_date`, `appointment_time`).
    - `visit_rejected`: Sent to tenant upon owner rejection.
    - `new_message`: Sent to chat participant upon receiving a message.
- **Chat (`/api/v1/chat/` & `/ws/chat/`):**
  - Unified across workspaces; WebSocket channel group `chat_user_{user_id}` covers all 1:1 direct conversations for the account.

### 🚫 7. Server-Side Guardrails & Status Codes
- **Self-Booking:** `POST /api/v1/properties/<id>/visits/` returns `400 Bad Request` with `"You cannot book a visit for your own property."` if `property.owner == request.user`.
- **Self-Chat:** `POST /api/v1/chat/conversations/create/` returns `400 Bad Request` with `"You cannot start a conversation with yourself."` if `user_id == request.user.id`.
- **Status Codes:**
  - `401 Unauthorized` is returned **strictly** when authentication cookies / tokens are missing, invalid, or expired.
  - `403 Forbidden` (with detailed reason in response body) is returned for permission, verification, moderation, or ownership violations.

---

## 3. What Needs to be Changed / Handled on the Frontend (Flutter)

1. **Registration Payload:**
   - Omit the `type` field when calling `POST auth/users/` (or `POST auth/register/`).
2. **Session & Workspace State:**
   - Do NOT send role-change or role-switch requests when switching between Tenant and Owner workspaces.
   - Maintain the active workspace selection in local device storage.
   - Retain existing session cookies across workspace switches.
3. **Empty State UI:**
   - Handle empty collections (`[]`) and `0` counts on owner screens as normal empty states (e.g. show "Add your first listing" prompts instead of treating empty lists as errors).
4. **Push Notification Routing:**
   - Route incoming notifications based on `notification_type`:
     - `visit_request` $\rightarrow$ Owner Visit Requests screen.
     - `visit_accepted` / `visit_rejected` $\rightarrow$ Tenant Visit Details screen.
     - `new_message` $\rightarrow$ Chat conversation screen.
5. **Error Handling:**
   - On `401 Unauthorized`: Treat as session expiry and redirect to Login.
   - On `403 Forbidden`: Display the server's error message (e.g., KYC required, not property owner) without logging out the user.

---

## 4. Test Verification Summary
Automated integration test suite `core_apps/properties/tests/test_workspace_account_handoff.py` verifies all requirements:
- `test_single_account_can_access_tenant_and_owner_endpoints`: ✅ PASSED
- `test_auth_me_returns_identity_and_metadata_type`: ✅ PASSED
- `test_reject_booking_own_property`: ✅ PASSED
- `test_reject_chat_with_oneself`: ✅ PASSED
- `test_profile_edit_syncs_across_my_account_and_owner_profile`: ✅ PASSED
- `test_notification_types_preserved`: ✅ PASSED
