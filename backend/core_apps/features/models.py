"""Feature model registry and stable public imports.

Concrete models live in domain modules; Django app labels, database tables and
existing migration imports retain their original identities.
"""

from .model_parts.marketplace import (
    BoostCampaign,
    SearchAlert,
    ListingSuggestion,
)
from .model_parts.agreements import (
    LeaseEligibleTenant,
    Lease,
    SigningSession,
)
from .model_parts.rental_experiences import (
    CompanyLeaseBinding,
    CompanyReviewAuthority,
    EmployeeOccupancyConfirmation,
    LeaseResponsibilityTransition,
)
from .model_parts.offers import (
    RentalInterest,
    TermsProposal,
    TenancyInvitation,
)
from .model_parts.owner_payments import (
    RentalCommercialPolicy,
    OwnerPaymentProfile,
    OwnerOnboardingSession,
)
from .model_parts.recovery import (
    IdempotencyRecord,
    RentalInventoryDayLock,
    RentalTimelineEvent,
)
from .model_parts.invoices import (
    BillingPeriod,
    RentInvoice,
    InvoiceLine,
    PaymentQuote,
)
from .model_parts.payments import (
    PaymentAttempt,
    CheckoutSession,
    ProviderWebhookEvent,
    InvoicePaymentAllocation,
    PaymentReceipt,
)
from .model_parts.ledger import (
    LedgerTransaction,
    LedgerEntry,
    OwnerPayable,
    PayoutBatch,
    RentalPayout,
    PayoutAuditEvent,
)
from .model_parts.condition import (
    RentalEvidence,
    RentalHandover,
    DepositAgreement,
)
from .model_parts.maintenance_changes import (
    MaintenanceRequest,
    MaintenanceEvent,
    RentalChange,
    ChangeSigningSession,
)
from .model_parts.settlements import (
    FinalSettlement,
    SettlementAdjustment,
    RefundRequest,
    RentalDispute,
    RentalDocument,
    RentalReview,
    PrivateAccessRevocation,
)

from .billing_models import AccountSubscription, SubscriptionPlan
from .planning_models import (  # noqa: E402,F401
    CommuteSearch,
    ConditionReport,
    GroupInvitation,
    GroupMembership,
    GroupProcess,
    HousingGroup,
    HousingOffer,
    HousingRequest,
    LifestyleProfile,
    RoommateConnection,
    TenancyTransition,
    TenantAssistantTurn,
)
from .catalog_models import PromotionOption
from .model_parts.summary_sharing import RentalSummaryGrant

from .model_parts.application_profiles import (
    ApplicationProfile,
    ApplicationProfileVersion,
    ApplicationAccessGrant,
    RentalVerificationClaim,
    RentalConsentRecord,
)
from .model_parts.decision_facts import (
    PropertyDecisionFact,
    RentalAvailabilityConfirmation,
)
from .model_parts.reservations import RentalInventoryUnit, ReservationHold
from .model_parts.group_bookings import GroupBookingProposal, GroupBookingParticipant
from .model_parts.operational_cases import (
    RentalOperationalCase,
    RentalAuditEvent,
    RentalProviderInstruction,
)

from .student_models import (
    University,
    Campus,
    StudentProfile,
    AcademicHousingPlan,
    AcademicPlanParticipant,
    AcademicRequirementRevision,
    SharedLivingAgreement,
    StudentOfferPolicy,
)

from .company_models import (
    Company,
    CompanyMembership,
    CompanyInvitation,
    PortfolioOffer,
    CompanyHousingRequest,
    CompanyBookingItem,
    CompanyApproval,
    CompanyBudgetReservation,
    EmployeeAssignment,
)
from .company_staff_models import (
    CompanyStaffRecord,
    CompanyAccountProvisioning,
    CompanyStaffBatch,
    CompanyStaffBatchRow,
    CompanyWorkContactProof,
)
from .company_contract_models import (
    CompanyMandate,
    CompanyContractPreparation,
    CompanyPreparationConsent,
    CompanyTenancy,
    CompanyTenancyChange,
    CompanyMaintenanceScope,
)

from .model_parts.reputation import (
    ReviewCase,
    ReviewOpportunity,
    ReviewSubmission,
    ReviewSection,
    ReviewReply,
    ReviewDraft,
    ReviewReport,
    ReviewModerationDecision,
    ReviewAppeal,
    ReputationAccessGrant,
    ReviewAuditEvent,
    ReviewDecisionNotice,
)

from .advanced_tender_models import (
    HousingTender,
    TenderParticipantRequirement,
    TenderDemandSnapshot,
    OwnerBid,
    TenderBidLine,
    PackageCandidate,
    PackageConsent,
    TenderPackageRun,
    TenderBidClarification,
)
from .living_lab_models import (
    SharedLivingLab,
    PrivateParticipantRequirement,
    LivingLabRun,
    ArrangementResponse,
    SharedArrangementSnapshot,
    LivingLabAuditEvent,
    LivingPreferenceDisclosure,
)
from .transition_network_models import (
    MoveIntent,
    TransitionMatchRun,
    TransitionCandidate,
    TransitionParticipant,
)
from .housing_scenario_models import (
    HousingScenario,
    HousingScenarioRun,
    HousingScenarioDecision,
    HousingScenarioComparison,
)
from .asset_passport_models import (
    AssetItem,
    AssetLocationPeriod,
    AssetLifecycleEvent,
    AssetObservation,
    AssetAnalysisJob,
    AssetAnalysisSuggestion,
    AssetSharedSystem,
    AssetPatternCase,
    AssetWarrantyReference,
)
from .advanced_execution_models import (
    AdvancedExecution,
    AdvancedExecutionLeg,
    AdvancedExecutionConsent,
    AdvancedExecutionStep,
)

from .model_parts.policy_decisions import PolicyDecision, PolicyDecisionHead

from .model_parts.habitability import HabitabilityRestriction

from .model_parts.chargebacks import (
    RentalChargeback,
    ChargebackReplacementPayment,
    ChargebackRestoration,
)

from .company_saved_models import CompanySavedList, CompanySavedItem
