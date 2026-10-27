"""Bilingual message, field and choice catalogs."""

EN_TO_AR_MESSAGES = {
    "Walls and floors": "الجدران والأرضيات",
    "Report submitted.": "تم إرسال التقرير.",
    "Acknowledgement must refer to the persisted report content.": "يجب أن يطابق الاعتماد محتوى نسخة التقرير المحفوظة. حدّث التقرير وراجعه قبل الاعتماد.",
    "Base rent": "الإيجار الأساسي",
    "Security deposit": "التأمين",
    "The legal agreement has not ended.": "لم ينتهِ العقد بعد.",
    "The final settlement is not accepted.": "لم يعتمد الطرفان التسوية النهائية بعد.",
    "A payment is still awaiting reconciliation.": "لا تزال إحدى عمليات الدفع قيد التحقق من النتيجة.",
    "Occupancy has not been returned.": "لم يتم تأكيد إخلاء السكن وتسليمه بعد.",
    "An invoice balance remains.": "لا يزال هناك رصيد مستحق على إحدى الفواتير.",
    "The deposit is unresolved.": "لم تتم تسوية مبلغ التأمين بعد.",
    "A refund is pending.": "لا يزال أحد طلبات الاسترداد قيد المتابعة.",
    "A dispute is unresolved.": "لا يزال هناك نزاع لم يُحسم.",
    "An owner payable or payout is unresolved.": "لا تزال هناك مستحقات للمالك أو عملية صرف قيد المتابعة.",
    "Owner funds must be recovered after a refunded payout.": "يلزم استرداد المبلغ المصروف للمالك بعد رد الدفعة.",
    "Rental inventory has not been returned.": "لم تُحرر الوحدة المؤجرة بعد التسليم.",
    "Settlement execution is incomplete.": "لم يكتمل تنفيذ التسوية بعد.",
    "Financial processing remains open.": "لا تزال المعالجة المالية قيد المتابعة.",
    "An independently reviewed settlement correction remains open.": "لا يزال تصحيح التسوية الخاضع لمراجعة مستقلة قيد المتابعة.",
    'Payment confirmed. Service activation requires follow-up.': 'تأكد الدفع. يحتاج تفعيل الخدمة إلى متابعة.',
    'Review the original invoice and activation attempt. Retry activation only; do not collect payment again.': 'راجع الفاتورة الأصلية ومحاولة التفعيل. أعد محاولة التفعيل فقط دون تحصيل جديد.',
    'The service is active. Review the original receipt and record the follow-up outcome.': 'الخدمة مفعلة. راجع إيصال الدفع الأصلي وسجل نتيجة المتابعة.',

    'This lease cannot receive this proposal in its current state.': 'لا تسمح حالة العقد الحالية بتقديم هذا المقترح.',
    'Review the current proposal and your role before responding.': 'راجع نسخة المقترح الحالية وصلاحيتك قبل الرد.',
    'The lease terms changed. The author must review and submit an updated proposal.': 'تغيرت شروط العقد. على صاحب المقترح مراجعتها وإرسال نسخة محدثة.',
    'This invoice no longer matches the proposed payment extension.': 'تغيرت الفاتورة المرتبطة بالتأجيل. راجع حالتها الحالية.',
    'This invoice no longer needs a payment extension.': 'لم تعد هذه الفاتورة بحاجة إلى تأجيل الدفع.',
    'Keep the original invoice.': 'احتفظ بالفاتورة الأصلية المرتبطة بالطلب.',
    'Only the proposal author can edit it before acceptance.': 'يمكن لصاحب المقترح فقط تعديله قبل القبول.',
    "Both parties must accept this version first.": "يلزم قبول الطرفين لهذه النسخة أولًا.",
    "Review a proposal with an explicit deadline.": "راجع مقترحًا له موعد انتهاء محدد.",
    "The negotiated terms expired. Obtain a new proposal.": "انتهت صلاحية الشروط المتفق عليها. اطلب مقترحًا جديدًا.",
    "This clause follows the published template and cannot be negotiated.": "هذا البند يتبع النموذج المعتمد ولا يمكن التفاوض عليه.",
    "Choose an explicit future deadline.": "حدد موعد انتهاء واضحًا في المستقبل.",
    "Choose the supported contract template.": "اختر نموذج العقد المدعوم.",
    "This workflow supports monthly accommodation.": "هذا المسار يدعم الإيجار الشهري.",
    "Specify a positive agreed rent.": "حدد قيمة إيجار متفق عليها أكبر من صفر.",
    "Use a supported future rental interval.": "حدد مدة إيجار مدعومة تبدأ في المستقبل.",
    "This field is not a negotiable rental term.": "هذا الحقل ليس من بنود الإيجار القابلة للتفاوض.",
    "Review the affected academic requirements and approvals first.": "راجع المتطلبات الأكاديمية والموافقات المتأثرة أولًا.",
    "Review the current academic requirements first.": "راجع المتطلبات الأكاديمية الحالية أولًا.",
    "Review the changed accommodation and eligibility.": "راجع تغيير الوحدة وشروط الأهلية.",
    "Only an eligible author or counterparty may propose this version.": "يمكن لصاحب المقترح أو الطرف الآخر المؤهل تقديم هذه النسخة فقط.",
    "Review the current negotiation and its deadline.": "راجع حالة التفاوض الحالية وموعد انتهاء الشروط.",
    "Explain why you are withdrawing.": "اكتب سبب العدول عن الشروط.",
    "Continue the existing negotiation.": "تابع سلسلة التفاوض القائمة.",
    "Cannot replace the source application.": "لا يمكن استبدال طلب الاهتمام المرتبط بالتفاوض.",
    "Choose the current rental workspace.": "اختر مساحة الإيجار الحالية.",

    "This message kind cannot be forwarded.": "لا يمكن تحويل هذا النوع من الرسائل.",
    "Choose each message and conversation only once.": "اختر كل رسالة ومحادثة مرة واحدة فقط.",
    "Refresh the selected conversations before forwarding.": "حدّث المحادثات المختارة قبل تحويل الرسائل.",
    "A selected message is unavailable.": "إحدى الرسائل المختارة لم تعد متاحة.",
    "Poll options must be different.": "يجب أن تكون اختيارات التصويت مختلفة.",
    "Polls are available in group chats only.": "التصويت متاح داخل محادثات الجروبات فقط.",
    "This message is not a poll.": "هذه الرسالة ليست تصويتًا.",
    "Only the poll creator or group administrator can close it.": "يمكن لمنشئ التصويت أو مسؤول المجموعة فقط إنهاؤه.",
    "This poll is closed.": "انتهى هذا التصويت.",
    "Choose valid poll options.": "اختر إجابات صالحة لهذا التصويت.",
    "Only group administrators can pin messages.": "يمكن لمسؤولي المجموعة فقط تثبيت الرسائل.",
    "Unpin a message before pinning another one.": "ألغِ تثبيت رسالة قبل تثبيت رسالة أخرى. الحد الأقصى ٣ رسائل.",
    "Only the sender can view message reading details.": "يمكن لمرسل الرسالة فقط الاطلاع على تفاصيل قراءتها.",
    "This saved reply is unavailable.": "الرد المحفوظ غير متاح.",
    "This saved reply was deleted. Create a new reply.": "تم حذف الرد المحفوظ. أنشئ ردًا جديدًا.",
    "This saved reply changed. Reload it before editing.": "تم تعديل الرد المحفوظ. حدّثه قبل إجراء تعديل جديد.",
    "You can save up to 50 quick replies.": "يمكنك حفظ ٥٠ ردًا سريعًا بحد أقصى.",
    "Only poll messages may carry a poll.": "يمكن إرفاق تصويت برسائل التصويت فقط.",
    "Polls cannot include attachments.": "لا يمكن إضافة مرفقات إلى التصويت.",

    "Choose another conversation.": "اختر محادثة أخرى لتحويل الرسالة إليها.",
    "System messages cannot be forwarded.": "لا يمكن تحويل رسائل النظام.",
    "Choose a member from the mention list.": "اختر العضو من قائمة المنشن.",
    "A message can mention up to 20 members.": "يمكنك الإشارة إلى 20 عضوًا بحد أقصى في الرسالة.",
    "Mentions are available in group conversations only.": "المنشن متاح داخل محادثات الجروبات فقط.",
    "A mentioned member is no longer in this conversation.": "أحد الأعضاء المشار إليهم لم يعد في المحادثة. حدّث قائمة الأعضاء واختر من جديد.",
    "A mentioned member changed. Choose them again from the list.": "تغيّر اسم أحد الأعضاء المشار إليهم. اختره مجددًا من القائمة.",
    "Choose a single emoji.": "اختر إيموجي واحدًا للتفاعل مع الرسالة.",
    "The selected property is unavailable.": "العقار أو الوحدة المختارة لم تعد متاحة. راجع عرضك أو قدّم عرضًا بديلًا.",
    "The selected accommodation or terms changed.": "تغيّرت الوحدة المختارة أو شروطها. قدّم عرضًا جديدًا بالشروط الحالية.",
    "Review the changed source housing response.": "تغيّر طلب السكن أو العرض المرتبط به. راجع التفاصيل وقدّم عرضًا مناسبًا للطلب الحالي.",
    "Review the offer and continue with a viewing or group application.": "راجع العرض وتابع من طلب المعاينة أو إجراءات المجموعة.",
    'The property type does not match the request.': 'نوع العقار لا يطابق المطلوب. راجع نوع العقار في تفاصيل طلب السكن، بالإضافة إلى نوع الوحدة المختارة.',
    'The furnishing requirement is not met.': 'حالة تأثيث العقار لا تطابق طلب السكن.',
    'The requested amenities are not available.': 'العقار لا يوفر كل المميزات المطلوبة في طلب السكن.',
    'The accommodation cannot hold the requested party.': 'سعة الوحدة أقل من عدد الأشخاص المطلوب في طلب السكن.',
    'The offer must use the requested price period.': 'دورية سعر العرض لا تطابق الدورية المطلوبة في طلب السكن.',
    'The rent is outside the requested budget.': 'سعر الإيجار خارج حدود الميزانية المطلوبة في طلب السكن.',
    'Only an eligible owner can respond to a published request.': 'يمكن للمالك المؤهل فقط إرسال عرض على طلب سكن منشور.',

    "The selected property is unavailable. Refresh and choose another property.": "العقار المختار لم يعد متاحًا. حدّث قائمة عقاراتك واختر عقارًا آخر.",
    "This property must be published and its ownership verified before it can be offered.": "يجب اعتماد نشر العقار وتوثيق ملكيته قبل إرسال عرض سكن به.",
    "The accommodation type must match the housing request.": "نوع السكن المختار يجب أن يطابق النوع المطلوب في طلب السكن.",
    "This email is unavailable.": "البريد الإلكتروني غير متاح.",
    "Upload the identity image itself.": "ارفع صورة مستند الهوية نفسها.",
    "Upload a valid supported image.": "ارفع صورة سليمة بإحدى الصيغ المدعومة.",
    "Identity images must not exceed 10 MiB.": "يجب ألا يتجاوز حجم صورة الهوية 10 ميجابايت.",
    "Invalid base64 image data.": "بيانات الصورة غير صالحة.",
    "Protected identity evidence is unavailable.": "مستند الهوية المحمي غير متاح.",
    "Upload confirmation is pending. Check the original upload before retrying.": "لم يصل تأكيد الرفع بعد. تحقق من حالة الرفع قبل إعادة المحاولة.",
    "Only the current owner can upload listing media.": "يمكن للمالك الحالي فقط رفع صور الإعلان.",
    "Upload authority changed. Review the property.": "تغيرت صلاحية الرفع. راجع العقار.",
    "Identity verification is required for recoverable image uploads.": "وثق هويتك لرفع الصور مع إمكانية استعادة حالة الرفع.",
    "A property cannot have more than 25 images.": "لا يمكن إضافة أكثر من 25 صورة للعقار.",
    "Image uploaded successfully.": "تم رفع الصورة بنجاح.",
    "Supply every current image exactly once.": "حدد جميع الصور الحالية مرة واحدة لكل صورة.",
    "The first image must be the cover.": "يجب أن تكون الصورة الأولى هي صورة الغلاف.",
    "Property photos changed. Reload before reordering.": "تغيرت صور العقار. أعد تحميلها قبل تغيير الترتيب.",
    "Search text must not exceed 250 characters.": "يجب ألا يزيد نص البحث عن 250 حرفًا.",

    # * Generic response messages
    "Created successfully.": "تم الإنشاء بنجاح.",
    "Updated successfully.": "تم التحديث بنجاح.",
    "Deleted successfully.": "تم الحذف بنجاح.",
    "Operation successful.": "تمت العملية بنجاح.",
    "An error occurred.": "حدث خطأ ما.",
    "Invalid token": "رمز غير صالح.",
    "Unauthorized": "غير مصرح.",
    "Not found.": "غير موجود.",
    "Authentication credentials were not provided.": "لم يتم تزويد بيانات الدخول.",
    "You do not have permission to perform this action.": "ليس لديك صلاحية للقيام بهذا الإجراء.",
    # * Auth & Users
    "Logged in Successfully": "تم تسجيل الدخول بنجاح.",
    "Logged in successfully.": "تم تسجيل الدخول بنجاح.",
    "Registration successful. A verification code has been sent to your email.": (
        "تم إنشاء الحساب بنجاح. تم إرسال رمز التحقق إلى بريدك الإلكتروني."
    ),
    "Email verified successfully.": "تم تأكيد البريد الإلكتروني بنجاح.",
    "A new verification code has been sent to your email.": (
        "تم إرسال رمز تحقق جديد إلى بريدك الإلكتروني."
    ),
    "Password changed successfully.": "تم تغيير كلمة المرور بنجاح.",
    "Password reset email sent.": "تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.",
    "Password has been reset successfully.": "تمت إعادة تعيين كلمة المرور بنجاح.",
    "Current password is incorrect.": "كلمة المرور الحالية غير صحيحة.",
    "User with this email does not exist.": "لا يوجد مستخدم مسجل بهذا البريد الإلكتروني.",
    "Invalid credentials": "بيانات الدخول غير صحيحة.",
    "Invalid credentials.": "بيانات الدخول غير صحيحة.",
    "Invalid verification code.": "رمز التحقق غير صالح.",
    "Verification code has expired. Please request a new one.": (
        "انتهت صلاحية رمز التحقق. يرجى طلب رمز جديد."
    ),
    "Email is already verified.": "هذا البريد الإلكتروني تم تأكيده بالفعل.",
    "This email is already verified.": "هذا البريد الإلكتروني تم تأكيده بالفعل.",
    "Email is required.": "البريد الإلكتروني مطلوب.",
    "Verification code is required.": "رمز التحقق مطلوب.",
    "User must have a valid email address.": "يجب إدخال عنوان بريد إلكتروني صالح.",
    "Enter a valid email address.": "أدخل عنوان بريد إلكتروني صالح.",
    "User account deleted successfully.": "تم حذف الحساب بنجاح.",
    # * Properties & Reviews
    "Property changes submitted for review.": "تم إرسال تعديلات العقار للمراجعة.",
    "Property created successfully.": "تم إنشاء العقار بنجاح.",
    "Property deleted successfully.": "تم حذف العقار بنجاح.",
    "Image uploaded successfully.": "تم رفع الصورة بنجاح.",
    "Images uploaded successfully.": "تم رفع الصور بنجاح.",
    "Video uploaded successfully.": "تم رفع الفيديو بنجاح.",
    "Video deleted successfully.": "تم حذف الفيديو بنجاح.",
    "Ownership proof uploaded successfully.": "تم رفع إثبات الملكية بنجاح.",
    "Ownership proof deleted successfully.": "تم حذف إثبات الملكية بنجاح.",
    "Property added to favorites.": "تمت إضافة العقار إلى المفضلة.",
    "Property removed from favorites.": "تم حذف العقار من المفضلة.",
    "Property saved successfully.": "تم حفظ العقار بنجاح.",
    "Property unsaved successfully.": "تم إلغاء حفظ العقار بنجاح.",
    # * Visits
    "Visit request submitted successfully.": "تم تقديم طلب الزيارة بنجاح.",
    "Availability saved successfully.": "تم حفظ المواعيد المتاحة بنجاح.",
    "Visit canceled successfully.": "تم إلغاء الزيارة بنجاح.",
    "Visit review submitted successfully.": "تم تقديم تقييم الزيارة بنجاح.",
    "Visit request accepted successfully.": "تم قبول طلب الزيارة بنجاح.",
    "Visit request rejected successfully.": "تم رفض طلب الزيارة بنجاح.",
    # * Notifications & Devices
    "Device token unregistered successfully.": "تم إلغاء تسجيل الجهاز بنجاح.",
    "Device token registered successfully.": "تم تسجيل الجهاز بنجاح.",
    # * Support
    "Support ticket created successfully.": "تم إنشاء تذكرة الدعم بنجاح.",
    "Support reply sent successfully.": "تم إرسال الرد بنجاح.",
    # * Validation errors
    "This field is required.": "هذا الحقل مطلوب.",
    "This field may not be blank.": "لا يمكن ترك هذا الحقل فارغاً.",
    "This field may not be null.": "لا يمكن أن تكون قيمة هذا الحقل فارغة.",
    "Ensure this field has at least 8 characters.": "يجب أن يحتوي هذا الحقل على 8 أحرف على الأقل.",
    "Passwords do not match.": "كلمتا المرور غير متطابقتين.",
}

