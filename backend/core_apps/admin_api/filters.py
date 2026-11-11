import django_filters
from django.db.models import Q, OuterRef, Subquery
from django.contrib.auth import get_user_model
from core_apps.admin_api.models import KYCSubmission, UserReport

User = get_user_model()


class AdminUserFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    role = django_filters.CharFilter(method="filter_role")
    status = django_filters.CharFilter(method="filter_status")
    kyc_status = django_filters.CharFilter(method="filter_kyc_status")

    class Meta:
        model = User
        fields = ["search", "role", "status", "kyc_status", "is_active", "is_verified"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
        )

    def filter_role(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        if value in ["مالك", "landlord", "owner"]:
            return queryset.filter(properties__isnull=False).distinct()
        elif value in ["مستأجر", "tenant"]:
            return queryset.filter(properties__isnull=True)
        return queryset

    def filter_status(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        if value in ["suspended", "موقوف"]:
            return queryset.filter(is_active=False)
        elif value in ["active", "نشط"]:
            return queryset.filter(is_active=True, is_verified=True)
        elif value in ["pending", "معلق", "قيد المراجعة"]:
            return queryset.filter(is_active=True, is_verified=False)
        return queryset

    def filter_kyc_status(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        if value in ["verified", "موثق"]:
            return queryset.filter(is_verified=True)
        statuses = {
            "pending": KYCSubmission.Status.PENDING,
            "قيد المراجعة": KYCSubmission.Status.PENDING,
            "rejected": KYCSubmission.Status.REJECTED,
            "مرفوض": KYCSubmission.Status.REJECTED,
        }
        if value in statuses:
            # Older databases can contain several non-superseded rows. Pick one
            # deterministic current submission instead of matching any history.
            current = KYCSubmission.objects.filter(
                profile__user_id=OuterRef("pk"),
                superseded_at__isnull=True,
            ).order_by("-created_at", "-pk")
            return queryset.annotate(
                _current_kyc_status=Subquery(current.values("status")[:1])
            ).filter(is_verified=False, _current_kyc_status=statuses[value])
        return queryset


class KYCSubmissionFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(method="filter_status")
    user_type = django_filters.CharFilter(method="filter_user_type")

    class Meta:
        model = KYCSubmission
        fields = ["status", "user_type"]

    def filter_status(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        return queryset.filter(status=value)

    def filter_user_type(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        if value in ["مالك", "landlord", "landlords"]:
            return queryset.filter(profile__user__properties__isnull=False).distinct()
        elif value in ["مستأجر", "tenant", "tenants"]:
            return queryset.filter(profile__user__properties__isnull=True)
        return queryset


class UserReportFilter(django_filters.FilterSet):
    id = django_filters.UUIDFilter(field_name="id")
    status = django_filters.CharFilter(method="filter_status")
    automation_level = django_filters.CharFilter(method="filter_automation_level")
    reason_type = django_filters.CharFilter(method="filter_reason_type")

    class Meta:
        model = UserReport
        fields = ["id", "status", "automation_level", "reason_type"]

    def filter_status(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        return queryset.filter(status=value)

    def filter_automation_level(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        return queryset.filter(automation_level=value)

    def filter_reason_type(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        return queryset.filter(reason_type=value)
