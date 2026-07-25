Please update the existing Sokoon Figma Make project with the following changes.

Important:
- Do NOT redesign the whole project from scratch.
- Keep the same existing Sokoon design system.
- Keep Arabic RTL.
- Keep Tajawal font.
- Keep the same colors, spacing, rounded cards, icons, buttons, inputs, upload cards, and prototype interactions.
- Only update the mentioned owner add-property screens.
- Make sure the updated flow stays connected and clickable.

==================================================
1. UPDATE SCREEN O-ADD-02 — PROPERTY PHOTOS
==================================================

Update this screen:
- O-ADD-02

This screen is for uploading property photos.

New requirement:
Each uploaded photo must have:
1. Photo name
2. Photo description

For every image upload card/slot, add fields under or beside the image preview:

Field 1:
Label:
“اسم الصورة”

Placeholder examples:
- “غرفة النوم”
- “الريسبشن”
- “المطبخ”
- “الحمام”
- “البلكونة”
- “واجهة العقار”

Field 2:
Label:
“وصف الصورة”

Placeholder:
“اكتب وصف بسيط للصورة”

Example:
“غرفة نوم واسعة بإضاءة طبيعية”

Photo upload card structure:
- Image thumbnail / upload placeholder
- Upload button or camera icon
- Remove / replace icon after upload
- Field: اسم الصورة
- Field: وصف الصورة
- Upload state:
  - Empty
  - Uploading
  - Uploaded
  - Failed
  - Replace image

Validation:
- If image is uploaded but name is empty:
  “اسم الصورة مطلوب”
- If image is uploaded but description is empty:
  “وصف الصورة مطلوب”
- If no images uploaded:
  “ارفع صور العقار”

Keep the existing photo upload requirement if already present.
If the app requires multiple photos, keep the photo count/progress visible.

Suggested helper card:
Title:
“نصائح لصور أفضل”
Bullets:
- “صوّر كل غرفة بوضوح”
- “استخدم إضاءة كويسة”
- “اكتب اسم ووصف لكل صورة”
- “متصورش أي مستندات أو أرقام شخصية”

Primary CTA:
“التالي”

The CTA should stay disabled until the required photo information is complete.

==================================================
2. ADD NEW SCREEN AFTER O-ADD-02 — PROPERTY VIDEO UPLOAD
==================================================

Create a new screen immediately after O-ADD-02.

New screen name:
- O-ADD-02V

Screen purpose:
The owner uploads or records a short video for the property.

Screen title:
“فيديو العقار”

Subtitle:
“صوّر فيديو قصير يوضح العقار للمستأجرين”

Video requirement:
- The video must not exceed 1 minute.
- Maximum duration: 60 seconds.

Add a clear requirement card:
Title:
“متطلبات الفيديو”
Bullets:
- “مدة الفيديو لا تزيد عن دقيقة واحدة”
- “صوّر مدخل العقار والغرف الأساسية”
- “خلي الفيديو واضح وثابت”
- “متظهرش أرقام تليفونات أو مستندات شخصية في الفيديو”

Video upload area:
- Large rounded upload card
- Icon: video camera / play
- Empty state text:
  “ارفع أو صوّر فيديو للعقار”
- Secondary text:
  “الحد الأقصى: 60 ثانية”
- Buttons:
  “تصوير فيديو”
  “رفع فيديو”

After upload:
- Show video thumbnail
- Play icon overlay
- Duration label, example:
  “00:45”
- Replace button:
  “تغيير الفيديو”
- Remove button:
  “حذف الفيديو”

Validation:
- If video duration is more than 60 seconds:
  “الفيديو لازم يكون أقل من دقيقة”
- If upload fails:
  “فشل رفع الفيديو، حاول تاني”
- If no video uploaded and video is optional:
  Allow “تخطي”
- If video is required:
  Disable “التالي” until a valid video is uploaded.

For this project, make the video strongly recommended but allow skipping unless the current flow says it is required.

Actions:
Primary CTA:
“التالي”

Secondary CTA:
“تخطي الفيديو”

Back:
“رجوع”

Privacy hint:
“الفيديو هيظهر للمستأجرين بعد مراجعة سكون، فمتظهرش فيه أي بيانات شخصية”

==================================================
3. UPDATE OWNER ADD PROPERTY FLOW
==================================================

Update the owner add-property prototype flow.

Current flow likely:
O-ADD-01 → O-ADD-02 → O-ADD-03

Change it to:
O-ADD-01 → O-ADD-02 → O-ADD-02V → O-ADD-03

Prototype rules:
- O-ADD-02 “التالي” should navigate to O-ADD-02V.
- O-ADD-02V “التالي” should navigate to O-ADD-03.
- O-ADD-02V “تخطي الفيديو” should also navigate to O-ADD-03.
- O-ADD-02V back button should return to O-ADD-02.
- Keep all later steps connected correctly.

==================================================
4. UPDATE REVIEW / SUBMIT SCREEN IF EXISTS
==================================================

If there is a review screen in the add-property flow, update it to show:

Photos section:
- Number of uploaded photos
- Each photo name
- Each photo short description

Video section:
- Video status:
  - “تم رفع الفيديو”
  - or “تم تخطي الفيديو”
- Video duration if uploaded:
  “00:45”

Do not show a huge video preview on review.
Use a clean summary card.

==================================================
5. UPDATE PROPERTY DETAILS IF NEEDED
==================================================

If the tenant property details screen shows property media, make sure the video appears in the media gallery after approval.

In T-PROP-01:
- Show photos with gallery
- Show video thumbnail if available
- Video duration label
- Play icon
- Do not autoplay video

Also keep photo names/descriptions available if the gallery design supports captions.

==================================================
6. FINAL CHECKLIST
==================================================

Before finishing, confirm:

- O-ADD-02 now requires name and description for every uploaded photo.
- O-ADD-02 keeps the same Sokoon design style.
- New screen O-ADD-02V exists after O-ADD-02.
- O-ADD-02V allows owner to upload or record property video.
- Video maximum duration is clearly shown as 1 minute / 60 seconds.
- Error state appears if video is longer than 60 seconds.
- Owner add-property flow is now:
  O-ADD-01 → O-ADD-02 → O-ADD-02V → O-ADD-03
- Back and next buttons work correctly.
- Review screen shows photo names/descriptions and video status if applicable.
- Arabic RTL is correct.
- Tajawal font is used.
- No unrelated screens are changed.

Final output:
Update O-ADD-02 to include photo name and description for each image, add the new O-ADD-02V video upload screen after it with a 1-minute maximum video limit, and reconnect the owner add-property prototype flow properly.