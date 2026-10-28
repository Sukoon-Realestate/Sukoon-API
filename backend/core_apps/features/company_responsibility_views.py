from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .company_views import company_api, mutate, page
from .company_tenancy_serializers import command_body
from .models import CompanyTenancy
from .services.company.access import company_for
from .services.company import responsibility_management as management


@company_api(["GET"])
def collection(request, company_id):
    company = company_for(request.user, company_id, "admin")
    query = CompanyTenancy.objects.filter(lease__renter_company=company).order_by(
        "created_at", "id"
    )
    return page(request, query, lambda item: management.payload(item, request.user))


@company_api(["GET"])
def detail(request, company_id, tenancy_id):
    item = management.get(request.user, company_id, tenancy_id)
    return Response(management.payload(item, request.user, choices=True))


@company_api(["POST"])
def action(request, company_id, tenancy_id, action):
    if action not in {"replace_authority", "respond_change"}:
        raise ValidationError("Choose an administrative responsibility action.")
    data = command_body(action, request.data)

    def authorize():
        item = management.get(request.user, company_id, tenancy_id, lock=True)
        if action == "respond_change":
            management.authorize_decision(item, request.user, data)
        return item

    return mutate(
        request,
        "company.responsibility." + action,
        authorize,
        lambda item: management.execute(item, request.user, action, data),
        lambda item: {"id": str(item.id), "revision": item.revision},
    )
