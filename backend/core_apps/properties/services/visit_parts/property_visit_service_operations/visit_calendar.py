"""VisitCalendar operations owned by PropertyVisitService."""

from datetime import date
from ....models import PropertyVisit


class VisitCalendarMixin:
    @classmethod
    def get_owner_visit_calendar(
        cls, owner, year, month, selected_date=None, language="ar"
    ):
        """Build monthly visit indicators and the selected-day appointment cards."""
        is_en = str(language).lower().startswith("en")
        arabic_months = {
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
        english_months = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }
        month_start = date(year, month, 1)
        next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        visits = list(
            PropertyVisit.objects.filter(
                property__owner=owner,
                visit_date__gte=month_start,
                visit_date__lt=next_month,
                status__in=cls.BOOKED_STATUSES,
            )
            .select_related("tenant", "tenant__profile", "property")
            .order_by("visit_date", "visit_time")
        )
        counts = {}
        for visit in visits:
            counts[visit.visit_date] = counts.get(visit.visit_date, 0) + 1

        selected_visits = (
            [visit for visit in visits if visit.visit_date == selected_date]
            if selected_date
            else []
        )

        def _fmt_time(t):
            h = t.hour
            m = t.minute
            period = ("AM" if h < 12 else "PM") if is_en else ("ص" if h < 12 else "م")
            h12 = h % 12 or 12
            return f"{h12}:{m:02d} {period}"

        visits_payload = []
        for visit in selected_visits:
            tenant_name = visit.tenant.get_full_name
            first_letter = (
                tenant_name.strip()[0] if tenant_name and tenant_name.strip() else ""
            )
            profile = getattr(visit.tenant, "profile", None)
            avatar_url = (
                profile.avatar.url
                if profile and getattr(profile, "avatar", None)
                else None
            )
            if is_en:
                status_label = (
                    "Confirmed"
                    if visit.status == PropertyVisit.Status.CONFIRMED
                    else "Pending"
                )
            else:
                status_label = (
                    "مؤكدة"
                    if visit.status == PropertyVisit.Status.CONFIRMED
                    else "معلقة"
                )
            visits_payload.append(
                {
                    "id": str(visit.id),
                    "tenant": {
                        "id": str(visit.tenant.id),
                        "name": tenant_name,
                        "initial": first_letter,
                        "avatar": avatar_url,
                    },
                    "property": {
                        "id": str(visit.property.id),
                        "title": visit.property.title,
                    },
                    "visit_time": visit.visit_time.strftime("%H:%M:%S"),
                    "time_formatted": _fmt_time(visit.visit_time),
                    "status": visit.status,
                    "status_label": status_label,
                }
            )

        months_dict = english_months if is_en else arabic_months
        month_label = f"{months_dict.get(month, '')} {year}".strip()
        if selected_date:
            selected_date_label = (
                f"Visits on day {selected_date.day}"
                if is_en
                else f"زيارات يوم {selected_date.day}"
            )
        else:
            selected_date_label = None

        return {
            "year": year,
            "month": month,
            "month_label": month_label,
            "days": [
                {
                    "date": visit_date.isoformat(),
                    "day": visit_date.day,
                    "visit_count": count,
                }
                for visit_date, count in counts.items()
            ],
            "selected_date": selected_date.isoformat() if selected_date else None,
            "selected_date_label": selected_date_label,
            "visits": visits_payload,
        }

    @classmethod
    def _owner_slot_payload(cls, slot, visit):
        if visit:
            return cls._booked_slot_payload(visit, slot_id=slot.id)
        return {
            "id": str(slot.id),
            "time": slot.time.strftime("%H:%M:%S"),
            "is_enabled": slot.is_enabled,
            "state": "available" if slot.is_enabled else "disabled",
            "visit": None,
        }

    @classmethod
    def _booked_slot_payload(cls, visit, slot_id=None):
        return {
            "id": str(slot_id) if slot_id else None,
            "time": visit.visit_time.strftime("%H:%M:%S"),
            "is_enabled": True,
            "state": "booked",
            "visit": {
                "id": str(visit.id),
                "tenant_name": visit.tenant.get_full_name,
                "property_id": str(visit.property.id),
                "property_title": visit.property.title,
                "status": visit.status,
            },
        }
