"""Private company API; selecting a company in Flutter never authorizes access."""

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
    CompanyBookingItem,
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
from .services.rental_lifecycle.common import command, require_revision
from .services.company import membership, portfolio, offers, bookings
from .services.company.access import (
    company_for,
    member_for,
    request_for,
    require_new_business,
)
from .services.company.projections import company_payload, membership_payload
from core_apps.properties.models import (
    ResidentialBuilding,
    ResidentialComplex,
    Property,
)


def company_api(methods, throttles=None, *, recovery_required=True):
    def decorate(fn):
        if throttles is not None:
            fn = throttle_classes(throttles)(fn)

        @api_view(methods)
        @permission_classes([IsAuthenticated])
        @renderer_classes([FeatureJsonRenderer])
        @wraps(fn)
        def endpoint(request, *args, **kwargs):
            from core_apps.common.recovery import require_scope

            if recovery_required:
                require_scope("company_authority")
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


def mutate(request, operation, authorize, execute, mapper, creating=False):
    def apply(subject):
        item = execute(subject)
        return item, mapper(item), 201 if creating else 200

    data, status = command(
        user=request.user,
        operation=operation,
        data=request.data,
        authorize=authorize,
        execute=apply,
    )
    return Response(data, status=status)


@company_api(["GET"], recovery_required=False)
def capabilities(request):
    from core_apps.common.recovery import RecoveryRequired, scope_available
    from .services.company.staff import delivery_ready
    from .providers import fake_provider_available

    # This response contains configuration only, never company/member records.
    # Keep it readable while the authority fence blocks the protected routes.
    available = scope_available("company_authority")
    return Response(
        {
            "available": available,
            "blocking_reasons": (
                [] if available else [str(RecoveryRequired.default_detail)]
            ),
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
            "payments": available
            and fake_provider_available()
            and scope_available("provider_outbound"),
        }
    )


@company_api(["GET", "POST"])
def companies(request):
    if request.method == "GET":
        return page(
            request,
            Company.objects.filter(
                memberships__user=request.user, memberships__is_active=True
            ).order_by("name", "id"),
            lambda c: company_payload(c, request.user),
        )
    data = validated(CompanyBody, request.data)
    return mutate(
        request,
        "company.create",
        lambda: request.user,
        lambda _: membership.create_company(request.user, data),
        lambda c: company_payload(c, request.user),
        creating=True,
    )


@company_api(["GET"])
def company_detail(request, company_id):
    return Response(
        company_payload(company_for(request.user, company_id), request.user)
    )


@company_api(["GET"])
def members(request, company_id):
    company = company_for(request.user, company_id, "admin")
    return page(
        request,
        company.memberships.select_related("user").order_by("id"),
        membership_payload,
    )


@company_api(["POST"])
def member_action(request, company_id, membership_id):
    data = validated(MembershipBody, request.data)
    return mutate(
        request,
        "company.member.update",
        lambda: company_for(request.user, company_id, "admin", lock=True),
        lambda _: _secured_member_update(request, company_id, membership_id, data),
        membership_payload,
    )


@company_api(["POST"])
def invitations(request, company_id):
    data = validated(InvitationBody, request.data)
    # The raw token is only returned to the initiating administrator, never sent.
    token = {}

    def create(_):
        result, token["value"] = membership.invite(
            request.user, company_id, data["email"], data["roles"]
        )
        return result

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


@company_api(["GET"])
def invitation_detail(request, invitation_id):
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


@company_api(["POST"])
def accept_invitation(request):
    data = validated(AcceptInvitationBody, request.data)
    return mutate(
        request,
        "company.invitation.accept",
        lambda: request.user,
        lambda _: membership.accept_invitation(request.user, data["token"]),
        lambda c: company_payload(c, request.user),
    )


@company_api(["GET", "POST"])
def housing_requests(request, company_id):
    company = company_for(request.user, company_id)
    member = member_for(request.user, company)
    if not (member.is_coordinator or member.is_approver):
        raise PermissionDenied(
            "Housing requests are visible to coordinators and expense approvers."
        )
    if request.method == "GET":
        return page(
            request,
            company.housing_requests.filter(
                Q(coordinator=request.user)
                | Q(items__assigned_approver__user=request.user)
            )
            .distinct()
            .order_by("-created_at", "id"),
            lambda item: bookings.request_payload(item, request.user),
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


@company_api(["GET", "POST"])
def housing_request(request, request_id):
    if request.method == "POST":
        data = validated(RequestBody, request.data)
        return mutate(
            request,
            "company.housing_request.update",
            lambda: request_for(request.user, request_id, lock=True),
            lambda _: bookings.update_request(request.user, request_id, data),
            lambda item: bookings.request_payload(item, request.user),
        )
    item = get_object_or_404(CompanyHousingRequest, id=request_id)
    member = member_for(request.user, item.company)
    if not (
        (member.is_coordinator and item.coordinator_id == request.user.pk)
        or (
            member.is_approver
            and item.items.filter(assigned_approver__user=request.user).exists()
        )
    ):
        raise PermissionDenied("You do not have access to the commercial request.")
    return Response(bookings.request_payload(item, request.user))


@company_api(["POST"])
def select_offer(request, request_id):
    data = validated(SelectionBody, request.data)
    return mutate(
        request,
        "company.package.create",
        lambda: request_for(request.user, request_id, lock=True),
        lambda _: bookings.select_offer(request.user, request_id, data),
        bookings.item_payload,
        creating=True,
    )


@company_api(["POST"])
def item_action(request, item_id, action):
    if action not in {"submit", "decide", "hold", "withdraw"}:
        raise ValidationError("Unsupported booking action.")
    data = validated(ApprovalBody if action == "decide" else CommandBody, request.data)

    def authorize():
        item = get_object_or_404(CompanyBookingItem, id=item_id)
        company_for(
            request.user,
            item.request.company.id,
            "approve" if action == "decide" else "coordinate",
            lock=True,
        )
        # The company lock may have waited for a reassignment to commit. Refresh
        # before authorization, including the authorization of receipt replay.
        item.refresh_from_db()
        if action != "decide" and item.request.coordinator_id != request.user.pk:
            raise PermissionDenied(
                "Only the assigned coordinator can manage this request."
            )
        if action == "decide" and (
            not item.assigned_approver_id
            or item.assigned_approver.user_id != request.user.pk
        ):
            raise PermissionDenied(
                "Only the currently assigned approver can decide this package."
            )
        return item

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
    )


