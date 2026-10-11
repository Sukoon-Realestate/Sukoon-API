# تسليم Backend: إصلاح تفعيل إعلانات بانر المالك

التاريخ: 11 أكتوبر 2026 بتوقيت `Africa/Cairo`.

**المطلوب: إصلاح HTTP `500` في `mock-payment/`، ثم إعادة تفعيل الإعلان الموجود بنفس معرف العملية.** رفع الصورة وحفظ الإعلان واسترداده وقراءته بجلسة المالك نجحت. آخر تحقق حي أبقى الإعلان في `pending_payment`، ولذلك لا يظهر في Tenant Home. لا يوجد إثبات حي لنجاح التفعيل حتى الآن.

هذا تسليم إصلاح مبني على الفحص المسجل، وليس إعلانًا عن نشر إصلاح Backend. المرجع الكامل للعقد هو [MOBILE_OWNER_BANNER_ADS_API_HANDOFF.md](../MOBILE_OWNER_BANNER_ADS_API_HANDOFF.md)، والتفاصيل والدليل في [LIVE_API_VERIFICATION.md](verification/owner_banner_ads/LIVE_API_VERIFICATION.md) و[live_api_result.json](verification/owner_banner_ads/live_api_result.json).

## 1. البيئة والسجل المتأثر

```text
Base URL: https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/
Advertisement ID: 85295dd1-f8bd-4c82-a903-9bdc3d90af98
Create operation ID: 74682688-4428-413c-a1ae-c4b87222c687
Payment operation ID: 74682688-4428-413c-a1ae-c4b87222c687-payment
Title: Sokoun live test 74682688
```

| الحقل | آخر قيمة مرصودة |
| --- | --- |
| `status` | `pending_payment` |
| `plan_id` / `plan_revision` | `weekly` / `1` |
| `price.amount_minor` / `currency` / `exponent` | `100000` / `EGP` / `2`؛ أي `EGP 1,000` |
| `property_id` / `offer_id` | `null` / `null` |
| `starts_at` / `ends_at` / `payment` | `null` / `null` / `null` |

الإعلان تعريفي بلا عقار، وهذا مسموح. الصورة شعار المشروع، ووصف الإعلان يوضح أنه اختبار تكامل بدفع تجريبي. لا تنشئوا إعلانًا آخر ولا تغيروا معرف العملية لإخفاء المشكلة.

## 2. الطلب الذي يعيد HTTP 500

يحتاج الطلب جلسة المالك المنشئ: `access` cookie أو app access token صالح وفق مصادقة التطبيق الحالية. Google ID token يُرسل إلى `auth/google/` لتسجيل الدخول، ولا يُعامل كأنه app access token لهذا المسار. لا يتضمن هذا الملف أي بيانات اعتماد.

```http
POST /api/v1/advertising/v1/owner-advertisements/85295dd1-f8bd-4c82-a903-9bdc3d90af98/mock-payment/
Accept: application/json
Accept-Language: en
Content-Type: application/json

{
  "operation_id": "74682688-4428-413c-a1ae-c4b87222c687-payment",
  "payment_mode": "mock"
}
```

أعاد الطلب المستقل المطابق للعقد:

```http
HTTP 500
Content-Type: text/plain; charset=utf-8
Date: Sat, 10 Oct 2026 23:20:36 GMT
```

تكرر الفشل باستخدام مسار Dart الفعلي للتطبيق وبطلب مستقل بنفس JSON. بعده، أعاد `GET owner-advertisements/{advertisement_id}/` HTTP `200` و`key="success"` وحالة الانتظار دون تواريخ أو دفع. لا توجد رسالة تحقق JSON منظمة تحدد السبب. **السبب الداخلي غير معروف؛ يلزم traceback من سجلات الخادم.** لا توجد مصادر Backend في مستودع Flutter لإصلاح الاستثناء هنا.

## 3. نتائج الاختبار التي تساعد في عزل المشكلة

| العملية | النتيجة المرصودة |
| --- | --- |
| Google login وقراءة `auth/users/me/` | نجاح المصادقة وقراءة الحساب |
| `GET advertising/v1/plans/` | نجاح قراءة الخطة والسعر من الخادم |
| Multipart `POST advertising/v1/owner-advertisements/` | نجاح الرفع وحفظ إعلان معلق |
| إعادة create بنفس العملية والمحتوى | نفس الإعلان دون سجل ثانٍ |
| `GET advertising/v1/operations/{operation_id}/` | استرداد نفس الإعلان |
| Media بجلسة المالك | نجاح ومطابقة bytes الرد بالملف الأصلي بعد إصلاح رأس العميل |
| Owner detail/list بعد فشل الدفع | إعلان معلق واحد للعملية نفسها |
| Public feed بالعربية والإنجليزية | HTTP `200` و`results=[]`؛ الإعلان المعلق غير مكشوف |
| Media كضيف بالعربية والإنجليزية | HTTP `404`؛ الصورة المعلقة محمية |

## 4. العمل المطلوب في Backend

