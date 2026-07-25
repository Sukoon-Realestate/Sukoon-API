Update the existing Sokoon UI design with the following changes.

Important:
- Do NOT redesign the whole project from scratch.
- Keep the same existing design system.
- Keep Arabic RTL layout.
- Keep Tajawal font.
- Keep the same colors, rounded cards, spacing, icons, buttons, and overall Sokoon style.
- Only update the affected screens and add the missing screens/states.
- Make sure all updated buttons and new flows are clickable in the prototype.

==================================================
1. UPDATE LOGIN / AUTH FLOW
==================================================

Update the Login screen.

The login should now be email-based.

Login screen requirements:
- Main title: “تسجيل الدخول”
- Subtitle: “ادخل بريدك الإلكتروني عشان نبعتهالك خطوة التحقق”
- Field:
  - “البريد الإلكتروني”
- Primary CTA:
  - “إرسال كود التحقق”
- Remove password-first login from the main login screen.
- After entering email, navigate to a new OTP screen.

Add a new OTP Verification screen:
- Title: “كود التحقق”
- Subtitle: “بعتنالك كود على البريد الإلكتروني”
- Show masked email example:
  “ah****@gmail.com”
- 6-digit OTP input
- Timer:
  “إعادة الإرسال بعد 45 ثانية”
- CTA:
  “تأكيد الدخول”
- Secondary action:
  “إعادة إرسال الكود”
- Back action:
  “تغيير البريد الإلكتروني”
- Error state:
  “الكود غير صحيح، حاول تاني”
- Success state should navigate to the correct app home based on user role.

Add social authentication buttons to Login and Sign Up screens:
- “المتابعة باستخدام Google”
- “المتابعة باستخدام Facebook”
- “المتابعة باستخدام Apple”
- Use clean branded icons but keep the buttons consistent with Sokoon style.
- Apple button should be included for iOS-style auth screens.

Add “Sign in as Visitor” option:
- Arabic label:
  “الدخول كزائر”
- Place it under the main auth options.
- Visitor mode behavior:
  - Visitor can browse properties.
  - Visitor can view property details.
  - Visitor cannot chat, book visits, save listings, or add property until creating an account.
- When visitor taps restricted actions, show a bottom sheet:
  - Title: “سجّل دخولك عشان تكمل”
  - Text: “الميزة دي محتاجة حساب عشان نحافظ على الأمان والثقة”
  - CTA: “تسجيل الدخول”
  - Secondary: “إنشاء حساب”

==================================================
2. UPDATE NATIONAL ID UPLOAD SCREEN
==================================================

On the National ID upload screen, add a very clear privacy hint.

Add a privacy hint card under the upload area:
- Icon: shield / lock / eye-off
- Text:
  “صورة البطاقة لا تظهر لأي مستخدم نهائياً”
- Subtext:
  “المستندات دي للمراجعة الداخلية فقط، ومش بتتعرض للمالك أو المستأجرين”
- Keep the tone reassuring and simple.
- Use soft teal/blue background, same Sokoon style.

This hint must appear near:
- National ID front upload
- National ID back upload
- Any identity document upload step

==================================================
3. OWNER HOME — ADD VISIT REQUESTS ICON
==================================================

Update Owner Home / Owner Dashboard.

Add a dedicated icon for “طلبات الزيارة” in the owner home dashboard.

Where to add:
- In the top dashboard shortcuts or metric cards.
- Also keep it connected to the Owner Requests screen.

Icon:
- Calendar / visit / appointment icon
- Label:
  “طلبات الزيارة”
- If there are pending requests, show a small badge count.
- Example:
  “3”
- Tapping this icon/card should navigate to:
  Owner Visit Requests List

==================================================
4. OWNER ADD PROPERTY — SMOKING OPTION
==================================================

In the Owner Add Property flow, add a new field for smoking rules.

Add this field in the property details / amenities / rules step.

Field title:
“التدخين مسموح؟”

Options:
- “مسموح”
- “ممنوع”
- “حسب الاتفاق”

Use pill buttons or radio cards.
Selected option should have teal border/background and check icon.

Also show this value later in Property Details under:
“قواعد السكن” or “معلومات إضافية”

Example display:
- “التدخين: ممنوع”

==================================================
5. PROPERTY SHARE BUTTON — OUTSIDE AND INSIDE
==================================================

Add Share functionality to property screens.

Outside property details:
- Add a share icon on property cards in lists.
- Examples:
  - Tenant Home property cards
  - Search results cards
  - Saved property cards
  - Nearby properties cards
- The share icon should be near the favorite/heart icon, but visually separate.
- Use a clean rounded icon button.

Inside property details:
- Add a share icon in the top overlay/header of the Property Details screen.
- It should appear next to favorite or more actions.
- Tapping share should open a small share bottom sheet or system share placeholder.

Share bottom sheet:
- Title:
  “مشاركة العقار”
- Options:
  - “نسخ الرابط”
  - “مشاركة”
  - “إلغاء”
- Toast after copy:
  “تم نسخ رابط العقار”

==================================================
6. TENANT FILTER — ADD SUITABLE FOR FIELD
==================================================

Update Tenant Filter screen / bottom sheet.

Add a new filter field that lets the tenant specify who the property is suitable for.

Field title:
“مناسب لـ”

Options:
- “الكل”
- “ولاد فقط”
- “بنات فقط”
- “عائلات”
- “أفراد”
- “مشاركة”

Use chips/pills.
Selected chip should use Sokoon primary teal style.

This filter should appear near:
- Property type
- Rental duration
- Rooms
- Price range

