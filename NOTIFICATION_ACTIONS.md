# دليل أحداث وإشعارات التطبيق (Notification Actions & Types Guide)

يحتوي هذا المستند على جميع الإجراءات (Actions) والأحداث التي تؤدي لإطلاق إشعارات (Push Notifications & In-App Notifications) عبر النظام، مع تنسيق الـ Payload لكل نوع بناءً على:
```json
"notification_type": "..."
```

---

## ملخص سريع لجميع أنواع الإشعارات (Summary Table)

| # | `notification_type` | الحدث المشغّل (Trigger Event) | المستلم (Recipient) | الفئة (Category) | الأيقونة (`icon_type`) | الإجراء (`action_type`) |
|---|---------------------|-------------------------------|---------------------|------------------|------------------------|-------------------------|
| 1 | `visit_request` | قيام مستأجر بحجز موعد زيارة جديد لعقار | المالك (Owner) | حجز زيارة | `calendar` | `view_visit` |
| 2 | `visit_accepted` | موافقة المالك على طلب الزيارة | المستأجر (Tenant) | حجز زيارة | `check_circle` | `view_visit` |
| 3 | `visit_rejected` | رفض المالك لطلب الزيارة | المستأجر (Tenant) | حجز زيارة | `cancel` | `view_property` |
| 4 | `visit_review` | انتهاء موعد الزيارة / طلب تقييم الزيارة | المستأجر (Tenant) | تقييم الزيارة | `star` | `review_visit` |
| 5 | `new_message` | إرسال رسالة جديدة في المحادثة | الطرف الآخر (مستأجر / مالك) | الرسائل | `chat` | `open_chat` |
| 6 | `property_verified` | توثيق واعتماد العقار من الإدارة | المالك (Owner) | توثيق العقار | `verified` | `view_property` |
| 7 | `property_views` | وصول العقار لعدد مشاهدات معين (Milestone) | المالك (Owner) | أداء العقار | `eye` | `view_property_stats` |
| 8 | `daily_bump` | تذكير يومي لتحديث ظهور العقارات في البحث | المالك (Owner) | تحديث العقارات | `warning` | `bump_properties` |
| 9 | `new_property` | إضافة عقار جديد في المنطقة الجغرافية للمستخدم | المستأجر / الباحثين | العقارات | `bell` | `view_property` |
| 10 | `property_update` | تحديث بيانات عقار محفوظ (مثل تخفيض السعر) | المستخدمين المهتمين | العقارات | `refresh` | `view_property` |
| 11 | `account_verification` | تذكير برفع مستندات الهوية وتوثيق الحساب | المستخدم (User) | الحساب | `warning` | `verify_account` |
| 12 | `security_alert` | تنبيه أمني (تسجيل دخول جديد / تغيير كلمة السر) | صاحب الحساب | الأمان | `shield` | `review_security` |
| 13 | `promotion` | حملة ترويجية أو خصومات وعروض خاصة | مستخدمين مستهدفين | العروض | `star` | `open_promotion` |
| 14 | `general` | إعلان عام أو رسالة من إدارة النظام | مستخدم محدد أو الكل | عام | `bell` | `open_general` |

---

## التفاصيل وصيغ البيانات لكل نوع (Payload Formats)

### 1. طلب زيارة جديد (`visit_request`)
* **الحدث**: يقوم المستأجر بتقديم طلب موعد لمعاينة العقار.
* **المستلم**: مالك العقار (`Owner`).
* **شاشة التنقل (Deep Link)**: تفاصيل طلب الزيارة للمالك (`/visits/{visit_id}`).
* **Payload Format**:
```json
{
  "notification_type": "visit_request",
  "title": "طلب زيارة جديد!",
  "body": "سارة أحمد تطلب زيارة شقة مفروشة - 2026-09-20 16:00",
  "category": "حجز زيارة",
  "icon_type": "calendar",
  "data": {
    "notification_type": "visit_request",
    "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "tenant_name": "سارة أحمد",
    "visit_date": "2026-09-20",
    "visit_time": "16:00:00",
    "address": "مدينة نصر - شارع عباس العقاد",
    "action_label": "عرض الزيارة",
    "action_type": "view_visit"
  }
}
```

