from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework import serializers
from rest_framework.response import Response
from .company_views import page
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


class CollectionView(FeatureAPIView):
    name = "Collection"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_saved_views",
            "collection",
            boundary="company",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "company_saved_views",
            "collection",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
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

    def post(self, request, company_id):
        data = validated(CreateBody, request.data)
        return private(
            mutate(
                request,
                "company.saved.create",
                lambda: service.authorize(
                    request.user, company_id, write=True, lock=True
                ),
                lambda company: service.create(request.user, company, data),
                service.payload,
                scope=company_id,
                creating=True,
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
collection = CollectionView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_saved_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, list_id):
        return private(
            Response(service.payload(service.get_list(request.user, list_id)))
        )


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()


class ItemsView(FeatureAPIView):
    name = "Items"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_saved_views",
            "items",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, list_id):
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


# Stable callable import for integrations; URLs use the explicit class.
items = ItemsView.as_view()


class ActionView(FeatureAPIView):
    name = "Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_saved_views",
            "action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, list_id, action):
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


# Stable callable import for integrations; URLs use the explicit class.
action = ActionView.as_view()
