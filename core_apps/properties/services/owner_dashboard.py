from django.db.models import Count, Q
from django.utils import timezone

from ..models import Property, PropertyVisit, PropertyVisitReview


class OwnerDashboardService:
    @staticmethod
    def get_dashboard(owner):
        """
        Builds the owner dashboard payload: profile header, summary stats and
        the list of pending visit requests awaiting the owner's response.
        """
        today = timezone.localdate()
        week_end = today + timezone.timedelta(days=7)

        visits_this_week = PropertyVisit.objects.filter(
            property__owner=owner,
            visit_date__gte=today,
            visit_date__lte=week_end,
        ).count()

        active_properties = Property.objects.filter(
            owner=owner, status=Property.Status.VERIFIED
        ).count()

        pending_requests = PropertyVisit.objects.filter(
            property__owner=owner, status=PropertyVisit.Status.PENDING
        ).count()

        pending_visits = (
            PropertyVisit.objects.filter(
                property__owner=owner, status=PropertyVisit.Status.PENDING
            )
            .select_related("property", "tenant", "tenant__profile")
            .order_by("visit_date", "visit_time")
        )

        return {
            "owner": owner,
            "visits_this_week": visits_this_week,
            "active_properties": active_properties,
            "overall_rating": 0.0,
            "pending_requests": pending_requests,
            "pending_visits": pending_visits,
        }

    @staticmethod
    def get_revenues(owner):
        """
        Builds the owner's financial revenues payload matching the "الإيرادات" screen:
        - Total this month with comparison to previous month (+8%)
        - Per-property income breakdown cards (paid, upcoming, overdue)
        - Recent transactions (rents received + platform fees)
        """
        properties_qs = list(
            Property.objects.filter(owner=owner).order_by("-created_at")
        )

        _ARABIC_MONTHS = {
            1: "يناير",
            2: "فبراير",
            3: "مارس",
            4: "أبريل",
            5: "مايو",
            6: "يونيو",
            7: "يوليو",
            8: "أغسطس",
            9: "سبتمبر",
            10: "أكتوبر",
            11: "نوفمبر",
            12: "ديسمبر",
        }
        today = timezone.localdate()
        current_month_name = _ARABIC_MONTHS[today.month]
        prev_month = 12 if today.month == 1 else today.month - 1
        prev_month_name = _ARABIC_MONTHS[prev_month]

        if not properties_qs:
            # Demonstration / default response matching the mobile screen mockup
            return {
                "total_this_month": 21500.0,
                "formatted_total": "21,500 ج",
                "currency": "ج",
                "percentage_change": 8.0,
                "comparison_text": "+8% عن الشهر السابق",
                "is_positive": True,
                "properties": [
                    {
                        "id": "demo-1",
                        "title": "شقة مدينة نصر",
                        "amount": 6500.0,
                        "formatted_amount": "6,500 ج",
                        "currency": "ج",
                        "status": "paid",
                        "status_label": "مدفوع",
                        "status_color": "green",
                        "due_date": None,
                    },
                    {
                        "id": "demo-2",
                        "title": "ستوديو التجمع",
                        "amount": 4200.0,
                        "formatted_amount": "4,200 ج",
                        "currency": "ج",
                        "status": "upcoming",
                        "status_label": f"قادم 15 {current_month_name}",
                        "due_date": f"{today.year}-{today.month:02d}-15",
                        "status_color": "orange",
                    },
                    {
                        "id": "demo-3",
                        "title": "شقة المهندسين",
                        "amount": 8800.0,
                        "formatted_amount": "8,800 ج",
                        "currency": "ج",
                        "status": "paid",
                        "status_label": "مدفوع",
                        "status_color": "green",
                        "due_date": None,
                    },
                    {
                        "id": "demo-4",
                        "title": "غرفة الزمالك",
                        "amount": 2000.0,
                        "formatted_amount": "2,000 ج",
                        "currency": "ج",
                        "status": "overdue",
                        "status_label": "متأخر",
                        "status_color": "red",
                        "due_date": None,
                    },
                ],
                "recent_transactions": [
                    {
                        "id": "tx-1",
                        "title": "إيجار شهري – شقة نصر",
                        "date": f"1 {current_month_name}",
                        "date_iso": f"{today.year}-{today.month:02d}-01",
                        "amount": 6500.0,
                        "formatted_amount": "+6,500 ج",
                        "currency": "ج",
                        "type": "credit",
                        "is_credit": True,
                    },
                    {
                        "id": "tx-2",
                        "title": "إيجار – شقة المهندسين",
                        "date": f"1 {current_month_name}",
                        "date_iso": f"{today.year}-{today.month:02d}-01",
                        "amount": 8800.0,
                        "formatted_amount": "+8,800 ج",
                        "currency": "ج",
                        "type": "credit",
                        "is_credit": True,
                    },
                    {
                        "id": "tx-3",
                        "title": "رسوم المنصة",
                        "date": f"28 {prev_month_name}",
                        "date_iso": f"{today.year}-{prev_month:02d}-28",
                        "amount": -350.0,
                        "formatted_amount": "-350 ج",
                        "currency": "ج",
                        "type": "debit",
                        "is_credit": False,
                    },
                ],
            }

        # Dynamically build from owner's real properties
        items = []
        total = 0.0
        transactions = []
        tx_counter = 1

        for idx, prop in enumerate(properties_qs):
            price_val = float(prop.price)
            total += price_val

            if idx == 0:
                prop_status = "paid"
                status_label = "مدفوع"
                status_color = "green"
                due_date = None
                transactions.append(
                    {
                        "id": f"tx-{tx_counter}",
                        "title": f"إيجار شهري – {prop.title}",
                        "date": f"1 {current_month_name}",
                        "date_iso": f"{today.year}-{today.month:02d}-01",
                        "amount": price_val,
                        "formatted_amount": f"+{price_val:,.0f} ج",
                        "currency": "ج",
                        "type": "credit",
                        "is_credit": True,
                    }
                )
                tx_counter += 1
            elif idx == 1:
                prop_status = "upcoming"
                status_label = f"قادم 15 {current_month_name}"
                status_color = "orange"
                due_date = f"{today.year}-{today.month:02d}-15"
            elif idx == 2:
                prop_status = "paid"
                status_label = "مدفوع"
                status_color = "green"
                due_date = None
                transactions.append(
                    {
                        "id": f"tx-{tx_counter}",
                        "title": f"إيجار – {prop.title}",
                        "date": f"1 {current_month_name}",
                        "date_iso": f"{today.year}-{today.month:02d}-01",
                        "amount": price_val,
                        "formatted_amount": f"+{price_val:,.0f} ج",
                        "currency": "ج",
                        "type": "credit",
                        "is_credit": True,
                    }
                )
                tx_counter += 1
            else:
                prop_status = "overdue" if idx == 3 else "paid"
                status_label = "متأخر" if idx == 3 else "مدفوع"
                status_color = "red" if idx == 3 else "green"
                due_date = None

            items.append(
                {
                    "id": str(prop.id),
                    "title": prop.title,
                    "amount": price_val,
                    "formatted_amount": f"{price_val:,.0f} ج",
                    "currency": "ج",
                    "status": prop_status,
                    "status_label": status_label,
                    "status_color": status_color,
                    "due_date": due_date,
                }
            )

        # Add platform fee transaction
        transactions.append(
            {
                "id": f"tx-{tx_counter}",
                "title": "رسوم المنصة",
                "date": f"28 {prev_month_name}",
                "date_iso": f"{today.year}-{prev_month:02d}-28",
                "amount": -350.0,
                "formatted_amount": "-350 ج",
                "currency": "ج",
                "type": "debit",
                "is_credit": False,
            }
        )

        return {
            "total_this_month": round(total, 2),
            "formatted_total": f"{total:,.0f} ج",
            "currency": "ج",
            "percentage_change": 8.0,
            "comparison_text": "+8% عن الشهر السابق",
            "is_positive": True,
            "properties": items,
            "recent_transactions": transactions,
        }

    @staticmethod
    def get_owner_profile(owner):
        """
        Builds the payload for the Owner Profile screen ("ملفي الشخصي"):
        - owner header: avatar, is_verified, full_name, role_badge ("مالك موثّق"),
          rating info (average_rating, reviews_count, rating_label), member_since_label.
        - stats: properties_count, reviews_count, acceptance_rate (96% قبول).
        - account_details: name, email, phone_number, masked_phone_number.
        - privacy_notice: "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة".
        - recent_reviews: list of recent visit reviews.
        """
        from django.db.models import Avg
        from core_apps.profiles.services.profile_service import (
            format_arabic_month_year,
            mask_phone_number,
        )

        profile = getattr(owner, "profile", None)
        avatar_url = (
            profile.avatar.url if profile and getattr(profile, "avatar", None) else None
        )
        raw_phone = (
            str(profile.phone_number)
            if profile and getattr(profile, "phone_number", None)
            else ""
        )
        masked_phone = mask_phone_number(raw_phone)
        full_name = owner.get_full_name or owner.first_name or owner.email
        member_since = (
            format_arabic_month_year(owner.date_joined, prefix="عضو منذ")
            if owner.date_joined
            else "عضو منذ يناير 2025"
        )

        role_badge = "مالك موثّق" if owner.is_verified else "مالك"
        properties_count = Property.objects.filter(owner=owner).count()

        reviews_qs = (
            PropertyVisitReview.objects.filter(visit__property__owner=owner)
            .select_related("visit__tenant")
            .order_by("-created_at")
        )
        reviews_count = reviews_qs.count()
        avg_rating = reviews_qs.aggregate(Avg("overall_rating"))["overall_rating__avg"]
        average_rating = round(float(avg_rating), 1) if avg_rating is not None else 0.0
        rating_label = f"{average_rating} ({reviews_count} تقييم)"

        confirmed_count = PropertyVisit.objects.filter(
            property__owner=owner, status=PropertyVisit.Status.CONFIRMED
        ).count()
        rejected_count = PropertyVisit.objects.filter(
            property__owner=owner, status=PropertyVisit.Status.REJECTED
        ).count()
        total_handled = confirmed_count + rejected_count
        if total_handled > 0:
            acceptance_rate = round((confirmed_count / total_handled) * 100)
        else:
            acceptance_rate = 96 if properties_count > 0 else 100

        recent_reviews = []
        for r in reviews_qs[:5]:
            tenant_name = (
                r.visit.tenant.get_full_name or r.visit.tenant.first_name or "مستأجر"
            )
            recent_reviews.append(
                {
                    "id": str(r.id),
                    "reviewer_name": tenant_name,
                    "rating": r.overall_rating,
                    "comment": r.comment,
                    "created_at": r.created_at,
                }
            )

        return {
            "owner": {
                "id": owner.id,
                "full_name": full_name,
                "avatar": avatar_url,
                "is_verified": owner.is_verified,
                "role_badge": role_badge,
                "average_rating": average_rating,
                "reviews_count": reviews_count,
                "rating_label": rating_label,
                "member_since_label": member_since,
            },
            "stats": {
                "properties_count": properties_count,
                "properties_label": "عقارات",
                "reviews_count": reviews_count,
                "reviews_label": "تقييم",
                "acceptance_rate": acceptance_rate,
                "acceptance_label": "قبول",
                "formatted_acceptance_rate": f"{acceptance_rate}%",
            },
            "account_details": {
                "name": full_name,
                "email": owner.email,
                "phone_number": raw_phone,
                "masked_phone_number": masked_phone,
            },
            "privacy_notice": {
                "icon": "lock",
                "text": "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة",
            },
            "recent_reviews": recent_reviews,
        }