1. البحث في سجلات البيئة عند `2026-10-10T23:20:36Z` باستخدام `advertisement_id` ومعرف الدفع أعلاه، واستخراج الاستثناء الحقيقي. تحققوا من نسخة النشر والمigrations إذا أشار الاستثناء إلى مخطط قاعدة البيانات. لا تُعتبر هذه الأسباب مثبتة قبل قراءة السجل.
2. مراجعة مسار التفعيل للإعلان التعريفي: `property_id=null` و`offer_id=null` صالحان، فلا يفترض التحقق وجود عقار. عند وجود رابط، يجب فحص ملكية العقار وحالة `verified` وصلاحية العرض نفسه.
3. اشتقاق هوية المالك من الجلسة، والتحقق من ملكيته للإعلان. لا يقبل الطلب `owner_id` من العميل ولا يستطيع تفعيل إعلان حساب آخر.
4. قفل سجل الإعلان داخل transaction، والتحقق من صلاحية media، ثم تسجيل نجاح mock وتغيير الحالة والتواريخ معًا. عند حدوث استثناء، يجب ألا يبقى دفع ناجح بلا تفعيل أو تفعيل بلا سجل دفع.
5. الحفاظ على `plan_snapshot` المشتراة وسعرها ومدتها. لا تُغيّر إعادة الدفع الخطة أو تعيد تسعير إعلان محفوظ بسبب تغيير إعدادات plans لاحقًا.
6. استخدام وقت التفعيل الفعلي لحساب `starts_at` و`ends_at`. لهذه الخطة الأسبوعية، المدة `604800` ثانية من التفعيل. لا يبدأ الوقت عند create ولا يحسب Flutter الانتهاء.
7. حفظ payment record واحد فقط، بحقول `payment_mode="mock"` و`status="mock_succeeded"` ومعرف الإعلان ومعرف العملية الصحيحين. الدفع التجريبي ينجح بعد المصادقة والتحقق دون تحصيل مال.
8. ضمان idempotency داخل transaction وقيود التخزين، بما يشمل الطلبات المتزامنة. إعادة الطلب بعد النجاح ترجع نفس الإعلان وpayment ID والتواريخ، حتى بعد الانتهاء الطبيعي؛ لا تمديد ولا payment record إضافي.
9. إعادة envelope JSON المتفق عليه ورسائل الأخطاء بالعربية والإنجليزية. خطأ المصادقة أو التحقق ليس نجاح دفع، ولا يُعاد `key="success"` دون حالة موثوقة.

لا حاجة إلى بوابة دفع أو SDK أو بيانات بطاقة أو WebView أو moderation queue. أسعار البانرات هي استثناء مدفوع مستقل عن الأدوات والترويج المجاني والفواتير والإيجار، ولا يوجد تجديد تلقائي.

## 5. شكل النجاح الذي يقبله التطبيق

هذا **مثال توضيحي للعقد المتوقع بعد الإصلاح**؛ payment UUID والتواريخ أدناه ليست نتيجة تفعيل حدث بالفعل. يجب أن تُستبدل بقيم محفوظة وموثوقة من الخادم. يرجع الطلب الإعلان الخاص كاملًا، بما يشمل المحتوى الأصلي ونسخة الخطة.

```json
{
  "key": "success",
  "message": "Advertisement activated with mock payment.",
  "data": {
    "id": "85295dd1-f8bd-4c82-a903-9bdc3d90af98",
    "operation_id": "74682688-4428-413c-a1ae-c4b87222c687",
    "status": "active",
    "title": "Sokoun live test 74682688",
    "description": "Integration test banner. Mock payment only; no money collected.",
    "banner_url": "https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/advertising/v1/media/85295dd1-f8bd-4c82-a903-9bdc3d90af98/",
    "property_id": null,
    "offer_id": null,
    "plan_snapshot": {
      "id": "weekly",
      "title": "Weekly",
      "duration_unit": "week",
      "duration_count": 1,
      "revision": "1",
      "active": true,
      "price": {
        "amount_minor": 100000,
        "currency": "EGP",
        "exponent": 2
      }
    },
    "starts_at": "2026-10-11T09:00:00Z",
    "ends_at": "2026-10-18T09:00:00Z",
    "payment": {
      "id": "eb521a53-c2ea-4719-8750-4f7179079292",
      "advertisement_id": "85295dd1-f8bd-4c82-a903-9bdc3d90af98",
      "operation_id": "74682688-4428-413c-a1ae-c4b87222c687-payment",
      "payment_mode": "mock",
      "status": "mock_succeeded"
    }
  }
}
```

يتحقق Flutter من `key` وهوية الإعلان ومعرف create ومعرف payment وحالة mock والتواريخ ونسخة الخطة والمحتوى. HTTP `200` وحده لا يكفي. إذا فُقد رد الدفع، يجلب التطبيق التفاصيل ويثبت التفعيل قبل إعلان النجاح أو تكرار الدفع.

أخطاء التحقق المتوقعة ترجع envelope منظمًا، مثل هذا المثال غير المرصود في خطأ `500` الحالي:

```json
{
  "key": "error",
  "message": "Invalid payment operation.",
  "data": null,
  "errors": {
    "operation_id": ["invalid_payment_operation"]
  }
}
```

