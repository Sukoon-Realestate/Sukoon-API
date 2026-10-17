"""Versioned rating policy and server-owned schemas. Never infer scores."""

import re
import unicodedata
from django.conf import settings
from django.utils.translation import get_language
from rest_framework.exceptions import APIException, NotFound

POLICY = {
    "version": "rating-v1",
    "schema_version": "rating-criteria-v1",
    "viewing_window_days": 7,
    "tenancy_window_days": 30,
    "co_living_window_days": 30,
    "co_living_min_nights": 7,
    "comment_max_length": 1500,
    "reply_max_length": 1000,
    "appeal_window_days": 14,
    "grant_default_days": 7,
    "grant_max_days": 30,
}
CRITERIA = {
    "property_visit": [
        "listing_accuracy",
        "cleanliness_at_visit",
        "information_clarity",
        "viewing_interaction",
    ],
    "property_stay": [
        "listing_accuracy",
        "cleanliness_at_move_in",
        "equipment_condition",
        "utilities",
        "shared_spaces",
        "quietness",
    ],
    "person_landlord": [
        "communication",
        "agreed_terms",
        "maintenance_response",
        "handover_cooperation",
        "coordination",
    ],
    "person_tenant": [
        "communication",
        "property_care",
        "agreed_house_rules",
        "handover_cooperation",
        "own_obligations",
    ],
    "person_housemate": [
        "shared_cleanliness",
        "quiet_and_privacy",
        "communication",
        "shared_agreements",
    ],
    "organization_renter": [
        "communication",
        "coordination",
        "company_obligations",
        "handover_cooperation",
        "issue_resolution",
    ],
    "organization_landlord": [
        "communication",
        "agreed_terms",
        "maintenance_response",
        "handover_cooperation",
        "coordination",
    ],
}
LABELS = {
    "property_visit": ("Viewing experience", "تجربة المعاينة"),
    "property_stay": ("Stay experience", "تجربة الإقامة"),
    "person_landlord": ("Landlord", "المالك"),
    "person_tenant": ("Tenant", "المستأجر"),
    "person_housemate": ("Housemate", "زميل السكن"),
    "organization_renter": ("Renting company", "الشركة المستأجرة"),
    "organization_landlord": ("Letting company", "الشركة المؤجرة"),
    "listing_accuracy": ("Listing accuracy", "مطابقة الإعلان"),
    "cleanliness_at_visit": ("Cleanliness during viewing", "النظافة أثناء المعاينة"),
    "information_clarity": ("Clarity of information", "وضوح المعلومات"),
    "viewing_interaction": ("Interaction during viewing", "التعامل أثناء المعاينة"),
    "cleanliness_at_move_in": ("Cleanliness on arrival", "النظافة عند الاستلام"),
    "equipment_condition": ("Equipment condition", "حالة التجهيزات"),
    "utilities": ("Available utilities", "المرافق المتاحة"),
    "shared_spaces": ("Shared spaces", "المساحات المشتركة"),
    "quietness": ("Quietness", "الهدوء"),
    "communication": ("Communication", "التواصل"),
    "agreed_terms": ("Agreed terms", "الالتزام بالشروط المتفق عليها"),
    "maintenance_response": ("Maintenance response", "معالجة الصيانة"),
    "handover_cooperation": ("Handover cooperation", "التعاون في التسليم"),
    "coordination": ("Coordination", "التنسيق"),
    "property_care": ("Care of the home", "العناية بالمسكن"),
    "agreed_house_rules": ("Agreed house rules", "قواعد السكن المتفق عليها"),
    "own_obligations": ("Personal obligations", "الالتزامات الواقعة عليه"),
    "shared_cleanliness": ("Shared cleanliness", "نظافة المساحات المشتركة"),
    "quiet_and_privacy": ("Quiet and privacy", "الهدوء والخصوصية"),
    "shared_agreements": ("Shared agreements", "الاتفاقات المشتركة"),
    "company_obligations": ("Company obligations", "التزامات الشركة"),
    "issue_resolution": ("Issue resolution", "معالجة المشكلات"),
    "clear_communication": ("Clear communication", "تواصل واضح"),
    "as_described": ("As described", "مطابق للوصف"),
}
TAGS = {
    kind: (
        ["as_described"] if kind.startswith("property_") else ["clear_communication"]
    )
    for kind in CRITERIA
}
REPORT_REASONS = [
    "personal_information",
    "abuse_or_threat",
    "discrimination",
    "outside_experience",
    "fake_experience",
    "extortion",
    "prohibited_content",
]
ERRORS = {
    "capability_unavailable": (
        "New reviews are currently unavailable.",
        "إرسال تقييمات جديدة غير متاح حاليًا.",
    ),
    "experience_not_confirmed": (
        "The experience has not been confirmed.",
        "لم يتم إثبات التجربة بعد.",
    ),
    "occupancy_not_ended": (
        "A confirmed end of occupancy is required.",
        "يلزم إثبات انتهاء الإقامة.",
    ),
    "company_lifecycle_unavailable": (
        "Corporate contract and occupancy reviews are not available yet.",
        "تقييم العلاقات والإقامة المؤسسية غير متاح بعد.",
    ),
    "co_living_overlap_insufficient": (
        "Seven confirmed shared nights are required.",
        "يلزم إثبات سبع ليالٍ مشتركة.",
    ),
    "review_window_closed": ("The review window has closed.", "انتهت مهلة التقييم."),
    "review_already_submitted": (
        "This opportunity has already been submitted.",
        "تم إرسال هذه الفرصة بالفعل.",
    ),
    "idempotency_payload_mismatch": (
        "This operation key belongs to different content.",
        "مفتاح العملية مرتبط بمحتوى مختلف.",
    ),
    "revision_conflict": (
        "Refresh the current version before continuing.",
        "حدّث النسخة الحالية قبل المتابعة.",
    ),
    "invalid_review_target": (
        "Select only the available review sections.",
        "اختر أقسام التقييم المتاحة فقط.",
    ),
    "unsupported_criteria": (
        "A rating or criterion is invalid.",
        "قيمة التقييم أو المعيار غير صالحة.",
    ),
    "invalid_review_text": (
        "Use plain text without contact details, markup or links, within the length limit.",
        "استخدم نصًا دون بيانات تواصل أو روابط أو تنسيق، ضمن الحد المسموح.",
    ),
    "self_review_forbidden": ("You cannot review yourself.", "لا يمكنك تقييم نفسك."),
    "review_not_eligible": (
        "This experience is not eligible for review.",
        "هذه التجربة غير مؤهلة للتقييم.",
    ),
    "conflict_of_interest": (
        "An independent reviewer is required.",
        "يلزم مراجع مستقل لهذه الحالة.",
    ),
    "client_update_required": (
        "Update the app to use the final review confirmation flow.",
        "حدّث التطبيق لاستخدام تأكيد إرسال التقييم النهائي.",
    ),
    "grant_expired": ("This sharing permission has expired.", "انتهت صلاحية المشاركة."),
    "grant_revoked": (
        "This sharing permission was revoked.",
        "تم سحب صلاحية المشاركة.",
    ),
}


