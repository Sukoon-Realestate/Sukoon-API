"""Supported product policy choices, not arbitrary executable configuration.

Defaults were selected under the owner's 2026-10-19 research/delegation request.
Publication is explicit, versioned and prospective. Never infer consent from a
timer, reinterpret an accepted contract, or enable a provider from this catalogue.
"""

from rest_framework.exceptions import ValidationError


CATALOG = {
    "D01": {
        "title": ["Response and escalation", "الرد والتصعيد"],
        "description": [
            "Unanswered cases escalate for review. A response target never establishes consent, fault, cancellation or payment.",
            "تُصعّد الحالات دون رد للمراجعة. مهلة الرد لا تعني الموافقة أو إثبات الخطأ أو الإلغاء أو الدفع.",
        ],
        "scope": ["cases.open"],
        "rules": {"case_hours": 72, "urgent_case_hours": 24},
        "bounds": {"case_hours": [1, 168], "urgent_case_hours": [1, 72]},
        "labels": {
            "case_hours": [
                "Regular response target (hours)",
                "مهلة الرد المعتادة بالساعات",
            ],
            "urgent_case_hours": [
                "Urgent response target (hours)",
                "مهلة الرد العاجلة بالساعات",
            ],
        },
        "consumer": "rental_lifecycle.cases.open_system_case; saved response_target and existing escalation worker",
    },
    "D02": {
        "title": ["Cancellation and missing participants", "الإلغاء وغياب الأطراف"],
        "description": [
            (
                'Uncommitted drafts may be withdrawn. Potentially signed changes require '
                'reconciliation and a separate mutually signed release. An initial company '
                'agreement may use that release only before possession, invoices or financial '
                'execution. Nonresponse opens an operational case and never signs for someone '
                'else.'
            ),
            (
                'يمكن سحب المسودات غير الملزمة. التعديلات المحتمل توقيعها تحتاج مراجعة وتسوية '
                'مستقلة بتوقيعات الأطراف. يمكن استخدام هذه التسوية للعقد الأول للشركة فقط قبل '
                'الحيازة أو الفواتير أو التنفيذ المالي. عدم الرد يستدعي حالة متابعة ولا يسمح '
                'بالتوقيع عن الغير.'
            ),
        ],
        "scope": ["company.continuation.release", "company.agreement.release"],
        "legacy_scope": ["company.continuation.release"],
        "rules": {
            "resolution_mode": "mutual_signed_release",
            "nonresponse": "operator_review",
        },
        "choices": {
            "resolution_mode": ["mutual_signed_release"],
            "nonresponse": ["operator_review"],
        },
        "consumer": (
            'company.tenancy_resolution and company.tenancy_initial_recovery; exact original '
            'signatories and independent current mandates; initial release only before possession '
            'or financial execution'
        ),
    },
    "D05": {
        "title": ["Monthly rental periods", "فترات الإيجار الشهرية"],
        "description": [
            "Monthly offers use whole calendar months from the agreed anchor. Short or partial periods need a separately supported price quotation; no daily rate is inferred from the monthly price.",
            "العروض الشهرية تُحسب بأشهر تقويمية كاملة من التاريخ المتفق عليه. الفترات الجزئية تحتاج عرض سعر مدعومًا مستقلًا ولا يُستنتج سعر يومي من السعر الشهري.",
        ],
        "scope": ["company.request.period"],
        "rules": {"period_mode": "whole_calendar_months", "maximum_months": 120},
        "choices": {"period_mode": ["whole_calendar_months"]},
        "bounds": {"maximum_months": [1, 120]},
        "labels": {
            "maximum_months": [
                "Maximum new request duration (months)",
                "أقصى مدة لطلب جديد بالأشهر",
            ]
        },
        "consumer": "company.request_period.validate_request_period; accepted booking periods remain unchanged",
    },
    "D08": {
        "title": ["Deposit custody", "حيازة التأمين"],
        "description": [
            "Platform collection supports only an explicitly disclosed platform-held deposit. Owner-held cash is not charged or represented as money held by Sokoun. Deductions require supported evidence and consent.",
            "التحصيل عبر المنصة يدعم التأمين المعلن بحيازة المنصة فقط. النقد لدى المالك لا يُحصّل أو يُعرض كأموال لدى سكون. الخصومات تحتاج أدلة وموافقات مدعومة.",
        ],
        "scope": ["rental.deposit.custody"],
        "rules": {"collection_holder": "platform", "automatic_forfeiture": False},
        "choices": {"collection_holder": ["platform"], "automatic_forfeiture": [False]},
        "consumer": "canonical rental terms and invoice custody validation; existing accepted custody is retained",
    },
    "D09": {
        "title": ["Corrections after settlement", "التصحيحات بعد التسوية"],
        "description": [
            "Corrections are separate records with an itemized amount, evidence and independent financial review. Late requests open an additional case; elapsed time does not erase a claim. No money is collected merely by opening a case.",
            "التصحيح سجل مستقل بمبلغ مفصل وأدلة ومراجعة مالية مستقلة. الطلب المتأخر يفتح حالة متابعة إضافية دون إسقاط المطالبة بمرور الوقت. فتح الحالة لا يُحصّل أموالًا.",
        ],
        "scope": ["company.settlement.adjustment"],
        "rules": {"late_review_days": 60, "review_mode": "independent_and_all_parties"},
        "bounds": {"late_review_days": [1, 365]},
        "choices": {"review_mode": ["independent_and_all_parties"]},
        "labels": {
            "late_review_days": [
                "Additional late-review target (days)",
                "بدء المراجعة الإضافية للطلبات المتأخرة بالأيام",
            ]
        },
        "consumer": "company.tenancy_adjustments.propose; original settlement, consent and funded capacity retained",
    },
    "D17": {
        "title": ["Reservation limits", "حدود الحجز المؤقت"],
        "description": [
            "New holds use bounded duration, extensions and per-actor concurrency. Each hold retains its accepted rule snapshot. Unknown payment or signature outcomes require reconciliation before release.",
            "للحجوزات الجديدة مدة وتمديدات وعدد متزامن محدود. يحتفظ كل حجز بنسخة قواعده. نتيجة الدفع أو التوقيع المجهولة تحتاج مراجعة قبل تحرير الحجز.",
        ],
        "scope": ["rental.hold.create"],
        "rules": {"hold_minutes": 30, "max_extensions": 1, "max_active_holds": 3},
        "bounds": {
            "hold_minutes": [1, 1440],
            "max_extensions": [0, 3],
            "max_active_holds": [1, 10],
        },
        "labels": {
            "hold_minutes": ["Hold duration (minutes)", "مدة الحجز بالدقائق"],
            "max_extensions": ["Maximum extensions", "أقصى عدد للتمديدات"],
            "max_active_holds": ["Maximum simultaneous holds", "أقصى حجوزات متزامنة"],
        },
        "consumer": "rental_lifecycle.common.lifecycle_policy; ReservationHold.policy_snapshot",
    },
    "D23": {
        "title": ["Notices and discovery", "الإشعارات والمتابعة"],
        "description": [
            "The authenticated inbox and current resource are the durable discovery paths. Push and email delivery can fail. Opening or missing a notification does not supply contractual consent.",
            "صندوق الإشعارات داخل الحساب والسجل الحالي هما مرجع المتابعة. قد يفشل البريد أو التنبيه. فتح الإشعار أو تفويته لا يمثل موافقة تعاقدية.",
        ],
        "scope": ["notifications.disclosure"],
        "rules": {"contractual_consent": "explicit_action", "preview": "generic"},
        "choices": {"contractual_consent": ["explicit_action"], "preview": ["generic"]},
        "consumer": "existing durable notifications and destination authorization; public policy disclosure",
    },
    "D25": {
        "title": ["Operational review and appeal", "المراجعة التشغيلية والاعتراض"],
        "description": [
            "An independent assigned operator reviews evidence and can reassign or reopen a case. Notes cannot overwrite a signature, refund, possession or invoice. A contested legal discharge requires the competent authority outside this automated workflow.",
            "يراجع مسؤول مستقل مكلّف الأدلة ويمكن إعادة إسناد الحالة أو فتحها. الملاحظات لا تغيّر توقيعًا أو استردادًا أو حيازة أو فاتورة. إنهاء التزام قانوني متنازع عليه يحتاج الجهة المختصة خارج هذا المسار الآلي.",
        ],
        "scope": ["cases.request_review"],
        "rules": {"reassessment_hours": 72, "silent_consent": False},
        "bounds": {"reassessment_hours": [1, 168]},
        "choices": {"silent_consent": [False]},
        "labels": {
            "reassessment_hours": [
                "Reassessment target (hours)",
                "مهلة إعادة المراجعة بالساعات",
            ]
        },
        "consumer": "rental_lifecycle.cases.request_review; canonical resolution blockers remain",
    },
    "D26": {
        "title": ["Private export verification", "التحقق لتصدير البيانات الخاصة"],
        "description": [
            "Private export requires fresh verification for the exact actor, session, resource revision and action details. Verified account email or the current staff authenticator is used. Verification never grants access to another party's records or authorizes other sensitive actions.",
            "تصدير البيانات الخاصة يحتاج تحققًا حديثًا مرتبطًا بالحساب والجلسة ومراجعة السجل وتفاصيل العملية نفسها. يُستخدم بريد الحساب المؤكد أو تطبيق التحقق الحالي للموظف. التحقق لا يمنح الوصول لسجلات الغير ولا يجيز عمليات حساسة أخرى.",
        ],
        "scope": ["private.export"],
        "rules": {
            "provider": "core_apps.users.services.assurance.AccountAssuranceProvider",
            "assurance": "email_otp_or_totp",
            "proof_lifetime_seconds": 300,
        },
        "choices": {
            "provider": ["core_apps.users.services.assurance.AccountAssuranceProvider"],
            "assurance": ["email_otp_or_totp"],
        },
        "bounds": {"proof_lifetime_seconds": [1, 300]},
        "labels": {
            "proof_lifetime_seconds": [
                "Maximum verification lifetime (seconds)",
                "أقصى صلاحية للتحقق بالثواني",
            ],
        },
        "consumer": (
            "users.services.sensitive_actions.begin/verify/consume and "
            "rental_phase6_views_parts.lease_reviews.rental_statement_create; "
            "existing party authority, session, security epoch, exact payload and single-use proof remain required"
        ),
    },
    "D29": {
        "title": ["Habitability assessment", "تقييم صلاحية السكن"],
        "description": [
            "An assigned independent assessor reviews the exact physical scope. Clearance needs inspected evidence and does not itself refund rent, end a contract or release occupied inventory.",
            "يراجع مقيم مستقل مكلّف النطاق الفعلي للسكن. رفع القيد يحتاج دليل فحص ولا يرد الإيجار أو ينهي العقد أو يحرر مكانًا مشغولًا تلقائيًا.",
        ],
        "scope": ["habitability.restrict", "habitability.clear", "habitability.reopen"],
        "rules": {"assessor_roles": ["habitability_assessor"]},
        "choices": {"assessor_roles": [["habitability_assessor"]]},
        "consumer": "rental_lifecycle.habitability.authorize_assessment; current independent staff assignment",
    },
}

