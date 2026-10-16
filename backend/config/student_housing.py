"""Independent, opt-in student rollout. Optional programs have no live adapter."""

from django.core.exceptions import ImproperlyConfigured

SERVICES = (
    "student_planning",
    "student_verification",
    "student_demand",
    "student_offer_policies",
    "student_study_facts",
    "shared_living",
    "exam_arrangements",
    "student_transitions",
    "rental_summary_sharing",
)
UNAVAILABLE = (
    "conditional_student_booking",
    "student_family_payments",
    "student_ambassadors",
    "student_services",
    "admission_refund_guarantee",
)


def enabled_from_env(value):
    chosen = {item.strip() for item in (value or "").split(",") if item.strip()}
    if not chosen or chosen == {"none"}:
        return []
    if chosen == {"all"}:
        return list(SERVICES)
    if chosen - set(SERVICES):
        raise ImproperlyConfigured(
            "STUDENT_ENABLED_SERVICES contains unsupported capabilities."
        )
    return [item for item in SERVICES if item in chosen]
