"""Live erasure barriers from existing lifecycle states, without retention periods."""

from django.db.models import Q
from django.utils import timezone


def blockers(user):
    from core_apps.features import models as rental
    from core_apps.features.company_models import CompanyMembership, EmployeeAssignment
    from core_apps.features.company_contract_models import CompanyMandate
    from core_apps.profiles.models import Contract
    from core_apps.admin_api.models import StaffProfile
    from core_apps.properties.models import PropertyVisit

    lease_party = Q(owner=user) | Q(tenant=user)
    invoice_party = (
        Q(payer=user)
        | Q(beneficiary=user)
        | Q(lease__tenant=user)
        | Q(lease__owner=user)
    )
    leases = rental.Lease.objects.filter(lease_party)
    invoices = rental.RentInvoice.objects.filter(invoice_party)
    result = []

    def add(code, label, query):
        count = query.count()
        if count:
            result.append({"code": code, "label": label, "count": count})

    add(
        "lease",
        "عقد أو إشغال أو إغلاق مالي قائم / Existing lease, occupancy or financial closure",
        leases.filter(
            ~Q(status__in=["ended", "cancelled", "expired"])
            | Q(status="ended") & ~Q(financial_closure_status="closed")
            | Q(
                occupancy_status__in=[
                    "occupied",
                    "move_out_pending",
                    "handover_disputed",
                ]
            )
        ),
    )
    add(
        "legacy_contract",
        "عقد قائم / Active contract",
        Contract.objects.filter(
            Q(tenant=user) | Q(property__owner=user), status="active"
        ),
    )
    add(
        "invoice",
        "فاتورة غير مسوّاة / Unsettled invoice",
        invoices.exclude(status__in=["paid", "settled", "cancelled", "written_off"]),
    )
    add(
        "payment",
        "نتيجة دفع معلقة / Pending payment result",
        rental.PaymentAttempt.objects.filter(
            Q(payer=user) | Q(invoice__in=invoices),
            payment_status__in=["created", "pending", "authorized"],
        ),
    )
    add(
        "reservation",
        "حجز أو استعلام قائم / Reservation or reconciliation",
        rental.ReservationHold.objects.filter(
            Q(actor=user) | Q(property__owner=user),
            status__in=["active", "reconciliation_pending"],
        ),
    )
    add(
        "refund",
        "استرداد غير مكتمل / Unfinished refund",
        rental.RefundRequest.objects.filter(
            Q(requester=user) | Q(lease__in=leases)
        ).exclude(status__in=["succeeded", "rejected"]),
    )
    add(
        "payout",
        "تحويل غير مكتمل / Unfinished payout",
        rental.RentalPayout.objects.filter(owner=user).exclude(status="paid"),
    )
    add(
        "payable",
        "مستحق لم يُصرف / Unpaid receivable",
        rental.OwnerPayable.objects.filter(
            invoice__beneficiary=user, net_minor__gt=0
        ).exclude(payout_status__in=["succeeded", "cancelled"]),
    )
    add(
        "dispute",
        "نزاع قائم / Open dispute",
        rental.RentalDispute.objects.filter(lease__in=leases, status="open"),
    )
    add(
        "chargeback",
        "اعتراض مالي قائم / Open chargeback",
        rental.RentalChargeback.objects.filter(
            payment_attempt__invoice__in=invoices, outcome="open"
        ),
    )
    add(
        "settlement",
        "تسوية لم تكتمل / Unfinished settlement",
        rental.FinalSettlement.objects.filter(lease__in=leases).exclude(
            execution_status="executed"
        ),
    )
    add(
        "operation",
        "متابعة تشغيلية مفتوحة / Open operational follow-up",
        rental.RentalOperationalCase.objects.filter(
            Q(lease__in=leases)
            | Q(payment_attempt__invoice__in=invoices)
            | Q(opened_by=user)
        ).exclude(status="resolved"),
    )
    add(
        "visit",
        "معاينة معلقة / Pending viewing",
        PropertyVisit.objects.filter(
            Q(tenant=user) | Q(property__owner=user),
            status__in=["pending", "confirmed"],
        ).filter(Q(visit_date__isnull=True) | Q(visit_date__gte=timezone.localdate())),
    )
    add(
        "company_occupancy",
        "إشغال شركة قائم / Active company occupancy",
        EmployeeAssignment.objects.filter(employee=user).exclude(
            occupancy_status__in=["returned", "cancelled"]
        ),
    )
    add(
        "company_mandate",
        "تفويض شركة قائم / Active company mandate",
        CompanyMandate.objects.filter(
            membership__user=user, state="approved", valid_until__gt=timezone.now()
        ),
    )
    # A company's sole administrator must transfer their existing responsibility.
    sole_admin = []
    for member in CompanyMembership.objects.filter(
        user=user, is_active=True, is_admin=True
    ):
        if (
            not CompanyMembership.objects.filter(
                company=member.company, is_active=True, is_admin=True
            )
            .exclude(user=user)
            .exists()
        ):
            sole_admin.append(member.pk)
    add(
        "company_admin",
        "نقل مسؤولية إدارة الشركة / Transfer company administration",
        CompanyMembership.objects.filter(pk__in=sole_admin),
    )
    add(
        "staff_authority",
        "إغلاق صلاحية الموظف أولًا / Close staff authority first",
        StaffProfile.objects.filter(user=user, is_active=True),
    )
    if user.is_superuser or user.is_staff:
        result.append(
            {
                "code": "staff_account",
                "label": "نقل صلاحيات الإدارة أولًا / Transfer administrative authority first",
                "count": 1,
            }
        )
    return result
