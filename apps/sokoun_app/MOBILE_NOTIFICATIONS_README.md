# Sukoon Mobile Notifications — Developer Integration Guide & README

This document is the complete reference for mobile developers implementing notifications and Firebase Cloud Messaging (FCM) push integration for both **Tenant** and **Owner** flows in the Sukoon mobile application.

---

## Table of Contents
1. [Screen Architecture & Mapping](#1-screen-architecture--mapping)
2. [API Quick Reference](#2-api-quick-reference)
3. [Firebase FCM Device Token Flow](#3-firebase-fcm-device-token-flow)
4. [Notification Endpoints Specification](#4-notification-endpoints-specification)
   - [4.1 List Notifications (`T-NOTIF-01` / `O-NOTIF-01`)](#41-list-notifications)
   - [4.2 Notification Details (`T-NOTIF-02` / `O-NOTIF-02`)](#42-notification-details)
   - [4.3 Mark Single Notification as Read](#43-mark-single-notification-as-read)
   - [4.4 Mark All as Read ("تحديد الكل")](#44-mark-all-as-read)
   - [4.5 Unread Count for App Badges](#45-unread-count-for-app-badges)
   - [4.6 Notification Settings (`T-NOTIF-SETT` / `O-NOTIF-SETT`)](#46-notification-settings)
5. [Notification Types, Icons & Deep Linking](#5-notification-types-icons--deep-linking)
6. [Empty State Handling (`O-NOTIF-03`)](#6-empty-state-handling)
7. [FCM Push Payload Structure](#7-fcm-push-payload-structure)

---

## 1. Screen Architecture & Mapping

| Figma Screen Code | User Role | Screen Title (AR) | Purpose / UI Description |
| :--- | :--- | :--- | :--- |
| **`T-NOTIF-01`** | المستأجر (Tenant) | **الإشعارات** | Notification list with unread indicators, Arabic relative time, and "تحديد الكل كمقروء". |
| **`T-NOTIF-02`** | المستأجر (Tenant) | **تفاصيل الإشعار** | Detail screen displaying appointment card, timestamp, and action buttons ("عرض الزيارة" / "تجاهل"). |
| **`T-NOTIF-SETT`** | المستأجر (Tenant) | **إعدادات الإشعارات** | 5 preference toggles controlling push delivery for visits, messages, updates, security, and promotions. |
| **`O-NOTIF-01`** | المالك (Owner) | **الإشعارات** | Owner notification list (visit requests, tenant messages, 50 views milestone, property verified, daily bump). |
| **`O-NOTIF-02`** | المالك (Owner) | **تفاصيل الإشعار** | Owner detail screen with request information and action buttons. |
| **`O-NOTIF-03`** | المالك (Owner) | **الإشعارات (فارغة)** | Empty state with bell illustration, "لا إشعارات حالياً", and action button "استكشف العقارات". |
| **`O-NOTIF-SETT`** | المالك (Owner) | **إعدادات الإشعارات** | Owner notification preferences with the same 5 toggles. |

---

## 2. API Quick Reference

Base URL: `{{base_url}}/api/v1/notifications/`  
Auth: Requires JWT or `access` cookie.

| Method | Endpoint | Screen | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/notifications/devices/` | App Launch / Login | Register/update device FCM token. |
| `POST` | `/api/v1/notifications/devices/unregister/` | Logout | Deactivate FCM token so user stops receiving push notifications. |
| `GET` | `/api/v1/notifications/` | `T-NOTIF-01`, `O-NOTIF-01` | Paginated notification list + `unread_count`. |
| `GET` | `/api/v1/notifications/{id}/` | `T-NOTIF-02`, `O-NOTIF-02` | Notification details (automatically marks as read). |
| `PATCH` | `/api/v1/notifications/{id}/read/` | List item swipe / tap | Mark single notification as read explicitly. |
| `POST` | `/api/v1/notifications/mark-all-read/` | "تحديد الكل" Button | Mark all unread notifications as read. |
| `GET` | `/api/v1/notifications/unread-count/` | Bottom Nav Bar | Unread badge counter for bottom tabs. |
| `GET` | `/api/v1/notifications/settings/` | `T-NOTIF-SETT`, `O-NOTIF-SETT` | Get 5 toggles with Arabic titles, subtitles, and footer note. |
| `PATCH` | `/api/v1/notifications/settings/` | Settings switches | Update notification toggles. |

---

## 3. Firebase FCM Device Token Flow

### 3.1 Register FCM Token
Call this endpoint after user login or when Firebase SDK generates/refreshes the FCM token.

* **Endpoint**: `POST /api/v1/notifications/devices/`
* **Headers**:
  ```http
  Authorization: Bearer <jwt_access_token>
  Content-Type: application/json
  ```

**Request Body:**
```json
{
  "token": "dK1X9z_ABC123fcm_device_token_from_firebase...",
  "device_type": "android",
  "device_name": "Samsung Galaxy S23"
}
```

* `token` (*required*, string): Device token from Firebase Messaging SDK.
* `device_type` (*optional*, string): `"android"` | `"ios"` | `"web"` (default: `"android"`).
* `device_name` (*optional*, string): Human-readable model name.

**Response (`201 Created`):**
```json
{
  "message": "Created successfully.",
  "data": {
    "id": "7b8f9e0a-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "token": "dK1X9z_ABC123fcm_device_token_from_firebase...",
    "device_type": "android",
    "device_name": "Samsung Galaxy S23",
    "is_active": true,
    "created_at": "2026-09-13T01:30:00Z"
  }
}
```

### 3.2 Unregister Token on Logout
Call this when the user logs out so they no longer receive push notifications on this device.

* **Endpoint**: `POST /api/v1/notifications/devices/unregister/` (or `DELETE /api/v1/notifications/devices/`)

**Request Body:**
```json
{
  "token": "dK1X9z_ABC123fcm_device_token_from_firebase..."
}
```

**Response (`200 OK`):**
```json
{
  "message": "Device token unregistered successfully."
}
```

---

## 4. Notification Endpoints Specification

### 4.1 List Notifications
* **Endpoint**: `GET /api/v1/notifications/`
* **Query Parameters**:
  * `page` (integer, default `1`)
  * `page_size` (integer, default `20`)
  * `unread` (boolean, pass `true` to filter unread only)

**Response (`200 OK`):**
```json
{
  "data": {
    "per_page": 20,
    "total_pages": 1,
    "unread_count": 2,
    "results": [
      {
        "id": "e67b26c7-3c5e-4c7a-9e1b-40277a06f364",
        "notification_type": "visit_request",
        "title": "طلب زيارة جديد!",
        "body": "سارة أحمد تطلب زيارة شقة مدينة نصر - النهارده 1م",
        "category": "حجز زيارة",
        "icon_type": "calendar",
        "is_read": false,
        "created_at": "2026-09-13T01:25:00Z",
        "time_ago": "منذ 5 دقائق",
        "data": {
          "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
          "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
          "visit_date": "2026-09-13",
          "visit_time": "13:00:00",
          "tenant_name": "سارة أحمد",
          "action_label": "عرض الزيارة"
        }
      },
      {
        "id": "b1234567-89ab-cdef-0123-456789abcdef",
        "notification_type": "new_message",
        "title": "رسالة جديدة من مستأجر",
        "body": "محمد علي: هل الشقة لسه متاحة؟",
        "category": "الرسائل",
        "icon_type": "chat",
        "is_read": false,
        "created_at": "2026-09-13T00:30:00Z",
        "time_ago": "منذ ساعة",
        "data": {
          "chat_id": "c1d2e3f4-0000-1111-2222-333344445555",
          "sender_name": "محمد علي",
          "action_label": "فتح المحادثة"
        }
      },
      {
        "id": "c7890123-4567-89ab-cdef-0123456789ab",
        "notification_type": "property_views",
        "title": "شقتك حصلت على 50 مشاهدة",
        "body": "شقة مفروشة، مدينة نصر - أداء متميز هذا الأسبوع",
        "category": "أداء العقار",
        "icon_type": "eye",
        "is_read": true,
        "created_at": "2026-09-13T09:00:00Z",
        "time_ago": "اليوم 9 ص",
        "data": {
          "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
          "views_count": 50,
          "action_label": "عرض الإحصائيات"
        }
      },
      {
        "id": "d8901234-5678-9abc-def0-123456789abc",
        "notification_type": "property_verified",
        "title": "عقارك تم توثيقه",
        "body": "استوديو، التجمع الخامس - يظهر الآن في نتائج البحث",
        "category": "توثيق العقار",
        "icon_type": "verified",
        "is_read": true,
        "created_at": "2026-09-12T14:00:00Z",
        "time_ago": "أمس",
        "data": {
          "property_id": "f2e3d4c5-b6a7-8901-2345-6789abcdef01",
          "action_label": "عرض العقار"
        }
      },
      {
        "id": "e9012345-6789-abcd-ef01-23456789abcd",
        "notification_type": "daily_bump",
        "title": "تحديث الظهور اليومي",
        "body": "حدّث عقاراتك يومياً للحفاظ على ترتيبها في البحث",
        "category": "تحديث العقارات",
        "icon_type": "warning",
        "is_read": true,
        "created_at": "2026-09-11T10:00:00Z",
        "time_ago": "منذ يومين",
        "data": {
          "action_label": "تحديث الآن"
        }
      }
    ]
  }
}
```

> [!TIP]
> Use `time_ago` directly in the UI list items — it is localized into Arabic (`"الآن"`, `"منذ 5 دقائق"`, `"منذ ساعة"`, `"منذ يومين"`, `"منذ 3 أيام"`, `"منذ أسبوع"`).

---

### 4.2 Notification Details
* **Endpoint**: `GET /api/v1/notifications/{id}/`
* **Behavior**: Automatically marks `is_read = true` upon being viewed.

**Response (`200 OK`):**
```json
{
  "data": {
    "id": "e67b26c7-3c5e-4c7a-9e1b-40277a06f364",
    "notification_type": "visit_accepted",
    "title": "تم قبول طلب زيارتك",
    "body": "وافق المالك أحمد محمد على موعد الزيارة. يُرجى الحضور في الوقت المحدد للاطلاع على الشقة.",
    "category": "حجز زيارة",
    "icon_type": "check_circle",
    "is_read": true,
    "read_at": "2026-09-13T01:35:00Z",
    "created_at": "2026-09-13T01:25:00Z",
    "time_ago": "منذ 5 دقائق",
    "formatted_time": "2:55 م",
    "appointment_details": {
      "title": "تفاصيل الموعد",
      "datetime_label": "الثلاثاء 14 يناير ، 3:00 م",
      "location_label": "مدينة نصر - شارع عباس العقاد"
    },
    "actions": {
      "primary": {
        "label": "عرض الزيارة",
        "action_type": "view_visit",
        "target_id": "98124b81-6453-488b-a3d8-e7a9b1c78112"
      },
      "secondary": {
        "label": "تجاهل",
        "action_type": "dismiss"
      }
    },
    "data": {
      "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
      "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "appointment_date": "الثلاثاء 14 يناير",
      "appointment_time": "3:00 م",
      "address": "مدينة نصر - شارع عباس العقاد"
    }
  }
}
```

---

### 4.3 Mark Single Notification as Read
* **Endpoint**: `PATCH /api/v1/notifications/{id}/read/`

**Response (`200 OK`):**
```json
{
  "message": "Updated successfully.",
  "data": {
    "id": "e67b26c7-3c5e-4c7a-9e1b-40277a06f364",
    "is_read": true,
    "read_at": "2026-09-13T01:36:00Z"
  }
}
```

---

### 4.4 Mark All as Read
Triggered by the top-left button **"تحديد الكل"** / **"تحديد الكل كمقروء"** on screens `T-NOTIF-01` and `O-NOTIF-01`.

* **Endpoint**: `POST /api/v1/notifications/mark-all-read/`

**Response (`200 OK`):**
```json
{
  "message": "Updated successfully.",
  "data": {
    "marked_count": 5,
    "message": "Marked 5 notifications as read."
  }
}
```

---

### 4.5 Unread Count
Use this endpoint to render badge counts on the bottom navigation icon or top app bar.

* **Endpoint**: `GET /api/v1/notifications/unread-count/`

**Response (`200 OK`):**
```json
{
  "data": {
    "unread_count": 3
  }
}
```

---

### 4.6 Notification Settings
Controls push notification delivery. When a user turns a toggle off, backend will automatically suppress push notifications for that event.

* **Get Settings**: `GET /api/v1/notifications/settings/`
* **Update Settings**: `PATCH /api/v1/notifications/settings/`

**Get Response (`200 OK`):**
```json
{
  "data": {
    "id": "6a7b8c9d-0e1f-2a3b-4c5d-6e7f8a9b0c1d",
    "visit_notifications": true,
    "owner_messages": true,
    "property_updates": false,
    "security_alerts": true,
    "promotions_and_updates": false,
    "sections": {
      "notifications": {
        "title": "الإشعارات",
        "items": [
          {
            "key": "visit_notifications",
            "title": "طلبات الزيارات",
            "subtitle": "قبول ورفض مواعيد الزيارة",
            "value": true,
            "enabled": true
          },
          {
            "key": "owner_messages",
            "title": "الرسائل الجديدة",
            "subtitle": "إشعار عند وصول رسالة",
            "value": true,
            "enabled": true
          },
          {
            "key": "property_updates",
            "title": "تحديثات العقارات",
            "subtitle": "تغيير السعر أو الحالة",
            "value": false,
            "enabled": true
          },
          {
            "key": "security_alerts",
            "title": "التنبيهات الأمنية",
            "subtitle": "دخول جديد وتغيير كلمة المرور",
            "value": true,
            "enabled": true
          },
          {
            "key": "promotions_and_updates",
            "title": "العروض الترويجية",
            "subtitle": "أخبار وعروض سكون",
            "value": false,
            "enabled": true
          }
        ],
        "footer_note": "يمكنك أيضاً إدارة إشعارات التطبيق من إعدادات هاتفك مباشرة."
      }
    }
  }
}
```

**Update Request (`PATCH`):**
```json
{
  "property_updates": true,
  "promotions_and_updates": false
}
```

---

## 5. Notification Types, Icons & Deep Linking

| `notification_type` | Default `icon_type` | Arabic Category | Deep Link Navigation Target | Target Screen / Flow |
| :--- | :--- | :--- | :--- | :--- |
| `visit_request` | `calendar` | حجز زيارة | `data.visit_id` | **Owner Visit Request Detail** (`/visits/{id}`) |
| `visit_accepted` | `check_circle` | حجز زيارة | `data.visit_id` | **Tenant Visit Confirmation** (`/visits/{id}`) |
| `visit_rejected` | `cancel` | حجز زيارة | `data.property_id` | **Property Details** to pick another slot |
| `visit_review` | `star` | تقييم الزيارة | `data.property_id` | **Review Modal / Screen** |
| `new_message` | `chat` | الرسائل | `data.chat_id` | **Direct Chat Screen** (`/chat/{id}`) |
| `property_verified`| `verified` | توثيق العقار | `data.property_id` | **Owner Property View** (`/my-properties/{id}`) |
| `property_views` | `eye` | أداء العقار | `data.property_id` | **Property Analytics** |
| `daily_bump` | `warning` | تحديث العقارات | — | **My Properties List** (`/my-properties`) |
| `new_property` | `bell` | العقارات | `data.property_id` | **Property Detail** (`/properties/{id}`) |
| `property_update` | `refresh` | العقارات | `data.property_id` | **Property Detail** (`/properties/{id}`) |
| `account_verification`| `warning` | الحساب | — | **KYC Document Upload** (`/profile/kyc`) |
| `security_alert` | `shield` | الأمان | — | **Security Settings / Change Password** |
| `promotion` | `star` | العروض | `data.promo_url` | **Promotional Webview / Banner** |

---

## 6. Empty State Handling (`O-NOTIF-03`)

When the user has no notifications, the API returns:
```json
{
  "data": {
    "per_page": 20,
    "total_pages": 1,
    "unread_count": 0,
    "results": []
  }
}
```

### UI Implementation for `O-NOTIF-03`:
1. Check `results.length === 0`.
2. Display:
   - **Icon**: Bell illustration.
   - **Headline**: "لا إشعارات حالياً"
   - **Subtitle**: "ستظهر هنا إشعاراتك عند وجود تحديثات على طلباتك أو عقاراتك"
   - **CTA Button**: "استكشف العقارات" (or "إضافة عقار" for Owners).

---

## 7. FCM Push Payload Structure

When the backend sends a push via Firebase Cloud Messaging, the payload received by the app looks like:

```json
{
  "notification": {
    "title": "تم قبول طلب زيارتك",
    "body": "وافق المالك أحمد محمد على موعد الزيارة..."
  },
  "data": {
    "notification_type": "visit_accepted",
    "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "action_type": "view_visit"
  }
}
```

### Handling in Foreground & Background:
1. **Background / Terminated**:
   - System notification tray shows `title` and `body`.
   - On tap, read `data.action_type` and `data.visit_id` / `data.property_id` to route the user directly to the relevant screen.
2. **Foreground**:
   - Show an in-app banner or toast with the title and message.
   - Increment unread notification badge counter by calling `GET /api/v1/notifications/unread-count/`.
