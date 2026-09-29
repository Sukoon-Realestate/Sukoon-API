# Mobile Backend Handoff — Sokoun — 28 September 2026

This document summarizes the backend implementations completed for the mobile team based on the handoff requests from 28 September 2026.

All endpoints adhere to existing conventions:
- Envelope: `{"status_code": 200, "data": ...}` on GET and `{"message": "...", "data": ...}` on POST/PATCH/PUT.
- Authentication: Standard Cookie / Bearer token via `CookieAuthentication`.
- Pagination: Standard pagination (`per_page`, `total_pages`, `results` or `count`, `next`, `previous`, `results`).

---

## 1. Property Walkthrough Video & Duration

### Property Creation
```http
POST /api/v1/properties/create/
Content-Type: multipart/form-data
```

**New / Extended Form Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `video` | Uploaded file / Data URI | No | Property walkthrough video file |
| `video_duration` | Integer (seconds) | No (1–60) | Video length in seconds (max 60 seconds) |

*Server Validation:* Durations exceeding 60 seconds or less than 1 second return `400 Bad Request`.

### Property Details Response
```http
GET /api/v1/properties/{property_id}/
```

**Added Fields in Response `data`:**
```json
{
  "id": "c0a80124-8b01-4b11-9a11-8899aabbccdd",
  "video": "https://res.cloudinary.com/.../properties/videos/sample.mp4",
  "video_duration": 45,
  "property_link": "https://sokoun.app/properties/c0a80124-8b01-4b11-9a11-8899aabbccdd"
}
```
* Note: If no video is uploaded, `"video": null` and `"video_duration": null` are returned.

---

## 2. Property Share & Deep Link

Canonical property link is now exposed in both create response and property detail responses:

```http
GET /api/v1/properties/{property_id}/
```

**Payload Field:**
```json
{
  "property_link": "https://sokoun.app/properties/{property_id}"
}
```
* Supports mobile Universal Links (iOS) and App Links (Android).

---

## 3. Scheduled Time on Received Visit Requests

```http
GET /api/v1/properties/visits/received/?page=1&page_size=10
```

Every item in `results` now includes the property ID and the scheduled visit time:

**List Item Example:**
```json
{
  "id": "97e6820a-e325-4fc1-a901-70081d09ec35",
  "property_id": "c0a80124-8b01-4b11-9a11-8899aabbccdd",
  "tenant": {
    "name": "أحمد محمود",
    "avatar": "https://res.cloudinary.com/.../avatar.jpg",
    "is_verified": true
  },
  "visit_date": "2026-10-01",
  "visit_time": "14:30:00",
  "time": "2:30 PM",
  "status": "pending"
}
```

- `visit_date`: `YYYY-MM-DD`
- `visit_time`: 24-hour format `HH:mm:ss`
- `time`: 12-hour formatted time display string (e.g. `"2:30 PM"`)

---

## 4. Owner & Tenant Badge / Unread Counts

Dedicated lightweight endpoints for screen badges and home counters:

### Owner Unread Counts
```http
GET /api/v1/profiles/owner/unread-counts/
```

**Response `data`:**
```json
{
  "visit_requests_count": 4,
  "unread_chat_messages_count": 7,
  "unread_notifications_count": 3
}
```
* `visit_requests_count`: Number of pending visit requests awaiting owner decision.
* `unread_chat_messages_count`: Account-wide total unread incoming chat messages.
* `unread_notifications_count`: Account-wide unread notifications count.

### Tenant Unread Counts
```http
GET /api/v1/profiles/tenant/unread-counts/
```

**Response `data`:**
```json
{
  "favorites_count": 6,
  "unread_chat_messages_count": 7,
  "unread_notifications_count": 3,
  "visit_requests_count": 2
}
```
* `favorites_count`: Total saved properties count across all pages.
* `visit_requests_count`: Active visit requests created by the tenant (`pending` + `confirmed`).

---

