"""Operational inspection is read-only; consequential changes use audited APIs."""

from django.contrib import admin
from .billing_admin import FinancialHistoryAdmin
from . import company_models as m
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
from core_apps.properties.models import (
    ResidentialComplex,
    ResidentialBuilding,
    PortfolioBatch,
    PortfolioBatchItem,
)


@admin.register(ResidentialBuilding)
class BuildingInspectionAdmin(FinancialHistoryAdmin):
    list_display = (
        "name",
        "code",
        "declared_units",
        "authority_status",
        "topology_revision",
    )
    list_filter = ("authority_status", "archived")
    search_fields = ("name", "code", "manager__email")


@admin.register(m.CompanyBookingItem)
class CompanyBookingInspectionAdmin(FinancialHistoryAdmin):
    list_display = ("id", "request", "status", "quote_expires_at", "hold", "lease")
    list_filter = ("status",)


@admin.register(PortfolioBatch)
class PortfolioBatchInspectionAdmin(FinancialHistoryAdmin):
    list_display = ("id", "owner", "complete", "revision", "updated_at")
    list_filter = ("complete",)


admin.site.register(
    [
        ResidentialComplex,
        PortfolioBatchItem,
        m.Company,
        m.CompanyMembership,
        m.CompanyInvitation,
        m.PortfolioOffer,
        m.CompanyHousingRequest,
        m.CompanyApproval,
        m.CompanyBudgetReservation,
        m.EmployeeAssignment,
        CompanyStaffRecord,
        CompanyAccountProvisioning,
        CompanyStaffBatch,
        CompanyStaffBatchRow,
        CompanyWorkContactProof,
        CompanyContractPreparation,
        CompanyPreparationConsent,
        CompanyTenancy,
        CompanyTenancyChange,
        CompanyMaintenanceScope,
    ],
    FinancialHistoryAdmin,
)