حافظوا على أكواد العقد الحالية وحالات HTTP المناسبة: `401` للجلسة غير الصالحة، `404` لإعلان لا يخص المستخدم، `400` للتحقق، و`409` للتعارض/المعالجة. لا يولد العميل معرف create جديدًا تلقائيًا عند فشل الدفع.

## 6. الصورة: إصلاح العميل المنجز

ظهر HTTP `406` أثناء تحميل صورة المالك لأن `Accept` كان يقتصر على الصور. عُدل `BannerArtworkData` ليرسل:

```http
Accept: image/jpeg, image/png, image/webp, application/json
```

نجحت قراءة الصورة الفعلية بعد التعديل. يرجى إبقاء endpoint متوافقًا مع هذا الرأس ومع JSON لردود API. استمر حد `10485760` bytes، ومسار الجلسة الحالي، ومنع redirects، وعدم إرسال بيانات اعتماد إلى مضيف صورة خارجي. إصلاح الصورة لا يعالج استثناء `mock-payment/`.

## 7. شروط قبول الإصلاح وإعادة الفحص

1. إعادة نفس طلب الدفع بإذن المالك المنشئ؛ يرجع الإعلان `active` و`mock_succeeded` مع تواريخ فعلية وسجل دفع واحد.
2. إعادة الطلب، ثم إرسال طلبين متزامنين بنفس المعرف. تبقى payment ID والتواريخ ونسخة الخطة ثابتة، وعدد السجلات واحدًا.
3. التأكد أن detail وowner list وoperation lookup تعيد نفس السجل المفعّل، وأن كل رد خاص محمي من الحسابات الأخرى.
4. التأكد أن `GET advertising/v1/placements/tenant-home/` يعيد الإعلان للمستخدمين الآخرين والضيوف بالعربية والإنجليزية، وأن media أصبحت عامة فقط أثناء أهلية العرض. feed لا يكشف `owner_id` أو `operation_id` أو `plan_snapshot` أو `payment` أو السعر.
5. أهلية feed يجب أن تتحقق مباشرة من `starts_at <= server_now < ends_at` و`status="active"` ونجاح الدفع التجريبي ونشاط حساب المالك وplacement الصحيح وصلاحية media والوجهة، دون انتظار worker الانتهاء. الحفاظ على ترتيب العقد: feed بـ `starts_at DESC, id DESC`، وقائمة المالك بـ `created_at DESC, id DESC`.
6. إعادة الاختبار [owner_banner_ads_live_test.dart](../apps/sokoun_app/test/owner_banner_ads_live_test.dart) من `apps/sokoun_app`، باستخدام Google ID token صالح في ملف خاص و**نفس journal للحساب والبيئة**:

```sh
export SOKOUN_BANNER_TEST_TOKEN_FILE=/private/path/google_id_token
export SOKOUN_BANNER_TEST_JOURNAL=/tmp/sokoun-banner-live-journal.json
export SOKOUN_BANNER_TEST_REPORT=/private/path/live_api_result.json
export SOKOUN_BANNER_TEST_BASE_URL=https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/
make bannerAdsLiveTest
```

الاختبار opt-in، ويسترد الإعلان المعروف قبل أي إنشاء، ولا يولد إعلانًا بديلًا عند الخطأ. لا تحذفوا journal بعد نتيجة ملتبسة. خطوات الجلسة والكوكيز في الاختبار لا تحفظ بيانات اعتماد داخل المستودع.

7. إتمام تجربة فعلية Owner A → Tenant B على الأجهزة بعد نجاح API، واختبارات انتهاء الإعلان والعقار/العرض والحساب الآخر والتخزين الدائم. هذه التجارب لم تثبت في التشغيل السابق بسبب فشل التفعيل.

الخطة الشهرية والسنوية تتبع إضافة شهر/سنة تقويمية في `Africa/Cairo` مع clamp لنهاية الشهر و29 فبراير؛ فجوة DST تتحرك إلى اللحظة المحلية الصالحة التالية، والتكرار يستخدم الحدوث المتأخر. الأسعار الأولية `monthly=300000` و`yearly=3000000` minor EGP. المرجع المستلم يحتوي العقد الكامل، ولا يتطلب هذا الإصلاح تغيير الأسعار أو طريقة اختيار الخطة.

## 8. ما نحتاج استلامه من فريق Backend

- سبب الاستثناء المؤكد من traceback وملخص الإصلاح ونسخة النشر.
- دليل تشغيل migrations اللازمة إذا كانت جزءًا من السبب.
- رد نجاح منقح للإعلان نفسه، ثم دليل إعادة الدفع بنفس payment ID والتواريخ.
- نتيجة الاختبار الحي وتأكيد وصول feed وmedia لحساب آخر/ضيف.

التحقق المحلي الأخير اجتاز `114` اختبارًا وتحليلًا مركزًا نظيفًا؛ اختبار API الحي المنفصل فشل عند HTTP `500`. الملف يصف نتيجة التشغيل المسجلة، ولا يدعي وجود إصلاح منشور أو تحصيل مبلغ أو اكتمال رحلة التفعيل.