def label(code):
    pair = LABELS.get(code, (code.replace("_", " "), code.replace("_", " ")))
    return pair[1 if (get_language() or "").startswith("ar") else 0]


ERRORS.update(
    {
        "signed_lease_required": (
            "Choose a lease signed by both original parties.",
            "اختر عقدًا موقعًا من الطرفين الأصليين.",
        ),
        "company_lease_mismatch": (
            "The lease does not match the approved company booking.",
            "العقد لا يطابق حجز الشركة المعتمد.",
        ),
        "company_signing_authority_required": (
            "Current verified company signing authority is required.",
            "يلزم تفويض توقيع شركة موثق وساري.",
        ),
        "invalid_occupancy_date": (
            "Choose an actual occupancy date within the assignment period.",
            "اختر تاريخ إشغال فعليًا ضمن فترة التخصيص.",
        ),
        "occupancy_overlap": (
            "This employee already has an overlapping assignment.",
            "يوجد لهذا الموظف تخصيص متداخل بالفعل.",
        ),
        "review_already_disclosed": (
            "A submitted or disclosed review period cannot be changed.",
            "لا يمكن تغيير فترة تقييم أُرسل أو أصبح مكشوفًا.",
        ),
        "review_already_generated": (
            "This source already has its review window.",
            "لهذا المصدر نافذة تقييم قائمة بالفعل.",
        ),
        "invalid_recovery_evidence": (
            "Provide the incident reference and valid outage interval.",
            "أدخل مرجع العطل وفترته الصحيحة.",
        ),
    }
)


