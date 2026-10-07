# Mobile Developer API Handoff: Localization & Translation (Accept-Language)

**Date:** 2026-10-06  
**Version:** 1.0  
**Scope:** Whole-project mobile API localization support via `Accept-Language: ar` / `en` for all mobile-consumed endpoints.

---

## 1. Overview & Protocol Specification

All mobile endpoints under `/api/v1/` (Auth, Profiles, Properties, Visits, Notifications, Support, Pages, and Chat) now support dynamic localization.

### How to Request Language

Mobile clients should pass the standard HTTP `Accept-Language` header with every request:

```http
Accept-Language: ar
```
or
```http
Accept-Language: en
```

- **Supported Languages:** Arabic (`ar`, `ar-EG`, `ar-SA`, etc.) and English (`en`, `en-US`, `en-GB`, etc.).
- **Default Fallback:** If the `Accept-Language` header is omitted, the API defaults to **English (`en`)**.
- **Query Parameter Support:** For manual overrides or testing, `?lang=ar` or `?lang=en` (or `?language=`) is also supported.
- **Response Headers:** The backend returns:
  - `Content-Language: ar` (or `en`): Confirms the language used for the response.
  - `Vary: Accept-Language`: Instructs HTTP caches and reverse proxies that responses differ by language.

> [!NOTE]
> Frontend Admin APIs (`/api/v1/admin/*`) and the Django Admin portal (`/admin/`) are excluded from mobile translation logic and retain their standard behavior.

---

## 2. What Gets Translated

| Layer | Arabic (`Accept-Language: ar`) | English (`Accept-Language: en` or omitted) |
| :--- | :--- | :--- |
| **Success Envelopes** | Translated Arabic `message` (e.g. `"تم تسجيل الدخول بنجاح."`) | English `message` (e.g. `"Logged in Successfully"`) |
| **Validation Errors** | Translated field error labels & messages (e.g. `"البريد الإلكتروني: هذا الحقل مطلوب."`) | Standard English field errors (e.g. `"Email: This field is required."`) |
| **HTTP Exceptions** | Standard DRF errors in Arabic (e.g. `"لم يتم تزويد بيانات الدخول."`) | Standard DRF errors in English (e.g. `"Authentication credentials were not provided."`) |
| **Filter Options** | Arabic labels for periods, suitable-for, amenities, and ordering | English labels (`"Daily"`, `"Families"`, `"WiFi"`, `"Newest"`) |
| **Property Card Tags** | Arabic chips (e.g. `"عائلات"`, `"ممنوع التدخين"`, `"أسانسير"`) | English chips (e.g. `"Families"`, `"No Smoking"`, `"Elevator"`) |
| **Static & Legal Pages** | Arabic text for About Us, Terms, and Privacy Policy | English text for About Us, Terms, and Privacy Policy |

---

## 3. Key API Request & Response Examples

### A. Authentication & User Management

#### 1. Login (`POST /api/v1/auth/login/`)

*Request (Arabic):*
```http
POST /api/v1/auth/login/
Content-Type: application/json
Accept-Language: ar

{
  "email": "user@example.com",
  "password": "Password123!"
}
```

*Response (`HTTP 200 OK`):*
```json
{
  "message": "تم تسجيل الدخول بنجاح.",
  "data": {
    "first_name": "Ahmed",
    "last_name": "Ali",
    "email": "user@example.com",
    "role": "tenant",
    "profile_photo": null,
    "has_completed_registration": true
  }
}
```

*Response (`HTTP 200 OK` with `Accept-Language: en`):*
```json
{
  "message": "Logged in Successfully",
  "data": { ... }
}
```

---

#### 2. Password Change (`POST /api/v1/auth/set-password/`)

*Request (English):*
```http
POST /api/v1/auth/set-password/
Accept-Language: en
```

*Response (`HTTP 200 OK`):*
```json
{
  "message": "Password changed successfully.",
  "data": {}
}
```

*Response (`HTTP 200 OK` with `Accept-Language: ar`):*
```json
{
  "message": "تم تغيير كلمة المرور بنجاح.",
  "data": {}
}
```

---

### B. Validation Errors (HTTP 400 Bad Request)

When submitting an invalid or incomplete form payload:

#### Missing Fields
*Request (Arabic):*
```http
POST /api/v1/auth/login/
Accept-Language: ar

{}
```

*Response (`HTTP 400 Bad Request`):*
```json
{
  "message": "البريد الإلكتروني: هذا الحقل مطلوب. كلمة المرور: هذا الحقل مطلوب."
}
```

*Request (English):*
```http
POST /api/v1/auth/login/
Accept-Language: en

{}
```

*Response (`HTTP 400 Bad Request`):*
```json
{
  "message": "Email: This field is required. Password: This field is required."
}
```

---

### C. Authentication & Authorization Errors

#### Unauthenticated (`HTTP 401 Unauthorized`)
When accessing a protected endpoint without an active session:

*With `Accept-Language: ar`:*
```json
{
  "message": "لم يتم تزويد بيانات الدخول."
}
```

*With `Accept-Language: en`:*
```json
{
  "message": "Authentication credentials were not provided."
}
```

