# Mobile Developer API Handoff — Profile, Settings & Support

This document details the newly implemented backend API endpoints for **Profile**, **Settings**, and **Support** across both **Tenant** and **Owner** workspaces.

---

## 1. General API & Architecture Conventions

- **Base URL**: `{{base_url}}/api/v1/` (keep trailing slashes).
- **Authentication**: Cookie JWT authentication (`CookieAuthentication`). The authenticated user is identified securely from session cookies (`access_token`), not from any client-supplied user ID.
- **Role & Workspace**:
  - `workspace=tenant|owner` indicates UI context.
  - Cross-user and cross-workspace access is strictly rejected with `404 Not Found` or `403 Forbidden`.
- **Languages**:
  - Default: `ar` (Arabic).
  - Supported: `ar`, `en`.
- **Response Envelopes**:
  - **Success**:
    ```json
    {
      "key": "success",
      "message": "نص الرسالة أو فارغ",
      "data": {}
    }
    ```
  - **Error**:
    ```json
    {
      "key": "error",
      "message": "وصف الخطأ",
      "data": { ... }
    }
    ```
- **Pagination Structure**:
  ```json
  {
    "count": 42,
    "per_page": 20,
    "total_pages": 3,
    "next": "http://.../?page=2",
    "results": [ ... ]
  }
  ```
  *Note: An empty list returns `200 OK` with `count: 0, per_page: 20, total_pages: 1, next: null, results: []`. It is not an error.*
- **Postman Collection**:
  - Authoritative collection path in repo: `docs/postman/profile_settings_support.postman_collection.json` (mirrored at project root `profile_settings_support.postman_collection.json`).

---

## 2. Endpoint Specifications

### 2.1. Change Password

Updates the authenticated user's password while keeping the current session active.

- **Method**: `POST`
- **Path**: `auth/users/set_password/`
- **Authentication**: Required (`IsAuthenticated`)
- **Content-Type**: `application/json`

#### Request Body
```json
{
  "current_password": "CurrentPassword123!",
  "new_password": "NewSecurePassword456!",
  "re_new_password": "NewSecurePassword456!"
}
```

| Field | Type | Required | Rules |
|---|---|---|---|
| `current_password` | String | Yes | Must match current account password. |
| `new_password` | String | Yes | Minimum 8 characters. Validated against standard Django password policies. |
| `re_new_password` | String | Yes | Must match `new_password` exactly. |

#### Success Response (`200 OK`)
```json
{
  "key": "success",
  "message": "تم تغيير كلمة المرور بنجاح",
  "data": {}
}
```

#### Error Cases
- **400 Bad Request** (Incorrect current password):
  ```json
  {
    "key": "error",
    "message": "كلمة المرور الحالية غير صحيحة",
    "data": {
      "current_password": ["كلمة المرور الحالية غير صحيحة"]
    }
  }
  ```
- **400 Bad Request** (Mismatched confirmation):
  ```json
  {
    "key": "error",
    "message": "كلمتا المرور غير متطابقتين",
    "data": {
      "re_new_password": ["كلمتا المرور غير متطابقتين"]
    }
  }
  ```
- **400 Bad Request** (Social Auth account without password):
  ```json
  {
    "key": "error",
    "message": "هذا الحساب مسجل بواسطة تسجيل الدخول الاجتماعي ولا يمتلك كلمة مرور حالية",
    "data": {}
  }
  ```

---

### 2.2. Verification Status

Returns the current KYC identity-verification status for the authenticated user (shared by Tenant and Owner).

- **Method**: `GET`
- **Path**: `profiles/verification-status/`
- **Authentication**: Required (`IsAuthenticated`)

#### Success Response (`200 OK`)
```json
{
  "key": "success",
  "message": "",
  "data": {
    "status": "pending",
    "full_name": "أحمد محمود",
    "submitted_at": "2026-10-03T10:15:00Z",
    "rejection_reason": ""
  }
}
```

