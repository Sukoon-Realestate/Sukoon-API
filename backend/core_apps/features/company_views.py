from functools import partial
from .services.company import membership_commands as entry_commands

"""Private company API; selecting a company in Flutter never authorizes access."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from functools import wraps
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    throttle_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from .renderers import FeatureJsonRenderer
from .pagination import FeaturePagination
from .company_models import (
    Company,
    CompanyMembership,
    CompanyHousingRequest,
    PortfolioOffer,
)
from .company_serializers import (
    CompanyBody,
    ContainerBody,
    BatchBody,
    InvitationBody,
    AcceptInvitationBody,
    MembershipBody,
    RequestBody,
    OfferBody,
    SelectionBody,
    ApprovalBody,
    CommandBody,
    AttachUnitBody,
)
from .rental_lifecycle_views.common import validated
from .services.rental_lifecycle.common import command
from .services.company import membership, portfolio, offers, bookings
from .services.company.access import company_for, member_for, request_for
from .services.company.projections import company_payload, membership_payload
from core_apps.properties.models import (
    ResidentialBuilding,
    ResidentialComplex,
    Property,
)


def company_api(methods, throttles=None):
    def decorate(fn):
        if throttles is not None:
            fn = throttle_classes(throttles)(fn)

        @api_view(methods)
        @permission_classes([IsAuthenticated])
        @renderer_classes([FeatureJsonRenderer])
        @wraps(fn)
        def endpoint(request, *args, **kwargs):
            from .services.company.role_routes import authorize as authorize_role

            authorize_role(request, fn)
            try:
                return fn(request, *args, **kwargs)
            except IntegrityError:
                raise ValidationError(
                    "An inventory code or operation identity already exists. Reload and review the current values."
                )

        return endpoint

    return decorate


def page(request, qs, mapper):
    paginator = FeaturePagination()
    return paginator.get_paginated_response(
        [mapper(i) for i in paginator.paginate_queryset(qs, request)]
    )


def mutate(
    request, operation, authorize, execute, mapper, creating=False, account_parties=None
):
    def apply(subject):
        item = execute(subject)
        return item, mapper(item), 201 if creating else 200

    data, status = command(
        user=request.user,
        operation=operation,
        data=request.data,
        authorize=authorize,
        execute=apply,
        account_parties=account_parties,
    )
    return Response(data, status=status)


class CapabilitiesView(FeatureAPIView):
    name = "Capabilities"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "capabilities",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        from .services.company.staff import delivery_ready
        from .providers import fake_provider_available

        # This response contains configuration only, never company/member records.
        # Actor and resource authority are checked by each protected operation.
        available = True
        return Response(
            {
                "available": available,
                "blocking_reasons": [],
                "new_bookings": available
                and bool(getattr(settings, "COMPANY_HOUSING_ENABLED", False)),
                "portfolio_creation": available,
                "staff_provisioning": available,
                "activation_email_delivery": available and delivery_ready(),
                "account_contexts": available,
                "assigned_approvals": available,
                "internal_request_discussions": available,
                "contract_preparation": available,
                "independent_mandates": available,
                "contracting": available,
                "tenancy_servicing": available,
                "provider_mode": "mock" if fake_provider_available() else "unavailable",
                "payments": fake_provider_available(),
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
capabilities = CapabilitiesView.as_view()


class CompaniesView(FeatureAPIView):
    name = "Companies"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "companies",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_views",
            "companies",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        return page(
            request,
            Company.objects.filter(
                memberships__user=request.user, memberships__is_active=True
            ).order_by("name", "id"),
            lambda c: company_payload(c, request.user, discovery_only=True),
        )

    def post(self, request):
        data = validated(CompanyBody, request.data)
        return mutate(
            request,
            "company.create",
            lambda: request.user,
            lambda _: membership.create_company(request.user, data),
            lambda c: company_payload(c, request.user, discovery_only=True),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
companies = CompaniesView.as_view()


class CompanyDetailView(FeatureAPIView):
    name = "Company Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "company_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        return Response(
            company_payload(company_for(request.user, company_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
company_detail = CompanyDetailView.as_view()


class RoleContextsView(FeatureAPIView):
    name = "Role Contexts"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "role_contexts",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        from .services.company.role_context import context_payload

        return Response(
            context_payload(get_object_or_404(Company, id=company_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
role_contexts = RoleContextsView.as_view()


class RoleWorkView(FeatureAPIView):
    name = "Role Work"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "role_work",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        from .services.company.role_work import rows

        company = company_for(request.user, company_id)
        return page(
            request,
            rows(request.user, company, request.query_params.get("section", "tasks")),
            lambda row: row,
        )


# Stable callable import for integrations; URLs use the explicit class.
role_work = RoleWorkView.as_view()


class MembersView(FeatureAPIView):
    name = "Members"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views", "members", boundary="company", capability=None, typed=False
        ),
    }

    def get(self, request, company_id):
        company = company_for(request.user, company_id, "admin")
        return page(
            request,
            company.memberships.select_related("user").order_by("id"),
            membership_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
members = MembersView.as_view()


class MemberActionView(FeatureAPIView):
    name = "Member Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "member_action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id, membership_id):
        data = validated(MembershipBody, request.data)
        return mutate(
            request,
            "company.member.update",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda _: _secured_member_update(request, company_id, membership_id, data),
            membership_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
member_action = MemberActionView.as_view()


class InvitationsView(FeatureAPIView):
    name = "Invitations"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "invitations",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id):
        data = validated(InvitationBody, request.data)
        # The raw token is only returned to the initiating administrator, never sent.
        token = {}

        create = partial(
            entry_commands.invitations_post_create,
            actor=request.user,
            company_id=company_id,
            data=data,
            token=token,
        )

        return mutate(
            request,
            "company.invitation.create",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            create,
            lambda i: {
                "id": str(i.id),
                "revision": 1,
                "token": token["value"],
                "email": i.recipient_email,
                "expires_at": i.expires_at.isoformat(),
            },
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
invitations = InvitationsView.as_view()


class InvitationDetailView(FeatureAPIView):
    name = "Invitation Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "invitation_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, invitation_id):
        from django.utils import timezone
        from .models import IdempotencyRecord
        from .company_models import CompanyInvitation

        invitation = get_object_or_404(
            CompanyInvitation, id=invitation_id, invited_by=request.user
        )
        company_for(request.user, invitation.company.id, "admin")
        # Recover only the initiating admin's already-issued token; never mint a new
        # invitation as a side effect of GET or reveal it after use/revocation/expiry.
        token = ""
        if (
            not invitation.consumed_at
            and not invitation.revoked_at
            and invitation.expires_at > timezone.now()
        ):
            record = IdempotencyRecord.objects.filter(
                user=request.user,
                operation="company.invitation.create",
                result_subject_id=invitation.id,
            ).first()
            if record:
                token = record.response_data.get("resource", {}).get("token", "")
        response = Response(
            {
                "id": str(invitation.id),
                "revision": 1,
                "email": invitation.recipient_email,
                "token": token,
                "expires_at": invitation.expires_at.isoformat(),
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
invitation_detail = InvitationDetailView.as_view()


class AcceptInvitationView(FeatureAPIView):
    name = "Accept Invitation"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "accept_invitation",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        data = validated(AcceptInvitationBody, request.data)
        return mutate(
            request,
            "company.invitation.accept",
            lambda: request.user,
            lambda _: membership.accept_invitation(request.user, data["token"]),
            lambda c: company_payload(c, request.user, discovery_only=True),
        )


# Stable callable import for integrations; URLs use the explicit class.
accept_invitation = AcceptInvitationView.as_view()


class HousingRequestsView(FeatureAPIView):
    name = "Housing Requests"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "housing_requests",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_views",
            "housing_requests",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        company = company_for(request.user, company_id)
        member = member_for(request.user, company)
        from .services.company.role_context import selected

        active_role = selected(request.user, company)
        if not (member.is_coordinator or member.is_approver):
            raise PermissionDenied(
                "Housing requests are visible to coordinators and expense approvers."
            )
        return page(
            request,
            company.housing_requests.filter(
                (
                    Q(coordinator=request.user)
                    if active_role == "coordinator"
                    else Q(items__assigned_approver__user=request.user)
                )
            )
            .distinct()
            .order_by("-created_at", "id"),
            lambda item: bookings.request_payload(item, request.user),
        )

    def post(self, request, company_id):
        company = company_for(request.user, company_id)
        member = member_for(request.user, company)
        from .services.company.role_context import selected

        selected(request.user, company)
        if not (member.is_coordinator or member.is_approver):
            raise PermissionDenied(
                "Housing requests are visible to coordinators and expense approvers."
            )
        data = validated(RequestBody, request.data)
        return mutate(
            request,
            "company.housing_request.create",
            lambda: company_for(request.user, company_id, "coordinate", lock=True),
            lambda c: bookings.save_request(request.user, c, data),
            lambda item: bookings.request_payload(item, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
housing_requests = HousingRequestsView.as_view()


class HousingRequestView(FeatureAPIView):
    name = "Housing Request"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "housing_request",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_views",
            "housing_request",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, request_id):
        item = get_object_or_404(CompanyHousingRequest, id=request_id)
        member = member_for(request.user, item.company)
        from .services.company.role_context import selected

        active_role = selected(request.user, item.company)
        if not (
            (
                active_role in {None, "coordinator"}
                and member.is_coordinator
                and item.coordinator_id == request.user.pk
            )
            or (
                active_role in {None, "approver"}
                and member.is_approver
                and item.items.filter(assigned_approver__user=request.user).exists()
            )
        ):
            raise PermissionDenied("You do not have access to the commercial request.")
        return Response(bookings.request_payload(item, request.user))

    def post(self, request, request_id):
        from .services.company.access import request_account_parties

        data = validated(RequestBody, request.data)
        return mutate(
            request,
            "company.housing_request.update",
            lambda: request_for(request.user, request_id, lock=True),
            lambda _: bookings.update_request(request.user, request_id, data),
            lambda item: bookings.request_payload(item, request.user),
            account_parties=lambda: request_account_parties(request_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
housing_request = HousingRequestView.as_view()


class SelectOfferView(FeatureAPIView):
    name = "Select Offer"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "select_offer",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, request_id):
        from .services.company.access import selection_account_parties

        data = validated(SelectionBody, request.data)
        return mutate(
            request,
            "company.package.create",
            lambda: request_for(request.user, request_id, lock=True),
            lambda _: bookings.select_offer(request.user, request_id, data),
            bookings.item_payload,
            creating=True,
            account_parties=lambda: selection_account_parties(request_id, data),
        )


# Stable callable import for integrations; URLs use the explicit class.
select_offer = SelectOfferView.as_view()


class ItemActionView(FeatureAPIView):
    name = "Item Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "item_action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, item_id, action):
        from .services.company.access import booking_account_parties

        if action not in {"submit", "decide", "hold", "withdraw"}:
            raise ValidationError("Unsupported booking action.")
        data = validated(
            ApprovalBody if action == "decide" else CommandBody, request.data
        )

        authorize = partial(
            entry_commands.item_action_post_authorize,
            action=action,
            actor=request.user,
            item_id=item_id,
        )

        from .services.company.approval_routing import submit

        handler = {
            "submit": submit,
            "decide": bookings.decide,
            "hold": bookings.hold_item,
            "withdraw": bookings.withdraw_item,
        }[action]
        return mutate(
            request,
            "company.package." + action,
            authorize,
            lambda _: handler(request.user, item_id, data),
            bookings.item_payload,
            account_parties=lambda: booking_account_parties(item_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
item_action = ItemActionView.as_view()


class ContainersView(FeatureAPIView):
    name = "Containers"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "containers",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_views",
            "containers",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        kind = request.query_params.get("kind", "building")
        if kind not in {"building", "complex"}:
            raise ValidationError("Choose building or complex.")
        model = ResidentialBuilding if kind == "building" else ResidentialComplex
        qs = model.objects.filter(manager=request.user, archived=False)
        return page(request, qs.order_by("name", "id"), portfolio.container_payload)

    def post(self, request):
        data = validated(ContainerBody, request.data)
        return mutate(
            request,
            "portfolio.container.create",
            lambda: request.user,
            lambda _: portfolio.create_container(request.user, data),
            portfolio.container_payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
containers = ContainersView.as_view()


class ContainerDetailView(FeatureAPIView):
    name = "Container Detail"
    http_method_names = ["get", "patch", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "container_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "patch": ActionPolicy(
            "company_views",
            "container_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, kind, asset_id):
        if kind not in {"building", "complex"}:
            raise ValidationError("Choose building or complex.")
        return Response(
            portfolio.container_payload(
                portfolio.parent_for(request.user, kind, asset_id)
            )
        )

    def patch(self, request, kind, asset_id):
        if kind not in {"building", "complex"}:
            raise ValidationError("Choose building or complex.")
        from .services.company.portfolio_changes import update_container

        data = validated(ContainerBody, request.data)
        return mutate(
            request,
            "portfolio.container.update",
            lambda: portfolio.parent_for(request.user, kind, asset_id),
            lambda _: update_container(request.user, kind, asset_id, data),
            portfolio.container_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
container_detail = ContainerDetailView.as_view()


class AttachUnitView(FeatureAPIView):
    name = "Attach Unit"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "attach_unit",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, kind, asset_id):
        if kind not in {"building", "complex"}:
            raise ValidationError("Choose building or complex.")
        data = validated(AttachUnitBody, request.data)
        return mutate(
            request,
            "portfolio.unit.attach",
            lambda: portfolio.parent_for(request.user, kind, asset_id, lock=True),
            lambda _: portfolio.attach_unit(request.user, kind, asset_id, data),
            portfolio.container_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
attach_unit = AttachUnitView.as_view()


class UnitTemplatesView(FeatureAPIView):
    name = "Unit Templates"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "unit_templates",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        units = Property.objects.filter(owner=request.user, retired_at=None)
        if request.query_params.get("unparented") == "true":
            units = units.filter(building=None, complex=None)
        return page(
            request,
            units.select_related("building", "complex").order_by("title", "id"),
            portfolio.unit_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
unit_templates = UnitTemplatesView.as_view()


class BatchUnitsView(FeatureAPIView):
    name = "Batch Units"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "batch_units",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        from .services.rental_lifecycle.common import require_actor

        require_actor(request.user)
        data = validated(BatchBody, request.data)
        return mutate(
            request,
            "portfolio.batch.submit",
            lambda: request.user,
            lambda _: portfolio.submit_batch(request.user, data),
            lambda batch: portfolio.batch_payload(
                batch, getattr(request, "LANGUAGE_CODE", "en")
            ),
        )


# Stable callable import for integrations; URLs use the explicit class.
batch_units = BatchUnitsView.as_view()


class BatchDetailView(FeatureAPIView):
    name = "Batch Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "batch_detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, batch_id):
        from core_apps.properties.models import PortfolioBatch

        return Response(
            portfolio.batch_payload(
                get_object_or_404(PortfolioBatch, id=batch_id, owner=request.user),
                getattr(request, "LANGUAGE_CODE", "en"),
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
batch_detail = BatchDetailView.as_view()


class PortfolioOffersView(FeatureAPIView):
    name = "Portfolio Offers"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_views",
            "portfolio_offers",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_views",
            "portfolio_offers",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        if request.query_params.get("owner") == "true":
            qs = PortfolioOffer.objects.filter(owner=request.user)
        else:
            company_for(
                request.user, request.query_params.get("company_id"), "coordinate"
            )
            qs = PortfolioOffer.objects.filter(status="published")
        if request.query_params.get("saved_list_id"):
            from .services.company.saved_lists import get_list

            saved = get_list(request.user, request.query_params["saved_list_id"])
            if (
                str(saved.company.id) != request.query_params.get("company_id")
                or saved.archived
            ):
                raise PermissionDenied("Choose an active list from this company.")
            qs = qs.filter(id__in=saved.items.values("portfolio_offer__id"))
        starts = ends = None
        requirement = None
        if request.query_params.get("request_id"):
            requirement = request_for(request.user, request.query_params["request_id"])
            if str(requirement.company.id) != request.query_params.get("company_id"):
                raise PermissionDenied(
                    "The request belongs to another company context."
                )
            starts, ends = requirement.starts_on, requirement.ends_on_exclusive
            from .services.company.viewing_handoff import filter_offers

            qs = filter_offers(qs, requirement)
        if requirement is not None:
            from .services.company.discovery import results

            response = page(
                request, results(qs, requirement, request.query_params), lambda row: row
            )
            response["Cache-Control"] = "private, no-store"
            return response
        return page(
            request,
            qs.order_by("-created_at", "id"),
            lambda o: offers.offer_payload(o, starts_on=starts, ends_on=ends),
        )

    def post(self, request):
        data = validated(OfferBody, request.data)
        return mutate(
            request,
            "portfolio.offer.create",
            lambda: request.user,
            lambda _: offers.create_offer(request.user, data),
            offers.offer_payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
portfolio_offers = PortfolioOffersView.as_view()


class PortfolioOfferActionView(FeatureAPIView):
    name = "Portfolio Offer Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_views",
            "portfolio_offer_action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, offer_id, action):
        if action not in {"publish", "pause"}:
            raise ValidationError("Unsupported offer action.")
        data = validated(CommandBody, request.data)

        authorize = partial(
            entry_commands.portfolio_offer_action_post_authorize,
            actor=request.user,
            offer_id=offer_id,
        )

        execute = partial(
            entry_commands.portfolio_offer_action_post_execute,
            action=action,
            actor=request.user,
            data=data,
        )

        return mutate(
            request,
            "portfolio.offer." + action,
            authorize,
            execute,
            offers.offer_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
portfolio_offer_action = PortfolioOfferActionView.as_view()


def _secured_member_update(request, company_id, membership_id, data):
    from core_apps.users.services.sensitive_actions import consume

    member = CompanyMembership.objects.select_for_update().get(
        id=membership_id, company__id=company_id
    )
    roles = set(data["roles"])
    # Revocations remain available; granting financial/admin authority is sensitive.
    grants = (
        ("approver" in roles and (not member.is_active or not member.is_approver))
        or ("admin" in roles and (not member.is_active or not member.is_admin))
        or (
            (data.get("can_execute_payments", member.can_execute_payments) is True)
            and (not member.is_active or not member.can_execute_payments)
        )
    ) and data["is_active"]
    if grants:
        consume(
            request,
            action="company.member.update",
            resource_id=member.id,
            revision=member.revision,
            payload={"company_id": str(company_id), "command": request.data},
        )
    return membership.update_member(request.user, company_id, membership_id, data)
