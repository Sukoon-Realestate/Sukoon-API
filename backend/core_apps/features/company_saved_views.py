from rest_framework import serializers
from rest_framework.response import Response
from .company_views import company_api, page
from .services.rental_lifecycle.common import command
from .company_serializers import CommandBody
from .rental_lifecycle_views.common import validated
from .services.company import saved_lists as service


class CreateBody(CommandBody):
    name = serializers.CharField(max_length=120)


class AddBody(CommandBody):
    property_id = serializers.UUIDField(required=False)
    offer_id = serializers.CharField(max_length=100, required=False)
    portfolio_offer_id = serializers.UUIDField(required=False)


class RemoveBody(CommandBody):
    item_id = serializers.UUIDField()


def mutate(request, operation, authorize, execute, mapper, *, scope, creating=False):
    def apply(subject):
        item = execute(subject)
        return item, mapper(item), 201 if creating else 200

    data, status = command(
        user=request.user,
        operation=operation,
        data={**request.data, "saved_scope": str(scope)},
        authorize=authorize,
        execute=apply,
    )
    return Response(data, status=status)


def private(response):
    response["Cache-Control"] = "private, no-store"
    return response


@company_api(["GET", "POST"])
def collection(request, company_id):
    if request.method == "GET":
        company = service.authorize(request.user, company_id)
        return private(
            page(
                request,
                company.saved_lists.filter(archived=False).order_by(
                    "-created_at", "id"
                ),
                service.payload,
            )
        )
    data = validated(CreateBody, request.data)
    return private(
        mutate(
            request,
            "company.saved.create",
            lambda: service.authorize(request.user, company_id, write=True, lock=True),
            lambda company: service.create(request.user, company, data),
            service.payload,
            scope=company_id,
            creating=True,
        )
    )


@company_api(["GET"])
def detail(request, list_id):
    return private(Response(service.payload(service.get_list(request.user, list_id))))


@company_api(["GET"])
def items(request, list_id):
    item = service.get_list(request.user, list_id)
    return private(
        page(
            request,
            item.items.select_related("property", "portfolio_offer").order_by(
                "-created_at", "id"
            ),
            service.item_payload,
        )
    )


@company_api(["POST"])
def action(request, list_id, action):
    body = {
        "rename": CreateBody,
        "archive": CommandBody,
        "add": AddBody,
        "remove": RemoveBody,
    }[action]
    data = validated(body, request.data)
    return private(
        mutate(
            request,
            "company.saved." + action,
            lambda: service.get_list(request.user, list_id, write=True, lock=True),
            lambda item: service.update(request.user, item, data, action),
            service.payload,
            scope=list_id,
        )
    )
