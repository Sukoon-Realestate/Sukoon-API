from django.contrib import admin

from .models import (
    BoostCampaign,
    CheckoutSession,
    Lease,
    LeaseEligibleTenant,
    ListingSuggestion,
    RentInvoice,
    SearchAlert,
    SigningSession,
)

admin.site.register(
    [
        BoostCampaign,
        SearchAlert,
        ListingSuggestion,
        LeaseEligibleTenant,
        Lease,
        SigningSession,
        RentInvoice,
        CheckoutSession,
    ]
)
