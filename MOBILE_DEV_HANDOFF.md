# Sokoun API — Mobile Developer Handoff Guide

**Date:** October 2, 2026  
**API Version:** `v1`  
**Base URL:** `/api/v1/`  
**Authentication:** Header `Authorization: Bearer <access_token>` or HTTP-only cookies (`access`, `refresh`).

---

## 📌 Executive Summary

All requested endpoints, models, queries, and validation contracts have been implemented and confirmed in the backend. This document provides the concrete API contracts, request payloads, response structures, query parameters, and error behaviors for the mobile application integration.

---

## 1. Profile City Support

### Endpoints
* **`GET /api/v1/profiles/user/my-profile/`** — User profile details
* **`GET /api/v1/profiles/edit/`** — Prefilled profile edit screen
* **`PATCH /api/v1/profiles/edit/`** (or `PATCH /api/v1/profiles/user/update/`) — Update profile

### City Field Specification
* **When set:** Returns a nested JSON object `{"id": "<uuid>", "name": "...", "slug": "..."}`.
* **When not set:** Returns `null`.
* **Updating city:** Send `city_id` with a valid UUID obtained from `/api/v1/properties/cities/`. To unset/clear, pass `null` or `""`.

### Sample Responses & Payloads

#### `GET /api/v1/profiles/edit/` Response (HTTP 200)
```json
{
  "data": {
    "full_name": "سامي يوسف",
    "first_name": "سامي",
    "last_name": "يوسف",
    "email": "sami@example.com",
    "phone_number": "+201012345432",
    "masked_phone_number": "010****432",
    "birth_date": "1995-03-15",
    "birth_date_label": "15 مارس 1995",
    "gender": "male",
    "gender_label": "ذكر",
    "city": {
      "id": "e8623b3f-18d4-4a25-a13b-a6369c0d1234",
      "name": "الإسكندرية",
      "slug": "alexandria"
    },
    "avatar": "https://res.cloudinary.com/.../avatar.jpg"
  }
}
```

#### `PATCH /api/v1/profiles/edit/` Request Body
```json
{
  "city_id": "e8623b3f-18d4-4a25-a13b-a6369c0d1234"
}
```

---

## 2. Property & Owner Verification Badges

### Endpoint
* **`GET /api/v1/properties/{property_id}/`**

### Three Independent Verification Flags
To support all 3 distinct badges in the property details screen:
1. **`is_verified`** (`Boolean`): Whether the **property listing** itself is reviewed and verified by admin/moderation.
2. **`owner.is_verified`** / **`owner_is_verified`** (`Boolean`): Whether the **owner's personal identity (KYC)** is approved.
3. **`is_ownership_verified`** (`Boolean`): Whether the **property deed / ownership document** has been approved.

### Sample Response (HTTP 200)
```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "شقة فاخرة للإيجار في مدينة نصر",
    "is_verified": true,
    "owner": {
      "id": "u1v2w3x4-y5z6-7890-abcd-ef1234567890",
      "full_name": "أحمد محمود",
      "name": "أحمد محمود",
      "avatar": "https://res.cloudinary.com/.../avatar.jpg",
      "is_verified": true
    },
    "owner_is_verified": true,
    "is_ownership_verified": true,
    "price": 12000.0,
    "price_period": "monthly",
    "bedrooms": 3,
    "bathrooms": 2,
    "area": 140,
    "district": "مدينة نصر",
    "city": {
      "id": "c1c2c3c4-0000-0000-0000-000000000000",
      "name": "القاهرة",
      "slug": "cairo"
    },
    "governorate": {
      "id": "g1g2g3g4-0000-0000-0000-000000000000",
      "name": "محافظة القاهرة",
      "slug": "cairo-gov"
    },
    "amenities": ["wifi", "elevator", "garage", "security", "natural_gas"],
    "is_fav": false,
    "is_saved": false,
    "rating": 4.9
  }
}
```

---

## 3. Visit Availability: Schedules & Week Navigation

### Endpoints
* **`GET /api/v1/properties/owner/properties/{property_id}/availability/`**
* **`PUT /api/v1/properties/owner/properties/{property_id}/availability/`**

### Query Parameters & Timezone
* **Default Week:** Current local week starting on Monday (Africa/Cairo timezone `UTC+2` / `UTC+3`).
* **Query Parameter:** `?week_start=YYYY-MM-DD` (e.g. `?week_start=2026-10-05`). Alias `?start_date=YYYY-MM-DD` is also accepted.

### PUT Behavior & Conflict Handling
* **Slot Replacement:** `PUT` replaces all non-booked slots for the given `availability_date`.
* **Booked Slot Protection:** Booked visit slots cannot be modified or disabled via availability PUT. If an attempt is made to disable a booked slot, the server rejects the request:
  * **Status:** `HTTP 400 Bad Request`
  * **Payload:** `{"message": "Booked visit slots cannot be disabled."}`

### Sample GET Request & Response
`GET /api/v1/properties/owner/properties/a1b2c3d4-e5f6-7890-abcd-ef1234567890/availability/?week_start=2026-10-05`

```json
{
  "data": {
    "week_start": "2026-10-05",
    "week_end": "2026-10-11",
    "days": [
      {
        "date": "2026-10-06",
        "day": "tuesday",
        "slots": [
          {
            "id": "s1s2s3s4-0000-0000-0000-000000000001",
            "time": "10:00:00",
            "is_enabled": true,
            "state": "available",
            "visit": null
          },
          {
            "id": "s1s2s3s4-0000-0000-0000-000000000002",
            "time": "14:00:00",
            "is_enabled": true,
            "state": "available",
            "visit": null
          }
        ]
      }
    ]
  }
}
```

