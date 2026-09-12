# Mobile Notifications & Firebase FCM API Guide

This guide documents the notification endpoints supporting both **Tenant** and **Owner** experiences:
- **Tenant**: `T-NOTIF-01` (List), `T-NOTIF-02` (Details), `T-NOTIF-SETT` (Settings)
- **Owner**: `O-NOTIF-01` (List), `O-NOTIF-02` (Details), `O-NOTIF-03` (Empty state), `O-NOTIF-SETT` (Settings)
- **Firebase Cloud Messaging (FCM)** device token registration and push delivery.

---

## 0. Notification Types & Triggers

### A. Owner Notifications (`O-NOTIF-01`)

| Notification Type | Title | Trigger / Action | Category |
| :--- | :--- | :--- | :--- |
| `visit_request` | **طلب زيارة جديد!** | Tenant books a new visit slot (`POST /api/v1/properties/{id}/visits/`) | حجز زيارة |
| `new_message` | **رسالة جديدة من مستأجر** | Tenant sends a new chat message | الرسائل |
| `property_views` | **شقتك حصلت على 50 مشاهدة** | Property reaches an impression/views milestone (50 views) | أداء العقار |
| `property_verified` | **عقارك تم توثيقه** | Admin or system approves/verifies the owner's property | توثيق العقار |
| `daily_bump` | **تحديث الظهور اليومي** | Daily reminder to update listings for search ranking | تحديث العقارات |

### B. Tenant Notifications (`T-NOTIF-01`)

| Notification Type | Title | Trigger / Action | Category |
| :--- | :--- | :--- | :--- |
| `visit_accepted` | **تم قبول طلب زيارتك** | Owner accepts visit request (`accept_visit`) | حجز زيارة |
| `visit_rejected` | **تم رفض طلب الزيارة** | Owner rejects visit request (`reject_visit`) | حجز زيارة |
| `new_property` | **عقار جديد في منطقتك** | New verified listing published in user's area | العقارات |
| `new_message` | **رسالة جديدة من المالك** | Owner sends a new chat message | الرسائل |
| `account_verification` | **أكمل توثيق حسابك** | KYC identity verification reminder | الحساب |
| `visit_review` | **قيّم تجربتك بعد الزيارة** | Scheduled visit completed | تقييم الزيارة |

## 1. Firebase Device Token Registration

When the tenant logs into the app or launches it, obtain the FCM registration token from the Firebase SDK and send it to the backend.

### 1.1 Register FCM Token
* **Endpoint**: `POST /api/v1/notifications/devices/`
* **Auth**: Required (`CookieAuthentication` or JWT)
* **Request Headers**: `Content-Type: application/json`

**Request Body:**
```json
{
  "token": "eK1X9z_ABC123...",
  "device_type": "android",
  "device_name": "Samsung Galaxy S23"
}
```
* `token` (*required*): FCM device token.
* `device_type` (*optional*): `"android"`, `"ios"`, or `"web"` (default: `"android"`).
* `device_name` (*optional*): Human-readable device model.

**Success Response (`201 Created`):**
```json
{
  "message": "Created successfully.",
  "data": {
    "id": "2d3e4f5a-6b7c-8d9e-0f1a-2b3c4d5e6f7a",
    "token": "eK1X9z_ABC123...",
    "device_type": "android",
    "device_name": "Samsung Galaxy S23",
    "is_active": true,
    "created_at": "2026-09-13T01:15:00Z"
  }
}
```

### 1.2 Unregister Token on Logout
Call this endpoint when the user logs out so they stop receiving push notifications on that device.
* **Endpoint**: `POST /api/v1/notifications/devices/unregister/` (or `DELETE /api/v1/notifications/devices/`)
* **Auth**: Required

**Request Body:**
```json
{
  "token": "eK1X9z_ABC123..."
}
```

**Success Response (`200 OK`):**
```json
{
  "message": "Device token unregistered successfully."
}
```

---

## 2. Notification Settings Screen (`T-NOTIF-SETT`)

Manages the 5 notification preference toggles. When a toggle is switched OFF, Firebase push notifications for that category are automatically suppressed by the backend.

* **Endpoints**:
  * `GET /api/v1/notifications/settings/` (or `GET /api/v1/profiles/settings/`)
  * `PATCH /api/v1/notifications/settings/` (or `PATCH /api/v1/profiles/settings/`)
* **Auth**: Required

### 2.1 Get Settings
**Request:** `GET /api/v1/notifications/settings/`

