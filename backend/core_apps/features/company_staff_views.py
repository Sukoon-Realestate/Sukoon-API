from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .company_views import company_api, page, mutate
from .company_serializers import CommandBody
from .company_staff_serializers import (
    StaffBody,
    StaffBatchBody,
    ActivationPreviewBody,
    ActivationResponseBody,
    ContactProofBody,
    ContactProofVerifyBody,
)
from .company_staff_models import (
    CompanyStaffRecord,
    CompanyStaffBatch,
    CompanyWorkContactProof,
)
from .rental_lifecycle_views.common import validated
from .services.company import staff
from .services.company import contact_proof
from .services.company.access import company_for, member_for
from .services.company.contexts import account_contexts


class ActivationThrottle(UserRateThrottle):
    scope = "company_activation"
    rate = "20/hour"


@company_api(["GET"])
def contexts(request):
    return Response(account_contexts(request.user))


@company_api(["GET", "POST"])
def roster(request, company_id):
    company = company_for(request.user, company_id, "admin")
    if request.method == "GET":
        return page(
            request,
            company.staff_records.select_related("membership").order_by(
                "display_name", "id"
            ),
            staff.staff_payload,
        )
    data = validated(StaffBody, request.data)
    return mutate(
        request,
        "company.staff.create",
        lambda: company_for(request.user, company_id, "admin", lock=True),
        lambda c: staff.create_staff(request.user, c, data),
        staff.staff_payload,
        creating=True,
    )


@company_api(["GET"])
def planning_people(request, company_id):
    company = company_for(request.user, company_id, "coordinate")
    return page(
        request,
        company.staff_records.filter(
            employment_status="active",
            membership__isnull=True,
            proposed_roles__contains=["employee"],
        ).order_by("display_name", "id"),
        lambda person: {
            "id": str(person.id),
            "company_id": str(company.id),
            "revision": person.revision,
            "display_name": person.display_name,
            "employee_code": person.employee_code,
            "access_status": "pending_activation",
            "proposal_revision": person.proposal_revision,
        },
    )


@company_api(["GET", "POST"])
def detail(request, company_id, staff_id):
    if request.method == "GET":
        return Response(
            staff.staff_payload(staff.staff_for(request.user, company_id, staff_id))
        )
    data = validated(StaffBody, request.data)
    return mutate(
        request,
        "company.staff.update",
        lambda: staff.staff_for(request.user, company_id, staff_id, lock=True),
        lambda _: staff.update_pending(request.user, company_id, staff_id, data),
        staff.staff_payload,
    )


@company_api(["POST"], throttles=[ActivationThrottle])
def activation(request, company_id, staff_id, action):
    from rest_framework.exceptions import ValidationError

    if action not in {"activation", "revoke"}:
        raise ValidationError("Unsupported staff action.")
    data = validated(CommandBody, request.data)
    handler = (
        staff.request_activation if action == "activation" else staff.revoke_activation
    )
    return mutate(
        request,
        "company.staff." + action,
        lambda: staff.staff_for(request.user, company_id, staff_id, lock=True),
        lambda _: handler(request.user, company_id, staff_id, data),
        staff.staff_payload,
    )


@company_api(["POST"])
def batch(request, company_id):
    data = validated(StaffBatchBody, request.data)
    return mutate(
        request,
        "company.staff.batch",
        lambda: company_for(request.user, company_id, "admin", lock=True),
        lambda _: staff.create_batch(request.user, company_id, data),
        staff.batch_payload,
    )


@company_api(["GET"])
def batch_detail(request, company_id, batch_id):
    company = company_for(request.user, company_id, "admin")
    item = get_object_or_404(
        CompanyStaffBatch, company=company, id=batch_id, created_by=request.user
    )
    return Response(staff.batch_payload(item))


@company_api(["POST"], throttles=[ActivationThrottle])
def access_preview(request):
    data = validated(ActivationPreviewBody, request.data)
    return Response(staff.preview(request.user, data["token"]))


@company_api(["POST"], throttles=[ActivationThrottle])
def access_response(request, action):
    from rest_framework.exceptions import ValidationError

    if action not in {"accept", "decline"}:
        raise ValidationError("Unsupported activation response.")
    data = validated(ActivationResponseBody, request.data)
    return mutate(
        request,
        "company.access." + action,
        lambda: request.user,
        lambda _: staff.respond(request.user, data, accept=action == "accept"),
        staff.response_payload,
    )


@company_api(["POST"], throttles=[ActivationThrottle])
def request_contact_proof(request):
    data = validated(ContactProofBody, request.data)
    return mutate(
        request,
        "company.access.contact_proof",
        lambda: request.user,
        lambda _: contact_proof.request_proof(request.user, data["token"]),
        contact_proof.payload,
        creating=True,
    )


@company_api(["GET", "POST"], throttles=[ActivationThrottle])
def verify_contact_proof(request, proof_id):
    if request.method == "GET":
        proof = get_object_or_404(
            CompanyWorkContactProof, id=proof_id, user=request.user
        )
        staff.validate_proposal(proof.provisioning)
        return Response(contact_proof.payload(proof))
    data = validated(ContactProofVerifyBody, request.data)
    proof = contact_proof.verify(request.user, proof_id, data["code"])
    # Attempt counting commits before this validation response. Successful
    # retries are idempotent; proof verification never accepts membership.
    if proof is None:
        from rest_framework.exceptions import ValidationError

        raise ValidationError(
            {
                "code": "The code is invalid or expired. Request a new code after the delivery cooldown."
            }
        )
    return Response(contact_proof.payload(proof))
