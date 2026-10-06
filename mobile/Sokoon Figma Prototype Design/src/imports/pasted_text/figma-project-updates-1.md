Please apply the following exact updates to the existing Sokoon Figma Make project.

Important:
- Do NOT redesign the whole project from scratch.
- Keep the same existing Sokoon design system.
- Keep Arabic RTL layout.
- Keep Tajawal font.
- Keep the same colors, spacing, rounded cards, icons, buttons, forms, bottom sheets, and prototype interactions.
- Only update the mentioned screens.
- After moving sections from temporary screens, delete the temporary screens.
- Fix all broken prototype links after deleting screens.

==================================================
1. MOVE MAP LOCATION SECTION FROM O-ADD-01U TO O-ADD-01
==================================================

There is a temporary screen:
- O-ADD-01U

It contains the section:
“موقع العقار على الخريطة”

Please move/copy this full map location section into the original screen:
- O-ADD-01

Requirements:
- Add the exact same “موقع العقار على الخريطة” section from O-ADD-01U into O-ADD-01.
- Keep the same map card, pin marker, location input, helper text, button, and privacy hint.
- Keep the same visual style and spacing.
- Make sure the section fits naturally inside O-ADD-01.
- If there is a button like “تحديد الموقع”, keep it clickable.
- If there is a map selection overlay/state, link to it correctly.

After adding it to O-ADD-01, delete this screen completely:
- O-ADD-01U

Do not keep O-ADD-01U as a duplicate, hidden screen, or unused screen.

==================================================
2. MOVE RENTAL PERIOD FROM O-ADD-03P TO O-ADD-03
==================================================

There is a temporary screen:
- O-ADD-03P

It contains the correct updated rental period field.

Please take the rental period component from O-ADD-03P and replace the existing rental period field in:
- O-ADD-03

The correct rental period field should be:

Field title:
“فترة التأجير”

Layout:
- One row with two inputs
- Arabic RTL direction:
  - Dropdown on the right
  - Number field on the left

Dropdown values:
- يوم
- شهر
- سنة

Number field:
- Accepts numbers only
- Placeholder:
  “اكتب العدد”

Example:
- Dropdown: “شهر”
- Number: “6”
- Meaning: 6 months

Validation:
- Empty:
  “اكتب مدة التأجير”
- Invalid:
  “اكتب رقم صحيح”

Requirements:
- Remove the old rental period design from O-ADD-03.
- Use the rental period field from O-ADD-03P instead.
- Keep the same existing Sokoon input style.
- Make dropdown and number field visually clear and clickable.

After updating O-ADD-03, delete this screen completely:
- O-ADD-03P

Do not keep O-ADD-03P as a duplicate, hidden screen, or unused screen.

==================================================
3. UPDATE PROPERTY DETAILS SCREEN T-PROP-01 WITH ALL OWNER-ADDED DETAILS
==================================================

Very important:

In the tenant property details screen:
- T-PROP-01

Add and display all relevant property details that were added from the owner Add Property flow screens:

- O-ADD-01
- O-ADD-02
- O-ADD-03
- O-ADD-03U

Please audit these owner add-property screens and make sure every public-facing property detail entered by the owner appears clearly in T-PROP-01.

T-PROP-01 should include all important public property information, such as:

1. Basic property information
- Property title
- Property type
- City
- Area / neighborhood
- Price
- Description

2. Location information
- Map preview
- Approximate location display
- Location privacy note:
  “الموقع قد يظهر بشكل تقريبي لحماية الخصوصية”

3. Structure details
- Number of rooms
- Number of bathrooms
- Area in meters
- Floor number
- Furnished / not furnished if available

4. Rental period
Use the updated format from O-ADD-03:
- Dropdown value + number value
Example display:
“فترة التأجير: 6 شهور”
or
“فترة التأجير: 1 سنة”

5. Suitable-for field
If the owner selected who the property is suitable for, show it in T-PROP-01:
Title:
“مناسب لـ”
Values may include:
- الكل
- ولاد فقط
- بنات فقط
- عائلات
- أفراد
- مشاركة

Example:
“مناسب لـ: عائلات”

6. Smoking rules
If this field exists in O-ADD screens, show it in T-PROP-01:
Title:
“التدخين”
Values:
- مسموح
- ممنوع
- حسب الاتفاق

Example:
“التدخين: ممنوع”

7. Amenities and services
Show all selected amenities from the owner Add Property flow, such as:
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

