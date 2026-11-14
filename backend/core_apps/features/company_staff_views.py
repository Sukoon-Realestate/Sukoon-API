from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .company_views import page, mutate
from .company_serializers import CommandBody
from .company_staff_serializers import (
    StaffBody,
    StaffBatchBody,
    ActivationPreviewBody,
    ActivationResponseBody,
    ContactProofBody,
    ContactProofVerifyBody,
)
from .company_staff_models import CompanyStaffBatch, CompanyWorkContactProof
from .rental_lifecycle_views.common import validated
from .services.company import staff
from .services.company import contact_proof
from .services.company.access import company_for
from .services.company.contexts import account_contexts


class ActivationThrottle(UserRateThrottle):
    scope = "company_activation"
    rate = "20/hour"


class ContextsView(FeatureAPIView):
    name = "Contexts"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_staff_views",
            "contexts",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        return Response(account_contexts(request.user))


# Stable callable import for integrations; URLs use the explicit class.
contexts = ContextsView.as_view()


class RosterView(FeatureAPIView):
    name = "Roster"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_staff_views",
            "roster",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_staff_views",
            "roster",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        company = company_for(request.user, company_id, "admin")
        return page(
            request,
            company.staff_records.select_related("membership").order_by(
                "display_name", "id"
            ),
            staff.staff_payload,
        )

    def post(self, request, company_id):
        company_for(request.user, company_id, "admin")
        data = validated(StaffBody, request.data)
        return mutate(
            request,
            "company.staff.create",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda c: staff.create_staff(request.user, c, data),
            staff.staff_payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
roster = RosterView.as_view()


class PlanningPeopleView(FeatureAPIView):
    name = "Planning People"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_staff_views",
            "planning_people",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
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


# Stable callable import for integrations; URLs use the explicit class.
planning_people = PlanningPeopleView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_staff_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_staff_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id, staff_id):
        return Response(
            staff.staff_payload(staff.staff_for(request.user, company_id, staff_id))
        )

    def post(self, request, company_id, staff_id):
        data = validated(StaffBody, request.data)
        return mutate(
            request,
            "company.staff.update",
            lambda: staff.staff_for(request.user, company_id, staff_id, lock=True),
            lambda _: staff.update_pending(request.user, company_id, staff_id, data),
            staff.staff_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()


class ActivationView(FeatureAPIView):
    name = "Activation"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [ActivationThrottle]
    action_policies = {
        "post": ActionPolicy(
            "company_staff_views",
            "activation",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id, staff_id, action):
        from rest_framework.exceptions import ValidationError

        if action not in {"activation", "revoke"}:
            raise ValidationError("Unsupported staff action.")
        data = validated(CommandBody, request.data)
        handler = (
            staff.request_activation
            if action == "activation"
            else staff.revoke_activation
        )
        return mutate(
            request,
            "company.staff." + action,
            lambda: staff.staff_for(request.user, company_id, staff_id, lock=True),
            lambda _: handler(request.user, company_id, staff_id, data),
            staff.staff_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
activation = ActivationView.as_view()


class BatchView(FeatureAPIView):
    name = "Batch"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_staff_views",
            "batch",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id):
        data = validated(StaffBatchBody, request.data)
        return mutate(
            request,
            "company.staff.batch",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda _: staff.create_batch(request.user, company_id, data),
            staff.batch_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
batch = BatchView.as_view()


class BatchDetailView(FeatureAPIView):
    name = "Batch Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_staff_views",
            "batch_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id, batch_id):
        company = company_for(request.user, company_id, "admin")
        item = get_object_or_404(
            CompanyStaffBatch, company=company, id=batch_id, created_by=request.user
        )
        return Response(staff.batch_payload(item))


# Stable callable import for integrations; URLs use the explicit class.
batch_detail = BatchDetailView.as_view()


class AccessPreviewView(FeatureAPIView):
    name = "Access Preview"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [ActivationThrottle]
    action_policies = {
        "post": ActionPolicy(
            "company_staff_views",
            "access_preview",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        data = validated(ActivationPreviewBody, request.data)
        return Response(staff.preview(request.user, data["token"]))


# Stable callable import for integrations; URLs use the explicit class.
access_preview = AccessPreviewView.as_view()


class AccessResponseView(FeatureAPIView):
    name = "Access Response"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [ActivationThrottle]
    action_policies = {
        "post": ActionPolicy(
            "company_staff_views",
            "access_response",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, action):
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


# Stable callable import for integrations; URLs use the explicit class.
access_response = AccessResponseView.as_view()


class RequestContactProofView(FeatureAPIView):
    name = "Request Contact Proof"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [ActivationThrottle]
    action_policies = {
        "post": ActionPolicy(
            "company_staff_views",
            "request_contact_proof",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        data = validated(ContactProofBody, request.data)
        return mutate(
            request,
            "company.access.contact_proof",
            lambda: request.user,
            lambda _: contact_proof.request_proof(request.user, data["token"]),
            contact_proof.payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
request_contact_proof = RequestContactProofView.as_view()


class VerifyContactProofView(FeatureAPIView):
    name = "Verify Contact Proof"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [ActivationThrottle]
    action_policies = {
        "get": ActionPolicy(
            "company_staff_views",
            "verify_contact_proof",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_staff_views",
            "verify_contact_proof",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, proof_id):
        proof = get_object_or_404(
            CompanyWorkContactProof, id=proof_id, user=request.user
        )
        staff.validate_proposal(proof.provisioning)
        return Response(contact_proof.payload(proof))

    def post(self, request, proof_id):
        data = validated(ContactProofVerifyBody, request.data)
        proof = contact_proof.verify(request.user, proof_id, data["code"])
        if proof is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "code": "The code is invalid or expired. Request a new code after the delivery cooldown."
                }
            )
        return Response(contact_proof.payload(proof))


# Stable callable import for integrations; URLs use the explicit class.
verify_contact_proof = VerifyContactProofView.as_view()