| Field | Type | Description |
|---|---|---|
| `status` | String | One of: `incomplete`, `pending`, `approved`, `rejected` |
| `full_name` | String | User's full name from profile |
| `submitted_at` | ISO 8601 / null | Timestamp when KYC was submitted (`null` if `incomplete`) |
| `rejection_reason` | String | Explanation if `status == "rejected"`; empty string otherwise |

*Note: Identity document URLs are intentionally excluded from this summary endpoint for privacy.*

---

### 2.3. Tenant Contracts

Returns paginated rental contracts for the authenticated tenant.

- **Method**: `GET`
- **Path**: `profiles/contracts/?page=1&page_size=20`
- **Authentication**: Required (`IsAuthenticated`)

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | Integer | No | `1` | Page number |
| `page_size` | Integer | No | `20` | Items per page (max 100) |

#### Success Response (`200 OK`)
```json
{
  "key": "success",
  "message": "",
  "data": {
    "count": 1,
    "per_page": 20,
    "total_pages": 1,
    "next": null,
    "results": [
      {
        "id": "e4b2d56a-1123-45c1-9238-984bb3e52701",
        "property_title": "شقة فاخرة في المعادي",
        "status": "active",
        "start_date": "2026-10-01",
        "end_date": "2027-09-30",
        "document_url": "https://res.cloudinary.com/.../contract_signed.pdf"
      }
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID String | Contract unique identifier |
| `property_title` | String | Name of the rented property |
| `status` | String | One of: `active`, `expired`, `cancelled` |
| `start_date` | Date (`YYYY-MM-DD`) | Contract start date |
| `end_date` | Date (`YYYY-MM-DD`) | Contract expiry date |
| `document_url` | String (URL) | Secure document URL (or empty string if not uploaded) |

---

### 2.4. Help Center (FAQs & Contacts)

Returns workspace-specific FAQs and official customer support contact details.

- **Method**: `GET`
- **Path**: `support/help-center/?workspace=tenant&lang=ar`
- **Authentication**: Required (`IsAuthenticated`)

#### Query Parameters
| Parameter | Type | Required | Default | Values |
|---|---|---|---|---|
| `workspace` | String | No | `tenant` | `tenant` \| `owner` |
| `lang` | String | No | `ar` | `ar` \| `en` |

#### Success Response (`200 OK`)
```json
{
  "key": "success",
  "message": "",
  "data": {
    "phone": "+201000000000",
    "email": "support@sokoun.com",
    "hours": "9:00 ص - 6:00 م (السبت - الخميس)",
    "faqs": [
      {
        "id": "faq-tenant-visit-booking",
        "question": "كيف أحجز زيارة؟",
        "answer": "افتح صفحة العقار، ثم اختر موعدًا متاحًا وأرسل طلب الزيارة."
      },
      {
        "id": "faq-tenant-cancel-visit",
        "question": "كيف يمكنني إلغاء موعد الزيارة؟",
        "answer": "يمكنك الذهاب إلى صفحة زياراتي والضغط على خيار إلغاء الزيارة قبل الموعد بـ 24 ساعة على الأقل."
      }
    ]
  }
}
```

---

### 2.5. List User Support Tickets

Returns a paginated list of tickets opened by the signed-in user in the requested workspace.

- **Method**: `GET`
- **Path**: `support/tickets/?workspace=tenant&page=1&page_size=20`
- **Authentication**: Required (`IsAuthenticated`)

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace` | String | Yes | `tenant` | `tenant` \| `owner` |
| `page` | Integer | No | `1` | Page number |
| `page_size` | Integer | No | `20` | Items per page (max 100) |