---

### 2. قبول طلب الزيارة (`visit_accepted`)
* **الحدث**: يوافق المالك على موعد الزيارة المحدد.
* **المستلم**: المستأجر (`Tenant`).
* **شاشة التنقل (Deep Link)**: تفاصيل الزيارة المؤكدة (`/visits/{visit_id}`).
* **Payload Format**:
```json
{
  "notification_type": "visit_accepted",
  "title": "تم قبول طلب زيارتك",
  "body": "وافق المالك أحمد محمد على موعد الزيارة. يُرجى الحضور في الوقت المحدد للاطلاع على الشقة.",
  "category": "حجز زيارة",
  "icon_type": "check_circle",
  "data": {
    "notification_type": "visit_accepted",
    "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "appointment_date": "2026-09-20",
    "appointment_time": "16:00:00",
    "address": "مدينة نصر - شارع عباس العقاد",
    "action_label": "عرض الزيارة",
    "action_type": "view_visit"
  }
}
```

---

### 3. رفض طلب الزيارة (`visit_rejected`)
* **الحدث**: يعتذر المالك عن قبول موعد الزيارة أو يرفضه.
* **المستلم**: المستأجر (`Tenant`).
* **شاشة التنقل (Deep Link)**: صفحة العقار لاختيار موعد بديل (`/properties/{property_id}`).
* **Payload Format**:
```json
{
  "notification_type": "visit_rejected",
  "title": "تم رفض طلب الزيارة",
  "body": "نعتذر، لم يتمكن المالك من قبول موعد الزيارة.",
  "category": "حجز زيارة",
  "icon_type": "cancel",
  "data": {
    "notification_type": "visit_rejected",
    "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "action_label": "عرض العقار",
    "action_type": "view_property"
  }
}
```

---

### 4. تقييم الزيارة (`visit_review`)
* **الحدث**: بعد إتمام موعد الزيارة، لدعوة المستأجر لتقييم التجربة والعقار.
* **المستلم**: المستأجر (`Tenant`).
* **شاشة التنقل (Deep Link)**: نموذج تقييم الزيارة.
* **Payload Format**:
```json
{
  "notification_type": "visit_review",
  "title": "قيّم زيارتك للعقار",
  "body": "كيف كانت زيارتك لشقة مدينة نصر؟ شاركنا رأيك لمساعدة الآخرين.",
  "category": "تقييم الزيارة",
  "icon_type": "star",
  "data": {
    "notification_type": "visit_review",
    "visit_id": "98124b81-6453-488b-a3d8-e7a9b1c78112",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "action_label": "تقييم الزيارة",
    "action_type": "review_visit"
  }
}
```

---

### 5. رسالة شات جديدة (`new_message`)
* **الحدث**: إرسال رسالة نصية جديدة في المحادثة بين المالك والمستأجر.
* **المستلم**: الطرف المستقبل للرسالة.
* **شاشة التنقل (Deep Link)**: شاشة المحادثة المباشرة (`/chat/{chat_id}`).
* **Payload Format**:
```json
{
  "notification_type": "new_message",
  "title": "رسالة جديدة من المالك",
  "body": "أحمد محمد: مرحباً، هل ناسبك الموعد؟",
  "category": "الرسائل",
  "icon_type": "chat",
  "data": {
    "notification_type": "new_message",
    "chat_id": "d135439a-9e77-4c7b-83c9-04dae7eead94",
    "conversation_id": "d135439a-9e77-4c7b-83c9-04dae7eead94",
    "sender_id": "426d0bb3-41bb-4592-80ba-cefa6468a54c",
    "sender_name": "أحمد محمد",
    "action_label": "فتح المحادثة",
    "action_type": "open_chat"
  }
}
```

