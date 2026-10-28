from django.urls import path
from . import company_rental_value_views as value
from . import company_views as v
from . import company_negotiation_views as terms
from . import company_admin_views as a
from . import company_staff_views as s
from . import company_work_views as w
from . import company_chat_views as c
from . import portfolio_views as p
from . import company_contract_views as contracts
from . import company_tenancy_views as tenancies
from . import company_responsibility_views as responsibilities

from . import company_saved_views as saved
from . import workspace_views

urlpatterns = [
    path(
        "companies/<uuid:company_id>/responsibility-assignments/",
        responsibilities.collection,
    ),
    path(
        "companies/<uuid:company_id>/responsibility-assignments/<uuid:tenancy_id>/",
        responsibilities.detail,
    ),
    path(
        "companies/<uuid:company_id>/responsibility-assignments/<uuid:tenancy_id>/<slug:action>/",
        responsibilities.action,
    ),
    path("companies/<uuid:company_id>/role-work/", v.role_work),
    path("companies/<uuid:company_id>/role-contexts/", v.role_contexts),
    path("company-terms-negotiations/", terms.negotiations),
    path("company-terms-negotiations/<uuid:negotiation_id>/", terms.detail),
    path(
        "company-terms-negotiations/<uuid:negotiation_id>/<slug:action>/", terms.detail
    ),
    path("company-booking-items/<uuid:item_id>/negotiation/", terms.start),
    path("workspace-summary/", workspace_views.summary),
    path("companies/<uuid:company_id>/saved-lists/", saved.collection),
    path("company-saved-lists/<uuid:list_id>/", saved.detail),
    path("company-saved-lists/<uuid:list_id>/items/", saved.items),
    *[
        path(
            "company-saved-lists/<uuid:list_id>/" + action + "/",
            saved.action,
            {"action": action},
        )
        for action in ("rename", "archive", "add", "remove")
    ],
    path("companies/<uuid:company_id>/rental-summary/", value.rental_summary),
    path("companies/<uuid:company_id>/housing-report/", value.housing_report),
    path("company-requirements/", value.catalog),
    path("company-housing-requests/<uuid:request_id>/assistance/", value.assistance),
    path(
        "companies/<uuid:company_id>/staff-batches/import-preview/",
        value.import_preview,
    ),
    path("company-tenancies/", tenancies.collection),
    path("company-tenancies/<uuid:tenancy_id>/", tenancies.detail),
    path(
        "company-tenancies/<uuid:tenancy_id>/resolve-operation/",
        tenancies.resolve_operation,
    ),
    path("company-tenancies/<uuid:tenancy_id>/<slug:action>/", tenancies.action),
    path(
        "company-contract-preparations/<uuid:preparation_id>/agreement/",
        tenancies.create,
    ),
    path(
        "company-mandates/<uuid:mandate_id>/execution-review/", tenancies.verify_mandate
    ),
    path("companies/<uuid:company_id>/mandates/", contracts.mandates),
    path("company-mandates/<uuid:mandate_id>/<slug:action>/", contracts.mandate_action),
    path(
        "company-booking-items/<uuid:item_id>/contract-preparation/",
        contracts.preparation,
    ),
    path("company-contract-preparations/", contracts.preparations),
    path("company-contract-preparations/<uuid:preparation_id>/", contracts.detail),
    path(
        "company-contract-preparations/<uuid:preparation_id>/<slug:action>/",
        contracts.preparation_action,
    ),
    path("residential-assets/<slug:kind>/<uuid:asset_id>/changes/", p.change_history),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/bulk-edit/preview/",
        p.preview,
        {"operation": "bulk-edit"},
    ),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/topology/preview/",
        p.preview,
        {"operation": "topology"},
    ),
    path("residential-changes/<uuid:change_id>/", p.change),
    path("residential-assets/<slug:kind>/<uuid:asset_id>/media/", p.media_collection),
    path("residential-media/<uuid:media_id>/", p.media_detail),
    path("residential-media/<uuid:media_id>/bytes/", p.media_bytes),
    path("residential-media/<uuid:media_id>/review/", p.media_review),
    path(
        "companies/<uuid:company_id>/housing-requests/<uuid:request_id>/discussion/",
        c.discussion,
    ),
    path("companies/<uuid:company_id>/approval-route/", w.approval_route),
    path("companies/<uuid:company_id>/work-items/", w.work),
    path("company-booking-items/<uuid:item_id>/reassign/", w.reassign),
    path("account-contexts/", s.contexts),
    path("companies/<uuid:company_id>/planning-staff/", s.planning_people),
    path("companies/<uuid:company_id>/staff/", s.roster),
    path("companies/<uuid:company_id>/staff/<uuid:staff_id>/", s.detail),
    path(
        "companies/<uuid:company_id>/staff/<uuid:staff_id>/<slug:action>/", s.activation
    ),
    path("companies/<uuid:company_id>/staff-batches/", s.batch),
    path("companies/<uuid:company_id>/staff-batches/<uuid:batch_id>/", s.batch_detail),
    path("company-access/preview/", s.access_preview),
    path("company-access/contact-proof/", s.request_contact_proof),
    path("company-access/contact-proof/<uuid:proof_id>/", s.verify_contact_proof),
    path("company-access/<slug:action>/", s.access_response),
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