#### Forbidden (`HTTP 403 Forbidden`)
*With `Accept-Language: ar`:*
```json
{
  "message": "ليس لديك صلاحية للقيام بهذا الإجراء."
}
```

---

### D. Property Filter Metadata (`GET /api/v1/properties/filters/`)

This endpoint feeds the mobile search and filter dialogs.

#### English Request
```http
GET /api/v1/properties/filters/
Accept-Language: en
```

*Response (`HTTP 200 OK`):*
```json
{
  "data": {
    "property_types": [
      {
        "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
        "value": "apartment",
        "label": "Apartment"
      },
      {
        "id": "c62580a6-5717-4562-b3fc-2c963f66afa6",
        "value": "villa",
        "label": "Villa"
      }
    ],
    "ordering": [
      { "value": "-created_at", "label": "Newest" },
      { "value": "created_at", "label": "Oldest" },
      { "value": "price", "label": "Lowest Price" },
      { "value": "-price", "label": "Highest Price" }
    ],
    "price_periods": [
      { "value": "daily", "label": "Daily" },
      { "value": "weekly", "label": "Weekly" },
      { "value": "monthly", "label": "Monthly" },
      { "value": "yearly", "label": "Yearly" }
    ],
    "suitable_for": [
      { "value": "families", "label": "Families" },
      { "value": "singles", "label": "Singles" },
      { "value": "students", "label": "Students" },
      { "value": "female_students", "label": "Female Students Only" },
      { "value": "all", "label": "All" }
    ],
    "amenities": [
      { "value": "wifi", "query_parameter": "has_wifi", "label": "WiFi" },
      { "value": "elevator", "query_parameter": "has_elevator", "label": "Elevator" },
      { "value": "garage", "query_parameter": "has_garage", "label": "Garage" },
      { "value": "security", "query_parameter": "has_security", "label": "Security" },
      { "value": "balcony", "query_parameter": "has_balcony", "label": "Balcony" },
      { "value": "air_conditioning", "query_parameter": "has_air_conditioning", "label": "Air Conditioning" },
      { "value": "near_metro", "query_parameter": "near_metro", "label": "Near Metro" },
      { "value": "natural_gas", "query_parameter": "has_natural_gas", "label": "Natural Gas" }
    ],
    "defaults": { "ordering": "-created_at" }
  }
}
```

#### Arabic Request
```http
GET /api/v1/properties/filters/
Accept-Language: ar
```

*Response (`HTTP 200 OK`):*
```json
{
  "data": {
    "property_types": [
      {
        "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
        "value": "apartment",
        "label": "شقة"
      }
    ],
    "ordering": [
      { "value": "-created_at", "label": "الأحدث" },
      { "value": "price", "label": "السعر الأقل" }
    ],
    "price_periods": [
      { "value": "daily", "label": "يومي" },
      { "value": "monthly", "label": "شهري" }
    ],
    "suitable_for": [
      { "value": "families", "label": "عائلات" },
      { "value": "students", "label": "طلاب" }
    ],
    "amenities": [
      { "value": "wifi", "query_parameter": "has_wifi", "label": "واي فاي" },
      { "value": "elevator", "query_parameter": "has_elevator", "label": "أسانسير" }
    ]
  }
}
```

---

### E. Property Feed Card Tags (`GET /api/v1/properties/new/`)

The property cards returned in listings contain a `tags` array used for UI chips.

*With `Accept-Language: en`:*
```json
{
  "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
  "title": "Furnished 3BR Apartment",
  "tags": [
    "Families",
    "No Smoking",
    "Elevator",
    "WiFi"
  ]
}
```

*With `Accept-Language: ar` (or default):*
```json
{
  "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
  "title": "شقة مفروشة 3 غرف",
  "tags": [
    "عائلات",
    "ممنوع التدخين",
    "أسانسير",
    "واي فاي"
  ]
}
```

---

## 4. Mobile Client Integration Best Practices (Flutter / React Native)

### 1. Set the Header Globally in Your HTTP Client

#### Flutter (`dio`):
```dart
final dio = Dio(
  BaseOptions(
    baseUrl: 'https://api.sukoon.app/api/v1',
    headers: {
      'Accept': 'application/json',
      'Accept-Language': isArabic ? 'ar' : 'en',
    },
  ),
);

// Whenever the user switches app language:
void updateAppLanguage(String languageCode) {
  dio.options.headers['Accept-Language'] = languageCode;
}
```

#### React Native (`axios`):
```typescript
import axios from 'axios';
import i18n from './i18n';

const apiClient = axios.create({
  baseURL: 'https://api.sukoon.app/api/v1',
});

apiClient.interceptors.request.use((config) => {
  config.headers['Accept-Language'] = i18n.language.startsWith('ar') ? 'ar' : 'en';
  return config;
});
```

### 2. Display Backend Messages Directly

Because all success and error messages are returned inside the standard envelope:
```json
{
  "message": "..."
}
```
You can display `response.data.message` directly in toasts, snackbars, and alert dialogs without needing to manually map status codes or strings on the client side.
