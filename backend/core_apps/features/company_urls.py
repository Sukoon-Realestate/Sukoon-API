from django.urls import path
from . import company_views as v
from . import company_admin_views as a

urlpatterns = [
    path("company-capabilities/", v.capabilities),
    path("companies/", v.companies),
    path("company-invitations/accept/", v.accept_invitation),
    path("company-invitations/<uuid:invitation_id>/", v.invitation_detail),
    path("companies/<uuid:company_id>/", v.company_detail),
    path("companies/<uuid:company_id>/members/", v.members),
    path("companies/<uuid:company_id>/occupants/", a.occupants),
    path("companies/<uuid:company_id>/budget/", a.company_budget),
    path(
        "company-housing-requests/<uuid:request_id>/coordinator/",
        a.reassign_coordinator,
    ),
    path("company-authority/<slug:kind>/<uuid:identity>/review/", a.authority_review),
    path("companies/<uuid:company_id>/members/<uuid:membership_id>/", v.member_action),
    path("companies/<uuid:company_id>/invitations/", v.invitations),
    path("companies/<uuid:company_id>/housing-requests/", v.housing_requests),
    path("company-housing-requests/<uuid:request_id>/", v.housing_request),
    path("company-housing-requests/<uuid:request_id>/items/", v.select_offer),
    path("company-booking-items/<uuid:item_id>/<slug:action>/", v.item_action),
    path("residential-assets/", v.containers),
    path("residential-assets/<slug:kind>/<uuid:asset_id>/", v.container_detail),
    path("residential-assets/<slug:kind>/<uuid:asset_id>/attach-unit/", v.attach_unit),
    path("residential-unit-templates/", v.unit_templates),
    path("residential-unit-batches/", v.batch_units),
    path("residential-unit-batches/<uuid:batch_id>/", v.batch_detail),
    path("portfolio-offers/", v.portfolio_offers),
    path("portfolio-offers/<uuid:offer_id>/<slug:action>/", v.portfolio_offer_action),
]
