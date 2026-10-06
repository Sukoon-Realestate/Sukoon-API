from typing import Optional
from django.utils.translation import get_language, gettext as _


# * Bidirectional dictionary of API response messages, error messages, choice labels, and tags
EN_TO_AR_MESSAGES = {
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


def translate_message(message: str, language: Optional[str] = None) -> str:
    """
    Translates an API message between English and Arabic based on the language.
    If language is not provided, defaults to Django's active language.
    """
    if not isinstance(message, str) or not message.strip():
        return message

    lang = (language or get_language() or "en").lower()

    if lang.startswith("ar"):
        # Target: Arabic
        # Check direct match
        trimmed = message.strip()
        if trimmed in EN_TO_AR_MESSAGES:
            return EN_TO_AR_MESSAGES[trimmed]
        # Check without trailing dot or with trailing dot
        if trimmed.endswith(".") and trimmed[:-1] in EN_TO_AR_MESSAGES:
            return EN_TO_AR_MESSAGES[trimmed[:-1]]
        if f"{trimmed}." in EN_TO_AR_MESSAGES:
            return EN_TO_AR_MESSAGES[f"{trimmed}."]
        # Dynamic templates e.g. "Marked 3 notifications as read."
        if trimmed.startswith("Marked ") and " notifications as read" in trimmed:
            import re

            m = re.search(r"\d+", trimmed)
            count = m.group() if m else ""
            return f"تم تحديد {count} إشعارات كمقروءة."
        # Fallback to gettext
        translated = _(trimmed)
        if translated != trimmed:
            return translated
        return message

    else:
        # Target: English
        trimmed = message.strip()
        if trimmed in AR_TO_EN_MESSAGES:
            return AR_TO_EN_MESSAGES[trimmed]
        if trimmed.endswith(".") and trimmed[:-1] in AR_TO_EN_MESSAGES:
            return AR_TO_EN_MESSAGES[trimmed[:-1]]
        if f"{trimmed}." in AR_TO_EN_MESSAGES:
            return AR_TO_EN_MESSAGES[f"{trimmed}."]
        # If it's already English or unknown, return message
        return message


def translate_field_label(label: str, language: Optional[str] = None) -> str:
    """Translates a field label (e.g. Email -> البريد الإلكتروني)."""
    lang = (language or get_language() or "en").lower()
    if lang.startswith("ar"):
        return FIELD_LABELS_AR.get(label, label)
    return label


def translate_tag(tag: str, language: Optional[str] = None) -> str:
    """Translates a tag label (e.g. عائلات <-> Families)."""
    lang = (language or get_language() or "en").lower()
    target_key = "ar" if lang.startswith("ar") else "en"

    # Search in TAG_TRANSLATIONS
    for key, trans in TAG_TRANSLATIONS.items():
        if tag == key or tag == trans.get("en") or tag == trans.get("ar"):
            return trans.get(target_key, tag)

    return tag


def translate_choice(choice: str, language: Optional[str] = None) -> str:
    """Translates a choice code to its localized label."""
    lang = (language or get_language() or "en").lower()
    target_key = "ar" if lang.startswith("ar") else "en"

    if choice in CHOICE_TRANSLATIONS:
        return CHOICE_TRANSLATIONS[choice].get(target_key, choice)

    return choice
