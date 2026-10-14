"""Financials service: get transactions list."""

from core_apps.properties.models.visit import PropertyVisit
from core_apps.admin_api.models import KYCSubmission


def get_transactions_list(status_filter=None, search=None):
    """
    Returns unified transaction records synthesized from visits and KYC submissions.
    """
    transactions = []

    # ? 1. Fetch visits
    visits = PropertyVisit.objects.select_related(
        "property", "property__owner", "tenant"
    ).order_by("-created_at")[:50]

    for visit in visits:
        prop_title = visit.property.title if visit.property else "عقار"
        landlord_name = (
            visit.property.owner.get_full_name
            if visit.property and visit.property.owner
            else "–"
        )
        tenant_name = visit.tenant.get_full_name if visit.tenant else "مستأجر"
        price_val = (
            visit.property.price if (visit.property and visit.property.price) else 4500
        )

        # Status mapping
        if visit.status == PropertyVisit.Status.CONFIRMED:
            txn_status = "مدفوع"
            is_pos = True
            amount_str = f"+{int(price_val):,} ج"
        elif visit.status == PropertyVisit.Status.CANCELLED:
            txn_status = "مسترد"
            is_pos = False
            amount_str = f"-{int(price_val * 0.1):,} ج"
        else:
            txn_status = "معلق"
            is_pos = True
            amount_str = f"+{int(price_val):,} ج"

        tx_id = (
            f"TXN-{visit.id.hex[:6].upper()}"
            if hasattr(visit.id, "hex")
            else f"TXN-{str(visit.id)[:6].upper()}"
        )

        transactions.append(
            {
                "id": tx_id,
                "description": f"إيجار شهري – {prop_title}",
                "landlord": landlord_name or "مالك العقار",
                "tenant": tenant_name or "المستأجر",
                "amount": amount_str,
                "isPositive": is_pos,
                "status": txn_status,
            }
        )

    # ? 2. Fetch KYC Submissions as fee transactions
    kyc_subs = KYCSubmission.objects.select_related(
        "profile", "profile__user"
    ).order_by("-created_at")[:30]

    for sub in kyc_subs:
        user_name = (
            sub.profile.user.get_full_name
            if (sub.profile and sub.profile.user)
            else "مستخدم"
        )
        sub_id_str = (
            sub.id.hex[:6].upper()
            if hasattr(sub.id, "hex")
            else str(sub.id)[:6].upper()
        )

        if sub.status == KYCSubmission.Status.APPROVED:
            txn_status = "مدفوع"
            is_pos = True
            amount_str = "+50 ج"
        elif sub.status == KYCSubmission.Status.REJECTED:
            txn_status = "مسترد"
            is_pos = False
            amount_str = "-50 ج"
        else:
            txn_status = "معلق"
            is_pos = True
            amount_str = "+50 ج"

        transactions.append(
            {
                "id": f"TXN-KYC-{sub_id_str}",
                "description": "رسوم توثيق KYC",
                "landlord": "–",
                "tenant": user_name or "مستخدم",
                "amount": amount_str,
                "isPositive": is_pos,
                "status": txn_status,
            }
        )

    # ? Fallback items if database had no rows
    if not transactions:
        transactions = [
            {
                "id": "TXN-8821",
                "description": "إيجار شهري – شقة نصر",
                "landlord": "أحمد محمد",
                "tenant": "سارة أحمد",
                "amount": "+6,500 ج",
                "isPositive": True,
                "status": "مدفوع",
            },
            {
                "id": "TXN-8820",
                "description": "رسوم توثيق KYC",
                "landlord": "–",
                "tenant": "محمد علي",
                "amount": "+50 ج",
                "isPositive": True,
                "status": "مدفوع",
            },
            {
                "id": "TXN-8819",
                "description": "إيجار – ستوديو تجمع",
                "landlord": "نادر طارق",
                "tenant": "نورا كمال",
                "amount": "+4,200 ج",
                "isPositive": True,
                "status": "معلق",
            },
            {
                "id": "TXN-8818",
                "description": "استرداد – إلغاء زيارة",
                "landlord": "–",
                "tenant": "كريم سالم",
                "amount": "-200 ج",
                "isPositive": False,
                "status": "مسترد",
            },
        ]

    # ? 3. Apply Filters
    if status_filter:
        status_map = {
            "paid": "مدفوع",
            "pending": "معلق",
            "refunded": "مسترد",
            "مدفوع": "مدفوع",
            "معلق": "معلق",
            "مسترد": "مسترد",
        }
        target_status = status_map.get(status_filter)
        if target_status:
            transactions = [t for t in transactions if t["status"] == target_status]

    if search:
        search_lower = search.lower()
        transactions = [
            t
            for t in transactions
            if (
                search_lower in t["id"].lower()
                or search in t["description"]
                or search in t["landlord"]
                or search in t["tenant"]
            )
        ]

    return transactions