Also show the selected value as a chip in Search Results when active.
Example:
“بنات فقط”

==================================================
7. OWNER ADD PROPERTY — ADD SUITABLE FOR FIELD
==================================================

In the Owner Add Property flow, add the same field so the owner can define who the property is suitable for.

Field title:
“العقار مناسب لـ”

Options:
- “الكل”
- “ولاد فقط”
- “بنات فقط”
- “عائلات”
- “أفراد”
- “مشاركة”

Use radio cards or selectable chips.
Selected option should be clearly visible.

Show this value in:
- Property review before submit
- Property details screen
- Property cards if useful as a small chip

Example display in details:
“مناسب لـ: عائلات”

==================================================
8. PLATFORM FEES DEDUCTED FROM OWNER EARNINGS
==================================================

Update any platform fee / revenue copy.

Rule:
Platform fees are deducted from the owner’s earnings, not charged directly to the tenant.

Add this note where relevant:
- Owner financial summary
- Owner dashboard earnings section, if present
- Add property / pricing hint, if needed
- Future finance screens

Arabic copy:
“رسوم المنصة يتم خصمها من أرباح المالك”

Alternative helper text:
“المستأجر يشوف السعر بوضوح، ورسوم المنصة بتتخصم من أرباح المالك حسب سياسة سكون”

Do not add a tenant-facing fee on property details unless it is explicitly needed.
Keep tenant pricing clear and simple.

==================================================
9. OWNER ADD PROPERTY — PROOF OF OWNERSHIP UPLOAD
==================================================

In the Owner Add Property flow, add a new required or strongly recommended field for uploading proof of property ownership.

Add this step or section:
“إثبات ملكية العقار”

Upload field:
- “ارفع إثبات الملكية”

Hint:
“ممكن ترفع وصل كهربا، وصل مياه، أو عقد الملكية”

Privacy hint:
“المستند ده للمراجعة الداخلية فقط ومش هيظهر للمستخدمين”

Accepted formats:
- PDF
- JPG
- PNG

Upload states:
- Empty
- Uploading
- Uploaded
- Failed
- Replace file
- Remove file

This field should appear in:
- Add Property Wizard
- Review & Submit screen
- Owner property status / rejection notes if rejected due to missing proof
- Admin listing review screen, if admin screens exist

==================================================
10. TENANT RENTAL PERIOD FIELD
==================================================

Update the rental period input for tenants.

Instead of the current style, make it a combination of:
1. Dropdown
2. Number text field

Field title:
“فترة التأجير”

Dropdown options:
- “يوم”
- “أسبوع”
- “شهر”

Number field:
- Placeholder:
  “اكتب العدد”
- Example:
  Dropdown: “شهر”
  Number: “3”
  Meaning: 3 months

Layout:
- Put the dropdown and number field next to each other in one row.
- Since the UI is Arabic RTL:
  - Dropdown on the right
  - Number field on the left
- Use rounded inputs and same Sokoon styling.

Validation:
- If number is empty:
  “اكتب مدة التأجير”
- If number is invalid:
  “اكتب رقم صحيح”

Show the selected rental period in results/details where relevant:
Example:
“مدة التأجير: 3 شهور”

==================================================
11. OWNER REQUESTS — REPLACE CHAT WORD WITH ICON
==================================================

Update Owner Visit Requests cards.

Currently the actions are:
- قبول
- رفض
- شات

Change this:
- Remove the word “شات”
- Replace it with only a chat icon.

Placement:
- Put the chat icon next to the “موثّق” badge or near the tenant verification area.
- It should be visually clear but not as a text action.
- Keep Accept and Reject as text buttons.
- Chat icon should still be clickable and navigate to Owner Chat Detail.

Updated request card actions:
- “قبول”
- “رفض”
- Chat icon only

Tenant info area should show:
- Tenant name
- Verification badge “موثّق”
- Chat icon beside/near the verified badge

Tooltip/label if needed:
“فتح الشات”

==================================================
12. PROTOTYPE CONNECTIONS
==================================================

Make all new updates interactive:

- Login email CTA → OTP screen
- OTP success → correct home screen
- Social login buttons → appropriate home or role selection placeholder
- Visitor login → Tenant Home visitor mode
- Restricted visitor actions → Login required bottom sheet
- Share icons → Share bottom sheet
- Tenant filter suitable-for chips → selected filter state
- Rental period dropdown → selectable state
- Owner visit requests icon → Owner Requests screen
- Owner request chat icon → Owner Chat Detail
- Proof ownership upload → upload states
- Smoking option → selected state
- Suitable-for owner field → selected state and review screen

==================================================
13. FINAL QUALITY CHECK
==================================================

Before finishing, make sure:

- No screen is redesigned from scratch.
- All updates match the existing Sokoon design.
- Arabic RTL is correct.
- Tajawal is used everywhere.
- The new login flow is email + OTP.
- Google / Facebook / Apple sign-in buttons are visible.
- “الدخول كزائر” is visible and works.
- National ID upload has a strong privacy hint.
- Owner Home has a Visit Requests icon.
- Owner Add Property includes:
  - Smoking option
  - Suitable-for option
  - Proof of ownership upload
- Property cards and details include Share.
- Tenant filters include:
  - Suitable-for field
  - Rental period dropdown + number field
- Platform fee copy says fees are deducted from owner earnings.
- Owner request cards show chat as an icon, not the word “شات”.
- All new buttons and icons are clickable in the prototype.

Final output:
Update the existing Sokoon design with these feature changes, keeping the same visual identity, and connect all new screens/states in the prototype.