AR_TO_EN_MESSAGES = {
    # * Arabic success / error strings mapped to English
    "تم الإنشاء بنجاح.": "Created successfully.",
    "تم التحديث بنجاح.": "Updated successfully.",
    "تم الحذف بنجاح.": "Deleted successfully.",
    "تمت العملية بنجاح.": "Operation successful.",
    "حدث خطأ ما.": "An error occurred.",
    "تم تغيير كلمة المرور بنجاح": "Password changed successfully.",
    "تم تغيير كلمة المرور بنجاح.": "Password changed successfully.",
    "لا يمكن تغيير كلمة المرور لحساب تم تسجيله بواسطة وسائل التواصل الاجتماعي.": (
        "You cannot change the password for an account registered via social login."
    ),
    "تم رفض طلب الزيارة بنجاح.": "Visit request rejected successfully.",
    "تم قبول طلب الزيارة بنجاح.": "Visit request accepted successfully.",
    "هذا المستأجر لم يوثق هويته بعد": "This tenant has not verified their identity yet.",
}

# Reverse-populate missing reverse mappings
from .advanced_housing_translations import MESSAGES as ADVANCED_MESSAGES
from .advanced_housing_translations import FIELD_LABELS as ADVANCED_FIELD_LABELS
from .billing_translations import MESSAGES as BILLING_MESSAGES
from .company_translations import MESSAGES as COMPANY_MESSAGES
from .company_translations import FIELD_LABELS as COMPANY_FIELD_LABELS

