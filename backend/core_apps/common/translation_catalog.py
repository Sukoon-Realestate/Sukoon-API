"""Bilingual message, field and choice catalogs."""

EN_TO_AR_MESSAGES = {
    "Choose a member from the mention list.": "اختر العضو من قائمة المنشن.",
    "A message can mention up to 20 members.": "يمكنك الإشارة إلى 20 عضوًا بحد أقصى في الرسالة.",
    "Mentions are available in group conversations only.": "المنشن متاح داخل محادثات الجروبات فقط.",
    "A mentioned member is no longer in this conversation.": "أحد الأعضاء المشار إليهم لم يعد في المحادثة. حدّث قائمة الأعضاء واختر من جديد.",
    "A mentioned member changed. Choose them again from the list.": "تغيّر اسم أحد الأعضاء المشار إليهم. اختره مجددًا من القائمة.",
    "Choose a single emoji.": "اختر إيموجي واحدًا للتفاعل مع الرسالة.",
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