## 5. Tenant “My Rates” (Reviews & Ratings)

```http
GET /api/v1/profiles/my-rates/?page=1&page_size=10
```

Returns paginated list of reviews submitted by the authenticated tenant:

**Response `data`:**
```json
{
  "per_page": 10,
  "total_pages": 1,
  "results": [
    {
      "id": "e4f8d910-1234-4567-89ab-cdef01234567",
      "property_id": "c0a80124-8b01-4b11-9a11-8899aabbccdd",
      "property_title": "شقة مفروشة في مدينة نصر",
      "property_image": "https://res.cloudinary.com/.../main_image.jpg",
      "visit_id": "97e6820a-e325-4fc1-a901-70081d09ec35",
      "rating": 5,
      "comment": "عقار رائع ومطابق للوصف تماماً والمالك متعاون جداً.",
      "created_at": "2026-09-28T14:13:00Z"
    }
  ]
}
```

---

## 6. Public Static Content Pages (About Us, Privacy Policy, Terms)

Public read endpoints (no authentication required) supporting Arabic and English:

### Endpoints
* `GET /api/v1/pages/about-us/`
* `GET /api/v1/pages/privacy-policy/`
* `GET /api/v1/pages/terms/`

### Language Negotiation
* Query param: `?lang=ar` or `?lang=en`
* Or HTTP header: `Accept-Language: ar` / `Accept-Language: en`

**Response `data` Example (`GET /api/v1/pages/about-us/?lang=ar`):**
```json
{
  "slug": "about-us",
  "title": "عن سكون",
  "content": "سكون هي منصة عقارية مبتكرة لتأجير واستكشاف العقارات، تهدف إلى تسهيل البحث عن العقارات وحجز الزيارات والتواصل المباشر بين الملاك والمستأجرين.",
  "content_format": "plain_text",
  "language": "ar",
  "updated_at": "2026-09-28T00:00:00Z"
}
```

---

## 7. Complete Registration / Missing KYC Upload

Allows existing authenticated accounts with incomplete registration/KYC data to upload documents without re-registering:

```http
POST /api/v1/auth/complete-register/
Content-Type: multipart/form-data
```

**Payload Form Fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `national_id` | String | Optional if already saved | Must be exactly 14 digits |
| `front_id_image` | File | Optional if already saved | National ID Front |
| `back_id_image` | File | Optional if already saved | National ID Back |
| `selfie_image` | File | Optional | Confirmation selfie |

**Response `data` Example (Complete Submission):**
```json
{
  "registration_complete": true,
  "verification_status": "pending",
  "missing_fields": []
}
```

**Response `data` Example (Partial / Missing Fields):**
```json
{
  "registration_complete": false,
  "verification_status": "pending",
  "missing_fields": [
    "back_id_image"
  ]
}
```

---

## 8. View All Properties

The standard collection endpoint remains available for browsing all public listings with complete filter, search, and sorting support:

```http
GET /api/v1/properties/?page=1&page_size=10&ordering=-created_at
```

---

## Summary of New & Updated Routes

| Feature | Method | Endpoint | Auth Required |
|---|---|---|---|
| Create Property (with video) | `POST` | `/api/v1/properties/create/` | Yes |
| Property Details (video & link) | `GET` | `/api/v1/properties/{id}/` | Optional / Yes |
| Received Visits (with time) | `GET` | `/api/v1/properties/visits/received/` | Yes |
| Owner Unread Counts | `GET` | `/api/v1/profiles/owner/unread-counts/` | Yes |
| Tenant Unread Counts | `GET` | `/api/v1/profiles/tenant/unread-counts/` | Yes |
| Tenant My Rates | `GET` | `/api/v1/profiles/my-rates/` | Yes |
| Static Pages | `GET` | `/api/v1/pages/{about-us,privacy-policy,terms}/` | No |
| Complete Registration | `POST` | `/api/v1/auth/complete-register/` | Yes |