from .shared_housing_translations import MESSAGES as SHARED_HOUSING_MESSAGES

EN_TO_AR_MESSAGES.update(SHARED_HOUSING_MESSAGES)
EN_TO_AR_MESSAGES.update(ADVANCED_MESSAGES)
EN_TO_AR_MESSAGES.update(BILLING_MESSAGES)
EN_TO_AR_MESSAGES.update(COMPANY_MESSAGES)
for en_msg, ar_msg in EN_TO_AR_MESSAGES.items():
    if ar_msg not in AR_TO_EN_MESSAGES:
        AR_TO_EN_MESSAGES[ar_msg] = en_msg

FIELD_LABELS_AR = {
    "Email": "البريد الإلكتروني",
    "Password": "كلمة المرور",
    "Current Password": "كلمة المرور الحالية",
    "New Password": "كلمة المرور الجديدة",
    "Re New Password": "تأكيد كلمة المرور الجديدة",
    "Otp": "رمز التحقق",
    "Phone Number": "رقم الهاتف",
    "First Name": "الاسم الأول",
    "Last Name": "اسم العائلة",
    "Title": "العنوان",
    "Description": "الوصف",
    "Price": "السعر",
    "Property Type": "نوع العقار",
    "Governorate": "المحافظة",
    "City": "المدينة",
    "District": "الحي",
    "Street": "الشارع",
    "Bedrooms": "غرف النوم",
    "Bathrooms": "الحمامات",
    "Area": "المساحة",
    "Floor": "الطابق",
    "Rental Period": "مدة الإيجار",
    "Suitable For": "مناسب لـ",
    "Name": "الاسم",
    "Subject": "الموضوع",
    "Message": "الرسالة",
    "Category": "الفئة",
    "Note": "الملاحظة",
}

