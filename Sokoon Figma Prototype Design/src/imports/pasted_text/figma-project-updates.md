Please apply the following exact updates to the existing Sokoon Figma Make project.

Important rules:
- Do NOT redesign the whole project from scratch.
- Keep the same existing Sokoon design system.
- Keep Arabic RTL layout.
- Keep Tajawal font.
- Keep the same colors, spacing, rounded cards, icons, buttons, bottom bars, and component style.
- Only update the mentioned screens.
- Remove deleted screens from the prototype flow and reconnect any broken links.
- Make sure all updated buttons/tabs are clickable in the prototype.

==================================================
1. DELETE OWNER DASHBOARD SCREEN
==================================================

Delete this screen completely:
- O-DASH-02

Do not keep it as a duplicate or hidden screen.
If any button or prototype arrow points to O-DASH-02, reroute it to the correct owner dashboard/request screen.

==================================================
2. UPDATE O-REQ-ICON WITH REQUEST STATUS SECTION
==================================================

In screen:
- O-REQ-ICON

Add the upper section from:
- O-REQ-01

Specifically, copy the top “request status” section from O-REQ-01 into O-REQ-ICON.

This section should include the request status controls/chips/cards, such as:
- الكل
- جديد
- مقبول
- مرفوض
- مكتمل

If O-REQ-01 has counts, badges, or status summary cards in that upper section, include them too.

Keep exactly the same styling from O-REQ-01:
- Same spacing
- Same rounded chips/cards
- Same active/inactive state
- Same colors
- Same typography

The goal:
O-REQ-ICON should become the main owner requests screen with the status section visible at the top.

==================================================
3. CONNECT OWNER BOTTOM BAR REQUESTS TAB
==================================================

Update the Owner bottom navigation.

The tab:
- الطلبات

Should now navigate to:
- O-REQ-ICON

Do NOT link the الطلبات tab to O-VISITS-01 or any old visits screen.

Make sure this works from all owner screens that have the bottom bar:
- Owner Dashboard
- My Properties
- Requests
- Owner Chat
- More/Profile

==================================================
4. DELETE OLD OWNER VISITS SCREEN
==================================================

Delete this screen completely:
- O-VISITS-01

Remove it from the prototype.
If any link points to O-VISITS-01, reroute it to:
- O-REQ-ICON

==================================================
5. UPDATE O-ADD-01 — ADD PROPERTY LOCATION MAP FIELD
==================================================

In screen:
- O-ADD-01

Add a new field/section for property location on the map.

Section title:
“موقع العقار على الخريطة”

Content:
- Map preview card
- Pin marker
- Search location input
- Button:
  “تحديد الموقع”
- Optional helper text:
  “حدد موقع العقار بدقة عشان نراجع الإعلان بشكل أسرع”

Privacy hint:
“قد يظهر الموقع للمستأجرين بشكل تقريبي لحماية الخصوصية”

This field should match the existing add-property form style:
- Rounded cards
- Soft border
- Teal active states
- Arabic RTL

Prototype interaction:
- Tapping “تحديد الموقع” should open a map selection state, map overlay, or placeholder if a full map screen does not exist.

==================================================
6. UPDATE O-ADD-03 — RENTAL PERIOD FIELD
==================================================

In screen:
- O-ADD-03

Change the rental period input.

Replace the current rental period design with:

Field title:
“فترة التأجير”

Layout:
- One row with two inputs
- Since the UI is Arabic RTL:
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
- Display meaning: 6 months

Validation messages:
- If number is empty:
  “اكتب مدة التأجير”
- If invalid:
  “اكتب رقم صحيح”

Keep the same existing input style.

==================================================
7. DELETE OLD TENANT LOGIN SCREEN
==================================================

Delete this screen completely:
- T-LOGIN-01

Do not keep it as a duplicate.
Any prototype links that go to T-LOGIN-01 should be redirected to:
- T-LOGIN-EMAIL

==================================================
8. UPDATE T-LOGIN-EMAIL — ADD PASSWORD FIELD
==================================================

In screen:
- T-LOGIN-EMAIL

Add a password field under the email field.

Fields should be:
1. “البريد الإلكتروني”
2. “كلمة المرور”

Password field requirements:
- Hidden password by default
- Eye icon to show/hide password
- Error state:
  “كلمة المرور مطلوبة”
- Forgot password link:
  “نسيت كلمة المرور؟”

Primary CTA:
“تسجيل الدخول”

Keep social login buttons if they already exist:
- Google
- Facebook
- Apple

Keep visitor login option if it already exists:
“الدخول كزائر”

Prototype:
- Successful login should go to Tenant Home.
- Forgot password should go to the forgot password flow.
- Visitor should go to tenant visitor mode if available.

==================================================
9. DELETE OLD OWNER LOGIN SCREEN
==================================================

Delete this screen completely:
- O-LOGIN-01

Do not keep it as a duplicate.
Any prototype links that go to O-LOGIN-01 should be redirected to:
- O-LOGIN-EMAIL

==================================================
10. UPDATE O-LOGIN-EMAIL — ADD PASSWORD FIELD
==================================================

In screen:
- O-LOGIN-EMAIL

Add a password field under the email field.

Fields should be:
1. “البريد الإلكتروني”
2. “كلمة المرور”

Password field requirements:
- Hidden password by default
- Eye icon to show/hide password
- Error state:
  “كلمة المرور مطلوبة”
- Forgot password link:
  “نسيت كلمة المرور؟”

Primary CTA:
“تسجيل الدخول”

Keep social login buttons if they already exist:
- Google
- Facebook
- Apple

Prototype:
- Successful login should go to Owner Dashboard.
- Forgot password should go to the forgot password flow.

==================================================
11. CONFIRM SHARE BUTTON ON T-PROP-01
==================================================

In screen:
- T-PROP-01

Make sure there is a visible Share button.

Placement:
- Add the share icon in the top action area of the property details screen.
- It should be near the favorite icon / back button / top header actions.
- Use a rounded icon button that matches the existing design style.

Icon:
- Share icon

Interaction:
- Tapping the share icon should open a share bottom sheet.

Share bottom sheet:
Title:
“مشاركة العقار”

Options:
- “نسخ الرابط”
- “مشاركة”
- “إلغاء”

After tapping “نسخ الرابط”, show toast:
“تم نسخ رابط العقار”

Do not hide or remove the favorite button.

==================================================
12. FINAL PROTOTYPE CHECK
==================================================

After applying all updates, check the prototype:

- O-DASH-02 is deleted.
- O-VISITS-01 is deleted.
- T-LOGIN-01 is deleted.
- O-LOGIN-01 is deleted.
- O-REQ-ICON contains the request status upper section from O-REQ-01.
- Owner bottom bar “الطلبات” links to O-REQ-ICON.
- O-ADD-01 has the property location map field.
- O-ADD-03 has rental period as number field + dropdown with:
  يوم / شهر / سنة
- T-LOGIN-EMAIL has email + password.
- O-LOGIN-EMAIL has email + password.
- T-PROP-01 has a working share button and share bottom sheet.
- All broken links from deleted screens are fixed.
- Arabic RTL remains correct.
- Tajawal font remains consistent.
- The design still matches the existing Sokoon style.

Final output:
Apply these exact screen updates, delete the mentioned obsolete screens, reconnect the prototype properly, and keep the Sokoon UI visually consistent.