---

### 6. توثيق العقار (`property_verified`)
* **الحدث**: موافقة فريق العمل على أوراق وبيانات العقار وتوثيقه رسميًا.
* **المستلم**: مالك العقار (`Owner`).
* **شاشة التنقل (Deep Link)**: صفحة العقار في عقاراتي (`/my-properties/{property_id}`).
* **Payload Format**:
```json
{
  "notification_type": "property_verified",
  "title": "عقارك تم توثيقه",
  "body": "شقة مفروشة 3 غرف - يظهر الآن بشارة التوثيق في نتائج البحث",
  "category": "توثيق العقار",
  "icon_type": "verified",
  "data": {
    "notification_type": "property_verified",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "action_label": "عرض العقار",
    "action_type": "view_property"
  }
}
```

---

### 7. إحصائيات ومشاهدات العقار (`property_views`)
* **الحدث**: وصول العقار إلى رقم مشاهدات قياسي (مثل 50 أو 100 مشاهدة).
* **المستلم**: مالك العقار (`Owner`).
* **شاشة التنقل (Deep Link)**: إحصائيات العقار (`/my-properties/{property_id}/analytics`).
* **Payload Format**:
```json
{
  "notification_type": "property_views",
  "title": "شقتك حصلت على 50 مشاهدة",
  "body": "شقة مفروشة 3 غرف - أداء متميز هذا الأسبوع",
  "category": "أداء العقار",
  "icon_type": "eye",
  "data": {
    "notification_type": "property_views",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "views_count": "50",
    "action_label": "عرض الإحصائيات",
    "action_type": "view_property_stats"
  }
}
```

---

### 8. تذكير التحديث اليومي (`daily_bump`)
* **الحدث**: تذكير دوري لمالك العقار لإعادة رفع وترتيب عقاراته في نتائج البحث.
* **المستلم**: مالك العقار (`Owner`).
* **شاشة التنقل (Deep Link)**: قائمة عقاراتي (`/my-properties`).
* **Payload Format**:
```json
{
  "notification_type": "daily_bump",
  "title": "تحديث الظهور اليومي",
  "body": "حدّث عقاراتك يومياً للحفاظ على ترتيبها في أول نتائج البحث",
  "category": "تحديث العقارات",
  "icon_type": "warning",
  "data": {
    "notification_type": "daily_bump",
    "action_label": "تحديث الآن",
    "action_type": "bump_properties"
  }
}
```

---

### 9. عقار جديد في المنطقة (`new_property`)
* **الحدث**: نشر عقار جديد مطابق للمنطقة الجغرافية أو اهتمامات المستخدم.
* **المستلم**: المستأجرون والباحثون عن عقار في تلك المنطقة.
* **شاشة التنقل (Deep Link)**: صفحة تفاصيل العقار (`/properties/{property_id}`).
* **Payload Format**:
```json
{
  "notification_type": "new_property",
  "title": "عقار جديد في منطقتك",
  "body": "شقة مفروشة 3 غرف – مدينة نصر 11,500 ج.م/شهر",
  "category": "العقارات",
  "icon_type": "bell",
  "data": {
    "notification_type": "new_property",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "action_label": "عرض العقار",
    "action_type": "view_property"
  }
}
```

---

### 10. تحديث على عقار (`property_update`)
* **الحدث**: تغيير سعر أو توفر أو مواصفات عقار قام المستخدم بحفظه في المفضلة.
* **المستلم**: المستخدمون المهتمون بالعقار.
* **شاشة التنقل (Deep Link)**: صفحة تفاصيل العقار (`/properties/{property_id}`).
* **Payload Format**:
```json
{
  "notification_type": "property_update",
  "title": "تخفيض في السعر!",
  "body": "تم تخفيض سعر الشقة التي تتابعها في مدينة نصر إلى 10,000 ج.م/شهر",
  "category": "العقارات",
  "icon_type": "refresh",
  "data": {
    "notification_type": "property_update",
    "property_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "action_label": "عرض التحديث",
    "action_type": "view_property"
  }
}
```