FIELD_LABELS_AR.update(COMPANY_FIELD_LABELS)
FIELD_LABELS_AR.update(ADVANCED_FIELD_LABELS)

# Tag translation mappings for Property cards
TAG_TRANSLATIONS = {
    # Suitable for
    "عائلات": {"en": "Families", "ar": "عائلات"},
    "أعزاب": {"en": "Singles", "ar": "أعزاب"},
    "طلاب": {"en": "Students", "ar": "طلاب"},
    "طالبات فقط": {"en": "Female Students Only", "ar": "طالبات فقط"},
    # Smoking
    "ممنوع التدخين": {"en": "No Smoking", "ar": "ممنوع التدخين"},
    "مسموح بالتدخين": {"en": "Smoking Allowed", "ar": "مسموح بالتدخين"},
    # Amenities
    "أسانسير": {"en": "Elevator", "ar": "أسانسير"},
    "واي فاي": {"en": "WiFi", "ar": "واي فاي"},
    "تكييف": {"en": "Air Conditioning", "ar": "تكييف"},
    "أمن": {"en": "Security", "ar": "أمن"},
    "بلكونة": {"en": "Balcony", "ar": "بلكونة"},
    "جراج": {"en": "Garage", "ar": "جراج"},
    "قريب من المترو": {"en": "Near Metro", "ar": "قريب من المترو"},
    "غاز طبيعي": {"en": "Natural Gas", "ar": "غاز طبيعي"},
}

