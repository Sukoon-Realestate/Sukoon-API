from typing import Any, Dict


HELP_CENTER_DATA = {
    "tenant": {
        "ar": {
            "phone": "+201012345678",
            "email": "support@sukoon.com",
            "hours": "يومياً من 9:00 ص إلى 9:00 م",
            "faqs": [
                {
                    "id": "visit-booking",
                    "question": "كيف أحجز زيارة لعقار؟",
                    "answer": "افتح صفحة العقار، ثم اختر موعدًا متاحًا من جدول المواعيد وأرسل طلب الزيارة للمالك.",
                },
                {
                    "id": "contracts-info",
                    "question": "كيف أصل إلى عقود الإيجار الخاصة بي؟",
                    "answer": "يمكنك الوصول إلى جميع عقودك من خلال قسم 'عقودي' في الملف الشخصي مع إمكانية عرض وتحميل المستند.",
                },
                {
                    "id": "report-owner",
                    "question": "كيف أبلغ عن مشكلة مع مالك عقار؟",
                    "answer": "يمكنك إنشاء تذكرة دعم جديدة واختيار تصنيف 'إبلاغ عن مالك' وكتابة تفاصيل المشكلة مع إمكانية إرفاق صور.",
                },
                {
                    "id": "id-verification",
                    "question": "كيف أتحقق من هويتي؟",
                    "answer": "توجه إلى ملخص الحساب واضغط على حالة التحقق من الهوية، ثم ارفع صور بطاقة الهوية الوطنية سارية المفعول.",
                },
                {
                    "id": "cancel-visit",
                    "question": "كيف أقوم بإلغاء طلب زيارة؟",
                    "answer": "من قائمة طلبات الزيارة الخاصة بك، اختر الطلب المطلوب واضغط على خيار إلغاء الزيارة قبل موعدها المحدد.",
                },
            ],
        },
        "en": {
            "phone": "+201012345678",
            "email": "support@sukoon.com",
            "hours": "Daily from 9:00 AM to 9:00 PM",
            "faqs": [
                {
                    "id": "visit-booking",
                    "question": "How do I book a property visit?",
                    "answer": "Open the property page, select an available date and time slot from the schedule, and submit your visit request.",
                },
                {
                    "id": "contracts-info",
                    "question": "How do I access my rental contracts?",
                    "answer": "You can view all your rental contracts in the 'My Contracts' section of your profile, with options to view the document.",
                },
                {
                    "id": "report-owner",
                    "question": "How do I report an issue with an owner?",
                    "answer": "Create a new support ticket and select the 'Report Owner' category, then provide details and optional photo attachments.",
                },
                {
                    "id": "id-verification",
                    "question": "How do I verify my identity?",
                    "answer": "Go to Account Summary, tap Verification Status, and upload clear photos of your valid National ID.",
                },
                {
                    "id": "cancel-visit",
                    "question": "How do I cancel a visit request?",
                    "answer": "From your visit requests list, select the visit and click 'Cancel' before the scheduled appointment.",
                },
            ],
        },
    },
    "owner": {
        "ar": {
            "phone": "+201012345678",
            "email": "support@sukoon.com",
            "hours": "يومياً من 9:00 ص إلى 9:00 م",
            "faqs": [
                {
                    "id": "listing-property",
                    "question": "كيف أقوم بإضافة عقار جديد؟",
                    "answer": "من القائمة الرئيسية، اضغط على 'إضافة عقار' واملأ المواصفات والأسعار وأرفق صوراً واضحة للعقار ليتم مراجعته ونشره.",
                },
                {
                    "id": "visit-requests",
                    "question": "كيف أدير طلبات الزيارة من المستأجرين؟",
                    "answer": "افتح قسم 'طلبات الزيارة' من لوحة التحكم، حيث يمكنك قبول الطلبات المتاحة أو رفضها وتحديد المواعيد المناسبة.",
                },
                {
                    "id": "report-tenant",
                    "question": "كيف أبلغ عن مشكلة مع مستأجر؟",
                    "answer": "يمكنك فتح تذكرة دعم واختيار تصنيف 'إبلاغ عن مستأجر' وكتابة تفاصيل الواقعة ليقوم فريق الدعم بالتحقق منها.",
                },
                {
                    "id": "identity-approval",
                    "question": "كم يستغرق توثيق هوية المالك؟",
                    "answer": "تتم مراجعة وثائق الهوية وإثبات الملكية خلال 24 إلى 48 ساعة عمل من قبل فريق التحقق والمراجعة.",
                },
                {
                    "id": "property-availability",
                    "question": "كيف أحدد أوقات الزيارة المتاحة لعقاراتي؟",
                    "answer": "من خلال تقويم الزيارات الخاص بك، يمكنك تحديد الأيام والساعات المتاحة لاستقبال طلبات المعاينة.",
                },
            ],
        },
        "en": {
            "phone": "+201012345678",
            "email": "support@sukoon.com",
            "hours": "Daily from 9:00 AM to 9:00 PM",
            "faqs": [
                {
                    "id": "listing-property",
                    "question": "How do I add a new property listing?",
                    "answer": "From the main menu, tap 'Add Property', fill in the details, photos, and pricing, then submit for review and publication.",
                },
                {
                    "id": "visit-requests",
                    "question": "How do I manage tenant visit requests?",
                    "answer": "Navigate to 'Visit Requests' on your dashboard to accept or decline incoming requests and confirm appointments.",
                },
                {
                    "id": "report-tenant",
                    "question": "How do I report an issue with a tenant?",
                    "answer": "Open a support ticket with the 'Report Tenant' category and detail the issue so our moderation team can investigate.",
                },
                {
                    "id": "identity-approval",
                    "question": "How long does owner verification take?",
                    "answer": "Identity and property ownership documents are typically verified within 24 to 48 business hours.",
                },
                {
                    "id": "property-availability",
                    "question": "How do I set available visit times?",
                    "answer": "Use your visit calendar to select available time slots and days for property viewings.",
                },
            ],
        },
    },
}


def get_help_center_content(
    workspace: str = "tenant", lang: str = "ar"
) -> Dict[str, Any]:
    """
    Returns role-specific and language-specific help center details and FAQs.
    Defaults to tenant / ar.
    """
    normalized_workspace = "owner" if workspace.lower() == "owner" else "tenant"
    normalized_lang = "en" if lang.lower() == "en" else "ar"

    workspace_data = HELP_CENTER_DATA.get(
        normalized_workspace, HELP_CENTER_DATA["tenant"]
    )
    return workspace_data.get(normalized_lang, workspace_data["ar"])