---

### 11. توثيق الحساب (`account_verification`)
* **الحدث**: حث المستخدم على إكمال بيانات الهوية الوطنية (KYC) لفتح جميع مميزات التطبيق.
* **المستلم**: المستخدم صاحب الحساب غير الموثق.
* **شاشة التنقل (Deep Link)**: شاشة رفع الهوية (`/profile/kyc`).
* **Payload Format**:
```json
{
  "notification_type": "account_verification",
  "title": "أكمل توثيق حسابك",
  "body": "وثّق هويتك الآن لتتمكن من استخدام المحادثات المباشرة وحجز الزيارات بدون قيود",
  "category": "الحساب",
  "icon_type": "warning",
  "data": {
    "notification_type": "account_verification",
    "action_label": "توثيق الحساب",
    "action_type": "verify_account"
  }
}
```

---

### 12. تنبيه أمان (`security_alert`)
* **الحدث**: تسجيل دخول من جهاز جديد، أو تغيير كلمة المرور، أو محاولات غير معتادة.
* **المستلم**: صاحب الحساب.
* **شاشة التنقل (Deep Link)**: إعدادات الأمان (`/profile/security`).
* **Payload Format**:
```json
{
  "notification_type": "security_alert",
  "title": "تنبيه أمني",
  "body": "تم تسجيل الدخول إلى حسابك من جهاز جديد. إذا لم تكن أنت، يرجى تغيير كلمة المرور فوراً.",
  "category": "الأمان",
  "icon_type": "shield",
  "data": {
    "notification_type": "security_alert",
    "action_label": "مراجعة الأمان",
    "action_type": "review_security"
  }
}
```

---

### 13. العروض الترويجية (`promotion`)
* **الحدث**: إرسال خصومات حصرية، عروض مواسم، أو حملات تسويقية.
* **المستلم**: المستخدمون المشتركون في العروض التسويقية.
* **شاشة التنقل (Deep Link)**: رابط العرض أو صفحة الويب الترويجية.
* **Payload Format**:
```json
{
  "notification_type": "promotion",
  "title": "خصم خاص على رسوم المعاينة",
  "body": "استمتع بخصم 20% على باقات المعاينة الذهبية لفترة محدودة!",
  "category": "العروض",
  "icon_type": "star",
  "data": {
    "notification_type": "promotion",
    "promo_url": "https://sukoon.app/promotions/summer-offer",
    "action_label": "عرض العرض",
    "action_type": "open_promotion"
  }
}
```

---

### 14. إشعار عام من النظام (`general`)
* **الحدث**: إعلانات الصيانة الدورية، تحديث الشروط والأحكام، أو رسائل عامة.
* **المستلم**: جميع المستخدمين أو فئة محددة.
* **شاشة التنقل (Deep Link)**: شاشة الإشعارات الرئيسية.
* **Payload Format**:
```json
{
  "notification_type": "general",
  "title": "تحديث شروط الاستخدام",
  "body": "قُمنا بتحديث سياسة الخصوصية وشروط الاستخدام لتحسين تجربتكم.",
  "category": "عام",
  "icon_type": "bell",
  "data": {
    "notification_type": "general",
    "action_label": "عرض التفاصيل",
    "action_type": "open_general"
  }
}
```

---

## بنية رسائل Firebase Cloud Messaging (FCM Push Payload)

عند إرسال الإشعار كـ Push Notification عبر FCM، يتم تضمين `notification_type` داخل `data` كالتالي:

```json
{
  "notification": {
    "title": "عنوان الإشعار",
    "body": "نص الإشعار المعروض في شريط الإشعارات"
  },
  "data": {
    "notification_type": "new_message",
    "action_type": "open_chat",
    "chat_id": "d135439a-9e77-4c7b-83c9-04dae7eead94",
    "sender_name": "أحمد محمد"
  }
}
```