#### Success Response (`200 OK`)
```json
{
  "key": "success",
  "message": "",
  "data": {
    "count": 1,
    "per_page": 20,
    "total_pages": 1,
    "next": null,
    "results": [
      {
        "id": "7f09825b-aeef-4475-bf59-4d6990429f55",
        "reference": "SUP-00101",
        "subject": "مشكلة في حجز الزيارة",
        "status": "open",
        "category": "visit",
        "created_at": "2026-10-03T10:15:00Z",
        "updated_at": "2026-10-03T10:15:00Z"
      }
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID String | Unique ticket ID |
| `reference` | String | Human-readable reference code (e.g. `SUP-00101`) |
| `subject` | String | Ticket subject |
| `status` | String | One of: `open`, `in_progress`, `resolved`, `closed` |
| `category` | String | Ticket category (see categories list below) |
| `created_at` | ISO 8601 | Creation timestamp |
| `updated_at` | ISO 8601 | Last activity timestamp |

---

### 2.6. Create Support Ticket

Opens a new support ticket. Supports JSON (without files) or `multipart/form-data` (with attachments).

- **Method**: `POST`
- **Path**: `support/tickets/`
- **Authentication**: Required (`IsAuthenticated`)
- **Content-Type**: `application/json` OR `multipart/form-data`

#### Fields
| Field | Type | Required | Rules |
|---|---|---|---|
| `workspace` | String | Yes | `tenant` \| `owner` |
| `category` | String | Yes | Valid category for the workspace (see below) |
| `subject` | String | Yes | 3 to 160 characters (trimmed) |
| `description` | String | Yes | 10 to 4000 characters (trimmed) |
| `attachments` | Files (repeated) | No | Max 3 images, 5 MB each. Allowed types: `image/jpeg`, `image/png`, `image/webp`. |

#### Valid Categories
- **Shared categories**: `visit`, `payment`, `verification`, `property`, `other`
- **Tenant-only category**: `report_owner`
- **Owner-only category**: `report_tenant`

#### Success Response (`201 Created`)
```json
{
  "key": "success",
  "message": "تم إنشاء التذكرة بنجاح",
  "data": {
    "id": "7f09825b-aeef-4475-bf59-4d6990429f55",
    "reference": "SUP-00101",
    "subject": "مشكلة في حجز الزيارة",
    "status": "open",
    "created_at": "2026-10-03T10:15:00Z",
    "messages": [
      {
        "id": "90db2077-3e11-4ca4-934c-d9c9b4e19197",
        "sender": "user",
        "body": "لا أستطيع إكمال طلب الزيارة بعد اختيار الوقت.",
        "created_at": "2026-10-03T10:15:00Z",
        "attachments": [
          {
            "id": "31bdf7f4-b258-45be-bb37-9759ad268f76",
            "name": "screenshot.png",
            "url": "https://res.cloudinary.com/.../screenshot.png"
          }
        ]
      }
    ]
  }
}
```

---

### 2.7. Ticket Detail & Thread

Fetches the complete message thread of a support ticket.

- **Method**: `GET`
- **Path**: `support/tickets/{id}/?workspace=tenant`
- **Authentication**: Required (`IsAuthenticated`)

#### Path & Query Parameters
| Parameter | Location | Required | Description |
|---|---|---|---|
| `id` | Path | Yes | UUID of the ticket |
| `workspace` | Query | Yes | `tenant` \| `owner` |

#### Success Response (`200 OK`)
```json
{
  "key": "success",
  "message": "",
  "data": {
    "id": "7f09825b-aeef-4475-bf59-4d6990429f55",
    "reference": "SUP-00101",
    "subject": "مشكلة في حجز الزيارة",
    "status": "open",
    "created_at": "2026-10-03T10:15:00Z",
    "messages": [
      {
        "id": "90db2077-3e11-4ca4-934c-d9c9b4e19197",
        "sender": "user",
        "body": "لا أستطيع إكمال طلب الزيارة بعد اختيار الوقت.",
        "created_at": "2026-10-03T10:15:00Z",
        "attachments": [
          {
            "id": "31bdf7f4-b258-45be-bb37-9759ad268f76",
            "name": "screenshot.png",
            "url": "https://res.cloudinary.com/.../screenshot.png"
          }
        ]
      },
      {
        "id": "ba3a0c56-f40c-4fa2-9387-9da57d192801",
        "sender": "support",
        "body": "مرحباً، تم حل المشكلة في النظام، يرجى إعادة المحاولة الآن.",
        "created_at": "2026-10-03T10:45:00Z",
        "attachments": []
      }
    ]
  }
}
```

*Note: `sender` is always `"user"` (client) or `"support"` (admin/staff), computed relative to the authenticated user.*

---

### 2.8. Reply to a Support Ticket

Appends a new reply to an existing active ticket.

- **Method**: `POST`
- **Path**: `support/tickets/{id}/replies/`
- **Authentication**: Required (`IsAuthenticated`)
- **Content-Type**: `application/json`

#### Request Body
```json
{
  "body": "شكراً جزيلاً، تم حجز الموعد بنجاح الآن."
}
```

| Field | Type | Required | Rules |
|---|---|---|---|
| `body` | String | Yes | 1 to 4000 characters (trimmed) |

#### Success Response (`200 OK`)
Returns the **complete updated ticket** including the newly appended message:
```json
{
  "key": "success",
  "message": "تم إرسال الرد بنجاح",
  "data": {
    "id": "7f09825b-aeef-4475-bf59-4d6990429f55",
    "reference": "SUP-00101",
    "subject": "مشكلة في حجز الزيارة",
    "status": "open",
    "created_at": "2026-10-03T10:15:00Z",
    "messages": [
      {
        "id": "90db2077-3e11-4ca4-934c-d9c9b4e19197",
        "sender": "user",
        "body": "لا أستطيع إكمال طلب الزيارة بعد اختيار الوقت.",
        "created_at": "2026-10-03T10:15:00Z",
        "attachments": []
      },
      {
        "id": "c1f7b884-7a13-4318-ae38-7bbfa1487229",
        "sender": "user",
        "body": "شكراً جزيلاً، تم حجز الموعد بنجاح الآن.",
        "created_at": "2026-10-03T11:00:00Z",
        "attachments": []
      }
    ]
  }
}
```

#### Error Cases
- **409 Conflict** (Ticket resolved or closed):
  ```json
  {
    "key": "error",
    "message": "لا يمكن الرد على تذكرة مغلقة أو تم حلها",
    "data": {}
  }
  ```
- **404 Not Found** (Ticket belongs to another account or does not exist):
  ```json
  {
    "key": "error",
    "message": "التذكرة غير موجودة",
    "data": {}
  }
  ```

---

## 3. Flutter Client Integration Checklist

- [ ] **Change Password**:
  - Connect `ChangePasswordScreen` to `POST /api/v1/auth/users/set_password/`.
  - Handle `400` errors for incorrect password and social accounts without passwords.
- [ ] **KYC Verification Status**:
  - Connect `ProfileVerificationScreen` to `GET /api/v1/profiles/verification-status/`.
  - Render status badge: `incomplete`, `pending`, `approved`, `rejected`.
  - Display `rejection_reason` card when status is `rejected`.
- [ ] **Contracts List**:
  - Connect `ProfileContractsScreen` to `GET /api/v1/profiles/contracts/?page=1&page_size=20`.
  - Render empty state when `results` is empty.
  - Link `document_url` to external system PDF viewer.
- [ ] **Help Center**:
  - Connect `SupportScreen` to `GET /api/v1/support/help-center/?workspace={workspace}&lang={lang}`.
  - Render phone, email, and working hours cards.
  - Render accordion FAQ items with client search filtering.
- [ ] **Ticket List**:
  - Connect `SupportTicketsScreen` to `GET /api/v1/support/tickets/?workspace={workspace}&page=1&page_size=20`.
  - Display ticket reference, subject, status badge, and date.
- [ ] **New Ticket Creation**:
  - Connect `SupportNewTicketScreen` to `POST /api/v1/support/tickets/`.
  - Use `multipart/form-data` with `attachments` for screenshots (up to 3 files, max 5 MB).
  - Use role-specific categories (`report_owner` for Tenant, `report_tenant` for Owner).
- [ ] **Ticket Detail & Thread**:
  - Connect `SupportTicketDetailScreen` to `GET /api/v1/support/tickets/{id}/?workspace={workspace}`.
  - Color-code messages by `sender`: `user` vs `support`.
  - Disable/hide reply input when ticket status is `resolved` or `closed`.
  - Connect reply form to `POST /api/v1/support/tickets/{id}/replies/` and update thread with response.
