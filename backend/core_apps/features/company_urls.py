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
        responsibilities.CollectionView.as_view(),
    ),
    path(
        "companies/<uuid:company_id>/responsibility-assignments/<uuid:tenancy_id>/",
        responsibilities.DetailView.as_view(),
    ),
    path(
        "companies/<uuid:company_id>/responsibility-assignments/<uuid:tenancy_id>/<slug:action>/",
        responsibilities.ActionView.as_view(),
    ),
    path("companies/<uuid:company_id>/role-work/", v.RoleWorkView.as_view()),
    path("companies/<uuid:company_id>/role-contexts/", v.RoleContextsView.as_view()),
    path("company-terms-negotiations/", terms.NegotiationsView.as_view()),
    path(
        "company-terms-negotiations/<uuid:negotiation_id>/", terms.DetailView.as_view()
    ),
    path(
        "company-terms-negotiations/<uuid:negotiation_id>/<slug:action>/",
        terms.DetailView.as_view(),
    ),
    path(
        "company-booking-items/<uuid:item_id>/negotiation/", terms.StartView.as_view()
    ),
    path("workspace-summary/", workspace_views.SummaryView.as_view()),
    path("companies/<uuid:company_id>/saved-lists/", saved.CollectionView.as_view()),
    path("company-saved-lists/<uuid:list_id>/", saved.DetailView.as_view()),
    path("company-saved-lists/<uuid:list_id>/items/", saved.ItemsView.as_view()),
    *[
        path(
            "company-saved-lists/<uuid:list_id>/" + action + "/",
            saved.ActionView.as_view(),
            {"action": action},
        )
        for action in ("rename", "archive", "add", "remove")
    ],
    path(
        "companies/<uuid:company_id>/rental-summary/", value.RentalSummaryView.as_view()
    ),
    path(
        "companies/<uuid:company_id>/housing-report/", value.HousingReportView.as_view()
    ),
    path("company-requirements/", value.CatalogView.as_view()),
    path(
        "company-housing-requests/<uuid:request_id>/assistance/",
        value.AssistanceView.as_view(),
    ),
    path(
        "companies/<uuid:company_id>/staff-batches/import-preview/",
        value.ImportPreviewView.as_view(),
    ),
    path("company-tenancies/", tenancies.CollectionView.as_view()),
    path("company-tenancies/<uuid:tenancy_id>/", tenancies.DetailView.as_view()),
    path(
        "company-tenancies/<uuid:tenancy_id>/resolve-operation/",
        tenancies.ResolveOperationView.as_view(),
    ),
    path(
        "company-tenancies/<uuid:tenancy_id>/<slug:action>/",
        tenancies.ActionView.as_view(),
    ),
    path(
        "company-contract-preparations/<uuid:preparation_id>/agreement/",
        tenancies.CreateView.as_view(),
    ),
    path(
        "company-mandates/<uuid:mandate_id>/execution-review/",
        tenancies.VerifyMandateView.as_view(),
    ),
    path("companies/<uuid:company_id>/mandates/", contracts.MandatesView.as_view()),
    path(
        "company-mandates/<uuid:mandate_id>/<slug:action>/",
        contracts.MandateActionView.as_view(),
    ),
    path(
        "company-booking-items/<uuid:item_id>/contract-preparation/",
        contracts.PreparationView.as_view(),
    ),
    path("company-contract-preparations/", contracts.PreparationsView.as_view()),
    path(
        "company-contract-preparations/<uuid:preparation_id>/",
        contracts.DetailView.as_view(),
    ),
    path(
        "company-contract-preparations/<uuid:preparation_id>/<slug:action>/",
        contracts.PreparationActionView.as_view(),
    ),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/changes/",
        p.ChangeHistoryView.as_view(),
    ),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/bulk-edit/preview/",
        p.PreviewView.as_view(),
        {"operation": "bulk-edit"},
    ),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/topology/preview/",
        p.PreviewView.as_view(),
        {"operation": "topology"},
    ),
    path("residential-changes/<uuid:change_id>/", p.ChangeView.as_view()),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/media/",
        p.MediaCollectionView.as_view(),
    ),
    path("residential-media/<uuid:media_id>/", p.MediaDetailView.as_view()),
    path("residential-media/<uuid:media_id>/bytes/", p.MediaBytesView.as_view()),
    path("residential-media/<uuid:media_id>/review/", p.MediaReviewView.as_view()),
    path(
        "companies/<uuid:company_id>/housing-requests/<uuid:request_id>/discussion/",
        c.DiscussionView.as_view(),
    ),
    path("companies/<uuid:company_id>/approval-route/", w.ApprovalRouteView.as_view()),
    path("companies/<uuid:company_id>/work-items/", w.WorkView.as_view()),
    path("company-booking-items/<uuid:item_id>/reassign/", w.ReassignView.as_view()),
    path("account-contexts/", s.ContextsView.as_view()),
    path("companies/<uuid:company_id>/planning-staff/", s.PlanningPeopleView.as_view()),
    path("companies/<uuid:company_id>/staff/", s.RosterView.as_view()),
    path("companies/<uuid:company_id>/staff/<uuid:staff_id>/", s.DetailView.as_view()),
    path(
        "companies/<uuid:company_id>/staff/<uuid:staff_id>/<slug:action>/",
        s.ActivationView.as_view(),
    ),
    path("companies/<uuid:company_id>/staff-batches/", s.BatchView.as_view()),
    path(
        "companies/<uuid:company_id>/staff-batches/<uuid:batch_id>/",
        s.BatchDetailView.as_view(),
    ),
    path("company-access/preview/", s.AccessPreviewView.as_view()),
    path("company-access/contact-proof/", s.RequestContactProofView.as_view()),
    path(
        "company-access/contact-proof/<uuid:proof_id>/",
        s.VerifyContactProofView.as_view(),
    ),
    path("company-access/<slug:action>/", s.AccessResponseView.as_view()),
    path("company-capabilities/", v.CapabilitiesView.as_view()),
    path("companies/", v.CompaniesView.as_view()),
    path("company-invitations/accept/", v.AcceptInvitationView.as_view()),
    path("company-invitations/<uuid:invitation_id>/", v.InvitationDetailView.as_view()),
    path("companies/<uuid:company_id>/", v.CompanyDetailView.as_view()),
    path("companies/<uuid:company_id>/members/", v.MembersView.as_view()),
    path("companies/<uuid:company_id>/occupants/", a.OccupantsView.as_view()),
    path("companies/<uuid:company_id>/budget/", a.CompanyBudgetView.as_view()),
    path(
        "company-housing-requests/<uuid:request_id>/coordinator/",
        a.ReassignCoordinatorView.as_view(),
    ),
    path(
        "company-authority/<slug:kind>/<uuid:identity>/review/",
        a.AuthorityReviewView.as_view(),
    ),
    path(
        "companies/<uuid:company_id>/members/<uuid:membership_id>/",
        v.MemberActionView.as_view(),
    ),
    path("companies/<uuid:company_id>/invitations/", v.InvitationsView.as_view()),
    path(
        "companies/<uuid:company_id>/housing-requests/", v.HousingRequestsView.as_view()
    ),
    path("company-housing-requests/<uuid:request_id>/", v.HousingRequestView.as_view()),
    path(
        "company-housing-requests/<uuid:request_id>/items/", v.SelectOfferView.as_view()
    ),
    path(
        "company-booking-items/<uuid:item_id>/<slug:action>/",
        v.ItemActionView.as_view(),
    ),
    path("residential-assets/", v.ContainersView.as_view()),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/",
        v.ContainerDetailView.as_view(),
    ),
    path(
        "residential-assets/<slug:kind>/<uuid:asset_id>/attach-unit/",
        v.AttachUnitView.as_view(),
    ),
    path("residential-unit-templates/", v.UnitTemplatesView.as_view()),
    path("residential-unit-batches/", v.BatchUnitsView.as_view()),
    path("residential-unit-batches/<uuid:batch_id>/", v.BatchDetailView.as_view()),
    path("portfolio-offers/", v.PortfolioOffersView.as_view()),
    path(
        "portfolio-offers/<uuid:offer_id>/<slug:action>/",
        v.PortfolioOfferActionView.as_view(),
    ),
]
