from functools import partial
from .services.company import responsibility_commands as entry_commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .company_views import mutate, page
from .company_tenancy_serializers import command_body
from .models import CompanyTenancy
from .services.company.access import company_for
from .services.company import responsibility_management as management


class CollectionView(FeatureAPIView):
    name = "Collection"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_responsibility_views",
            "collection",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        company = company_for(request.user, company_id, "admin")
        query = CompanyTenancy.objects.filter(lease__renter_company=company).order_by(
            "created_at", "id"
        )
        return page(request, query, lambda item: management.payload(item, request.user))


# Stable callable import for integrations; URLs use the explicit class.
collection = CollectionView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "company_responsibility_views",
            "detail",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id, tenancy_id):
        item = management.get(request.user, company_id, tenancy_id)
        return Response(management.payload(item, request.user, choices=True))


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()


class ActionView(FeatureAPIView):
    name = "Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "company_responsibility_views",
            "action",
            boundary="company",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, company_id, tenancy_id, action):
        if action not in {"replace_authority", "respond_change"}:
            raise ValidationError("Choose an administrative responsibility action.")
        data = command_body(action, request.data)

        authorize = partial(
            entry_commands.action_post_authorize,
            action=action,
            actor=request.user,
            company_id=company_id,
            data=data,
            tenancy_id=tenancy_id,
        )

        return mutate(
            request,
            "company.responsibility." + action,
            authorize,
            lambda item: management.execute(item, request.user, action, data),
            lambda item: {"id": str(item.id), "revision": item.revision},
        )


# Stable callable import for integrations; URLs use the explicit class.
action = ActionView.as_view()