**Success Response (`200 OK`):**
```json
{
  "data": {
    "id": "1c7d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
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
      },
      "privacy": {
        "title": "الخصوصية",
        "items": [...]
      }
    }
  }
}
```

### 2.2 Update Settings
Send only the keys that have changed.

**Request:** `PATCH /api/v1/notifications/settings/`
```json
{
  "property_updates": true,
  "promotions_and_updates": false
}
```

---

## 3. Notification List Screen (`T-NOTIF-01`)

Displays the notifications list with relative Arabic time stamps, read/unread dots, and category icons.

### 3.1 Get Notifications List
* **Endpoint**: `GET /api/v1/notifications/`
* **Query Parameters**:
  * `page` (optional, default `1`)
  * `page_size` (optional, default `20`)
  * `unread` (optional, `true` / `1` to filter unread only)
* **Auth**: Required

**Success Response (`200 OK`):**
```json
{
  "data": {
    "per_page": 20,
    "total_pages": 1,
    "unread_count": 2,
    "results": [
      {
        "id": "e67b26c7-3c5e-4c7a-9e1b-40277a06f364",
        "notification_type": "visit_accepted",
        "title": "تم قبول طلب زيارتك",
        "body": "المالك أحمد محمد وافق على موعد الزيارة",
        "category": "حجز زيارة",
        "icon_type": "check_circle",
        "is_read": false,
        "created_at": "2026-09-13T01:10:00Z",
        "time_ago": "منذ 5 دقائق",
        "data": {
          "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
          "appointment_date": "الثلاثاء 14 يناير",
          "appointment_time": "3:00 م",
          "address": "مدينة نصر - شارع عباس العقاد"
        }
      },
      {
        "id": "f51b9e28-1111-2222-3333-444455556666",
        "notification_type": "new_property",
        "title": "عقار جديد في منطقتك",
        "body": "شقة مفروشة 3 غرف – مدينة نصر 11,500 ج.م/شهر",
        "category": "العقارات",
        "icon_type": "bell",
        "is_read": false,
        "created_at": "2026-09-13T00:15:00Z",
        "time_ago": "منذ ساعة",
        "data": {
          "property_id": "a90b8c7d-1234-5678-90ab-cdef12345678"
        }
      },
      {
        "id": "d43a1f90-aaaa-bbbb-cccc-ddddeeeeffff",
        "notification_type": "account_verification",
        "title": "أكمل توثيق حسابك",
        "body": "وثّق هويتك عشان تستخدم الشات بدون قيود",
        "category": "الحساب",
        "icon_type": "warning",
        "is_read": true,
        "created_at": "2026-09-11T01:15:00Z",
        "time_ago": "منذ يومين",
        "data": {}
      }
    ]
  }
}
```

### 3.2 Unread Count (for App Badges)
* **Endpoint**: `GET /api/v1/notifications/unread-count/`
* **Auth**: Required

**Success Response (`200 OK`):**
```json
{
  "data": {
    "unread_count": 2
  }
}
```

### 3.3 Mark All as Read ("تحديد الكل كمقروء")
Triggered by the top-left button on screen `T-NOTIF-01`.
* **Endpoint**: `POST /api/v1/notifications/mark-all-read/`
* **Auth**: Required

**Success Response (`200 OK`):**
```json
{
  "message": "Updated successfully.",
  "data": {
    "marked_count": 2,
    "message": "Marked 2 notifications as read."
  }
}
```

---

## 4. Notification Details Screen (`T-NOTIF-02`)

* **Endpoint**: `GET /api/v1/notifications/{id}/`
* **Auth**: Required
* **Behavior**: Automatically marks the notification as read upon retrieval.

**Success Response (`200 OK`):**
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
    "read_at": "2026-09-13T01:16:30Z",
    "created_at": "2026-09-13T01:10:00Z",
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
      "appointment_date": "الثلاثاء 14 يناير",
      "appointment_time": "3:00 م",
      "address": "مدينة نصر - شارع عباس العقاد"
    }
  }
}
```

---

## 5. Explicit Mark Single Notification as Read
* **Endpoint**: `PATCH /api/v1/notifications/{id}/read/`
* **Auth**: Required

**Success Response (`200 OK`):**
```json
{
  "message": "Updated successfully.",
  "data": {
    "id": "e67b26c7-3c5e-4c7a-9e1b-40277a06f364",
    "is_read": true,
    "read_at": "2026-09-13T01:16:30Z"
  }
}
```