CHOICE_TRANSLATIONS = {
    # Property status
    "verified": {"en": "Verified", "ar": "موثق"},
    "under_review": {"en": "Under Review", "ar": "قيد المراجعة"},
    "needs_revision": {"en": "Needs Revision", "ar": "يحتاج مراجعة"},
    "hidden": {"en": "Hidden", "ar": "مخفي"},
    # Price period
    "daily": {"en": "Daily", "ar": "يومي"},
    "weekly": {"en": "Weekly", "ar": "أسبوعي"},
    "monthly": {"en": "Monthly", "ar": "شهري"},
    "yearly": {"en": "Yearly", "ar": "سنوي"},
    # Suitable for
    "families": {"en": "Families", "ar": "عائلات"},
    "singles": {"en": "Singles", "ar": "أعزاب"},
    "students": {"en": "Students", "ar": "طلاب"},
    "female_students": {"en": "Female Students Only", "ar": "طالبات فقط"},
    "all": {"en": "All", "ar": "الكل"},
    # Visit status
    "pending": {"en": "Pending", "ar": "قيد الانتظار"},
    "confirmed": {"en": "Confirmed", "ar": "مؤكد"},
    "canceled": {"en": "Canceled", "ar": "ملغي"},
    "rejected": {"en": "Rejected", "ar": "مرفوض"},
}
