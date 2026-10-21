from django.conf import settings
from ...company_models import CompanyMembership
from ...student_models import StudentProfile
from .projections import membership_payload


def account_contexts(user):
    contexts = [
        {
            "context_id": f"personal:{user.id}",
            "type": "user",
            "available_workspaces": ["tenant", "owner"],
            "presentation_workspaces": ["individual", "owner", "student", "company"],
            "allowed_actions": [],
        }
    ]
    profile = StudentProfile.objects.filter(user=user).first()
    if profile:
        contexts.append(
            {
                "context_id": f"student:{profile.id}",
                "type": "student",
                "profile_id": str(profile.id),
                "enrollment_status": profile.enrollment_status,
                "allowed_actions": ["edit_student_profile"],
            }
        )
    enabled = bool(getattr(settings, "COMPANY_HOUSING_ENABLED", False))
    for member in (
        CompanyMembership.objects.filter(user=user, is_active=True)
        .select_related("company")
        .order_by("company__name", "id")
    ):
        actions = ["read"]
        if member.is_admin:
            actions += ["manage_people", "manage_approval_route"]
        if member.is_coordinator:
            actions += ["requests", "my_work"]
            if enabled:
                actions += ["create_request"]
        if member.is_approver:
            actions += ["my_work", "assigned_approvals"]
        contexts.append(
            {
                "context_id": f"company:{member.company.id}",
                "type": "company",
                "company_id": str(member.company.id),
                "company_name": member.company.name,
                "membership_id": str(member.id),
                "membership_status": "active",
                "roles": membership_payload(member)["roles"],
                "authorization_revision": member.revision,
                "allowed_actions": actions,
            }
        )
    return {
        "user_id": str(user.id),
        "contexts": contexts,
        "preferred_context_id": contexts[0]["context_id"],
    }