@company_api(["GET", "POST"])
def containers(request):
    if request.method == "GET":
        kind = request.query_params.get("kind", "building")
        if kind not in {"building", "complex"}:
            raise ValidationError("Choose building or complex.")
        model = ResidentialBuilding if kind == "building" else ResidentialComplex
        qs = model.objects.filter(manager=request.user, archived=False)
        return page(request, qs.order_by("name", "id"), portfolio.container_payload)
    data = validated(ContainerBody, request.data)
    return mutate(
        request,
        "portfolio.container.create",
        lambda: request.user,
        lambda _: portfolio.create_container(request.user, data),
        portfolio.container_payload,
        creating=True,
    )


@company_api(["GET", "PATCH"])
def container_detail(request, kind, asset_id):
    if kind not in {"building", "complex"}:
        raise ValidationError("Choose building or complex.")
    if request.method == "PATCH":
        from .services.company.portfolio_changes import update_container

        data = validated(ContainerBody, request.data)
        return mutate(
            request,
            "portfolio.container.update",
            lambda: portfolio.parent_for(request.user, kind, asset_id),
            lambda _: update_container(request.user, kind, asset_id, data),
            portfolio.container_payload,
        )
    return Response(
        portfolio.container_payload(portfolio.parent_for(request.user, kind, asset_id))
    )


@company_api(["POST"])
def attach_unit(request, kind, asset_id):
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


@company_api(["GET"])
def unit_templates(request):
    units = Property.objects.filter(owner=request.user, retired_at=None)
    if request.query_params.get("unparented") == "true":
        units = units.filter(building=None, complex=None)
    return page(
        request,
        units.select_related("building", "complex").order_by("title", "id"),
        portfolio.unit_payload,
    )


@company_api(["POST"])
def batch_units(request):
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


@company_api(["GET"])
def batch_detail(request, batch_id):
    from core_apps.properties.models import PortfolioBatch

    return Response(
        portfolio.batch_payload(
            get_object_or_404(PortfolioBatch, id=batch_id, owner=request.user),
            getattr(request, "LANGUAGE_CODE", "en"),
        )
    )


@company_api(["GET", "POST"])
def portfolio_offers(request):
    if request.method == "POST":
        data = validated(OfferBody, request.data)
        return mutate(
            request,
            "portfolio.offer.create",
            lambda: request.user,
            lambda _: offers.create_offer(request.user, data),
            offers.offer_payload,
            creating=True,
        )
    if request.query_params.get("owner") == "true":
        qs = PortfolioOffer.objects.filter(owner=request.user)
    else:
        company = company_for(
            request.user, request.query_params.get("company_id"), "coordinate"
        )
        qs = PortfolioOffer.objects.filter(status="published")
    starts = ends = None
    if request.query_params.get("request_id"):
        requirement = request_for(request.user, request.query_params["request_id"])
        if str(requirement.company.id) != request.query_params.get("company_id"):
            raise PermissionDenied("The request belongs to another company context.")
        starts, ends = requirement.starts_on, requirement.ends_on_exclusive
    return page(
        request,
        qs.order_by("-created_at", "id"),
        lambda o: offers.offer_payload(o, starts_on=starts, ends_on=ends),
    )


@company_api(["POST"])
def portfolio_offer_action(request, offer_id, action):
    if action not in {"publish", "pause"}:
        raise ValidationError("Unsupported offer action.")
    data = validated(CommandBody, request.data)

    def authorize():
        return get_object_or_404(
            PortfolioOffer.objects.select_for_update(), id=offer_id, owner=request.user
        )

    def execute(offer):
        require_revision(offer, data["expected_revision"])
        if action == "publish":
            offers.resolve_scope(offer, lock=True)
        offer.status = "published" if action == "publish" else "paused"
        offer.revision += 1
        offer.save()
        from .services.rental_lifecycle.common import audit

        audit(offer, request.user, "portfolio_offer_" + action)
        return offer

    return mutate(
        request, "portfolio.offer." + action, authorize, execute, offers.offer_payload
    )


def _secured_member_update(request, company_id, membership_id, data):
    from core_apps.features.company_models import CompanyMembership
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