SOURCES = {
    "D01": "https://www.airbnb.com/help/article/767",
    "D02": "https://www.airbnb.com/help/article/1361",
    "D05": "https://docs.stripe.com/billing/subscriptions/prorations",
    "D08": "https://www.airbnb.com/help/article/767",
    "D09": "https://www.airbnb.com/help/article/767",
    "D17": "https://docs.stripe.com/api/idempotent_requests",
    "D23": "https://www.airbnb.com/help/article/767",
    "D25": "https://cpa.gov.eg/ar-eg/كيف-تتقدم-بشكوى",
    "D26": "Sokoun existing first-party AccountAssuranceProvider and action-bound private.export contract",
    "D29": "Sokoun existing independent habitability assessment and clearance contract",
}


def definition(code):
    if not isinstance(code, str) or code not in CATALOG:
        raise ValidationError(
            {
                "code": "This decision has no configurable executable contract. Provider setup and deferred disaster recovery are separate."
            }
        )
    return CATALOG[code]


def validate_rules(code, rules):
    spec = definition(code)
    if not isinstance(rules, dict) or set(rules) != set(spec["rules"]):
        raise ValidationError({"rules": "Supply exactly the supported rule fields."})
    for key, (minimum, maximum) in spec.get("bounds", {}).items():
        if type(rules[key]) is not int or not minimum <= rules[key] <= maximum:
            raise ValidationError(
                {"rules": {key: f"Use an integer from {minimum} to {maximum}."}}
            )
    for key, choices in spec.get("choices", {}).items():
        if not any(
            type(rules[key]) is type(option) and rules[key] == option
            for option in choices
        ):
            raise ValidationError(
                {
                    "rules": {
                        key: "This behavior is not implemented; a policy value cannot create a new execution path."
                    }
                }
            )
    if code == "D01" and rules["urgent_case_hours"] > rules["case_hours"]:
        raise ValidationError(
            {"rules": "Urgent review cannot have a longer target than regular review."}
        )
    return rules
