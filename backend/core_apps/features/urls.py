from .payment_resume_views import payment_attempt_resume
from . import refund_operations
from . import beneficiary_views
from .signing_views import SigningCallbackView, SigningStatusView
from django.urls import include, path
from .chargeback_views import chargeback_detail
from .rental_phase6_views_parts.lease_reviews import DocumentContentView

from . import views
from . import business_policy_views
from .continuation_views import ContinuationItemsView
from . import rental_phase2_views as views_phase2
from . import rental_phase3_views as views_phase3
from . import rental_phase4_views as views_phase4
from . import rental_phase5_views as views_phase5
from . import rental_phase6_views as views_phase6
from . import mock_provider_views
from .models import RentalChange

from .rental_lifecycle_views import habitability

from .views_parts.listing_suggestions import OwnerAnalyticsExportView
from .views_parts.boost_campaigns import boost_campaign_detail, boost_campaign_resolve

urlpatterns = [
    path("", include("core_apps.features.experience.urls")),
    path("operations/refunds/", refund_operations.queue, name="operation-refund-queue"),
    path(
        "operations/refunds/<uuid:refund_id>/review/",
        refund_operations.review,
        name="operation-refund-review",
    ),
    path(
        "operations/refunds/<uuid:refund_id>/reconcile/",
        refund_operations.reconcile,
        name="operation-refund-reconcile",
    ),
    path(
        "operations/refunds/<uuid:refund_id>/reauthorize/",
        refund_operations.reauthorize,
        name="operation-refund-reauthorize",
    ),
    path(
        "operations/refunds/<uuid:refund_id>/retry/",
        refund_operations.retry,
        name="operation-refund-retry",
    ),
    path(
        "signing/provider-events/",
        SigningCallbackView.as_view(),
        name="signwell-provider-events",
    ),
    path(
        "signing/documents/<uuid:document_id>/",
        SigningStatusView.as_view(),
        name="rental-signing-status",
    ),
    path(
        "payment-attempts/<uuid:attempt_id>/resume/",
        payment_attempt_resume,
        name="payment-attempt-resume",
    ),
    path(
        "owner-analytics/<uuid:property_id>/export/",
        OwnerAnalyticsExportView.as_view(),
        name="owner-analytics-export",
    ),
    path(
        "operator/chargebacks/<uuid:chargeback_id>/",
        chargeback_detail,
        name="operator-chargeback-detail",
    ),
    path(
        "business-policies/",
        business_policy_views.current_policies,
        name="business-policies",
    ),
    path(
        "business-policies/<str:code>/versions/<str:version>/",
        business_policy_views.policy_version,
        name="business-policy-version",
    ),
    path(
        "operator/business-policies/",
        business_policy_views.administer_policies,
        name="business-policy-administration",
    ),
    path(
        "rental-documents/<uuid:document_id>/content/",
        DocumentContentView.as_view(),
        name="rental-document-content",
    ),
    path(
        "rental-cases/<uuid:case_id>/habitability/",
        habitability.AssessmentView.as_view(),
    ),
    path(
        "continuation-items/",
        ContinuationItemsView.as_view(),
        name="continuation-items",
    ),
    path("", include("core_apps.features.advanced_execution_urls")),
    path("", include("core_apps.features.advanced_tender_urls")),
    path("", include("core_apps.features.living_lab_urls")),
    path("", include("core_apps.features.housing_scenario_urls")),
    path("", include("core_apps.features.transition_network_urls")),
    path("", include("core_apps.features.reputation_urls")),
    path("", include("core_apps.features.company_urls")),
    path("", include("core_apps.features.rental_lifecycle_urls")),
    path("", include("core_apps.features.student_urls")),
    path("", include("core_apps.features.billing_urls")),
    path("", include("core_apps.features.planning_urls")),
    path(
        "mock-provider/onboarding-sessions/<uuid:session_id>/complete/",
        mock_provider_views.onboarding_complete,
    ),
    path(
        "mock-provider/signing-sessions/<uuid:session_id>/complete/",
        mock_provider_views.signing_complete,
    ),
    path(
        "mock-provider/change-signing-sessions/<uuid:session_id>/complete/",
        mock_provider_views.signing_complete,
        {"change": True},
    ),
    path(
        "mock-provider/payment-attempts/<uuid:attempt_id>/events/",
        mock_provider_views.payment_event,
    ),
    path(
        "rental-capabilities/",
        views.RentalCapabilitiesView.as_view(),
        name="rental-capabilities",
    ),
    path(
        "planning-capabilities/",
        views.PlanningCapabilitiesView.as_view(),
        name="planning-capabilities",
    ),
    path(
        "rental-operations/<uuid:request_key>/",
        views.RentalOperationLookupView.as_view(),
        name="rental-operation-lookup",
    ),
    path(
        "configuration/",
        views.ConfigurationView.as_view(),
        name="feature-configuration",
    ),
    path("boost-campaigns/", views.boost_campaigns, name="boost-campaigns"),
    path(
        "boost-campaigns/resolve/",
        boost_campaign_resolve,
        name="boost-campaign-resolve",
    ),
    path(
        "boost-campaigns/<uuid:campaign_id>/",
        boost_campaign_detail,
        name="boost-campaign-detail",
    ),
    path("search-alerts/", views.SearchAlertsView.as_view(), name="search-alerts"),
    path(
        "search-alerts/<uuid:alert_id>/",
        views.SearchAlertDetailView.as_view(),
        name="search-alert-detail",
    ),
    path(
        "owner-analytics/<uuid:property_id>/",
        views.OwnerAnalyticsView.as_view(),
        name="owner-analytics",
    ),
    path(
        "listing-suggestions/",
        views.ListingSuggestionsView.as_view(),
        name="listing-suggestions",
    ),
    path(
        "lease-configuration/",
        views.LeaseConfigurationView.as_view(),
        name="lease-configuration",
    ),
    path(
        "owner-payment-profile/",
        views_phase2.owner_payment_profile,
        name="owner-payment-profile",
    ),
    path(
        "owner-payment-profile/beneficiary-details/",
        beneficiary_views.submit_details,
        name="owner-beneficiary-details",
    ),
    path(
        "owner-payment-profile/confirm-beneficiary/",
        beneficiary_views.confirm,
        name="owner-beneficiary-confirm",
    ),
    path(
        "owner-payment-profile/onboarding-session/",
        views_phase2.owner_onboarding_session,
        name="owner-onboarding-session",
    ),
    path(
        "rental-interests/",
        views_phase2.RentalInterestsView.as_view(),
        name="rental-interests",
    ),
    path(
        "rental-interests/<uuid:interest_id>/",
        views_phase2.RentalInterestDetailView.as_view(),
        name="rental-interest-detail",
    ),
    path(
        "rental-interests/<uuid:interest_id>/respond/",
        views_phase2.RentalInterestRespondView.as_view(),
        name="rental-interest-respond",
    ),
    path(
        "terms-proposals/",
        views_phase2.TermsProposalsView.as_view(),
        name="terms-proposals",
    ),
    path(
        "terms-proposals/<uuid:proposal_id>/",
        views_phase2.TermsProposalDetailView.as_view(),
        name="terms-proposal-detail",
    ),
    path(
        "terms-proposals/<uuid:proposal_id>/respond/",
        views_phase2.TermsProposalRespondView.as_view(),
        name="terms-proposal-respond",
    ),
    path("lease-tenants/", views.LeaseTenantsView.as_view(), name="lease-tenants"),
    path(
        "tenancy-invitations/",
        views.TenancyInvitationsView.as_view(),
        name="tenancy-invitations",
    ),
    path(
        "tenancy-invitations/create/resolve/",
        views.TenancyInvitationCreateResolveView.as_view(),
        name="tenancy-invitation-create-resolve",
    ),
    path(
        "tenancy-invitations/<uuid:invitation_id>/respond/resolve/",
        views.TenancyInvitationResponseResolveView.as_view(),
        name="tenancy-invitation-response-resolve",
    ),
    path(
        "tenancy-invitations/<uuid:invitation_id>/",
        views.TenancyInvitationDetailView.as_view(),
        name="tenancy-invitation-detail",
    ),
    path(
        "tenancy-invitations/<uuid:invitation_id>/respond/",
        views.TenancyInvitationRespondView.as_view(),
        name="tenancy-invitation-respond",
    ),
    path(
        "tenancy-invitations/<uuid:invitation_id>/revoke/",
        views_phase2.TenancyInvitationRevokeView.as_view(),
        name="tenancy-invitation-revoke",
    ),
    path("leases/", views.LeasesView.as_view(), name="leases"),
    path(
        "leases/<uuid:lease_id>/", views.LeaseDetailView.as_view(), name="lease-detail"
    ),
    path(
        "leases/<uuid:lease_id>/signing-session/",
        views.LeaseSigningSessionView.as_view(),
        name="lease-signing-session",
    ),
    path(
        "leases/<uuid:lease_id>/review/",
        views_phase2.LeaseReviewView.as_view(),
        name="lease-review",
    ),
    path(
        "leases/<uuid:lease_id>/submit-for-signature/",
        views_phase2.LeaseSubmitForSignatureView.as_view(),
        name="lease-submit-for-signature",
    ),
    path(
        "leases/<uuid:lease_id>/timeline/",
        views_phase2.LeaseTimelineView.as_view(),
        name="lease-timeline",
    ),
    path(
        "leases/<uuid:lease_id>/billing-schedule/",
        views_phase2.LeaseBillingScheduleView.as_view(),
        name="lease-billing-schedule",
    ),
    path(
        "provider-webhooks/rental/",
        views_phase2.fake_rental_provider_webhook,
        name="fake-rental-provider-webhook",
    ),
    path(
        "leases/<uuid:lease_id>/cancel/",
        views.LeaseCancelView.as_view(),
        name="lease-cancel",
    ),
    path("rent-invoices/", views.RentInvoicesView.as_view(), name="rent-invoices"),
    path(
        "rent-invoices/<uuid:invoice_id>/",
        views.RentInvoiceDetailView.as_view(),
        name="rent-invoice-detail",
    ),
    path(
        "rent-invoices/<uuid:invoice_id>/checkout/",
        views_phase3.rent_invoice_checkout,
        name="rent-invoice-checkout",
    ),
    path(
        "rent-invoices/<uuid:invoice_id>/quote/",
        views_phase3.rent_invoice_quote,
        name="rent-invoice-quote",
    ),
    path("payment-attempts/", views_phase3.payment_attempts, name="payment-attempts"),
    path(
        "rent-invoices/<uuid:invoice_id>/payments/",
        views_phase3.rent_invoice_payments,
        name="rent-invoice-payments",
    ),
    path(
        "payment-attempts/<uuid:attempt_id>/",
        views_phase3.payment_attempt_detail,
        name="payment-attempt-detail",
    ),
    path(
        "payment-attempts/<uuid:attempt_id>/reconcile/",
        views_phase3.payment_attempt_reconcile,
        name="payment-attempt-reconcile",
    ),
    path("owner-payables/", views_phase3.owner_payables, name="owner-payables"),
    path(
        "provider-webhooks/payments/",
        views_phase3.fake_payment_webhook,
        name="fake-payment-webhook",
    ),
    path(
        "leases/<uuid:lease_id>/handovers/",
        views_phase4.LeaseHandoversView.as_view(),
        name="lease-handovers",
    ),
    path(
        "handovers/<uuid:handover_id>/",
        views_phase4.HandoverDetailView.as_view(),
        name="handover-detail",
    ),
    path(
        "handovers/<uuid:handover_id>/respond/",
        views_phase4.HandoverRespondView.as_view(),
        name="handover-respond",
    ),
    path(
        "rental-attachments/",
        views_phase4.RentalEvidenceUploadView.as_view(),
        name="rental-evidence-upload",
    ),
    path(
        "rental-attachments/<uuid:evidence_id>/",
        views_phase4.RentalEvidenceDetailView.as_view(),
        name="rental-evidence-detail",
    ),
    path(
        "rental-attachments/<uuid:evidence_id>/content/",
        views_phase4.RentalEvidenceContentView.as_view(),
        name="rental-evidence-content",
    ),
    path(
        "rental-attachments/<uuid:evidence_id>/download/",
        views_phase4.RentalEvidenceDownloadView.as_view(),
        name="rental-evidence-download",
    ),
    path(
        "leases/<uuid:lease_id>/deposit/",
        views_phase4.lease_deposit,
        name="lease-deposit",
    ),
    path("payouts/", views_phase4.payouts, name="rental-payouts"),
    path(
        "payouts/<uuid:payout_id>/",
        views_phase4.payout_detail,
        name="rental-payout-detail",
    ),
    path(
        "operations/payouts/execute/",
        views_phase4.operations_execute_payout,
        name="operations-payout-execute",
    ),
    path(
        "operations/payouts/preview/",
        views_phase4.payout_preview,
        name="operations-payout-preview",
    ),
    path(
        "operations/payouts/", views_phase4.payout_queue, name="operations-payout-queue"
    ),
    path(
        "operations/payables/",
        views_phase4.payable_queue,
        name="operations-payable-queue",
    ),
    path(
        "operations/payouts/<uuid:payout_id>/review/",
        views_phase4.payout_review,
        name="operations-payout-review",
    ),
    path(
        "operations/payouts/<uuid:payout_id>/reauthorize/",
        views_phase4.reauthorize_payout,
        name="operations-payout-reauthorize",
    ),
    path(
        "operations/payouts/<uuid:payout_id>/retry/",
        views_phase4.retry_failed_payout,
        name="operations-payout-retry",
    ),
    path(
        "operations/payouts/<uuid:payout_id>/reconcile/",
        views_phase4.operations_reconcile_payout,
        name="operations-payout-reconcile",
    ),
    path(
        "leases/<uuid:lease_id>/maintenance-requests/",
        views_phase5.MaintenanceRequestsView.as_view(),
        name="maintenance-requests",
    ),
    path(
        "maintenance-requests/<uuid:request_id>/",
        views_phase5.MaintenanceDetailView.as_view(),
        name="maintenance-detail",
    ),
    path(
        "maintenance-requests/<uuid:request_id>/actions/",
        views_phase5.MaintenanceActionView.as_view(),
        name="maintenance-action",
    ),
    path(
        "leases/<uuid:lease_id>/payment-extension-requests/",
        views_phase5.payment_extensions,
        name="payment-extensions",
    ),
    path(
        "leases/<uuid:lease_id>/amendments/",
        views_phase5.AmendmentsView.as_view(),
        name="amendments",
    ),
    path(
        "leases/<uuid:lease_id>/renewals/",
        views_phase5.RenewalsView.as_view(),
        name="renewals",
    ),
    path(
        "leases/<uuid:lease_id>/termination-requests/",
        views_phase5.TerminationsView.as_view(),
        name="terminations",
    ),
    path(
        "rent-invoices/<uuid:invoice_id>/external-payment-claims/",
        views_phase5.external_claim_create,
        name="external-claim-create",
    ),
    path(
        "leases/<uuid:lease_id>/external-payment-claims/",
        views_phase5.external_claims,
        name="external-claims",
    ),
    path(
        "payment-extension-requests/<uuid:change_id>/",
        views_phase5.ChangeDetailView.as_view(),
        {"kind": RentalChange.Kind.PAYMENT_EXTENSION},
        name="payment-extension-detail",
    ),
    path(
        "payment-extension-requests/<uuid:change_id>/respond/",
        views_phase5.ChangeRespondView.as_view(),
        {"kind": RentalChange.Kind.PAYMENT_EXTENSION},
        name="payment-extension-respond",
    ),
    path(
        "amendments/<uuid:change_id>/",
        views_phase5.ChangeDetailView.as_view(),
        {"kind": RentalChange.Kind.AMENDMENT},
        name="amendment-detail",
    ),
    path(
        "amendments/<uuid:change_id>/respond/",
        views_phase5.ChangeRespondView.as_view(),
        {"kind": RentalChange.Kind.AMENDMENT},
        name="amendment-respond",
    ),
    path(
        "amendments/<uuid:change_id>/submit-for-signature/",
        views_phase5.SubmitChangeForSignatureView.as_view(),
        {"kind": RentalChange.Kind.AMENDMENT},
        name="amendment-submit",
    ),
    path(
        "amendments/<uuid:change_id>/signing-session/",
        views_phase5.ChangeSigningSessionView.as_view(),
        {"kind": RentalChange.Kind.AMENDMENT},
        name="amendment-signing",
    ),
    path(
        "renewals/<uuid:change_id>/",
        views_phase5.ChangeDetailView.as_view(),
        {"kind": RentalChange.Kind.RENEWAL},
        name="renewal-detail",
    ),
    path(
        "renewals/<uuid:change_id>/respond/",
        views_phase5.ChangeRespondView.as_view(),
        {"kind": RentalChange.Kind.RENEWAL},
        name="renewal-respond",
    ),
    path(
        "renewals/<uuid:change_id>/submit-for-signature/",
        views_phase5.SubmitChangeForSignatureView.as_view(),
        {"kind": RentalChange.Kind.RENEWAL},
        name="renewal-submit",
    ),
    path(
        "renewals/<uuid:change_id>/signing-session/",
        views_phase5.ChangeSigningSessionView.as_view(),
        {"kind": RentalChange.Kind.RENEWAL},
        name="renewal-signing",
    ),
    path(
        "termination-requests/<uuid:change_id>/",
        views_phase5.ChangeDetailView.as_view(),
        {"kind": RentalChange.Kind.TERMINATION},
        name="termination-detail",
    ),
    path(
        "termination-requests/<uuid:change_id>/respond/",
        views_phase5.ChangeRespondView.as_view(),
        {"kind": RentalChange.Kind.TERMINATION},
        name="termination-respond",
    ),
    path(
        "external-payment-claims/<uuid:change_id>/",
        views_phase5.ChangeDetailView.as_view(),
        {"kind": RentalChange.Kind.EXTERNAL_PAYMENT},
        name="external-claim-detail",
    ),
    path(
        "external-payment-claims/<uuid:change_id>/respond/",
        views_phase5.ChangeRespondView.as_view(),
        {"kind": RentalChange.Kind.EXTERNAL_PAYMENT},
        name="external-claim-respond",
    ),
    path(
        "refund-requests/<uuid:refund_id>/execute/",
        views_phase6.refund_execute,
        name="refund-execute",
    ),
    path(
        "leases/<uuid:lease_id>/final-settlement/",
        views_phase6.FinalSettlementDetailView.as_view(),
        name="final-settlement",
    ),
    path(
        "leases/<uuid:lease_id>/final-settlement/propose/",
        views_phase6.FinalSettlementProposeView.as_view(),
        name="final-settlement-propose",
    ),
    path(
        "leases/<uuid:lease_id>/final-settlement/respond/",
        views_phase6.FinalSettlementRespondView.as_view(),
        name="final-settlement-respond",
    ),
    path("refund-requests/", views_phase6.refund_requests, name="refund-requests"),
    path(
        "refund-requests/<uuid:refund_id>/",
        views_phase6.refund_detail,
        name="refund-detail",
    ),
    path(
        "refund-requests/<uuid:refund_id>/respond/",
        views_phase6.refund_respond,
        name="refund-respond",
    ),
    path("disputes/", views_phase6.DisputesView.as_view(), name="rental-disputes"),
    path(
        "disputes/<uuid:dispute_id>/",
        views_phase6.DisputeDetailView.as_view(),
        name="rental-dispute-detail",
    ),
    path(
        "disputes/<uuid:dispute_id>/responses/",
        views_phase6.DisputeRespondView.as_view(),
        name="rental-dispute-responses",
    ),
    path(
        "disputes/<uuid:dispute_id>/respond/",
        views_phase6.DisputeRespondView.as_view(),
        name="rental-dispute-respond",
    ),
    path(
        "leases/<uuid:lease_id>/documents/",
        views_phase6.LeaseDocumentsView.as_view(),
        name="lease-documents",
    ),
    path(
        "rental-documents/<uuid:document_id>/download/",
        views_phase6.DocumentDownloadView.as_view(),
        name="rental-document-download",
    ),
    path(
        "rental-statements/",
        views_phase6.RentalStatementCreateView.as_view(),
        name="rental-statement-create",
    ),
    path(
        "leases/<uuid:lease_id>/reviews/",
        views_phase6.LeaseReviewsView.as_view(),
        name="lease-reviews",
    ),
    path(
        "leases/<uuid:lease_id>/rental-center/",
        views_phase6.RentalCenterView.as_view(),
        name="rental-center",
    ),
]