### Sample PUT Request Body
```json
{
  "availability_date": "2026-10-06",
  "slots": [
    { "time": "10:00:00", "is_enabled": true },
    { "time": "12:00:00", "is_enabled": true },
    { "time": "14:00:00", "is_enabled": true }
  ]
}
```

---

## 4. Owner Analytics & Revenue

### 4.1 Property Statistics
* **Endpoint:** `GET /api/v1/properties/{property_id}/statistics/?period=30_days`
* **Filters:** `?period=7_days`, `?period=30_days`, `?period=90_days`

#### Response (HTTP 200)
```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "شقة مدينة نصر",
    "period": "30_days",
    "period_label": "آخر 30 يوم",
    "visit_requests_count": 8,
    "views_count": 142,
    "acceptance_rate": 95,
    "saved_count": 24,
    "views_last_14_days": [
      { "date": "2026-09-18", "day": "18", "day_name": "الجمعة", "count": 12 },
      { "date": "2026-09-19", "day": "19", "day_name": "السبت", "count": 15 },
      { "date": "2026-09-20", "day": "20", "day_name": "الأحد", "count": 8 }
    ],
    "top_search_criteria": [
      { "key": "location", "label": "الموقع والحي", "percentage": 85 },
      { "key": "price", "label": "السعر المناسب", "percentage": 70 },
      { "key": "amenities", "label": "الخدمات والمرافق", "percentage": 60 }
    ]
  }
}
```

---

### 4.2 Owner Revenue & Earnings
* **Endpoints:** `GET /api/v1/properties/owner/revenues/` (or `GET /api/v1/properties/owner/earnings/`)

#### Response (HTTP 200)
```json
{
  "data": {
    "total_this_month": 36000.0,
    "formatted_total": "36,000",
    "currency": "ج",
    "percentage_change": 8.0,
    "comparison_text": "+8% عن الشهر السابق",
    "is_positive": true,
    "properties": [
      {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "شقة مدينة نصر",
        "amount": 12000.0,
        "formatted_amount": "12,000",
        "currency": "ج",
        "status": "paid",
        "status_label": "مدفوع",
        "due_date": null
      },
      {
        "id": "b2c3d4e5-f6a7-8901-bcde-fa2345678901",
        "title": "فيلا التجمع الخامس",
        "amount": 24000.0,
        "formatted_amount": "24,000",
        "currency": "ج",
        "status": "upcoming",
        "status_label": "قادم 15 أكتوبر",
        "due_date": "2026-10-15"
      }
    ],
    "recent_transactions": [
      {
        "id": "tx-101",
        "title": "إيجار شقة مدينة نصر",
        "date": "1 أكتوبر 2026",
        "date_iso": "2026-10-01",
        "amount": 12000.0,
        "formatted_amount": "12,000",
        "currency": "ج",
        "type": "rental_income",
        "is_credit": true
      }
    ]
  }
}
```

---

## 5. Confirmed Real Profile Counters & Dynamic Labels

| Endpoint | Fields & Real Source |
| --- | --- |
| `GET /api/v1/properties/owner/profile/` | `owner.average_rating` (calculated from completed visits reviews), `owner.reviews_count`, `owner.is_verified`, `owner.rating_label`, `owner.member_since_label`. |
| `GET /api/v1/profiles/my-account/` | `user.role_label` ("مستأجر"), `user.member_since_label` ("عضو منذ أكتوبر 2025"), `menu_items.contracts.count`, `menu_items.reviews.count`, `stats.saved_count`, `stats.visits_count`. |
| `GET /api/v1/profiles/account-summary/` | `user.role_label`, `user.member_since_label`, `user.profile_completion_percentage` (calculated dynamically 0–100%), `identity_verification.is_verified`. |

---

## 6. Business Policies, Options & Validation Rules

| Rule / Setting | Backend Enforced Value | Description & Mobile Recommendation |
| --- | --- | --- |
| **Property Photos** | 1 – 25 images | Supported via `POST /api/v1/properties/{id}/images/`. Mobile UI recommended: 10–25 photos. |
| **Property Video** | Max 60 seconds | Validated on backend (`video_duration <= 60`). |
| **KYC Document Upload Size** | Max 10 MB per file | Allowed formats: JPEG, PNG, WEBP. |
| **Avatar / Profile Photo** | Max 10 MB | JPEG, PNG, WEBP, GIF, or base64 Data URI string. |
| **Password Reset Token** | 24 hours | Dispatched via email. |
| **Verification OTP** | 10 minutes lifetime | 6 digits, 60-second resend cooldown timer. |
| **Filter Options Lookup** | `GET /api/v1/properties/filter-options/` | Returns supported governorates, cities, property types, price periods, amenities, and tenant categories. |

---

## 7. Error Response Standard

When validation fails (`HTTP 400 Bad Request`), the backend returns a formatted message:
```json
{
  "message": "<Field Name>: <Specific explanation>"
}
```
*Examples:*
* `{"message": "City Id: City with this ID does not exist."}`
* `{"message": "Video Duration: Video duration must be between 1 and 60 seconds."}`
* `{"message": "Booked visit slots cannot be disabled."}`

---
*For any questions or custom additions, contact the backend team.*