8. Ownership verification
If the owner uploaded proof of ownership, do NOT show the actual document to tenants.
Instead, show a safe public-facing trust indicator only:
- “تم التحقق من إثبات الملكية”
or
- “إثبات الملكية قيد المراجعة”

Important privacy rule:
Never show the uploaded ownership document, water bill, electricity bill, contract, or any private document inside T-PROP-01.
Only show a public trust/status badge.

9. Platform fees note if relevant
If price or fee information appears, keep tenant pricing clear.
If a platform fee note is needed, use:
“رسوم المنصة يتم خصمها من أرباح المالك”

Do not make it look like the tenant pays an extra hidden fee.

10. Owner box
Keep owner information:
- Owner avatar
- Owner name
- Rating
- Verified badge
- Phone privacy note:
  “رقم الموبايل مخفي ومش هيظهر غير بموافقة واضحة”

Requirements:
- T-PROP-01 must feel complete and detailed.
- Do not make it cluttered.
- Use grouped sections/cards:
  - السعر والموقع
  - تفاصيل العقار
  - فترة التأجير
  - مناسب لـ
  - قواعد السكن
  - المرافق والخدمات
  - الموقع
  - بيانات المالك
- Keep the layout clean, readable, and consistent with the existing Sokoon style.

==================================================
4. MOVE SHARE BUTTON FROM T-PROP-01U TO T-PROP-01
==================================================

There is a temporary screen:
- T-PROP-01U

It contains the correct share button/design.

Please move/copy the share button from:
- T-PROP-01U

Into the original property details screen:
- T-PROP-01

Requirements:
- Add the share icon in the top action area of T-PROP-01.
- It should be placed near the favorite icon / top header actions.
- Use the exact same share styling from T-PROP-01U.
- Keep the favorite button; do not remove it.
- Make the share button clickable.

Share interaction:
Tapping the share icon should open a share bottom sheet.

Share bottom sheet:
Title:
“مشاركة العقار”

Options:
- “نسخ الرابط”
- “مشاركة”
- “إلغاء”

After tapping “نسخ الرابط”, show toast:
“تم نسخ رابط العقار”

After adding the share button to T-PROP-01, delete this screen completely:
- T-PROP-01U

Do not keep T-PROP-01U as a duplicate, hidden screen, or unused screen.

==================================================
5. DELETE TEMPORARY SCREENS AFTER MERGING
==================================================

After completing the updates, delete these temporary screens completely:

- O-ADD-01U
- O-ADD-03P
- T-PROP-01U

Do not keep them hidden or disconnected.
Remove them from the prototype map and from the screen overview.

If any links point to these deleted screens, reroute them to:

- O-ADD-01U links → O-ADD-01
- O-ADD-03P links → O-ADD-03
- T-PROP-01U links → T-PROP-01

==================================================
6. PROTOTYPE CONNECTIONS
==================================================

Update all prototype connections:

- Any owner add-property flow should use O-ADD-01, not O-ADD-01U.
- Any owner add-property flow should use O-ADD-03, not O-ADD-03P.
- Any property details link should go to T-PROP-01, not T-PROP-01U.
- The share button in T-PROP-01 should open the share bottom sheet.
- Back buttons should still work correctly.
- Continue buttons in the owner add-property flow should still go to the next correct step.
- The property details screen should remain connected from:
  - Tenant Home
  - Search Results
  - Saved
  - Nearby Properties
  - Notifications if applicable

==================================================
7. FINAL CHECKLIST
==================================================

Before finishing, confirm:

- O-ADD-01 now contains “موقع العقار على الخريطة”.
- O-ADD-01U is deleted.
- O-ADD-03 now contains the updated rental period field from O-ADD-03P.
- O-ADD-03P is deleted.
- T-PROP-01 now contains all public-facing details added by the owner in:
  - O-ADD-01
  - O-ADD-02
  - O-ADD-03
  - O-ADD-03U
- T-PROP-01 includes the share button from T-PROP-01U.
- T-PROP-01U is deleted.
- Private ownership documents are NOT visible to tenants.
- Ownership proof appears only as a safe verification/status indicator.
- All links to deleted screens are fixed.
- Arabic RTL is correct.
- Tajawal font is still used.
- The UI still matches the Sokoon design system.
- No duplicate temporary screens remain.

Final output:
Merge the useful sections from the temporary screens into the original screens, update T-PROP-01 with all public owner-added property details, add the share button, delete the temporary screens, and reconnect the prototype properly.