class ReviewError(APIException):
    status_code = 409

    def __init__(self, code, status=409):
        self.status_code = status
        pair = ERRORS.get(code, ERRORS["review_not_eligible"])
        super().__init__(
            pair[1 if (get_language() or "").startswith("ar") else 0], code=code
        )


def require_enabled():
    if not getattr(settings, "REVIEWS_ENABLED", False):
        raise ReviewError("capability_unavailable")


def require_actor(user):
    if not user or not user.is_authenticated or not user.is_active:
        raise NotFound()


def revision(item, value):
    if type(value) is not int or value != item.revision:
        raise ReviewError("revision_conflict")


def keys(body, allowed, required=()):
    if (
        not isinstance(body, dict)
        or set(body) - set(allowed)
        or set(required) - set(body)
    ):
        raise ReviewError("invalid_review_target", 400)


def text_value(value, limit):
    if not isinstance(value, str):
        raise ReviewError("invalid_review_text", 400)
    value = unicodedata.normalize("NFC", value).strip()
    if (
        len(value) > limit
        or re.search(
            r"<[^>]*>|https?://|www\.|\b\S+@\S+\b|(?:\+?\d[\s().-]*){7,}", value, re.I
        )
        or any(unicodedata.category(c) == "Cc" and c not in "\n\t" for c in value)
    ):
        raise ReviewError("invalid_review_text", 400)
    return value


def validate_sections(opportunity, body):
    case = opportunity.case
    keys(
        body,
        [
            "request_key",
            "expected_revision",
            "policy_version",
            "criteria_schema_version",
            "sections",
        ],
        [
            "request_key",
            "expected_revision",
            "policy_version",
            "criteria_schema_version",
            "sections",
        ],
    )
    if (
        body["policy_version"] != case.policy_version
        or body["criteria_schema_version"] != case.criteria_schema_version
    ):
        raise ReviewError("revision_conflict")
    targets = {t["key"]: t for t in opportunity.allowed_targets}
    sections = body["sections"]
    if not isinstance(sections, list) or not 1 <= len(sections) <= len(targets):
        raise ReviewError("invalid_review_target", 400)
    seen, clean = set(), []
    for section in sections:
        keys(
            section,
            ["target_key", "overall_score", "criteria", "comment", "tag_codes"],
            ["target_key", "overall_score"],
        )
        if not isinstance(section["target_key"], str):
            raise ReviewError("invalid_review_target", 400)
        target = targets.get(section["target_key"])
        if target is None or target["key"] in seen:
            raise ReviewError("invalid_review_target", 400)
        seen.add(target["key"])
        score = section["overall_score"]
        if type(score) is not int or not 1 <= score <= 5:
            raise ReviewError("unsupported_criteria", 400)
        criteria = section.get("criteria", {})
        if not isinstance(criteria, dict) or set(criteria) - set(target["criteria"]):
            raise ReviewError("unsupported_criteria", 400)
        if any(
            v is not None and (type(v) is not int or not 1 <= v <= 5)
            for v in criteria.values()
        ):
            raise ReviewError("unsupported_criteria", 400)
        tags = section.get("tag_codes", [])
        if (
            not isinstance(tags, list)
            or len(tags) > 5
            or any(not isinstance(t, str) or t not in target["tag_codes"] for t in tags)
            or len(set(tags)) != len(tags)
        ):
            raise ReviewError("unsupported_criteria", 400)
        clean.append(
            (
                target,
                score,
                criteria,
                text_value(
                    section.get("comment", ""),
                    case.policy_snapshot["comment_max_length"],
                ),
                tags,
            )
        )
    return clean
