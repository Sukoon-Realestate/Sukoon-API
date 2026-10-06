Please update the existing Sokoon design with the following rule:

Everything that exists in the Owner Add Property flow, starting from property type until proof of ownership, must also be reflected in:
1. Tenant Property Details screen
2. Tenant Filter screen

Important:
- Do NOT redesign the project from scratch.
- Keep the same Sokoon design system.
- Keep Arabic RTL.
- Keep Tajawal font.
- Keep the same colors, spacing, rounded cards, inputs, chips, icons, and buttons.
- Only update the affected screens.
- Make sure all new fields are visible, well-organized, and clickable where needed.

==================================================
1. SOURCE OF TRUTH
==================================================

Use the Owner Add Property flow as the source of truth.

Check all fields in the owner add-property screens, including but not limited to:

- نوع العقار
- عنوان العقار
- السعر
- المدينة
- المنطقة / الحي
- العنوان التفصيلي
- موقع العقار على الخريطة
- الوصف
- عدد الغرف
- عدد الحمامات
- المساحة
- رقم الدور
- فترة التأجير
- مناسب لـ
- التدخين مسموح؟ / ممنوع التدخين
- المرافق والخدمات
- الصور والفيديوهات
- إثبات ملكية العقار
- أي تفاصيل إضافية موجودة في Add Property

The goal:
Any public-facing property data entered by the owner should be visible in the property details screen and usable in tenant filtering where it makes sense.

==================================================
2. UPDATE PROPERTY DETAILS SCREEN
==================================================

Update this screen:
- T-PROP-01

Add all public-facing details from the Owner Add Property flow into T-PROP-01.

The property details screen should include these sections:

1. Basic Info
- نوع العقار
- عنوان العقار
- السعر
- المدينة
- المنطقة / الحي
- الوصف

2. Location
- موقع العقار على الخريطة
- Map preview
- Approximate location note:
  “الموقع قد يظهر بشكل تقريبي لحماية الخصوصية”

3. Structure Details
- عدد الغرف
- عدد الحمامات
- المساحة
- رقم الدور

4. Rental Period
Show the rental period clearly using the same values from owner add property:
- يوم
- شهر
- سنة

Example:
“فترة التأجير: 6 شهور”

5. Suitable For
Show the selected suitable-for value:
- الكل
- ولاد فقط
- بنات فقط
- عائلات
- أفراد
- مشاركة

Example:
“مناسب لـ: عائلات”

6. Smoking Rule
Show smoking rule clearly:
- مسموح
- ممنوع
- حسب الاتفاق

Example:
“التدخين: ممنوع”

7. Amenities and Services
Show all amenities selected by the owner as chips/cards/icons:
- WiFi
- أسانسير
- جراج
- أمن
- بلكونة
- تكييف
- مفروش
- قريب من المترو
- غاز طبيعي
- عداد كهرباء
- عداد مياه
- Any other amenities from the owner add-property flow

8. Media
Show property photos/videos from owner upload:
- Image gallery
- Video preview if available
- Image counter

9. Ownership Proof
Important privacy rule:
Do NOT show the actual ownership proof document to tenants.

Do NOT show:
- Electricity bill image
- Water bill image
- Ownership contract file
- Any private uploaded document

Instead, show only a safe public trust indicator:
- “تم التحقق من إثبات الملكية”
or
- “إثبات الملكية قيد المراجعة”

Use a small verified/trust badge.

10. Owner Info
Keep owner card:
- Owner avatar
- Owner name
- Rating
- Verified badge
- Phone privacy note:
  “رقم الموبايل مخفي ومش هيظهر غير بموافقة واضحة”

11. Share Button
Make sure the share button exists in T-PROP-01.
It should open the share bottom sheet:
- نسخ الرابط
- مشاركة
- إلغاء

==================================================
3. UPDATE TENANT FILTER SCREEN
==================================================

Update the tenant filter screen / filter bottom sheet.

The tenant should be able to filter using the same searchable fields that the owner entered.

Add or confirm these filter fields:

1. نوع العقار
Options:
- شقة
- ستوديو
- غرفة

2. المدينة

3. المنطقة / الحي

4. السعر
- من
- إلى

5. عدد الغرف

6. عدد الحمامات

7. المساحة

8. الدور
Optional field:
- رقم الدور
or floor range if needed

9. فترة التأجير
Use the new format:
- Dropdown:
  - يوم
  - شهر
  - سنة
- Number field:
  “اكتب العدد”

10. مناسب لـ
Options:
- الكل
- ولاد فقط
- بنات فقط
- عائلات
- أفراد
- مشاركة

11. التدخين
Options:
- الكل
- مسموح
- ممنوع
- حسب الاتفاق

12. المرافق والخدمات
Use chips:
- WiFi
- أسانسير
- جراج
- أمن
- بلكونة
- تكييف
- مفروش
- قريب من المترو
- غاز طبيعي
- عداد كهرباء
- عداد مياه

13. التوثيق
Options/toggles:
- عقارات موثقة فقط
- إثبات ملكية تم التحقق منه

Important:
Do NOT add “upload proof of ownership” to tenant filters.
Only add a filter for verified ownership status:
“إثبات ملكية تم التحقق منه”

==================================================
4. UPDATE SEARCH RESULTS CHIPS
==================================================

When filters are selected, show active filter chips on the Search Results screen.

Example chips:
- “شقة”
- “مدينة نصر”
- “6 شهور”
- “عائلات”
- “التدخين ممنوع”
- “أسانسير”
- “إثبات ملكية موثق”

Each chip should have a small remove icon.

==================================================
5. UPDATE PROPERTY CARDS IF NEEDED
==================================================

On property cards, show only the most important extra info as small chips.

Possible chips:
- “موثّق”
- “عائلات”
- “ممنوع التدخين”
- “6 شهور”
- “أسانسير”

Do not overcrowd the cards.
Keep the full details inside T-PROP-01.

==================================================
6. PRIVACY RULES
==================================================

Very important:

- Ownership proof documents are private.
- Do not display uploaded documents to tenants.
- Do not display electricity bill, water bill, or ownership contract files.
- Only show verification status/badge.
- Do not show full phone numbers.
- Keep phone numbers hidden by default.
- Keep all privacy hints consistent with Sokoon style.

Use copy like:
“إثبات الملكية للمراجعة الداخلية فقط”
“تم التحقق من إثبات الملكية”
“المستندات الخاصة لا تظهر للمستخدمين”

==================================================
7. PROTOTYPE CONNECTIONS
==================================================

Make sure:
- Filter button opens the updated tenant filter screen/bottom sheet.
- Applying filters returns to Search Results with active chips.
- Property card opens T-PROP-01.
- T-PROP-01 shows all details from owner add-property fields.
- Share button opens share bottom sheet.
- Back buttons still work.
- No broken links.

==================================================
8. FINAL CHECK
==================================================

Before finishing, confirm:

- Every public field from Owner Add Property appears in T-PROP-01.
- Every searchable field from Owner Add Property appears in Tenant Filter.
- Proof of ownership is shown only as verification status, not as a document.
- Filter includes:
  - نوع العقار
  - المدينة
  - المنطقة
  - السعر
  - الغرف
  - الحمامات
  - المساحة
  - فترة التأجير
  - مناسب لـ
  - التدخين
  - المرافق
  - إثبات ملكية موثق
- T-PROP-01 is complete but not cluttered.
- Arabic RTL is correct.
- Tajawal font is used.
- The UI still matches the existing Sokoon design system.

Final output:
Update the tenant property details and tenant filtering experience so they fully reflect the owner add-property fields, while keeping private ownership documents hidden and showing only safe verification status.