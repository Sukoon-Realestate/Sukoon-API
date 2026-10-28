from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .company_contract_models import CompanyMandate
from .company_contract_serializers import (
    MandateBody,
    MandateDecisionBody,
    PreparationBody,
    PreparationResponseBody,
)
from .company_serializers import CommandBody
from .company_views import company_api, mutate, page
from .rental_lifecycle_views.common import validated
from .services.company.access import company_for, member_for
from .services.company import (
    mandates as m,
    contract_preparation as c,
    contract_access as a,
    contract_projection as p,
)


@company_api(["GET", "POST"])
def mandates(request, company_id):
    if request.method == "POST":
        body = validated(MandateBody, request.data)
        return mutate(
            request,
            "company.mandate.propose",
            lambda: company_for(request.user, company_id, "admin", lock=True),
            lambda _: m.propose(request.user, company_id, body),
            lambda item: m.payload(item, request.user),
            creating=True,
        )
    company = company_for(request.user, company_id)
    member = member_for(request.user, company)
    query = (
        CompanyMandate.objects.filter(company=company)
        .select_related("membership__user")
        .order_by("-created_at", "id")
    )
    if not member.is_admin and not member.is_coordinator:
        query = query.filter(membership=member)
    return page(request, query, lambda item: m.payload(item, request.user))


@company_api(["POST"])
def mandate_action(request, mandate_id, action):
    if action not in {"approve", "reject", "revoke"}:
        raise ValidationError("Unsupported mandate action.")
    body = validated(MandateDecisionBody, request.data)
    return mutate(
        request,
        "company.mandate." + action,
        lambda: m.authorize(
            request.user, mandate_id, lock=True, admin=action != "revoke"
        ),
        lambda _: m.decide(request.user, mandate_id, action, body),
        lambda item: m.decision_payload(item, request.user, action),
    )


@company_api(["GET", "POST"])
def preparation(request, item_id):
    if request.method == "GET":
        return Response(p.context(c.booking_for(request.user, item_id), request.user))
    body = validated(PreparationBody, request.data)
    return mutate(
        request,
        "company.contract.prepare",
        lambda: c.booking_for(request.user, item_id, lock=True),
        lambda _: c.prepare(request.user, item_id, body),
        lambda item: p.payload(item, request.user),
        creating=True,
        account_parties=lambda: c.account_parties(item_id, body),
    )


@company_api(["GET"])
def preparations(request):
    query = a.visible(request.user)
    if request.query_params.get("company_id"):
        identity = serializers.UUIDField().run_validation(
            request.query_params["company_id"]
        )
        query = query.filter(booking__request__company__id=identity)
    # Employee-only rows are projected without coworkers or commercial amounts.
    return page(
        request,
        query,
        lambda item: p.payload(a.get(request.user, item.id), request.user),
    )


@company_api(["GET"])
def detail(request, preparation_id):
    return Response(p.payload(a.get(request.user, preparation_id), request.user))


@company_api(["POST"])
def preparation_action(request, preparation_id, action):
    if action not in {"respond", "withdraw", "reserve"}:
        raise ValidationError("Unsupported preparation action.")
    body = validated(
        PreparationResponseBody if action == "respond" else CommandBody, request.data
    )
    handler = {"respond": c.respond, "withdraw": c.withdraw, "reserve": c.reserve}[
        action
    ]
    return mutate(
        request,
        "company.contract." + action,
        lambda: a.get(request.user, preparation_id, lock=True),
        lambda _: handler(request.user, preparation_id, body),
        lambda item: p.payload(item, request.user),
        account_parties=lambda: c.existing_account_parties(preparation_id),
    )
