from django.contrib import admin
from . import business_policy_admin  # noqa: F401
from . import chargeback_admin  # noqa: F401
from . import company_admin  # noqa: F401
from . import company_execution_admin  # noqa: F401
from . import portfolio_admin  # noqa: F401
from . import reputation_admin  # noqa: F401
from .billing_admin import FinancialHistoryAdmin

from .models import (
    BoostCampaign,
    CheckoutSession,
    IdempotencyRecord,
    Lease,
    LeaseEligibleTenant,
    ListingSuggestion,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    RentalCommercialPolicy,
    RentalInterest,
    RentalInventoryDayLock,
    RentalTimelineEvent,
    RentInvoice,
    SearchAlert,
    SigningSession,
    TenancyInvitation,
    TermsProposal,
    BillingPeriod,
    InvoiceLine,
    PaymentQuote,
    PaymentAttempt,
    ProviderWebhookEvent,
    LedgerTransaction,
    LedgerEntry,
    InvoicePaymentAllocation,
    PaymentReceipt,
    OwnerPayable,
    RentalEvidence,
    RentalHandover,
    DepositAgreement,
    PayoutBatch,
    RentalPayout,
    PayoutAuditEvent,
    MaintenanceRequest,
    MaintenanceEvent,
    RentalChange,
    ChangeSigningSession,
    FinalSettlement,
    RefundRequest,
    RentalDispute,
    RentalDocument,
    RentalReview,
    PrivateAccessRevocation,
)

admin.site.register(
    [
        BoostCampaign,
        SearchAlert,
        ListingSuggestion,
        LeaseEligibleTenant,
    ]
)

admin.site.register(
    [
        RentInvoice,
        InvoiceLine,
        PaymentQuote,
        PaymentAttempt,
        LedgerTransaction,
        LedgerEntry,
        InvoicePaymentAllocation,
        PaymentReceipt,
    ],
    FinancialHistoryAdmin,
)

from . import catalog_admin  # noqa: E402,F401

from . import models as lifecycle_models

admin.site.register(
    [
        getattr(lifecycle_models, name)
        for name in [
            "Lease",
            "SigningSession",
            "CheckoutSession",
            "TenancyInvitation",
            "IdempotencyRecord",
            "OwnerPaymentProfile",
            "OwnerOnboardingSession",
            "RentalInterest",
            "TermsProposal",
            "RentalInventoryDayLock",
            "RentalTimelineEvent",
            "BillingPeriod",
            "ProviderWebhookEvent",
            "OwnerPayable",
            "RentalEvidence",
            "RentalHandover",
            "DepositAgreement",
            "PayoutBatch",
            "RentalPayout",
            "PayoutAuditEvent",
            "MaintenanceRequest",
            "MaintenanceEvent",
            "RentalChange",
            "ChangeSigningSession",
            "FinalSettlement",
            "RefundRequest",
            "RentalDispute",
            "RentalDocument",
            "RentalReview",
            "PrivateAccessRevocation",
            "ApplicationProfile",
            "ApplicationProfileVersion",
            "ApplicationAccessGrant",
            "RentalVerificationClaim",
            "PropertyDecisionFact",
            "RentalAvailabilityConfirmation",
            "RentalInventoryUnit",
            "ReservationHold",
            "RentalConsentRecord",
            "RentalAuditEvent",
            "RentalProviderInstruction",
            "GroupBookingProposal",
            "GroupBookingParticipant",
        ]
    ],
    FinancialHistoryAdmin,
)

admin.site.register(RentalCommercialPolicy, FinancialHistoryAdmin)

from . import student_admin  # noqa: E402,F401
from . import case_admin  # noqa: E402,F401
